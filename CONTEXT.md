# Context Router

> Routes agents to the right context for each task type.
> Principle: "What should I NOT load?" — only load what the task requires.

## Task Routing

| Task Type | Load | Skip |
|-----------|------|------|
| **Building features** | build-process skill SKILL.md, coding_standards rule | client_onboarding/, identity context |
| **Client onboarding** | client_onboarding/*.md, context/brand_profile.md, context/icp.md | coding_standards, dashboard skill |
| **Marketing/content** | content-writer agent, context/brand_profile.md, context/icp.md | coding_standards, tool scripts |
| **Deployment** | coding_standards rule, security rule | client_onboarding/, context/ knowledge files |
| **Debugging** | coding_standards rule, tools/manifest.md, relevant skill SKILL.md | client_onboarding/, context/ knowledge files |
| **Memory operations** | memory skill SKILL.md only | everything else |
| **Telegram bot** | telegram skill SKILL.md only | client_onboarding/, dashboard |
| **Dashboard** | dashboard skill SKILL.md only | client_onboarding/, telegram |
| **Task execution** | Relevant skill for the task type, tools/manifest.md | client_onboarding/ |
| **Security review** | security rule, pre_tool_guard.py patterns | client_onboarding/, brand context |
| **Research** | researcher agent definition | coding_standards, tool scripts |

## What to NEVER Load Together

- All `context/` files at once (token waste)
- Multiple skill SKILL.md files (each skill is self-contained)
- `client_onboarding/` files during coding tasks
- `args/` files not relevant to the current task

## Cross-Skill Dependencies

| Skill | Depends On | Why |
|-------|-----------|-----|
| telegram | memory | Injects relevant memories into Claude context |
| dashboard | memory | Reads activity data for display |
| build-process | memory | Accounts registry lookup when onboarding services |
| memory | — | Foundation layer |
| _example-brand | — | Self-contained |

## Context Budget Reference

| Component | Loaded When |
|-----------|-------------|
| CLAUDE.md | Always |
| .claude/rules/ (all files) | Always |
| memory/MEMORY.md | Always |
| context/*.md | On-demand per task type |
| args/*.yaml | On-demand per task type |
| client_onboarding/*.md | Onboarding tasks only |
