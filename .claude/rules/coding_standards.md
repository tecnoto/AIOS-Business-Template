## Coding Standards

### Language & Compatibility
- Python 3.9+ compatibility: use `Optional[str]` not `str | None`
- Use `pathlib.Path` for file paths, resolve relative to `PROJECT_ROOT`

### Configuration
- Read configuration from `setup_config.yaml` — never hardcode business-specific values
- Use `python-dotenv` to load environment variables from `.env`

### Security in Code
- Use parameterized queries for ALL SQLite operations: `cursor.execute("SELECT * FROM t WHERE id = ?", (id,))`
- Never use string concatenation or f-strings for SQL: `f"SELECT * FROM t WHERE id = {id}"` is FORBIDDEN
- Never use `subprocess.Popen(..., shell=True)` or `os.system()` — use subprocess with argument lists
- Never hardcode credentials in source files
- Validate and sanitize ALL input at system boundaries

### Error Handling
- Wrap external API calls in try/except with clear error messages
- Don't assume APIs support batch operations — check first
- Verify tool output format before chaining into another tool
- Preserve intermediate outputs before retrying failed workflows

### Organization
- Every new tool script must be added to `tools/manifest.md`
- Every new skill must have a `SKILL.md` with frontmatter
- One script = one job. Keep scripts focused and testable.
- Scripts return JSON with `{"success": true/false, ...}` for composability
