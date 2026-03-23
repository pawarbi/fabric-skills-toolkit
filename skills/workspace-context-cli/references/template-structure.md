# WORKSPACE-CONTEXT Template Structure

The WORKSPACE-CONTEXT notebook template (`templates/WORKSPACE-CONTEXT.ipynb`)
has 15 cells that alternate between auto-discovery code and curated markdown.

## Cell Layout

| # | Type | Purpose |
|---|------|---------|
| 0 | Markdown | Title and overview - describes what the notebook is and how to use it |
| 1 | Code | Auto-discover workspace identity (name, ID, capacity via `sempy.fabric`) |
| 2 | Code | Workspace settings via Fabric REST APIs (Git status, Spark settings, capacity info) |
| 3 | Code | Item inventory via `sempy.fabric.list_items()` - lists all workspace items with type, name, ID |
| 4 | Markdown | Projects - rich template per project with purpose, ownership, items, data sources, data flow, business rules, sensitive data |
| 5 | Code | Project-to-item validation - cross-references project item lists against actual inventory, flags orphans |
| 6 | Markdown | Architecture and data flow - describes how data moves through the workspace (e.g., bronze -> silver -> gold) |
| 7 | Code | Schema discovery via `notebookutils.fs.ls()` - iterates lakehouses, discovers schemas and tables |
| 8 | Markdown | Schema conventions - naming patterns, column standards, data types |
| 9 | Markdown | Conventions and standards - naming patterns, branching strategy, code standards, review process |
| 10 | Markdown | Gotchas and lessons learned - workspace-specific hard-won knowledge |
| 11 | Markdown | Ownership and contacts - item-level ownership table |
| 12 | Markdown | Changelog - append-only log of major changes with dates |
| 13 | Code | AI assistant context - builds structured JSON combining auto-discovered metadata with curated sections |
| 14 | Code | Save context JSON to OneLake as WORKSPACE-CONTEXT.json for programmatic access |

## Auto-Discovered Sections

These code cells query live workspace metadata each time the notebook runs.
Their output stays current without manual maintenance.

**Cell 1 - Workspace Identity**: Uses `sempy.fabric` to get the current
workspace name and ID. Displays as a summary table.

**Cell 2 - Workspace Settings**: Calls Fabric REST APIs to retrieve Git
connection status, Spark compute settings, and capacity information. Handles
403 errors gracefully if the user lacks Admin permissions.

**Cell 3 - Item Inventory**: Calls `sempy.fabric.list_items()` to list every
item in the workspace. Returns columns: `Type`, `Display Name`, `Id`,
`Description`. Displays as a formatted table grouped by item type.

**Cell 5 - Project Validation**: Reads the project definitions from Cell 4 and
cross-references each project's listed items against the actual inventory from
Cell 3. Flags items that exist in the workspace but are not assigned to any
project (orphans).

**Cell 7 - Schema Discovery**: Iterates over all lakehouses in the workspace
and uses `notebookutils.fs.ls()` to discover schemas and tables. This approach
works with both schema-enabled and non-schema lakehouses (unlike
`sempy.fabric.list_tables()`, which has a known bug with schema-enabled
lakehouses).

**Cell 13 - AI Context JSON**: Builds a structured JSON object that combines
auto-discovered metadata (workspace ID, items, schemas) with curated sections
(conventions, gotchas, projects). This is the primary output for AI assistants.

## Curated Sections

These markdown cells are maintained by developers. They capture knowledge that
cannot be auto-discovered.

**Cell 0 - Title**: Overview of the notebook and instructions.

**Cell 4 - Projects**: The most valuable curated section. A workspace often
hosts items from multiple projects, but Fabric has no native "project" concept.
This section formalizes the grouping with:
- Purpose and ownership
- Which items belong to this project
- Data sources (ERPs, APIs, files)
- Data flow (how data moves through items)
- Business rules (fiscal year definitions, revenue formulas, segmentation logic)
- Sensitive data (PII columns, masking rules, retention policies)

**Cell 6 - Architecture**: Describes the overall data flow through the
workspace, e.g., "bronze lakehouse -> silver transform notebook -> gold
lakehouse -> semantic model -> Power BI report."

**Cell 8 - Schema Conventions**: Naming standards for schemas, tables, and
columns. Data type conventions. What each schema prefix means.

**Cell 9 - Conventions and Standards**: Team-level standards for naming items,
branching strategy, code review process, and coding patterns.

**Cell 10 - Gotchas**: Hard-won lessons specific to this workspace. Examples:
- "Silver lakehouse SQL endpoint is READ-ONLY - use Spark for writes"
- "orders table has 50M rows - always filter by order_date"
- "Deployment pipeline takes 8 min - do not re-trigger"

**Cell 11 - Ownership**: Item-level ownership table mapping each lakehouse,
pipeline, notebook, and semantic model to a responsible person or team.

**Cell 12 - Changelog**: Append-only log of major changes with dates. Gives
developers and AI assistants a sense of recent workspace evolution.

## AI Context JSON

Cell 13 builds a JSON object with this structure:

```json
{
  "workspace_id": "82ad2591-...",
  "workspace_name": "Sales Analytics - DEV",
  "stage": "development",
  "projects": {
    "Sales Analytics": {
      "owner": "@data-team-lead",
      "description": "End-to-end sales reporting",
      "status": "active",
      "items": ["bronze_lakehouse", "silver_transform", "gold_lakehouse"]
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

AI assistants read this output to bootstrap a session with full workspace
awareness - no need to ask the user for workspace ID, SQL endpoints, table
names, or conventions.

## OneLake Output

Cell 14 saves the AI context JSON to OneLake as a file:

```
abfss://<workspace-id>@onelake.dfs.fabric.microsoft.com/<lakehouse-id>/Files/WORKSPACE-CONTEXT.json
```

This enables programmatic access to workspace context without running the
notebook interactively. Use cases:

- CI/CD pipelines that need workspace metadata
- AI assistants that read context from OneLake directly
- Governance scripts that audit multiple workspaces
- Scheduled pipeline runs that refresh the context file on a cadence

The save cell requires a default lakehouse to be attached to the notebook.
