## Risk Tier Classification

All significant actions should be classified into a risk tier before execution. When unsure, classify UP, not down.

### Tier Definitions

| Tier | Criteria (any match = this tier) | Examples |
|------|----------------------------------|----------|
| **HIGH** | Handles credentials, PII, payment data; writes to production; public-facing exposure; sends external communications | Payment processing, production writes, social media posting, email sending, external API mutations |
| **MEDIUM** | Reads sensitive business data; internal-only operations; modifies workspace files; uses skills or sub-agents | Lead research, internal dashboards, file operations, memory updates, skill creation |
| **LOW** | Public info only; non-sensitive operations; dev/sandbox only; no external tool use | Web research, internal analysis, documentation, planning |

### Required Controls by Tier

| Control | LOW | MEDIUM | HIGH |
|---------|-----|--------|------|
| Input validation | SHOULD | MUST | MUST |
| Human approval before execution | MAY | SHOULD | MUST |
| Rollback plan documented | MAY | SHOULD | MUST |
| Audit logging | SHOULD | MUST | MUST |
| Secrets handled via .env only | MUST | MUST | MUST |

### Classification Rules

- New/unverified skills start at MEDIUM minimum
- Skills that send external communications are ALWAYS HIGH
- Skills that modify production data are ALWAYS HIGH
- When a previous action in the same workflow failed, escalate the next action one tier up
