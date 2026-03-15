# Context Layer (SCHEMA — C)

Domain knowledge that shapes AI reasoning quality and style.
Part of the **Context** layer in the SCHEMA framework.

## What Goes Here

- `brand_profile.md` — Voice, tone, visual identity (from onboarding)
- `icp.md` — Ideal Customer Profile descriptions
- `industry_knowledge.md` — Domain-specific facts and terminology
- `case_studies.md` — Past successes and patterns
- `competitor_landscape.md` — Competitive intelligence
- `department_onboarding.md` — Guide for adding new department sub-agents

## How to Use

Populate these files during client onboarding (see `client_onboarding/`).
The AI reads context files when reasoning about business decisions, writing content, or making recommendations.

**Context routing:** Check `CONTEXT.md` at the project root for which files to load per task type.
