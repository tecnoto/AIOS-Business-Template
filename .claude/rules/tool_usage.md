## Tool Usage Rules

- Always check `tools/manifest.md` before writing a new script
- Always check `.claude/skills/` for a matching skill before starting a task
- Read the full skill SKILL.md before starting — don't skim
- When a workflow fails mid-execution, preserve intermediate outputs before retrying
- Never execute work yourself — delegate to tools and scripts
- If a tool doesn't exist, build it, test it, then add it to the manifest
- Prefer editing existing tools over creating new ones
- When tools fail, fix and document the failure in the relevant skill or tool
