# Workspace Context Notebook - A Self-Documentation Pattern for Microsoft Fabric

> **TL;DR**: Put a `WORKSPACE-CONTEXT` notebook in every Fabric workspace. It auto-discovers items and schemas, documents conventions and ownership, and outputs structured context for AI assistants. One notebook, three audiences: developers, AI tools, and governance.

---

## The Problem

Fabric workspaces accumulate items - lakehouses, warehouses, notebooks, pipelines, semantic models, data agents - but there's no built-in way to answer:

- **"What's in this workspace and how does it all connect?"**
- **"What are the conventions here?"**
- **"What should I know before making changes?"**

This context gap hurts three audiences:

| Audience | Pain | Cost |
|----------|------|------|
| **New developer** | Reverse-engineers everything from scratch | Days of ramp-up |
| **AI assistant** | Re-asks for workspace ID, schemas, conventions every session | 5-10 min × dozens of sessions |
| **Governance team** | No standardized way to audit what's in a workspace | Sprawl, compliance risk |

## The Solution

A **WORKSPACE-CONTEXT notebook** - a Fabric notebook that lives in every workspace and serves as the workspace's self-documentation. It's a hybrid:

- **Auto-discovery cells** call `sempy.fabric` and `notebookutils` to inventory items, schemas, and relationships
- **Curated markdown cells** document conventions, ownership, gotchas, and changelog
- **Structured output cell** prints machine-readable JSON for AI assistants

### Why a Notebook (Not a Wiki Page or Markdown File)

1. **First-class Fabric item** - visible in the workspace alongside everything else
2. **Executable** - auto-discovery cells stay current by querying live metadata
3. **Deployable** - Fabric deployment pipelines carry notebooks across stages with lakehouse auto-binding
4. **Dual-audience** - markdown for humans, code output for AI/machine consumption
5. **Git-integrated** - stored as `notebook-content.py` in Git, versioned, diffable
6. **Searchable** - workspace search finds notebook content

---

## Who Benefits and How

### Multi-Developer Teams

**Onboarding**: A new team member opens `WORKSPACE-CONTEXT`, sees every item, who owns it, how they connect, and what conventions to follow - without asking anyone.

**Conventions at the source**: Naming patterns, branching strategy, and code standards live *in the workspace*, not in a wiki nobody reads. When a developer creates a new notebook, they see the naming convention right next to the other notebooks.

**Ownership clarity**: An item-level ownership table answers "who do I ask about the silver lakehouse transform?" without Slack archaeology.

**Project context**: When multiple projects share a workspace, the project registry makes it clear which items belong to which initiative - and who's responsible for each grouping.

### AI-Assisted Development

**Session bootstrap**: An AI assistant reads the structured output cell and instantly knows the workspace ID, SQL endpoints, table schemas, and conventions. No more:

```
AI: "What's your workspace ID?"
You: "82ad2591-974a-..."
AI: "What's the SQL endpoint?"
You: "xpkymsttihxelp6..."
```

**Reduced hallucination**: Auto-discovered schemas mean the AI generates correct table and column names instead of guessing. Documented conventions mean it uses the right auth pattern, naming style, and branching strategy.

**Cross-session learning**: Gotchas persist in the notebook. The AI doesn't re-learn that the orders table has 50M rows or that the SQL endpoint is read-only.

### Governance

**Workspace audit**: Run the notebook and get a current inventory of all items with types and IDs. If every workspace uses the same structure, governance teams can compare workspaces programmatically.

**Stage awareness**: The notebook clearly labels "this is DEV" or "this is PROD." This sounds trivial, but it prevents accidental production changes - especially for AI assistants that don't inherently know which workspace they're operating in.

---

## Notebook Structure

The template has 9 sections, alternating between manually maintained markdown and auto-discovery code:

### Section 1: Workspace Identity *(Markdown)*

A table with workspace name, ID, deployment stage, capacity, owner, team, Git repo, and related workspaces (DEV/TEST/PROD counterparts). This is the "business card" of the workspace.

### Section 2: Item Inventory *(Code)*

Calls `sempy.fabric.list_items()` to auto-discover everything in the workspace. Followed by a curated markdown cell describing the architecture and data flow (e.g., "bronze -> silver -> gold -> semantic model -> reports").

### Section 3: Projects *(Markdown + Code)*

A workspace often hosts items from multiple projects, but Fabric has no native "project" concept - the grouping is tribal knowledge. This section formalizes it with a rich markdown template per project that includes:

- **Purpose & ownership** - what business problem it solves and who's responsible
- **Items** - which lakehouses, notebooks, pipelines, and models belong to this project
- **Data sources** - where data comes from (ERPs, APIs, files, etc.)
- **Data flow** - how data moves through the items (lineage)
- **Business rules** - domain-specific logic that AI assistants must know to generate correct code (fiscal year definitions, revenue formulas, customer segmentation rules, currency handling)
- **Sensitive data** - PII columns, masking rules, retention policies

The business rules field is especially critical for AI-assisted development - without it, an AI assistant will guess at formulas, fiscal calendars, and segmentation logic.

A lightweight validation code cell cross-references the project->item mapping against the actual workspace inventory and flags orphan items not assigned to any project.

### Section 4: Schema Discovery *(Code + Markdown)*

Iterates over lakehouses and uses `notebookutils.fs.ls()` to discover schemas and tables. This approach works with both schema-enabled and non-schema lakehouses (unlike `sempy.fabric.list_tables()`, which has a known bug with schema-enabled lakehouses). Followed by curated notes on naming conventions, column standards, and data types.

### Section 5: Conventions & Standards *(Markdown)*

Naming patterns, branching strategy, code standards, review process. These are the conventions a new developer (or AI) needs to follow.

### Section 6: Gotchas & Lessons Learned *(Markdown)*

Hard-won lessons specific to this workspace. Examples:
- "Silver lakehouse SQL endpoint is READ-ONLY - use Spark for writes"
- "`orders` table has ~50M rows - always filter by `order_date`"
- "Deployment pipeline takes ~8 min - don't re-trigger"

### Section 7: Ownership & Contacts *(Markdown)*

Item-level ownership table: who owns each lakehouse, pipeline, semantic model, and who to contact for questions.

### Section 8: Changelog *(Markdown)*

Append-only log of major changes with dates. Gives developers and AI a sense of recent evolution.

### Section 9: AI Assistant Context *(Code)*

The payoff cell. Outputs a structured JSON object combining auto-discovered metadata with manually curated context. This is what an AI assistant reads to bootstrap a session:

```json
{
  "workspace_id": "82ad2591-...",
  "workspace_name": "Sales Analytics - DEV",
  "stage": "development",
  "projects": {
    "Sales Analytics": {
      "owner": "@data-team-lead",
      "description": "End-to-end sales reporting from ERP to Power BI",
      "status": "active",
      "items": ["bronze_lakehouse", "silver_orders_transform", "gold_lakehouse", "sales_model"]
    }
  },
  "lakehouses": {
    "bronze_lakehouse": {
      "dbo": ["customers", "orders", "products"]
    }
  },
  "conventions": {
    "naming": "snake_case",
    "date_columns": "*_date for DATE, *_at for DATETIME2"
  },
  "gotchas": [
    "Silver SQL endpoint is read-only",
    "orders table: always filter by order_date (50M rows)"
  ]
}
```

---

## Dev/Test/Prod Workspaces

### Branched Workspaces (Feature Development)

When a developer uses Fabric's **"Branch out"** feature, they get an isolated workspace with a copy of all items - including the WORKSPACE-CONTEXT notebook. This means:

- The developer's AI assistant immediately has the same conventions, gotchas, and architecture understanding as the shared DEV workspace
- Auto-discovery cells re-run against the branched workspace, so the inventory reflects their isolated environment
- No context gap between "what the team knows" and "what my AI assistant knows"

This is one of the strongest arguments for keeping context in-workspace rather than in an external wiki or config file - it travels with the workspace.

### DEV Workspace (Read-Write)

The notebook is fully interactive. Developers maintain the curated sections and run auto-discovery cells as needed. This is the "source of truth" for conventions, ownership, and lessons learned.

### UAT/PROD Workspaces (Read-Only)

Most teams restrict UAT and PROD to read-only access. Two approaches:

#### Approach 1: Deploy from DEV via Deployment Pipeline

The notebook deploys alongside other items. Lakehouse auto-binding rebinds the default lakehouse to the target workspace. When someone runs the notebook in PROD, the auto-discovery cells query PROD metadata, so the inventory reflects the production state.

The curated sections (conventions, ownership) carry over from DEV, which is usually correct - conventions flow downstream.

#### Approach 2: Programmatic Generation

A Fabric pipeline runs a notebook or script that:
1. Calls `sempy.fabric.list_items()` and `notebookutils.fs.ls()` against the PROD workspace
2. Writes a `WORKSPACE-CONTEXT.json` to OneLake

No manual sections needed. PROD context is inventory/audit focused - it answers "what's deployed here?" not "how do we work?"

This approach is better when:
- Contributors can't create notebooks in PROD
- You want a machine-readable artifact without running a notebook
- You need scheduled refreshes (daily/weekly via pipeline trigger)

---

## How to Use the Template

### Step 1: Import

Download `templates/WORKSPACE-CONTEXT.ipynb` and import it into your Fabric workspace:
- Open the workspace in Fabric portal
- Click **Import** -> **Notebook** -> select the `.ipynb` file
- Keep the name `WORKSPACE-CONTEXT` (all caps so it stands out in the workspace item list)

### Step 2: Customize the Curated Sections

Fill in the markdown cells:
- **Section 1**: Your workspace name, ID, stage, owner, team
- **Section 3**: Define your projects - purpose, items, data sources, data flow, business rules, sensitive data
- **Section 5**: Your naming conventions, branching strategy, code standards
- **Section 6**: Any gotchas you've already discovered
- **Section 7**: Item ownership table
- **Section 8**: Initial changelog entry

### Step 3: Run the Auto-Discovery Cells

Execute the notebook. The code cells will:
- List all items in the workspace (Section 2)
- Discover table schemas for each lakehouse (Section 3)
- Generate the structured JSON context (Section 8)

Review the output. If any API calls fail or return unexpected results, adjust the code.

### Step 4: Integrate with AI Assistants

Tell your AI assistant to read the notebook's output. For example, in your custom instructions:

```markdown
At session start, check if this workspace has a `WORKSPACE-CONTEXT` notebook.
If so, read its structured output for workspace metadata, schemas, and conventions.
```

Or copy the JSON output from Section 8 into your `.copilot/memory.json` for offline access.

### Step 5: Maintain

- **After major changes**: Update the changelog (Section 7)
- **After new discoveries**: Add gotchas (Section 5)
- **Periodically**: Re-run auto-discovery cells to refresh item/schema inventory
- **On team changes**: Update ownership table (Section 6)

---

## Integration with This Toolkit

The WORKSPACE-CONTEXT notebook complements the existing toolkit:

| Component | Scope | Format |
|-----------|-------|--------|
| `memory.json` | User/project-level | Machine-readable JSON |
| `CONTEXT.md` | User/project-level | Human-readable markdown |
| **WORKSPACE-CONTEXT notebook** | Workspace-level | Both (executable) |

They work together:
1. The **notebook** discovers metadata and documents conventions *in the workspace*
2. The structured output feeds into **memory.json** for offline/cross-workspace use
3. **CONTEXT.md** references the notebook as the authoritative source for workspace-specific context

---

## FAQ

**Q: Won't the curated sections go stale?**
A: Yes - that's the #1 risk. Mitigate it by: (1) keeping curated sections short and high-level, (2) relying on auto-discovery for anything that can be discovered, (3) adding a "last reviewed" date to Section 1, (4) making the notebook part of your onboarding checklist so new team members update it.

**Q: Can Viewer-role users run the code cells?**
A: No - code cells require at least Contributor role. Viewers can read the markdown cells and any previously-rendered output, but can't execute code. This is another reason the programmatic approach works better for read-only workspaces.

**Q: What if I have 10 lakehouses? Won't the schema discovery be slow?**
A: `notebookutils.fs.ls()` is fast for individual lakehouses. If you have many, consider limiting auto-discovery to the most important ones and listing others by name only.

**Q: Should every workspace have one, even small/temporary ones?**
A: No. This pattern is most valuable for shared workspaces with multiple contributors or workspaces that persist across sprints. Personal scratch workspaces don't need it.
