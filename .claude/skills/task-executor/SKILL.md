---
name: task-executor
description: >
  Execute pending tasks from the queue. Retrieves queued tasks from activity.db,
  parses the goal type, executes the work, and marks tasks complete.
  Use when the user says "run task", "execute pending tasks", "check queued tasks",
  "run my Telegram tasks", or references a specific task by name or ID.
user-invokable: true
argument-hint: "<task-name-or-id> | list | search <keywords>"
---

# Skill: Task Executor

Pick up queued tasks from `data/activity.db` and execute them.

Tasks are queued by the Telegram bot when the user sends workflow trigger messages (e.g., "Research AI trends"). This skill describes how to retrieve, execute, and close those tasks.

## Tools Required

- `tools/tasks/task_executor.py` — Read, update, and complete tasks in the queue

## Process

### Step 1: Retrieve the Task

```bash
# By name/keywords (preferred — human-friendly):
python3 tools/tasks/task_executor.py --get "research AI trends"

# By task ID (also works):
python3 tools/tasks/task_executor.py --get b4a914a0

# Search for matching tasks:
python3 tools/tasks/task_executor.py --search "AI trends"

# If no specific task given — list all pending:
python3 tools/tasks/task_executor.py --list
```

The `--get` flag tries ID lookup first, then falls back to keyword search automatically.

If multiple tasks are pending and no specific one was given, show the list and ask which one to run (or offer to run all sequentially).

### Step 2: Mark as In Progress

```bash
python3 tools/tasks/task_executor.py --start "research AI trends"
```

### Step 3: Parse the Request

The task `request` field has the format: `[GOAL_TYPE] original message`

- Extract the **goal type** (e.g., RESEARCH, ANALYZE, CONTENT, LEAD_GEN, BUILD_APP, SUMMARIZE)
- Extract the **original message** (the user's actual request from Telegram)

### Step 4: Execute Based on Goal Type

| Goal Type | Action |
|-----------|--------|
| RESEARCH | Search the web, compile findings, save a summary to memory |
| ANALYZE | Load the subject, apply analysis, generate insights, save report |
| CONTENT | Define audience/goal, outline, draft, save to memory or file |
| LEAD_GEN | Define target, search sources, qualify, export to data/ |
| BUILD_APP | Use the `build-process` skill for structured app building |
| SUMMARIZE | Load content, extract key points, save summary to memory |

For each goal type:
1. Check `.claude/skills/` for a matching skill
2. If a specific skill exists, invoke it
3. If not, use general reasoning based on the goal type and the user's request

### Step 5: Save Output

- Save results to the appropriate location (memory.db, files, etc.)
- Use the `memory` skill if saving to persistent memory

### Step 6: Mark Task Complete

```bash
python3 tools/tasks/task_executor.py --complete "research AI trends" --summary "Brief description of what was done"
```

If the task failed:
```bash
python3 tools/tasks/task_executor.py --fail "research AI trends" --summary "What went wrong"
```

## Edge Cases

- **Task not found**: Tell the user and offer to list pending tasks
- **Task already completed**: Inform the user, show the summary
- **Multiple pending tasks**: List them and ask which to execute (or run all)
- **No pending tasks**: Tell the user the queue is clear

## Context Dependencies

- `memory` skill — for saving task results
- `build-process` skill — for BUILD_APP goal type
- `tools/manifest.md` — for available tools
