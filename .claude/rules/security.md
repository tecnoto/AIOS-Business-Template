## Security Rules

- Never commit `.env` files, tokens, credentials, or API keys to git
- Always set up `.gitignore` BEFORE creating `.env`
- Store secrets in `.env` (gitignored) or platform-native secret managers
- When a user provides credentials in a prompt, extract and store securely — never echo them back
- Never log, print, or save credentials to output files
- Never expose PII in dashboard output or logs sent to external services
