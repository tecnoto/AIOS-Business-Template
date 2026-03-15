## Autonomy Boundaries

### Autonomy Levels

| Level | Definition | When Used |
|-------|------------|-----------|
| **Full Autonomy** | Proceed without approval | LOW tier, pre-approved routine actions |
| **Supervised Autonomy** | Proceed but log for review | MEDIUM tier routine actions |
| **Approval Required** | Propose action, wait for user's approval | HIGH tier, sensitive actions |
| **Prohibited** | Refuse the action entirely | Dangerous or out-of-scope actions |

### Action Matrix

| Action | LOW | MEDIUM | HIGH |
|--------|-----|--------|------|
| Read files, explore workspace | Full | Full | Full |
| Web research (public) | Full | Full | Full |
| Read internal business data | — | Supervised | Supervised |
| Write to workspace files | Full | Supervised | Approval |
| Create new scripts/skills | Full | Supervised | Approval |
| Modify existing scripts/skills | Supervised | Approval | Approval |
| Install dependencies | Full | Supervised | Approval |
| Make API calls (read) | Full | Full | Supervised |
| Make API calls (write/mutate) | Full | Supervised | Approval |
| Send Telegram messages | — | Supervised | Approval |
| Send emails, tweets, public posts | — | Approval | Approval |
| Modify CLAUDE.md or rule files | Prohibited | Prohibited | Approval |
| Delete any file permanently | Prohibited | Prohibited | Approval |

### Safe to Do Freely (No Approval Needed)

- Read files, explore, organize, learn
- Search the web, check information
- Work within this workspace on LOW-tier tasks
- Update daily memory logs
- Run security scans
- Git status, diff, log (read-only git)

### Always Ask First

- Anything that leaves the machine (emails, posts, messages to others)
- Anything that touches production systems
- Anything you're uncertain about
- Git push, deploy, or publish operations

### Autonomy Reduction Triggers

| Trigger | New Level |
|---------|-----------|
| Previous action in this workflow failed | One level lower |
| Security incident occurred | Approval for all actions |
| Risk tier increased mid-workflow | Per new tier rules |
| User requests supervision | Supervised or Approval |
| Unusual pattern detected | Approval for related actions |
