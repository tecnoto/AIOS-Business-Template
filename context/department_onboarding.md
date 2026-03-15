# Department Onboarding Guide

How to add a new department sub-agent to the AI Operating System.
Each department gets its own skills, context, args, and a DEPARTMENT.md that defines its scope.

## When This Applies

- "Add the sales department"
- "Create a marketing agent"
- "Onboard new department: operations"
- Setting up a multi-department AI OS

## Process

### Step 1: Create Department Directory

```bash
cp -r departments/_template/ departments/{{department_name}}/
```

### Step 2: Configure DEPARTMENT.md

Fill in the department's identity, scope, skills, context, and guardrails.
Reference `client_onboarding/02_department_map.md` for the org chart.

### Step 3: Build Department Skills

Create skills in `departments/{{department_name}}/skills/`:

```
departments/sales/skills/
├── lead-research/
│   ├── SKILL.md
│   └── scripts/
├── outreach-email/
│   ├── SKILL.md
│   └── scripts/
└── pipeline-tracker/
    ├── SKILL.md
    └── scripts/
```

Each skill follows the standard SKILL.md format with front matter.

### Step 4: Add Department Context

Populate `departments/{{department_name}}/context/` with department-specific knowledge:
- ICP for this department's customers
- Playbooks and processes
- Past performance data

### Step 5: Configure Department Args

Create department-specific behavior settings in `departments/{{department_name}}/args/`:

```yaml
# departments/sales/args/sales.yaml
department:
  name: sales
  lead: "Jane Smith"
  reporting_frequency: daily
  escalation_threshold: 3  # escalate after 3 failed attempts
```

### Step 6: Update Dashboard

The dashboard automatically picks up new departments via the `department` column in the database. No manual configuration needed — just ensure tasks and messages for this department are tagged with `department={{department_name}}`.

### Step 7: Test

1. Create a test task tagged with the new department
2. Verify it appears in the dashboard under the correct department
3. Run a department-specific skill to confirm it works
4. Generate the dashboard and verify the department hierarchy section

## Edge Cases

- **Department already exists**: Warn the user, offer to update instead
- **No skills defined yet**: Create the directory structure, add skills later
- **Enterprise with sub-teams**: Create sub-directories within the department for teams

## Output

- Department directory created with DEPARTMENT.md, skills/, context/, args/
- Department visible in the agent dashboard
- CEO agent aware of the new department's scope and capabilities
