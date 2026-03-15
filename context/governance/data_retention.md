## Data Retention Policies

### Retention Defaults

| Data Type | Default Retention | Notes |
|-----------|------------------|-------|
| Daily logs (`memory/logs/`) | 30 days | Archive significant items to MEMORY.md before cleanup |
| `MEMORY.md` | Indefinite | Quarterly review for relevance and security |
| Intermediate files (`.tmp/`) | Session only | Delete after workflow completes |
| Database entries (`data/`) | 90 days default | Extend with documented justification |
| Vector memory (Pinecone) | Indefinite | Periodic relevance review; delete stale entries |

### Memory Security Rules

- **NEVER store** in memory files: API keys, tokens, passwords, SSNs, financial account numbers
- **Quarterly audit**: Review MEMORY.md for outdated or accidentally sensitive content
- Scrub secrets before writing to any memory tier

### Data Classification

| Class | Retention Rules |
|-------|----------------|
| **PUBLIC** | No restrictions |
| **INTERNAL** | Access logging; no external sharing; standard retention |
| **CONFIDENTIAL** | Need-to-know access; encryption at rest; defined retention period |
| **PII** | Encryption; access logging; retention limits; MUST NOT appear in memory files or embeddings |

### Cleanup Protocol

When performing retention cleanup:

1. Check daily logs older than 30 days
2. Extract any significant items to MEMORY.md before deletion
3. Scan for accidentally stored sensitive data
4. Archive rather than delete when in doubt
5. Log the cleanup action
