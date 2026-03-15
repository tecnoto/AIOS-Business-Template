---
name: build-process
description: >
  Streamlined build process SOP for new projects. Handles "setting the stage" (idea → build order → tech stack),
  maintains build-order.md with HUMAN/AGENT task tagging, tracks progress with checkboxes, and continuously
  optimizes for speed-to-MVP. Applies to every new project.
  Use when the user says "new project", "set the stage", "build order", "what's next to build",
  "update build order", "mark complete", or when starting any new build.
user-invokable: true
argument-hint: "stage <project-name> | update | status | optimize"
---

# Skill: Build Process

Standardized SOP for taking a project from idea to MVP as fast as possible.

## Core Principles

1. **AGENT-first** — Default every task to AGENT. Only tag HUMAN when it genuinely requires human judgment, credentials, external approval, or physical action.
2. **Free/low-cost first** — Always prefer free tiers and open-source. Only recommend paid tools when free alternatives can't scale or are unreliable.
3. **Scalable choices only** — Every service, tool, and architecture decision must support 10x growth without rearchitecting.
4. **Token-efficient** — Apply SCHEMA 60/30/10 principle. Push reliability into deterministic code (60%), use rules/templates for consistency (30%), reserve AI judgment for creative decisions (10%).
5. **Minimize back-and-forth** — Don't ask "where do you want to start?" Present the logical build order. Only ask when there's a genuine fork in the road.

## Operations

### 1. Set the Stage (new project)

When starting a new project, follow this sequence WITHOUT asking for permission at each step:

```
Step 1: UNDERSTAND — Read the idea/vision (user explains or points to context docs)
Step 2: DEFINE — Capture: problem, ICP, core features (MVP only), success metrics
Step 3: TECH STACK — Recommend stack based on requirements + scalability + cost
Step 4: BUILD ORDER — Generate build-order.md with logical dependency chain
Step 5: SCAFFOLD — Create repo structure (scaffold with SCHEMA)
Step 6: BEGIN — Start building from item #1
```

**Output:** A `build-order.md` file in the project root.

### 2. Build Order Format

Every `build-order.md` follows this structure:

```markdown
# Build Order — [Project Name]

> Generated: [date] | Last updated: [date]
> Status: [phase] | MVP Target: [date or TBD]

## Tech Stack
| Layer | Choice | Why | Cost | Scales To |
|-------|--------|-----|------|-----------|

## Phase 1: Foundation
- [ ] **[AGENT]** Scaffold repo with SCHEMA framework
- [ ] **[AGENT]** Initialize git, .gitignore, .env.example
- [ ] **[AGENT]** Set up project CLAUDE.md and CONTEXT.md
- [ ] **[HUMAN]** Create accounts for required services (see accounts registry)
- [ ] **[AGENT]** Configure environment variables

## Phase 2: Core Build
- [ ] **[AGENT]** [feature 1 — most dependencies build on this]
- [ ] **[AGENT]** [feature 2]
- [ ] **[HUMAN]** [anything requiring external approval/credentials]

## Phase 3: Polish & Launch
- [ ] **[AGENT]** Testing and bug fixes
- [ ] **[HUMAN]** Content review and approval
- [ ] **[AGENT]** Deploy to staging
- [ ] **[HUMAN]** Final review
- [ ] **[AGENT]** Deploy to production

## Efficiency Log
| Date | Optimization | Impact | Applied To |
|------|-------------|--------|------------|
```

### 3. Updating Build Order

When completing a task:
```
- [x] **[AGENT]** ~~Scaffold repo with SCHEMA framework~~ ✓ 2026-03-14
```

When adding new tasks discovered during build:
- Insert at the correct dependency position (not just appended)
- Tag HUMAN/AGENT
- Note why it was added

### 4. Efficiency Analysis

After each phase completion, analyze the build process:

1. **Time audit** — Which tasks took longest? Could any be automated?
2. **HUMAN→AGENT conversion** — Were any HUMAN tasks actually doable by AGENT?
3. **Tool evaluation** — Did any tool slow us down? Is there a better alternative?
4. **Token audit** — Did we load unnecessary context? Can we optimize CONTEXT.md routing?
5. **Pattern extraction** — Is this build step common across projects? Should it become a skill or template?

Log findings in the Efficiency Log table at the bottom of build-order.md.

### 5. Continuous Improvement

After every project reaches MVP:
- Extract reusable patterns → update AIOS-Business-Template
- Extract reusable skills → add to the project's skill library
- Update this skill's recommended tech stack based on what worked
- Update SCHEMA framework if token efficiency improvements were found

## Default Tech Stack Recommendations

### Web Apps (Next.js)
| Layer | Recommendation | Cost | Why |
|-------|---------------|------|-----|
| Framework | Next.js (latest) | Free | Industry standard, Vercel-native, scales to millions |
| Hosting | Vercel | Free tier → $20/mo | Zero-config deploys, edge functions, analytics |
| Database | Supabase | Free tier → $25/mo | Postgres + Auth + Storage + Realtime, generous free tier |
| Auth | Supabase Auth | Free | Built-in, supports OAuth (Google, GitHub, etc.) |
| Payments | Stripe | 2.9% + $0.30/txn | Industry standard, scales infinitely |
| UI | shadcn/ui + Tailwind | Free | Copy-paste components, no vendor lock-in |
| Icons | Lucide | Free | Tree-shakeable, consistent with shadcn |
| Analytics | PostHog | Free tier (1M events) | Product analytics + session replay + feature flags |
| Email | Resend | Free tier (100/day) | Developer-friendly, scales to millions |
| DNS/Domain | Cloudflare | Free | Fast DNS, DDoS protection, edge caching |

### AI/Agent Projects
| Layer | Recommendation | Cost | Why |
|-------|---------------|------|-----|
| LLM | Claude API (Anthropic) | Pay-per-use | Best reasoning, native tool use |
| Vectors | Pinecone | Free tier (1 index) | Serverless, scales automatically |
| Memory | mem0 + Pinecone | Free | Automatic fact extraction + dedup |
| Embeddings | OpenAI text-embedding-3-small | $0.02/1M tokens | Best price/performance ratio |
| Local LLM | Ollama | Free | Offline capability, no API costs |

### Content/Marketing Projects
| Layer | Recommendation | Cost | Why |
|-------|---------------|------|-----|
| CMS | Markdown in repo | Free | Version-controlled, no vendor lock-in |
| Email marketing | ConvertKit or Beehiiv | Free tier | Creator-focused, scales with audience |
| Forms/Quizzes | Tally | Free tier | Clean, embeddable, Zapier-compatible |
| Automation | Zapier or n8n (self-hosted) | Free (n8n) | n8n is free self-hosted, Zapier for quick wins |
| Social scheduling | Buffer | Free tier (3 channels) | Simple, reliable, API available |

## HUMAN vs AGENT Decision Tree

```
Can it be done with code/CLI/API?
  YES → AGENT
  NO  → Is it a creative/strategic decision?
    YES → Does it have clear criteria?
      YES → AGENT (with human review)
      NO  → HUMAN
    NO  → Is it an external action (signup, payment, legal)?
      YES → HUMAN
      NO  → AGENT
```

**Always HUMAN:**
- Account creation (credentials)
- Payment/billing decisions
- Legal agreements
- Content approval for external publication
- Strategic pivots
- Domain purchases

**Always AGENT:**
- Repo scaffolding
- Code generation
- Configuration
- Testing
- Deployment (after human approval)
- Documentation
- Database migrations
- API integrations
- Build order generation
- Progress tracking

## Context Dependencies

- `coding_standards` rule (always-on) — code quality
- `security` rule (always-on) — credential handling
- `build-app` skill (optional) — for structured methodology on complex builds
- `memory` skill — accounts registry lookup when onboarding services
