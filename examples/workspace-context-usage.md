# Workspace Context Notebook - Usage Guide

> How to import, customize, and use the workspace-context notebook across dev/test/prod workspaces.

---

## Quick Start

### Step 1: Import into Your Workspace

1. Download `templates/WORKSPACE-CONTEXT.ipynb` from this repo
2. Open your Fabric workspace in the browser
3. Click **Import** -> **Notebook** -> select the `.ipynb` file
4. The notebook appears in your workspace as "WORKSPACE-CONTEXT"

### Step 2: Customize the Curated Sections

Open the notebook and edit the markdown cells:

**Section 1 - Workspace Identity**: Replace the placeholder table with your actual workspace name, ID, stage, capacity, owner, and Git repo.

**Projects - Project Registry**: Fill in the markdown template for each project in the workspace. This is the most valuable section for AI-assisted coding. Include:
- **Purpose**: One sentence on what the project does
- **Items table**: Map each workspace item to its role in this project
- **Data sources**: Where does data come from?
- **Data flow**: Draw the lineage (source -> pipeline -> lakehouse -> model -> report)
- **Business rules**: Fiscal year start, revenue formulas, segmentation logic, currency rules - anything an AI needs to generate correct code
- **Sensitive data**: PII columns, masking rules, retention policies

Then update the `PROJECT_ITEMS` dictionary in the validation code cell to match.

**Section 4 - Architecture**: Describe how your items relate. Delete the example rows and add your own. If you don't have a bronze/silver/gold pattern, describe whatever architecture you do have.

**Section 5 - Conventions**: Update naming patterns, branching strategy, and code standards to match your team's actual practices. Delete anything that doesn't apply.

**Section 6 - Gotchas**: Start with any lessons you've already learned. This list grows over time - add entries when you discover something the hard way.

**Section 7 - Ownership**: Fill in who owns each major item. This is the section new team members will thank you for.

### Step 3: Run the Auto-Discovery Cells

Click **Run All** or run cells individually:

- **Cell 2** discovers the workspace ID and name via `notebookutils.runtime.context`
- **Cell 3** lists all items via `sempy.fabric.list_items()`
- **Cell 5** validates the project-to-item mapping and flags orphans
- **Cell 7** discovers tables in each lakehouse via `notebookutils.fs.ls()`
- **Cell 13** generates the structured JSON context combining auto-discovered + curated data

Review the output. If any API calls fail, check:
- Do you have Contributor role on the workspace?
- Is the Spark session started (code cells require compute)?
- Are the lakehouse names correct in Section 5?

### Step 4: Tell Your AI Assistant

Add to your custom instructions (`.github/copilot-instructions.md`, `CLAUDE.md`, `.cursorrules`, etc.):

```markdown
At session start, check if this workspace has a `WORKSPACE-CONTEXT` notebook.
If so, read its structured JSON output (last code cell) for workspace metadata,
schemas, conventions, and gotchas.
```

Or copy the JSON output into your `.copilot/memory.json`.

---

## Using Across Dev/Test/Prod

### DEV Workspace (Read-Write)

This is where you maintain the notebook. Edit markdown cells, run auto-discovery, and commit to Git.

The notebook evolves as your workspace evolves:
- Added a new lakehouse? Re-run auto-discovery
- Discovered a gotcha? Add it to Section 6
- Team member changed? Update ownership

### Deploying to TEST / PROD

#### Option A: Deployment Pipeline

If your workspace uses Fabric deployment pipelines:

1. The notebook deploys alongside other items
2. Lakehouse auto-binding remaps the default lakehouse to the target workspace
3. When someone runs the notebook in PROD, the auto-discovery cells query **PROD metadata**
4. The curated sections (conventions, ownership) carry over from DEV - which is usually correct

This is the simplest approach. The notebook "just works" in each stage.

#### Option B: Programmatic Generation (Read-Only Workspaces)

If contributors can't create or edit notebooks in UAT/PROD:

1. Uncomment the last code cell ("Save context to OneLake")
2. Set up a Fabric pipeline with a **Notebook activity** that runs `WORKSPACE-CONTEXT`
3. Schedule it daily/weekly
4. The pipeline runs the auto-discovery cells and writes `WORKSPACE-CONTEXT.json` to OneLake

External tools and AI assistants can then read the JSON from OneLake without needing to run the notebook.

```
Pipeline: pl_workspace_context_refresh
  └── Notebook Activity: WORKSPACE-CONTEXT
       └── Output: /lakehouse/default/Files/WORKSPACE-CONTEXT.json
```

---

## Integrating with the Toolkit

### Feeding memory.json

After running the notebook, copy the JSON output from Section 10 into your `memory.json`:

```json
{
  "workspaces": {
    "sales_dev": {
      "id": "from-notebook-output",
      "note": "Sales Analytics - DEV"
    }
  },
  "lakehouses": {
    "bronze_lakehouse": {
      "tables": ["from", "notebook", "output"]
    }
  }
}
```

The notebook is the authoritative source; `memory.json` is the offline cache for AI sessions that can't access the workspace directly.

### Comparing Across Workspaces

If you have `WORKSPACE-CONTEXT.json` files from multiple workspaces (DEV, TEST, PROD), use the toolkit's diff tool:

```bash
python tools/analyze.py diff dev-context.json prod-context.json --type json
```

This shows what's different between environments - new tables in DEV not yet in PROD, missing items, schema drift.

---

## Maintenance Tips

1. **Re-run auto-discovery monthly** or after major changes (new lakehouses, schema updates)
2. **Update gotchas immediately** - when you discover something, add it before you forget
3. **Keep the changelog current** - major changes only, one line each
4. **Review ownership quarterly** - people change teams
5. **Commit to Git** - the notebook should be version-controlled alongside your other items
