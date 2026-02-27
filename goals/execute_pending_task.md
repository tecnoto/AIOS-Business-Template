# Execute Pending Task

## Objective

Pick up a queued task from `data/activity.db` and execute it using the GOTCHA framework.

Tasks are queued by the Telegram bot when the user sends workflow trigger messages (e.g., "Research AI trends"). This goal describes how to retrieve, execute, and close those tasks.

## When This Goal Applies

The user says something like:
- "Run the research AI trends task"
- "Run the research task"
- "Execute pending tasks"
- "Check for queued tasks"
- "Run my Telegram tasks"

## Inputs

- **Task name or keywords** (preferred): Natural language like "research AI trends" or "content marketing draft"
- **Task ID** (also works): Full UUID or 8-character prefix

If neither is provided, list all pending tasks and ask which one to run.

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
# Works with keywords or ID:
python3 tools/tasks/task_executor.py --start "research AI trends"
```

### Step 3: Parse the Request

The task `request` field has the format: `[GOAL_TYPE] original message`

- Extract the **goal type** (e.g., RESEARCH, ANALYZE, CONTENT, LEAD_GEN, BUILD_APP, SUMMARIZE)
- Extract the **original message** (the user's actual request from Telegram)

### Step 4: Execute Based on Goal Type

Use the goal type to determine what to do:

| Goal Type | Action |
|-----------|--------|
| RESEARCH | Search the web, compile findings, save a summary to memory |
| ANALYZE | Load the subject, apply analysis, generate insights, save report |
| CONTENT | Define audience/goal, outline, draft, save to memory or file |
| LEAD_GEN | Define target, search sources, qualify, export to data/ |
| BUILD_APP | Architect, design, implement using GOTCHA framework |
| SUMMARIZE | Load content, extract key points, save summary to memory |

For each goal type:
1. Check `goals/` for a dedicated goal file (e.g., `goals/research_lead.md`)
2. If a specific goal exists, follow it
3. If not, use general reasoning based on the goal type and the user's request

### Step 5: Save Output

- Save results to the appropriate location (memory.db, files, etc.)
- Use `tools/memory/memory_write.py` if saving to memory

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

## Expected Output

- Task executed according to its goal type
- Results saved to memory or files
- Task marked as completed in activity.db with a summary
- User can verify via `/status` in Telegram
