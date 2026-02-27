# Department Map

> Maps the organizational structure to the AI agent hierarchy.
> Skip for solo/small businesses — they use a flat agent structure.

---

## Organizational Structure

| Department | Lead | Team Size | Primary Workflows | Agent Priority |
|------------|------|-----------|-------------------|----------------|
| | | | | High / Medium / Low |
| | | | | |
| | | | | |
| | | | | |

## Agent Hierarchy Design

```
CEO Agent ({{AGENT_NAME}})
│
├── {{DEPARTMENT_1}} Lead Agent
│   ├── Skills: [list skills this department needs]
│   ├── Context: [what knowledge does this agent need?]
│   └── Sub-agents: [if team is large enough to warrant sub-agents]
│
├── {{DEPARTMENT_2}} Lead Agent
│   ├── Skills: [...]
│   ├── Context: [...]
│   └── Sub-agents: [...]
│
└── {{DEPARTMENT_3}} Lead Agent
    ├── Skills: [...]
    ├── Context: [...]
    └── Sub-agents: [...]
```

## Cross-Department Workflows

These workflows span multiple departments — the CEO agent coordinates them:

| Workflow | Departments Involved | Trigger | Output |
|----------|---------------------|---------|--------|
| | | | |
| | | | |

## Communication Patterns

**How do departments share information today?**
>

**What information needs to flow between agent departments?**
>

**Escalation path** (when does a department agent escalate to CEO agent?):
>

## Rollout Order

Which departments get their agent first?

| Phase | Department | Reason | Timeline |
|-------|-----------|--------|----------|
| 1 | | Highest impact / most willing | Week 1-2 |
| 2 | | | Week 3-4 |
| 3 | | | Week 5+ |

---

*Mapped by: ___*
*Date: ___*
