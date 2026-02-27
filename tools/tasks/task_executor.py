"""
Execute pending tasks from the task queue

Responsibilities:
- List pending tasks from activity.db
- Fetch a specific task by ID (full or prefix)
- Mark tasks as in_progress, completed, or failed
- Provide task details for the orchestration layer to act on

Usage:
    python tools/tasks/task_executor.py --list                # List pending tasks
    python tools/tasks/task_executor.py --get <task_id>       # Get task by ID
    python tools/tasks/task_executor.py --search "AI trends"  # Find task by keywords
    python tools/tasks/task_executor.py --start <task_id>     # Mark as in_progress
    python tools/tasks/task_executor.py --complete <task_id> --summary "Done"  # Mark completed
    python tools/tasks/task_executor.py --fail <task_id> --summary "Error..."  # Mark failed
"""

import sqlite3
import os
import sys
import argparse
import json
from datetime import datetime
from pathlib import Path

# Resolve project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ACTIVITY_DB = os.getenv('ACTIVITY_DB_PATH', str(PROJECT_ROOT / 'data' / 'activity.db'))


def get_connection():
    """Get database connection"""
    return sqlite3.connect(ACTIVITY_DB)


def list_pending_tasks(source=None, limit=10):
    """
    List pending tasks from the queue

    Args:
        source: Filter by source (e.g. 'telegram'). None = all sources.
        limit: Max number of tasks to return.

    Returns:
        list[dict]: Pending tasks
    """
    conn = get_connection()
    cursor = conn.cursor()

    if source:
        cursor.execute('''
            SELECT id, source, request, status, created_at
            FROM tasks
            WHERE status = 'pending' AND source = ?
            ORDER BY created_at ASC
            LIMIT ?
        ''', (source, limit))
    else:
        cursor.execute('''
            SELECT id, source, request, status, created_at
            FROM tasks
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT ?
        ''', (limit,))

    rows = cursor.fetchall()
    conn.close()

    tasks = []
    for row in rows:
        tasks.append({
            'id': row[0],
            'source': row[1],
            'request': row[2],
            'status': row[3],
            'created_at': row[4],
        })

    return tasks


def get_task(task_id_prefix):
    """
    Fetch a task by full or partial ID

    Args:
        task_id_prefix: Full UUID or first 8 characters

    Returns:
        dict or None: Task details
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, source, request, status, created_at, completed_at, summary
        FROM tasks
        WHERE id LIKE ?
        ORDER BY created_at DESC
        LIMIT 1
    ''', (f"{task_id_prefix}%",))

    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        'id': row[0],
        'source': row[1],
        'request': row[2],
        'status': row[3],
        'created_at': row[4],
        'completed_at': row[5],
        'summary': row[6],
    }


def search_tasks(keywords, status='pending', limit=5):
    """
    Search tasks by keywords in the request field

    Args:
        keywords: Space-separated search terms (all must match)
        status: Filter by status ('pending', 'completed', etc.) or None for all
        limit: Max results

    Returns:
        list[dict]: Matching tasks, most recent first
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Build WHERE clause: each keyword must appear in request (case-insensitive)
    words = keywords.strip().split()
    conditions = ["request LIKE ?"] * len(words)
    params = [f"%{w}%" for w in words]

    if status:
        conditions.append("status = ?")
        params.append(status)

    where = " AND ".join(conditions)
    params.append(limit)

    cursor.execute(f'''
        SELECT id, source, request, status, created_at, completed_at, summary
        FROM tasks
        WHERE {where}
        ORDER BY created_at DESC
        LIMIT ?
    ''', params)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            'id': r[0], 'source': r[1], 'request': r[2],
            'status': r[3], 'created_at': r[4],
            'completed_at': r[5], 'summary': r[6],
        }
        for r in rows
    ]


def find_task(identifier):
    """
    Resolve a task by ID prefix OR keyword search.

    Tries ID lookup first. If that fails, searches by keywords
    among pending tasks and returns the best match.

    Args:
        identifier: Task ID prefix or natural language keywords

    Returns:
        dict or None: Task details
    """
    # Try ID lookup first
    task = get_task(identifier)
    if task:
        return task

    # Fall back to keyword search among pending tasks
    results = search_tasks(identifier, status='pending')
    if results:
        return results[0]

    # Try across all statuses
    results = search_tasks(identifier, status=None)
    if results:
        return results[0]

    return None


def update_task_status(task_id_prefix, new_status, summary=None):
    """
    Update a task's status

    Args:
        task_id_prefix: Full UUID or first 8 characters
        new_status: 'in_progress', 'completed', or 'failed'
        summary: Optional summary text

    Returns:
        dict: Result with success status
    """
    task = get_task(task_id_prefix)
    if not task:
        return {'success': False, 'error': f'No task found matching: {task_id_prefix}'}

    full_id = task['id']
    conn = get_connection()
    cursor = conn.cursor()

    if new_status in ('completed', 'failed'):
        cursor.execute('''
            UPDATE tasks
            SET status = ?, completed_at = ?, summary = ?
            WHERE id = ?
        ''', (new_status, datetime.now().isoformat(), summary, full_id))
    else:
        cursor.execute('''
            UPDATE tasks
            SET status = ?
            WHERE id = ?
        ''', (new_status, full_id))

    conn.commit()
    conn.close()

    return {'success': True, 'task_id': full_id, 'new_status': new_status}


def format_task_for_execution(task):
    """
    Format a task dict into a human-readable execution brief

    Args:
        task: Task dict from get_task()

    Returns:
        str: Formatted task brief
    """
    if not task:
        return "No task found."

    request = task['request']

    # Parse the goal type from the request (format: [GOAL_TYPE] original message)
    goal_type = None
    original_message = request
    if request.startswith('['):
        bracket_end = request.find(']')
        if bracket_end != -1:
            goal_type = request[1:bracket_end].lower()
            original_message = request[bracket_end + 1:].strip()

    lines = [
        f"PENDING TASK",
        f"============",
        f"Task ID:  {task['id']}",
        f"Source:   {task['source']}",
        f"Status:   {task['status']}",
        f"Created:  {task['created_at']}",
        f"",
        f"Request:  {original_message}",
    ]

    if goal_type:
        lines.append(f"Goal:     {goal_type}")

    lines.append("")
    lines.append("To execute this task, follow the relevant goal workflow in goals/.")
    lines.append(f"Mark complete when done: python tools/tasks/task_executor.py --complete {task['id'][:8]}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Manage pending tasks')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true', help='List pending tasks')
    group.add_argument('--get', metavar='ID_OR_KEYWORDS', help='Get task by ID or keywords')
    group.add_argument('--search', metavar='KEYWORDS', help='Search tasks by keywords')
    group.add_argument('--start', metavar='ID_OR_KEYWORDS', help='Mark task as in_progress')
    group.add_argument('--complete', metavar='ID_OR_KEYWORDS', help='Mark task as completed')
    group.add_argument('--fail', metavar='ID_OR_KEYWORDS', help='Mark task as failed')

    parser.add_argument('--summary', help='Summary text for completion/failure')
    parser.add_argument('--source', help='Filter by source (e.g. telegram)')
    parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    if args.list:
        tasks = list_pending_tasks(source=args.source)
        if args.json:
            print(json.dumps(tasks, indent=2))
        elif not tasks:
            print("No pending tasks.")
        else:
            print(f"Pending Tasks ({len(tasks)}):\n")
            for t in tasks:
                print(f"  [{t['id'][:8]}] ({t['source']}) {t['request'][:70]}")
                print(f"           Created: {t['created_at']}")
                print()

    elif args.get:
        task = find_task(args.get)
        if args.json:
            print(json.dumps(task, indent=2))
        elif task:
            print(format_task_for_execution(task))
        else:
            print(f"No task found matching: {args.get}")

    elif args.search:
        tasks = search_tasks(args.search, status=None)
        if args.json:
            print(json.dumps(tasks, indent=2))
        elif not tasks:
            print(f"No tasks found matching: {args.search}")
        else:
            print(f"Tasks matching '{args.search}' ({len(tasks)}):\n")
            for t in tasks:
                print(f"  [{t['id'][:8]}] [{t['status']}] {t['request'][:70]}")
                print(f"           Created: {t['created_at']}")
                print()

    elif args.start:
        task = find_task(args.start)
        if not task:
            print(f"No task found matching: {args.start}")
        else:
            result = update_task_status(task['id'], 'in_progress')
            if args.json:
                print(json.dumps(result, indent=2))
            elif result['success']:
                print(f"Task {result['task_id'][:8]} marked as in_progress.")
            else:
                print(f"Error: {result['error']}")

    elif args.complete:
        task = find_task(args.complete)
        if not task:
            print(f"No task found matching: {args.complete}")
        else:
            result = update_task_status(task['id'], 'completed', summary=args.summary)
            if args.json:
                print(json.dumps(result, indent=2))
            elif result['success']:
                print(f"Task {result['task_id'][:8]} marked as completed.")
            else:
                print(f"Error: {result['error']}")

    elif args.fail:
        task = find_task(args.fail)
        if not task:
            print(f"No task found matching: {args.fail}")
        else:
            result = update_task_status(task['id'], 'failed', summary=args.summary)
            if args.json:
                print(json.dumps(result, indent=2))
            elif result['success']:
                print(f"Task {result['task_id'][:8]} marked as failed.")
            else:
                print(f"Error: {result['error']}")


if __name__ == '__main__':
    main()
