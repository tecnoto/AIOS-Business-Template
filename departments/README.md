# Departments — Multi-Agent Hierarchy

> Each department gets a sub-directory that defines its agent's scope, skills, and context.
> The CEO Agent (root CLAUDE.md) coordinates across all departments.

## How It Works

1. Copy `_template/` to create a new department: `cp -r _template/ sales/`
2. Fill in `DEPARTMENT.md` with the department's scope and constraints
3. Add department-specific skills, context, and args
4. Tag tasks with `department=sales` to route them

## Architecture

```
CEO Agent (CLAUDE.md)
├── departments/sales/       → Sales Lead Agent
├── departments/marketing/   → Marketing Lead Agent
├── departments/operations/  → Operations Lead Agent
└── departments/support/     → Support Lead Agent
```

## Communication Model

All agents share `data/activity.db`. Tasks and messages have a `department` column for filtering. The CEO Agent sees everything. Department agents are scoped to their own data.

## Adding a Department

See `goals/onboard_new_department.md` for the full process.
