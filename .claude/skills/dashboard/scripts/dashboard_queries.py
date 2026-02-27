#!/usr/bin/env python3
"""
Dashboard Queries — All SQL queries for the agent dashboard.
Returns Python dicts/lists ready for Jinja2 rendering.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


def _connect(db_path):
    """Connect to a SQLite database, return None if it doesn't exist."""
    if not Path(db_path).exists():
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _safe_query(conn, query, params=()):
    """Execute a query safely, return empty list on error."""
    if conn is None:
        return []
    try:
        return [dict(row) for row in conn.execute(query, params).fetchall()]
    except Exception:
        return []


def _safe_scalar(conn, query, params=(), default=0):
    """Execute a scalar query safely."""
    if conn is None:
        return default
    try:
        result = conn.execute(query, params).fetchone()
        return result[0] if result else default
    except Exception:
        return default


# === Executive Summary ===

def get_summary(activity_db, memory_db, mem0_db):
    """Get at-a-glance KPIs."""
    a_conn = _connect(activity_db)
    m_conn = _connect(memory_db)
    h_conn = _connect(mem0_db)

    today = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    summary = {
        "tasks_total": _safe_scalar(a_conn, "SELECT COUNT(*) FROM tasks"),
        "tasks_completed": _safe_scalar(a_conn, "SELECT COUNT(*) FROM tasks WHERE status='completed'"),
        "tasks_pending": _safe_scalar(a_conn, "SELECT COUNT(*) FROM tasks WHERE status='pending'"),
        "tasks_failed": _safe_scalar(a_conn, "SELECT COUNT(*) FROM tasks WHERE status='failed'"),
        "messages_today": _safe_scalar(
            a_conn,
            "SELECT COUNT(*) FROM messages WHERE date(created_at) = ?",
            (today,)
        ),
        "messages_week": _safe_scalar(
            a_conn,
            "SELECT COUNT(*) FROM messages WHERE date(created_at) >= ?",
            (week_ago,)
        ),
        "messages_total": _safe_scalar(a_conn, "SELECT COUNT(*) FROM messages"),
        "events_total": _safe_scalar(a_conn, "SELECT COUNT(*) FROM telegram_events"),
        "memories_local": _safe_scalar(m_conn, "SELECT COUNT(*) FROM memory_entries"),
        "memories_vector": _safe_scalar(h_conn, "SELECT COUNT(*) FROM memory_fts"),
        "memories_new_week": _safe_scalar(
            h_conn,
            "SELECT COUNT(*) FROM history WHERE date(created_at) >= ? AND event='ADD'",
            (week_ago,)
        ),
        "departments": _get_departments(a_conn),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    for conn in [a_conn, m_conn, h_conn]:
        if conn:
            conn.close()

    return summary


def _get_departments(conn):
    """Get unique departments from tasks and messages."""
    depts = set()
    for table in ["tasks", "messages"]:
        try:
            rows = conn.execute(f"SELECT DISTINCT department FROM {table}").fetchall()
            depts.update(r[0] for r in rows if r[0])
        except Exception:
            pass
    return sorted(depts) if depts else ["general"]


# === Activity Feed ===

def get_activity_feed(activity_db, limit=50):
    """Get recent activity across all tables, merged chronologically."""
    conn = _connect(activity_db)
    if not conn:
        return []

    # Merge telegram_events and messages into a unified feed
    events = _safe_query(conn, """
        SELECT
            'event' as source,
            created_at,
            intent,
            handler,
            message_text as content,
            processing_time_ms,
            COALESCE(department, 'general') as department
        FROM telegram_events
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))

    tasks = _safe_query(conn, """
        SELECT
            'task' as source,
            created_at,
            request as content,
            status,
            COALESCE(department, 'general') as department,
            summary
        FROM tasks
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))

    conn.close()

    # Merge and sort
    feed = []
    for e in events:
        feed.append({
            "time": e["created_at"],
            "type": "event",
            "department": e.get("department", "general"),
            "content": (e.get("content") or "")[:200],
            "detail": f"{e.get('intent', '')} → {e.get('handler', '')}",
            "latency": e.get("processing_time_ms"),
        })
    for t in tasks:
        feed.append({
            "time": t["created_at"],
            "type": "task",
            "department": t.get("department", "general"),
            "content": (t.get("content") or "")[:200],
            "detail": f"Status: {t.get('status', 'unknown')}",
            "latency": None,
        })

    feed.sort(key=lambda x: x["time"] or "", reverse=True)
    return feed[:limit]


# === Project Tracker ===

def get_task_board(activity_db):
    """Get tasks grouped by status for kanban view."""
    conn = _connect(activity_db)
    if not conn:
        return {"pending": [], "in_progress": [], "completed": [], "failed": []}

    tasks = _safe_query(conn, """
        SELECT id, request, status, department, created_at, completed_at, summary
        FROM tasks
        ORDER BY created_at DESC
    """)
    conn.close()

    board = {"pending": [], "in_progress": [], "completed": [], "failed": []}
    for t in tasks:
        status = t.get("status", "pending")
        if status in board:
            board[status].append(t)
        else:
            board["pending"].append(t)
    return board


# === Performance Metrics ===

def get_performance(activity_db):
    """Get handler performance metrics."""
    conn = _connect(activity_db)
    if not conn:
        return {"by_handler": [], "by_day": [], "routing": []}

    by_handler = _safe_query(conn, """
        SELECT
            handler,
            COUNT(*) as count,
            ROUND(AVG(processing_time_ms)) as avg_ms,
            MIN(processing_time_ms) as min_ms,
            MAX(processing_time_ms) as max_ms
        FROM telegram_events
        WHERE handler IS NOT NULL AND handler != ''
        GROUP BY handler
        ORDER BY count DESC
    """)

    by_day = _safe_query(conn, """
        SELECT
            date(created_at) as day,
            COUNT(*) as count
        FROM telegram_events
        WHERE created_at > datetime('now', '-30 days')
        GROUP BY date(created_at)
        ORDER BY day
    """)

    # LLM routing distribution from messages metadata
    routing = []
    try:
        rows = conn.execute("""
            SELECT metadata FROM messages
            WHERE metadata IS NOT NULL AND metadata != ''
        """).fetchall()
        ollama_count = 0
        claude_count = 0
        for row in rows:
            try:
                meta = json.loads(row[0])
                source = meta.get("llm_source", "")
                if source == "ollama":
                    ollama_count += 1
                elif source == "claude":
                    claude_count += 1
            except (json.JSONDecodeError, TypeError):
                pass
        routing = [
            {"source": "ollama", "count": ollama_count},
            {"source": "claude", "count": claude_count},
        ]
    except Exception:
        pass

    conn.close()
    return {"by_handler": by_handler, "by_day": by_day, "routing": routing}


# === Memory Insights ===

def get_memory_stats(memory_db, mem0_db):
    """Get memory system statistics."""
    m_conn = _connect(memory_db)
    h_conn = _connect(mem0_db)

    by_type = _safe_query(m_conn, """
        SELECT entry_type, COUNT(*) as count
        FROM memory_entries
        GROUP BY entry_type
        ORDER BY count DESC
    """)

    recent_memories = _safe_query(h_conn, """
        SELECT memory_id, new_memory as content, event, created_at
        FROM history
        WHERE event IN ('ADD', 'UPDATE')
        ORDER BY created_at DESC
        LIMIT 10
    """)

    growth = _safe_query(h_conn, """
        SELECT date(created_at) as day, COUNT(*) as count
        FROM history
        WHERE event = 'ADD' AND created_at > datetime('now', '-30 days')
        GROUP BY date(created_at)
        ORDER BY day
    """)

    for conn in [m_conn, h_conn]:
        if conn:
            conn.close()

    return {
        "by_type": by_type,
        "recent": recent_memories,
        "growth": growth,
    }


# === Department Stats ===

def get_department_stats(activity_db):
    """Get per-department activity stats."""
    conn = _connect(activity_db)
    if not conn:
        return []

    stats = _safe_query(conn, """
        SELECT
            COALESCE(department, 'general') as department,
            COUNT(*) as message_count,
            ROUND(AVG(processing_time_ms)) as avg_latency
        FROM telegram_events
        GROUP BY department
        ORDER BY message_count DESC
    """)

    task_stats = _safe_query(conn, """
        SELECT
            COALESCE(department, 'general') as department,
            COUNT(*) as task_count,
            SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed
        FROM tasks
        GROUP BY department
    """)

    conn.close()

    # Merge
    dept_map = {}
    for s in stats:
        dept_map[s["department"]] = {
            "department": s["department"],
            "messages": s["message_count"],
            "avg_latency": s["avg_latency"],
            "tasks": 0,
            "tasks_completed": 0,
        }
    for t in task_stats:
        d = t["department"]
        if d not in dept_map:
            dept_map[d] = {
                "department": d, "messages": 0, "avg_latency": 0,
                "tasks": 0, "tasks_completed": 0,
            }
        dept_map[d]["tasks"] = t["task_count"]
        dept_map[d]["tasks_completed"] = t["completed"]

    return list(dept_map.values())
