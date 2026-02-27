#!/usr/bin/env python3
"""
Generate Dashboard — Queries SQLite databases and renders a static HTML dashboard.

Usage:
    python3 .claude/skills/dashboard/scripts/generate_dashboard.py
    python3 .claude/skills/dashboard/scripts/generate_dashboard.py --no-open
"""

import os
import sys
import webbrowser
import yaml
from pathlib import Path

# Find project root
def _find_root():
    path = Path(__file__).resolve().parent
    while path != path.parent:
        if (path / "CLAUDE.md").exists() or (path / "setup_config.yaml").exists():
            return path
        path = path.parent
    return Path.cwd()

PROJECT_ROOT = _find_root()
sys.path.insert(0, str(PROJECT_ROOT / ".claude" / "skills" / "dashboard" / "scripts"))

from dashboard_queries import (
    get_summary,
    get_activity_feed,
    get_task_board,
    get_performance,
    get_memory_stats,
    get_department_stats,
)

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("ERROR: jinja2 is required. Install with: pip install jinja2")
    sys.exit(1)


def load_config():
    """Load dashboard configuration."""
    config_path = PROJECT_ROOT / ".claude" / "skills" / "dashboard" / "references" / "dashboard_config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            return yaml.safe_load(f).get("dashboard", {})
    return {}


def main():
    config = load_config()
    no_open = "--no-open" in sys.argv

    # Database paths
    activity_db = str(PROJECT_ROOT / config.get("databases", {}).get("activity", "data/activity.db"))
    memory_db = str(PROJECT_ROOT / config.get("databases", {}).get("memory", "data/memory.db"))
    mem0_db = str(PROJECT_ROOT / config.get("databases", {}).get("mem0_history", "data/mem0_history.db"))

    print("Querying databases...")

    # Gather all data
    summary = get_summary(activity_db, memory_db, mem0_db)
    activity_feed = get_activity_feed(activity_db, config.get("recent_activity_limit", 50))
    task_board = get_task_board(activity_db)
    performance = get_performance(activity_db)
    memory_stats = get_memory_stats(memory_db, mem0_db)
    department_stats = get_department_stats(activity_db)

    # Prepare chart data
    perf_days = performance.get("by_day", [])
    performance_days_labels = [d["day"] for d in perf_days]
    performance_days_data = [d["count"] for d in perf_days]

    routing = performance.get("routing", [])
    routing_labels = [r["source"] for r in routing if r["count"] > 0]
    routing_data = [r["count"] for r in routing if r["count"] > 0]
    if not routing_labels:
        routing_labels = ["No data"]
        routing_data = [1]

    # Load business name from setup_config if available
    title = config.get("title", "AI Operating System — Dashboard")
    setup_config_path = PROJECT_ROOT / "setup_config.yaml"
    if setup_config_path.exists():
        with open(setup_config_path) as f:
            sc = yaml.safe_load(f) or {}
        biz_name = sc.get("business_name", "")
        if biz_name:
            title = f"{biz_name} — Agent Dashboard"

    # Render template
    template_dir = PROJECT_ROOT / ".claude" / "skills" / "dashboard" / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("dashboard.html")

    html = template.render(
        title=title,
        summary=summary,
        activity_feed=activity_feed,
        task_board=task_board,
        performance=performance,
        memory_stats=memory_stats,
        department_stats=department_stats,
        performance_days_labels=performance_days_labels,
        performance_days_data=performance_days_data,
        routing_labels=routing_labels,
        routing_data=routing_data,
    )

    # Write output
    output_dir = PROJECT_ROOT / config.get("output_path", "dashboard/index.html")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    output_dir.write_text(html, encoding="utf-8")

    print(f"Dashboard generated: {output_dir}")
    print(f"  Tasks: {summary['tasks_completed']} completed / {summary['tasks_pending']} pending")
    print(f"  Messages: {summary['messages_total']} total ({summary['messages_today']} today)")
    print(f"  Memories: {summary['memories_vector']} vector + {summary['memories_local']} local")
    print(f"  Departments: {', '.join(summary['departments'])}")

    if not no_open and config.get("auto_open", True):
        webbrowser.open(f"file://{output_dir.resolve()}")
        print("  Opened in browser.")


if __name__ == "__main__":
    main()
