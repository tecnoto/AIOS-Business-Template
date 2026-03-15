## Threat Model

### Common Threats

| Vulnerability | Watch For | Mitigation |
|--------------|-----------|------------|
| **Prompt Injection** | External input (Telegram, webhooks) attempting to manipulate agent behavior | Validate all external inputs; separate instructions from data |
| **Credential Exposure** | Secrets leaking into logs, memory files, outputs, or error messages | .env only; redaction in all logging; PostToolUse hook scans output |
| **Tool Abuse** | Tools invoked with malicious or unvalidated parameters | Input validation at system boundaries; PreToolUse hook blocks dangerous patterns |
| **Memory Poisoning** | Adversarial data corrupting persistent memory | Source validation; regular memory audits; no PII/secrets in memory |
| **Scope Creep** | Gradual expansion of autonomous actions beyond approved scope | Regular autonomy review; tier enforcement |
| **Supply Chain** | Compromised dependencies, untrusted skill sources | Pin versions; verify provenance; review permissions before adding integrations |

### When to Conduct Security Review

- New skill or tool added to the system
- Significant scope change in any workflow
- After any security incident
- Quarterly scheduled review
- New integration or dependency added

### Integration Checklist (Before Adding Any New Tool/Dependency)

- [ ] Check for known vulnerabilities
- [ ] Verify active maintenance (last commit, open issues)
- [ ] Review permissions/scopes requested
- [ ] Confirm it does not exceed needed scope
- [ ] Pin to specific version (no floating versions)
- [ ] Document in tools/manifest.md
- [ ] Classify risk tier
