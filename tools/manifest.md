# Tools Manifest

> Master index of all available tools organized by workflow.
> Always check this before creating new scripts.

## Memory Tools

- `memory/memory_db.py` — SQLite CRUD for memory_entries table with embedding storage and keyword search
- `memory/embed_memory.py` — Text embedding via fastembed (BAAI/bge-small-en-v1.5, 384 dimensions)
- `memory/semantic_search.py` — Vector similarity search over embedded memory entries
- `memory/hybrid_search.py` — Combined keyword + semantic search using Reciprocal Rank Fusion

## Messaging Tools

- `messaging/telegram_handler.py` — Core message handler: security, context injection, LLM routing, memory
- `messaging/message_db.py` — Persistent conversation history in activity.db
- `messaging/security.py` — Rate limiting, blocked pattern detection, confirmation gates
- `messaging/workflow_invoker.py` — Invokes Claude Code CLI as subprocess for workflow execution
- `messaging/ollama_client.py` — Local LLM calls via Ollama HTTP API
- `messaging/escalation.py` — Escalation rules: keyword-based, length-based, self-assessment detection

## Task Management Tools

- `tasks/task_executor.py` — Read, update, and complete queued tasks from activity.db

## Lead Generation Tools

*(Add lead gen tools here as you build them)*

---

## Skills (Reusable Patterns)

See `.claude/skills/` for documented methodologies with scripts:

- `memory/` — Persistent memory management (mem0 + Pinecone)
- `telegram/` — Telegram bot orchestration
- `dashboard/` — Agent activity dashboard generation
- `_example-brand/` — Sample brand skill (image generation pattern)

---

**Required**: When you create a new tool, add it here with a one-sentence description.
