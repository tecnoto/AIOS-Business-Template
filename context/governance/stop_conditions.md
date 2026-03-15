## Stop Conditions

Hard stops. When triggered, halt immediately and do not proceed without user guidance.

### Immediate Stop Triggers

| Category | Trigger | Action |
|----------|---------|--------|
| **Credential Exposure** | Secret detected in output, log, or memory file | Halt, purge, alert user |
| **Scope Violation** | Action would exceed defined scope or risk tier | Halt, log, notify |
| **Approval Bypass** | Attempt to skip required approval chain | Halt, log, alert |
| **Rate Limit** | External API blocking requests | Halt, backoff, log |
| **Execution Timeout** | Task exceeded reasonable time with no progress | Halt, preserve state, log |
| **Integrity Failure** | Tool/skill file modified unexpectedly | Halt, alert |
| **Trust Boundary** | Unapproved external domain contacted | Halt, block, log |

### Absolute Prohibitions (All Tiers, No Exceptions)

- Disable logging or audit trails
- Bypass authentication on any system
- Execute code from untrusted/unverified sources
- Store credentials in memory or embeddings
- Delete audit logs or memory archives
- Operate without risk tier classification

### Stop Condition Response Protocol

When a stop condition triggers:

1. **Halt** — Stop the current action immediately
2. **Preserve** — Save state for debugging (without sensitive data)
3. **Log** — Record stop trigger, context, and timestamp
4. **Notify** — Alert the user via primary channel
5. **Await** — Do not retry without user guidance
6. **Document** — Add to guardrails if it represents a new learned behavior

### Relationship to Hooks

The `pre_tool_guard.py` hook enforces stop conditions deterministically for tool use (blocked commands, protected files, secret exposure). These rules cover the judgment-based stop conditions that hooks cannot detect — scope violations, data classification surprises, and contextual risk escalation.
