# The SCHEMA Framework

> *Skills, Context, Hooks, Execution, Memory, Agents*
> An Anthropic-native architecture for AI operating systems.

## What SCHEMA Is

SCHEMA is a 6-layer framework for building AI agent systems on top of Claude Code's native primitives. Each layer maps 1:1 to capabilities Anthropic ships and maintains. As Claude Code evolves, SCHEMA evolves with it.

## The 6 Layers

### S — Skills

**What:** Procedural knowledge and workflows, packaged as auto-activated modules.
**Where:** `.claude/skills/*/SKILL.md`

Skills are the primary unit of capability. Each skill has:
- **Front matter** (YAML) — name, description, triggers. Loaded into every session (~100 tokens).
- **Body** (Markdown) — Full instructions, steps, examples. Lazy-loaded only when triggered.
- **Scripts** — Deterministic Python code the skill can invoke.

### C — Context

**What:** Everything the system knows — identity, behavioral constraints, domain knowledge.
**Where:** `CLAUDE.md`, `.claude/rules/`, `context/`, `args/`

Context sub-layers:
1. **Identity** (`CLAUDE.md`) — Who the system is, how it operates. Always loaded.
2. **Rules** (`.claude/rules/*.md`) — Modular behavioral constraints. Auto-loaded.
3. **Domain knowledge** (`context/`) — Reference material. Loaded on-demand.
4. **Runtime config** (`args/`) — YAML files that tune behavior without changing code.

### H — Hooks

**What:** Deterministic lifecycle automation that Claude cannot bypass.
**Where:** `.claude/settings.local.json` + `.claude/hooks/`

| Event | When | Use Case |
|-------|------|----------|
| `PreToolUse` | Before any tool runs | Block dangerous commands |
| `PostToolUse` | After any tool runs | Validate output, warn about leaked secrets |
| `Stop` | After every response | Auto-capture memories, log activity |

Hooks are the safety backbone. Rules are advisory. Hooks are deterministic (exit code 2 = hard stop).

### E — Execution

**What:** Deterministic scripts, external service connections, and tool scoping.
**Where:** `tools/`, `.claude/skills/*/scripts/`, MCP servers

Key principle: **LLMs reason, scripts execute.** Push reliability into deterministic code. Push flexibility into the LLM.

### M — Memory

**What:** Persistent knowledge across sessions.
**Where:** `memory/MEMORY.md`, `data/*.db`, Pinecone vectors

Three tiers:
1. **Core memory** (`memory/MEMORY.md`) — Always in system prompt. Curated facts.
2. **Session memory** (`memory/logs/`) — Daily logs for session continuity.
3. **Long-term memory** (mem0 + Pinecone) — Automatic fact extraction via Stop hook. Semantic search.

### A — Agents

**What:** Sub-agents with scoped tools for specialized tasks.
**Where:** `.claude/agents/`

Agents handle work that benefits from isolation or specialization. The main agent orchestrates; sub-agents execute with scoped permissions.

## Operating Principles

1. **Skills first.** Before doing work manually, check if a skill exists.
2. **Hooks enforce, rules guide.** Critical safety goes in hooks. Guidance goes in rules.
3. **Scripts execute, LLMs reason.** Push reliability into deterministic code.
4. **Memory is automatic.** The Stop hook captures facts. No manual duplication needed.
5. **Agents for isolation, not everything.** Use sub-agents when you need scoped permissions or parallel execution.
6. **Progressive disclosure.** Skill front matter loads always. Full body loads on trigger. Keep the always-on footprint small.

## File Structure

```
project/
├── .claude/
│   ├── skills/          # S — Skills (auto-discovered)
│   ├── agents/          # A — Agent definitions
│   ├── rules/           # C — Behavioral constraints
│   ├── hooks/           # H — Lifecycle scripts
│   └── settings.local.json  # E — Permissions + hook config
├── context/             # C — Domain knowledge
│   ├── governance/      # C — Risk tiers, incident response, policies
│   └── schema_framework.md
├── args/                # C — Runtime configuration
├── tools/               # E — Deterministic scripts
├── memory/              # M — Persistent knowledge
│   ├── MEMORY.md
│   └── logs/
├── data/                # M — Databases (SQLite)
└── CLAUDE.md            # C — System identity
```
