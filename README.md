# AI Operating System — Business Template

> Clone this repo to create an AI-powered operating system for any business.
> Built on the SCHEMA framework with Claude Code as the AI manager.

## Quick Start

```bash
# 1. Clone this template
git clone https://github.com/tecnoto/AIOS-Business-Template.git my-business-ai
cd my-business-ai

# 2. Run the setup wizard
python3 setup.py

# 3. Install dependencies
pip install -r requirements.txt

# 4. Open in Claude Code
claude

# 5. Start building!
```

## What This Is

A folder-based AI Operating System that turns a repository into a fully operational business automation system. It uses Claude Code as the AI manager, with deterministic Python scripts handling execution.

## Architecture (SCHEMA Framework)

| Layer | Directory | Purpose |
|-------|-----------|---------|
| **Skills** | `.claude/skills/` | Procedural knowledge and workflows, auto-activated by description matching |
| **Context** | `CLAUDE.md` + `.claude/rules/` + `context/` + `args/` | Identity, routing, rules, domain knowledge, runtime config |
| **Hooks** | `.claude/hooks/` | Deterministic lifecycle automation (safety, logging, memory capture) |
| **Execution** | `tools/` + `.claude/skills/*/scripts/` | Deterministic scripts and external service connections |
| **Memory** | `memory/` + `data/` | Persistent knowledge across sessions |
| **Agents** | `.claude/agents/` | Sub-agents with scoped tools for specialized tasks |

## Included Skills

| Skill | Purpose |
|-------|---------|
| `memory` | 3-tier persistent memory (MEMORY.md + daily logs + Pinecone vectors) |
| `telegram` | Telegram bot with local LLM + Claude API escalation |
| `dashboard` | Agent activity dashboard with charts and insights |
| `_example-brand` | Sample brand skill (DALL-E image generation pattern) |

## Scaling

| Business Size | Architecture |
|--------------|-------------|
| **Solo / Small** | Single agent, direct skills |
| **Mid-Market** | Multiple skills, sub-agents for specialized tasks |
| **Enterprise** | Lead agent + specialized sub-agents + agent teams |

## Client Onboarding

Fill in the templates in `client_onboarding/` to capture business requirements:

1. `01_discovery_interview.md` — Business questionnaire
2. `02_department_map.md` — Org chart and team structure
3. `03_workflow_inventory.md` — Workflows to automate
4. `04_brand_profile.md` — Voice, colors, ICP
5. `05_technical_requirements.md` — Tools and integrations
6. `06_scope_of_work.md` — Skills to build, timeline, pricing
7. `07_compiled_business_kb.md` — Auto-compiled knowledge base

## Security

- Pre-tool hooks block dangerous operations (rm -rf, force push, credential exposure)
- Stop hooks auto-capture conversation facts to memory
- `.env` for credentials (gitignored)
- Rate limiting and blocked pattern detection on all inputs
- All safety enforced programmatically — Claude cannot bypass hooks

## Author

Forrest Shaw / [tecnoto](https://github.com/tecnoto)

## License

MIT
