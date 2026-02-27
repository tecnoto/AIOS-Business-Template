"""
Invoke Claude Code CLI as a subprocess for workflow execution

Responsibilities:
- Find the claude CLI binary (PATH, common install locations)
- Execute workflow prompts via `claude -p` from the project root
- Timeout enforcement (default 300 seconds)
- Truncate output for Telegram's 4096 char limit
- Fallback: queue task in activity.db if CLI not found

Usage (imported by telegram_handler.py):
    from tools.messaging.workflow_invoker import invoke_workflow
    result = invoke_workflow("Research AI trends in 2026")
"""

import os
import subprocess
import shutil
import json
import yaml
from pathlib import Path
from typing import Optional
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_config() -> dict:
    """Load workflow config from args/messaging.yaml."""
    config_path = PROJECT_ROOT / 'args' / 'messaging.yaml'
    if not config_path.exists():
        return {}
    with open(config_path, 'r') as f:
        raw = yaml.safe_load(f)
    return raw.get('messaging', {}).get('workflow', {})


def _find_claude_binary() -> Optional[str]:
    """Find the claude CLI binary.

    Checks:
    1. PATH via shutil.which
    2. Common npm global install locations
    3. Local node_modules/.bin

    Returns:
        str: Path to claude binary, or None if not found
    """
    # Check PATH first
    found = shutil.which('claude')
    if found:
        return found

    # Common install locations
    home = Path.home()
    candidates = [
        home / '.npm-global' / 'bin' / 'claude',
        home / '.local' / 'bin' / 'claude',
        Path('/usr/local/bin/claude'),
        Path('/opt/homebrew/bin/claude'),
        # nvm installs
        home / '.nvm' / 'versions' / 'node',
    ]

    for candidate in candidates:
        if candidate.is_dir():
            # For nvm — search subdirectories
            for node_dir in sorted(candidate.iterdir(), reverse=True):
                bin_path = node_dir / 'bin' / 'claude'
                if bin_path.exists():
                    return str(bin_path)
        elif candidate.exists():
            return str(candidate)

    # Check local node_modules
    local_bin = PROJECT_ROOT / 'node_modules' / '.bin' / 'claude'
    if local_bin.exists():
        return str(local_bin)

    return None


def _queue_fallback_task(description: str) -> Optional[str]:
    """Queue a task in activity.db when CLI is unavailable.

    Args:
        description: The workflow description

    Returns:
        str: Task ID if queued successfully
    """
    import sqlite3
    import uuid

    activity_db = os.getenv('ACTIVITY_DB_PATH', str(PROJECT_ROOT / 'data' / 'activity.db'))
    task_id = str(uuid.uuid4())

    try:
        conn = sqlite3.connect(activity_db)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (id, source, request, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            task_id,
            'telegram_workflow',
            f"[WORKFLOW] {description}",
            'pending',
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        return task_id
    except Exception as e:
        print(f"Error queuing fallback task: {e}")
        return None


def invoke_workflow(description: str) -> Optional[str]:
    """Execute a workflow via Claude Code CLI.

    Runs `claude -p <prompt>` from the project root directory.
    The prompt instructs Claude Code to read CLAUDE.md, check goals/,
    and execute the described workflow.

    Args:
        description: Natural language description of the workflow

    Returns:
        str: Workflow result text, or None if queued as fallback
    """
    config = _load_config()
    timeout = config.get('timeout_seconds', 300)
    max_response = config.get('max_response_length', 3800)
    fallback = config.get('fallback_to_queue', True)

    claude_bin = _find_claude_binary()

    if not claude_bin:
        if fallback:
            task_id = _queue_fallback_task(description)
            if task_id:
                print(f"Claude CLI not found. Task queued: {task_id[:8]}")
                return None
        print("Claude CLI not found and fallback disabled.")
        return None

    # Build the prompt for Claude Code
    prompt = (
        f"Read CLAUDE.md for system instructions. "
        f"Check goals/manifest.md for relevant workflows. "
        f"Execute the following task and return a concise summary of what was done:\n\n"
        f"{description}"
    )

    try:
        result = subprocess.run(
            [claude_bin, '-p', prompt, '--output-format', 'text'],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, 'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY', '')}
        )

        output = result.stdout.strip()

        if not output and result.stderr:
            print(f"Claude CLI stderr: {result.stderr[:500]}")
            output = "Workflow executed but produced no output."

        # Truncate for Telegram
        if len(output) > max_response:
            output = output[:max_response - 3] + "..."

        return output

    except subprocess.TimeoutExpired:
        print(f"Workflow timed out after {timeout}s: {description[:80]}")
        return f"Workflow timed out after {timeout} seconds. The task may still be running."

    except FileNotFoundError:
        print(f"Claude binary not executable: {claude_bin}")
        if fallback:
            task_id = _queue_fallback_task(description)
            if task_id:
                return None
        return None

    except Exception as e:
        print(f"Workflow invocation error: {e}")
        return f"Error executing workflow: {str(e)}"
