---
name: dashboard
description: Generate an agent activity dashboard with charts, metrics, and insights from SQLite data
triggers:
  - generate dashboard
  - show dashboard
  - agent dashboard
  - activity report
  - show metrics
  - what has the agent been doing
tools: [generate_dashboard.py, dashboard_queries.py, serve_dashboard.py]
---

# Skill: Agent Dashboard

> Generates a static HTML dashboard from SQLite databases showing agent activity,
> task progress, memory stats, performance metrics, and department hierarchy.

## Usage

```bash
# Generate dashboard (opens in browser)
python3 .claude/skills/dashboard/scripts/generate_dashboard.py

# Generate without opening
python3 .claude/skills/dashboard/scripts/generate_dashboard.py --no-open

# Serve with auto-refresh (for live monitoring)
python3 .claude/skills/dashboard/scripts/serve_dashboard.py
```

## Dashboard Sections

1. **Executive Summary** — At-a-glance KPIs (tasks, messages, memories, health)
2. **Activity Feed** — Chronological log of agent actions (filterable)
3. **Project Tracker** — Task queue status grouped by type (kanban view)
4. **Agent Hierarchy** — Department structure with per-agent stats
5. **Performance Metrics** — Latency, LLM routing, cost estimates
6. **Memory Insights** — Growth, recent captures, type distribution
7. **Full Logs** — Searchable table of all events

## Data Sources

All data comes from existing SQLite databases — no external dependencies:
- `data/activity.db` — tasks, telegram_events, messages
- `data/memory.db` — memory_entries
- `data/mem0_history.db` — mem0 history + FTS index

## Output

Single self-contained HTML file at `dashboard/index.html`.
Charts via Chart.js (CDN). Styling via embedded CSS.
