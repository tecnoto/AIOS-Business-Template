## Incident Response Protocol

### When Something Goes Wrong

Follow this sequence:

1. **Contain** — Stop the bleeding (disable webhook, pause automation, revoke tool access)
2. **Assess** — What data was affected? What is the blast radius?
3. **Notify** — Alert the user immediately for HIGH tier incidents; log for review for MEDIUM
4. **Remediate** — Fix root cause; verify fix; test
5. **Document** — Update skills/rules with what was learned

### Severity Levels

| Severity | Definition | Response Time | Notification |
|----------|------------|---------------|-------------|
| **Critical** | Credential exposed, data breach, production down | Immediate | Alert user now via all available channels |
| **High** | Security vulnerability found, service degraded | Within current session | Notify at next interaction |
| **Medium** | Non-critical bug, workflow failure, minor data issue | Log for review | Include in session summary |
| **Low** | Documentation gap, minor process deviation | When convenient | Mention if relevant |

### Post-Incident Actions

- Update guardrails in CLAUDE.md if it represents a new learned behavior
- Update relevant rule file if a policy gap was exposed
- Update pre_tool_guard.py if a new dangerous pattern was discovered
- Add to threat_model.md if a new vulnerability class was identified

### Error Handling Philosophy

Every failure strengthens the system:

1. **Read** the error carefully — understand what broke and why
2. **Fix** the tool or script
3. **Test** until it works reliably
4. **Document** the fix in the relevant skill or rule
