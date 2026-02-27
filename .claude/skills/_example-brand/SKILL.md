---
name: brand-images
description: Generate branded images using DALL-E 3 with business-specific style guidelines
triggers:
  - generate image
  - create hero image
  - make illustration
  - generate graphics
  - create banner
tools: [generate_images.py]
---

# Skill: Brand Image Generation

> Example brand skill — customize for your business.
> This pattern shows how to create client-specific skills that wrap generic tools
> with business-specific context (brand colors, style, voice).

## How to Customize

1. Copy this directory: `cp -r _example-brand/ my-brand/`
2. Edit `SKILL.md` — update the name, description, and triggers
3. Edit `scripts/generate_images.py` — replace BRAND_STYLES with your brand
4. Add brand assets to a `references/` directory if needed

## Usage

```bash
python3 .claude/skills/my-brand/scripts/generate_images.py \
  --type hero \
  --prompt "Modern SaaS dashboard with analytics" \
  --output builds/my-site/public/images/
```

## The Pattern

Every brand skill follows this structure:
1. **SKILL.md** — Defines what the skill does and when to trigger it
2. **scripts/** — Executable code that does the work
3. **references/** — Brand guidelines, color palettes, style examples

The key insight: the **mechanism** (DALL-E API wrapper) is generic.
The **content** (brand colors, style prompts, output paths) is client-specific.
Separate them clearly.
