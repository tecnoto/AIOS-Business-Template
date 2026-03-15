# Onboarding Guide

How to configure and extend the AI Operating System for a new business.

## When This Applies

- Initial setup after cloning the template
- Adding new capabilities (skills, agents, tools)
- Scaling from solo to multi-agent architecture

## Process

### Step 1: Run the Setup Wizard

```bash
python3 setup.py
```

This creates `.env`, `setup_config.yaml`, database schemas, and initial memory files.

### Step 2: Complete Client Onboarding Documents

Fill in the templates in `client_onboarding/`:

1. `01_discovery_interview.md` — Business questionnaire
2. `02_department_map.md` — Team structure
3. `03_workflow_inventory.md` — Workflows to automate
4. `04_brand_profile.md` — Voice, colors, ICP
5. `05_technical_requirements.md` — Tools and integrations
6. `06_scope_of_work.md` — Skills to build, timeline
7. `07_compiled_business_kb.md` — Auto-compiled knowledge base

### Step 3: Populate Context Files

Add domain knowledge to `context/`:

- `brand_profile.md` — Voice, tone, visual identity
- `icp.md` — Ideal Customer Profile
- `industry_knowledge.md` — Domain-specific terminology and facts

### Step 4: Build Skills

Create skills in `.claude/skills/` for repeatable workflows:

```
.claude/skills/
├── my-skill/
│   ├── SKILL.md        # Instructions + front matter
│   └── scripts/        # Deterministic scripts
```

Each skill has a `SKILL.md` with YAML front matter (name, description, triggers) and markdown body (full instructions).

### Step 5: Configure Agents (Optional)

For specialized tasks, create sub-agents in `.claude/agents/`:

- Researcher — Read-only web and file research
- Content writer — Drafts in the brand's voice
- Code reviewer — Code quality analysis

### Step 6: Test

1. Open the project in Claude Code
2. Ask the agent to identify itself (should read `setup_config.yaml`)
3. Run a skill to confirm it works
4. Send a test Telegram message (if configured)

## Edge Cases

- **Already configured**: Warn the user, offer to update instead of overwrite
- **Missing API keys**: System works with reduced capabilities (no Telegram, no vector memory)
- **Enterprise scale**: Add more skills and agents as the business grows
