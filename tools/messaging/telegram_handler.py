"""
Core Telegram message handler — Claude as router

Responsibilities:
- Security checks (whitelist, rate limit, blocked patterns)
- Slash command fast-path (delegates to command_handler)
- Persistent conversation history (message_db)
- Context injection: MEMORY.md + hybrid search + recent messages
- Claude API call with full context
- Workflow detection and invocation
- Confirmation gates for destructive operations
- Fact extraction from user messages

This file replaces the old message_router → intent_classifier → handler chain
with a single handler that delegates routing entirely to Claude.
"""

import os
import sys
import re
import time
import yaml
from pathlib import Path
from typing import Optional

import anthropic

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.messaging.security import run_all_checks, needs_confirmation
from tools.messaging.message_db import save_message, format_conversation_for_prompt
from tools.messaging.ollama_client import call_ollama, is_ollama_available
from tools.messaging.escalation import should_escalate, response_requests_escalation
from tools.telegram.log_interaction import log_telegram_event

# Lazy imports for memory search (heavy dependencies)
_hybrid_search = None

# Path to mem0 scripts installed by setup_memory.py
MEM0_SCRIPTS = PROJECT_ROOT / '.claude' / 'skills' / 'memory' / 'scripts'


def _get_hybrid_search():
    global _hybrid_search
    if _hybrid_search is None:
        from tools.memory.hybrid_search import hybrid_search
        _hybrid_search = hybrid_search
    return _hybrid_search


import json as _json
import subprocess as _subprocess

# mem0 requires Python 3.11+ (mem0ai dependency)
# The bot daemon runs on system Python 3.9, so we call mem0 scripts as subprocesses.
PYTHON311 = '/opt/homebrew/bin/python3.11'


def _load_messaging_config() -> dict:
    """Load messaging config from args/messaging.yaml."""
    config_path = PROJECT_ROOT / 'args' / 'messaging.yaml'
    if not config_path.exists():
        return {}
    with open(config_path, 'r') as f:
        raw = yaml.safe_load(f)
    return raw.get('messaging', {})


def _load_memory_md() -> str:
    """Load MEMORY.md contents for context injection."""
    config = _load_messaging_config()
    ctx = config.get('context', {})

    if not ctx.get('load_memory_md', True):
        return ""

    memory_path = PROJECT_ROOT / ctx.get('memory_md_path', 'memory/MEMORY.md')
    if not memory_path.exists():
        return ""

    try:
        return memory_path.read_text().strip()
    except Exception:
        return ""


def _get_relevant_memories(message: str, max_results: int = 5) -> str:
    """Run hybrid search for memories relevant to this message."""
    try:
        search = _get_hybrid_search()
        results = search(message, top_k=max_results)
        if not results:
            return ""

        lines = []
        for r in results:
            score = r.get('semantic_score', r.get('rrf_score', '?'))
            lines.append(f"- [{r.get('entry_type', 'note')}] {r['content']}")
        return "\n".join(lines)
    except Exception as e:
        print(f"Memory search error: {e}")
        return ""


def _get_pinecone_memories(message: str, max_results: int = 5) -> str:
    """Search mem0/Pinecone for long-term memories. Calls Python 3.11 subprocess."""
    search_script = MEM0_SCRIPTS / 'mem0_search.py'
    if not search_script.exists():
        return ""

    try:
        result = _subprocess.run(
            [PYTHON311, str(search_script), '--query', message, '--limit', str(max_results)],
            capture_output=True, text=True, timeout=15,
            cwd=str(PROJECT_ROOT)
        )
        if result.returncode != 0:
            print(f"[mem0] Search failed: {result.stderr[:200]}")
            return ""

        data = _json.loads(result.stdout)

        memories = []
        results_list = data.get("results", []) if isinstance(data, dict) else data
        for item in results_list:
            if isinstance(item, dict):
                mem = item.get("memory", "")
                score = item.get("score", 0)
                if mem and score > 0.2:  # Filter low-relevance noise
                    memories.append(f"- {mem}")

        return "\n".join(memories) if memories else ""
    except _subprocess.TimeoutExpired:
        print("[mem0] Search timed out (15s)")
        return ""
    except Exception as e:
        print(f"[mem0] Pinecone search error: {e}")
        return ""


def _capture_to_mem0(user_message: str, bot_response: str):
    """Feed conversation into mem0 for fact extraction. Fire-and-forget subprocess."""
    add_script = MEM0_SCRIPTS / 'mem0_add.py'
    if not add_script.exists():
        return

    try:
        messages = _json.dumps([
            {"role": "user", "content": user_message[:1500]},
            {"role": "assistant", "content": bot_response[:1500]},
        ])
        # Fire-and-forget: don't wait for completion, don't block the response
        _subprocess.Popen(
            [PYTHON311, str(add_script), '--messages', messages,
             '--metadata', '{"source": "telegram"}'],
            stdout=_subprocess.DEVNULL,
            stderr=_subprocess.DEVNULL,
            cwd=str(PROJECT_ROOT)
        )
        print(f"[mem0] Capture launched (async)")
    except Exception as e:
        print(f"[mem0] Capture launch error (non-fatal): {e}")


def _build_system_prompt(user_id: str, message: str) -> str:
    """Build the full system prompt with injected context."""
    config = _load_messaging_config()
    ctx_config = config.get('context', {})
    max_history = ctx_config.get('max_conversation_history', 20)
    max_memory = ctx_config.get('max_memory_results', 5)

    # Load MEMORY.md
    memory_md = _load_memory_md()

    # Get relevant memories via hybrid search
    relevant_memories = _get_relevant_memories(message, max_results=max_memory)

    # Get recent conversation history
    conversation = format_conversation_for_prompt(user_id, limit=max_history)

    # Load agent name from config
    agent_name = "Assistant"
    setup_config_path = PROJECT_ROOT / "setup_config.yaml"
    if setup_config_path.exists():
        try:
            with open(setup_config_path) as f:
                setup_cfg = yaml.safe_load(f)
                if setup_cfg and isinstance(setup_cfg, dict):
                    agent_name = setup_cfg.get("agent_name", "Assistant")
        except Exception:
            pass

    # Build system prompt
    sections = [
        f"You are {agent_name}, a personal AI assistant communicating via Telegram.",
        "Be concise and direct. Telegram messages should be short and actionable.",
        "Use plain text — no markdown formatting (Telegram renders it poorly in plain mode).",
        "Keep responses under 3800 characters.",
    ]

    if memory_md:
        sections.append(f"\n## Persistent Memory (MEMORY.md)\n{memory_md}")

    if relevant_memories:
        sections.append(f"\n## Relevant Memories (Local)\n{relevant_memories}")

    # Pinecone long-term memories via mem0
    pinecone_memories = _get_pinecone_memories(message, max_results=max_memory)
    if pinecone_memories:
        sections.append(f"\n## Long-Term Memory (Pinecone)\n{pinecone_memories}")

    if conversation:
        sections.append(f"\n## Recent Conversation\n{conversation}")

    sections.append(
        "\n## Special Instructions\n"
        "- If the user asks you to perform a multi-step task (research, analysis, content creation, "
        "lead generation, app building, summarization), respond ONLY with a marker line:\n"
        "  [WORKFLOW: brief description of the task]\n"
        "  followed by a short confirmation message.\n"
        "- For simple questions, greetings, or conversation, just respond normally.\n"
        "- If the user references something from memory or past conversation, use that context.\n"
        "- Never fabricate facts. If you don't know something, say so."
    )

    return "\n".join(sections)


def _is_slash_command(message: str) -> bool:
    """Check if message is a slash command."""
    return message.startswith('/')


def _handle_slash_command(message: str) -> dict:
    """Delegate slash commands to command_handler."""
    from tools.telegram.handlers.command_handler import handle_command

    # Parse command and args
    parts = message.split(' ', 1)
    command = parts[0].lstrip('/').lower()
    args = parts[1] if len(parts) > 1 else ''

    result = handle_command(command, args)
    return {
        'response': result.get('response', 'Command processed.'),
        'intent': f'command_{command}',
        'handler': 'command_handler'
    }


def _call_claude(system_prompt: str, user_message: str) -> str:
    """Call Claude API with the assembled prompt. Retries on 529 overloaded."""
    config = _load_messaging_config()
    model_config = config.get('model', {})
    model = model_config.get('conversation', 'claude-sonnet-4-20250514')
    max_tokens = model_config.get('max_tokens', 1024)

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return "Error: ANTHROPIC_API_KEY not configured."

    client = anthropic.Anthropic(api_key=api_key)

    # Retry up to 2 times on overloaded (529) errors with backoff
    for attempt in range(3):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            return response.content[0].text
        except anthropic.OverloadedError:
            if attempt < 2:
                wait = (attempt + 1) * 5  # 5s, 10s
                print(f"Claude API overloaded (529), retrying in {wait}s (attempt {attempt + 1}/3)")
                time.sleep(wait)
            else:
                print(f"Claude API overloaded after 3 attempts")
                return "Claude is currently overloaded. Try again in a few minutes."
        except anthropic.APIError as e:
            print(f"Claude API error: {e}")
            return "I encountered an API error. Try again shortly."
        except Exception as e:
            print(f"Unexpected error calling Claude: {e}")
            return "Something went wrong processing your message. Try again."


def _call_llm(system_prompt: str, user_message: str) -> tuple:
    """
    Route to local Ollama or Claude API based on escalation rules.

    Flow:
        1. Check escalation rules (keywords, length, explicit triggers)
        2. If no escalation needed and Ollama is available → use Ollama
        3. If Ollama self-escalates ([ESCALATE] marker) → fall through to Claude
        4. If Ollama fails → fall through to Claude
        5. If Claude fails → return fallback message

    Returns:
        (response_text: str, source: str) where source is 'ollama', 'claude', or 'fallback'
    """
    # Check if message should escalate directly to Claude
    escalate, reason = should_escalate(user_message)

    if not escalate and is_ollama_available():
        # Add self-assessment instruction for local model
        local_prompt = system_prompt + (
            "\n\n## Self-Assessment\n"
            "If you are not confident you can answer this accurately, "
            "or the question requires deep analysis, code generation, or multi-step reasoning, "
            "respond with ONLY: [ESCALATE] followed by a one-line reason.\n"
            "Otherwise, answer normally."
        )
        response = call_ollama(local_prompt, user_message)

        if response and not response_requests_escalation(response):
            print(f"[LLM] Handled locally by Ollama")
            return response, 'ollama'

        if response and response_requests_escalation(response):
            print(f"[LLM] Ollama self-escalated to Claude")
            # Fall through to Claude
        else:
            print(f"[LLM] Ollama failed, escalating to Claude")
    elif escalate:
        print(f"[LLM] Escalating to Claude: {reason}")

    # Claude API as escalation/fallback
    response = _call_claude(system_prompt, user_message)
    if response and not response.startswith("Error:") and not response.startswith("Something went wrong"):
        return response, 'claude'

    # Last resort: static fallback
    return "I'm having trouble processing your message right now. Try again in a moment.", 'fallback'


def _extract_workflow_marker(response: str) -> Optional[str]:
    """Extract [WORKFLOW: ...] marker from Claude's response if present."""
    match = re.search(r'\[WORKFLOW:\s*(.+?)\]', response)
    if match:
        return match.group(1).strip()
    return None


def _truncate_response(text: str, max_length: int = 3800) -> str:
    """Truncate response to fit Telegram's 4096 char limit with margin."""
    config = _load_messaging_config()
    max_len = config.get('workflow', {}).get('max_response_length', max_length)

    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


# Pending confirmation tracking: {user_id: {'message': str, 'timestamp': float}}
_pending_confirmations = {}


def handle_message(user_id: str, message: str) -> dict:
    """
    Process an incoming Telegram message through the full pipeline.

    Flow:
        Security checks → Slash command fast-path → Save inbound →
        Load context → Call Claude → Detect workflow → Save outbound →
        Return response

    Args:
        user_id: Telegram user ID as string
        message: The message text

    Returns:
        dict with keys: response, intent, handler
    """
    start_time = time.time()

    # --- Check for pending confirmation ---
    if user_id in _pending_confirmations:
        pending = _pending_confirmations[user_id]
        # Expire after 60 seconds
        if time.time() - pending['timestamp'] < 60:
            if message.strip().lower() in ('yes', 'y', 'confirm'):
                del _pending_confirmations[user_id]
                # Re-process the original message, bypassing confirmation
                original = pending['message']
                return _process_message(user_id, original, skip_confirmation=True)
            else:
                del _pending_confirmations[user_id]
                return {
                    'response': 'Action cancelled.',
                    'intent': 'confirmation_cancelled',
                    'handler': 'telegram_handler'
                }
        else:
            del _pending_confirmations[user_id]

    # --- Security checks ---
    passed, reason = run_all_checks(user_id, message)
    if not passed:
        if reason == "unauthorized":
            # Silent rejection for unauthorized users
            return {
                'response': None,
                'intent': 'unauthorized',
                'handler': 'security'
            }
        elif reason == "blocked":
            # Silent rejection for blocked patterns
            return {
                'response': None,
                'intent': 'blocked_pattern',
                'handler': 'security'
            }
        else:
            # Rate limit — send the cooldown message
            return {
                'response': reason,
                'intent': 'rate_limited',
                'handler': 'security'
            }

    return _process_message(user_id, message, skip_confirmation=False)


def _process_message(user_id: str, message: str, skip_confirmation: bool = False) -> dict:
    """Internal message processing after security checks pass."""

    # --- Slash command fast-path ---
    if _is_slash_command(message):
        result = _handle_slash_command(message)
        # Save both directions to message_db
        save_message(user_id, 'inbound', message, intent=result.get('intent'))
        save_message(user_id, 'outbound', result['response'])
        return result

    # --- Confirmation gate for destructive operations ---
    if not skip_confirmation and needs_confirmation(message):
        _pending_confirmations[user_id] = {
            'message': message,
            'timestamp': time.time()
        }
        confirm_response = (
            f"This looks like a destructive operation.\n\n"
            f"Your message: \"{message[:100]}\"\n\n"
            f"Reply 'yes' to confirm or anything else to cancel."
        )
        save_message(user_id, 'inbound', message, intent='confirmation_required')
        save_message(user_id, 'outbound', confirm_response)
        return {
            'response': confirm_response,
            'intent': 'confirmation_required',
            'handler': 'telegram_handler'
        }

    # --- Save inbound message ---
    save_message(user_id, 'inbound', message)

    # --- Build context and call LLM (Ollama primary, Claude escalation) ---
    system_prompt = _build_system_prompt(user_id, message)
    response_text, llm_source = _call_llm(system_prompt, message)

    # --- Check for workflow marker ---
    workflow_desc = _extract_workflow_marker(response_text)
    intent = 'conversation'
    handler = llm_source

    if workflow_desc:
        # Only trust workflow markers from Claude — Ollama (3b) generates false positives
        # on casual messages like "there seems to be a glitch"
        if llm_source == 'claude':
            intent = 'workflow_trigger'
            handler = 'workflow_invoker'
            # Try to invoke workflow via Claude Code CLI
            try:
                from tools.messaging.workflow_invoker import invoke_workflow
                workflow_result = invoke_workflow(workflow_desc)
                if workflow_result:
                    clean_response = re.sub(r'\[WORKFLOW:\s*.+?\]', '', response_text).strip()
                    response_text = f"{clean_response}\n\n--- Workflow Result ---\n{workflow_result}"
            except ImportError:
                pass
            except Exception as e:
                print(f"Workflow invocation error: {e}")
        else:
            # Strip false workflow markers from Ollama responses
            print(f"[LLM] Ignoring workflow marker from {llm_source}: {workflow_desc[:60]}")
            response_text = re.sub(r'\[WORKFLOW:\s*.+?\]\s*', '', response_text).strip()

    # --- Truncate for Telegram ---
    response_text = _truncate_response(response_text)

    # --- Save outbound message ---
    save_message(user_id, 'outbound', response_text, intent=intent,
                 metadata={'llm_source': llm_source})

    # --- Capture to mem0/Pinecone for long-term memory ---
    # Best-effort: failures don't block the response
    try:
        _capture_to_mem0(message, response_text)
    except Exception as e:
        print(f"[mem0] Auto-capture error (non-fatal): {e}")

    return {
        'response': response_text,
        'intent': intent,
        'handler': handler
    }
