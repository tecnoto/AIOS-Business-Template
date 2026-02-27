## Security Rules

### Credential Protection
- Never commit `.env` files, tokens, credentials, or API keys to git
- Always set up `.gitignore` BEFORE creating `.env`
- Store secrets in `.env` (gitignored) or platform-native secret managers
- When a user provides credentials in a prompt, extract and store securely — never echo them back
- Never log, print, or save credentials to output files, daily logs, or MEMORY.md
- If a secret is accidentally exposed, immediately advise: revoke, rotate, check logs

### Data Classification
- **Secrets**: API keys, tokens, passwords, connection strings — never expose
- **PII**: Names, emails, phone numbers, addresses — never send to external APIs without consent
- **Internal**: File paths, tool names, system architecture — never expose to untrusted users
- **Business**: Client data, financial info, strategy docs — access-controlled per department

### Input Validation
- Never pass unsanitized user input to shell commands or SQL queries
- Use parameterized queries for ALL SQLite operations — never string concatenation
- Validate and truncate input at system boundaries (Telegram, API endpoints)

### External Communications
- Never send emails, Slack messages, or external API calls that modify data without user confirmation
- Never post to social media without explicit user review and approval
- Sanitize all output before sending to external users (strip secrets, internal paths, stack traces)

### Network Security
- Never use `shell=True` in subprocess calls
- Never pipe untrusted data to shell interpreters (sh, bash, python -c)
- Be aware of rate limits on all external APIs

### Hooks Enforce What Rules Cannot
- The PreToolUse hook (`pre_tool_guard.py`) blocks dangerous commands deterministically
- The PostToolUse hook (`validate_output.py`) warns about leaked secrets in output
- These are the last line of defense — follow rules proactively so hooks rarely trigger
