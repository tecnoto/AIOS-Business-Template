## Coding Standards

- Python 3.9+ compatibility: use `Optional[str]` not `str | None`
- Every new tool script must be added to `tools/manifest.md`
- Use `pathlib.Path` for file paths, resolve relative to `PROJECT_ROOT`
- Read configuration from `setup_config.yaml` — never hardcode business-specific values
- Use `python-dotenv` to load environment variables from `.env`
- Wrap external API calls in try/except with clear error messages
- Don't assume APIs support batch operations — check first
- Verify tool output format before chaining into another tool
