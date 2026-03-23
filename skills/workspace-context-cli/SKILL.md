---
name: workspace-context-cli
description: Deploy and extract WORKSPACE-CONTEXT notebooks for Fabric workspace self-documentation
version: 1.0.0
tags: [fabric, workspace, context, documentation, governance]
tools: [tools/workspace_context.py]
---

# Workspace Context CLI

This skill enables AI assistants to deploy and extract WORKSPACE-CONTEXT
notebooks in Microsoft Fabric workspaces. A WORKSPACE-CONTEXT notebook is a
self-documentation pattern: a notebook that lives in every workspace,
auto-discovers items and schemas, captures curated knowledge (conventions,
projects, architecture), and outputs structured JSON for AI assistants.

Three audiences benefit:

- **Developers** get instant onboarding - open WORKSPACE-CONTEXT and see every
  item, who owns it, how they connect, and what conventions to follow.
- **AI assistants** get structured context (workspace ID, SQL endpoints, table
  schemas, conventions) without asking the user for each piece every session.
- **Governance teams** get a standardized inventory across workspaces.

All operations go through `tools/workspace_context.py`, which handles
authentication, template conversion, Fabric REST API calls, and LRO polling.

## What is WORKSPACE-CONTEXT?

A Fabric notebook that serves as the workspace's self-documentation. It is a
hybrid of executable code and curated markdown:

- **Auto-discovery cells** call `sempy.fabric` and `notebookutils` to inventory
  items, schemas, workspace settings, and relationships.
- **Curated markdown cells** document conventions, ownership, projects,
  architecture, gotchas, and changelog.
- **Structured output cell** prints machine-readable JSON combining
  auto-discovered metadata with curated context - this is what AI assistants
  read to bootstrap a session.

The notebook is a first-class Fabric item: visible in the workspace, executable,
deployable via pipelines, Git-integrated, and searchable.

## Prerequisites

- Azure CLI installed and authenticated (`az login`)
- Python 3.x
- This toolkit repo cloned locally
- A Fabric workspace ID (GUID) for all operations

## Commands

### Deploy

Deploy the WORKSPACE-CONTEXT template to a workspace. The command reads
`templates/WORKSPACE-CONTEXT.ipynb`, converts it to Fabric source format, and
creates or updates the notebook via the REST API.

```bash
python tools/workspace_context.py deploy --workspace-id "82ad2591-974a-..."
```

Behavior:
- If no notebook named WORKSPACE-CONTEXT exists, creates a new one
- If one already exists, updates its definition in place
- Handles 201 (immediate create), 202 (LRO polling), and 200 (immediate update)
- The template is always read from `templates/WORKSPACE-CONTEXT.ipynb`

### Extract

Extract context from an existing WORKSPACE-CONTEXT notebook without running it.
The command pulls the notebook definition via the Fabric API, parses the cells,
and outputs structured content.

```bash
# JSON output to stdout (array of {type, title, content} objects)
python tools/workspace_context.py extract --workspace-id "82ad2591-974a-..." --format json

# Markdown output saved to file
python tools/workspace_context.py extract --workspace-id "82ad2591-974a-..." --format markdown --output context.md
```

Output formats:
- `json` - array of objects, each with `type` ("code" or "markdown"), `title`
  (first heading or empty), and `content` (raw cell text). Best for
  programmatic consumption by AI assistants.
- `markdown` - concatenated cells with code fences around code cells. Best for
  human review and documentation.

The extract command does not run the notebook. It reads the notebook definition
(the source cells), not execution output.

## Notebook Structure

The WORKSPACE-CONTEXT template has 15 cells:

| # | Type | Purpose |
|---|------|---------|
| 0 | Markdown | Title and overview of the WORKSPACE-CONTEXT notebook |
| 1 | Code | Auto-discover workspace identity (name, ID, capacity) |
| 2 | Code | Workspace settings via Fabric REST APIs (Git status, Spark settings) |
| 3 | Code | Item inventory via `sempy.fabric.list_items()` |
| 4 | Markdown | Projects - purpose, items, data sources, data flow, business rules, sensitive data |
| 5 | Code | Project-to-item validation (flags orphan items not assigned to any project) |
| 6 | Markdown | Architecture and data flow (bronze -> silver -> gold -> semantic model) |
| 7 | Code | Schema discovery via `notebookutils.fs.ls()` for all lakehouses |
| 8 | Markdown | Schema conventions (naming, column standards, data types) |
| 9 | Markdown | Conventions and standards (naming patterns, branching, code standards, review process) |
| 10 | Markdown | Gotchas and lessons learned (workspace-specific hard-won knowledge) |
| 11 | Markdown | Ownership and contacts (item-level ownership table) |
| 12 | Markdown | Changelog (append-only log of major changes) |
| 13 | Code | AI assistant context - structured JSON combining auto-discovered and curated data |
| 14 | Code | Save context JSON to OneLake for programmatic access |

Cells 1, 2, 3, 5, 7, 13, and 14 are code cells that execute inside Fabric.
Cells 0, 4, 6, 8, 9, 10, 11, and 12 are markdown cells maintained by developers.

## Multi-Environment Strategy

### DEV (read-write)

The notebook is fully interactive. Developers maintain curated sections
(Projects, Conventions, Gotchas, Ownership, Changelog) and run auto-discovery
cells as needed. This is the source of truth.

### UAT/PROD (read-only)

Most teams restrict these workspaces to read-only. Two options:

1. **Deploy via pipeline** - the notebook deploys alongside other items.
   Lakehouse auto-binding rebinds to the target workspace. Run the notebook in
   the target stage to get that environment's metadata.
2. **Programmatic generation** - a pipeline runs the notebook or a script that
   writes `WORKSPACE-CONTEXT.json` to OneLake. No manual sections needed - PROD
   context is inventory/audit focused.

### Branched workspaces

When a developer uses Fabric's "Branch out" feature, they get an isolated
workspace with a copy of all items - including WORKSPACE-CONTEXT. The notebook
travels with the branch, so the developer's AI assistant immediately has the
same conventions, gotchas, and architecture understanding. Auto-discovery cells
re-run against the branched workspace, so the inventory reflects the isolated
environment.

## Must

- Always deploy using the `deploy` command (it handles create vs update
  automatically)
- Always use WORKSPACE-CONTEXT as the notebook name (all caps, stands out in the
  workspace item list and is the convention the extract command looks for)
- Run the notebook after deploying to populate auto-discovered sections (item
  inventory, schemas, workspace settings, AI context JSON)
- Keep the Projects section up to date as items are added or removed from the
  workspace

## Prefer

- Extract with `--format json` for programmatic consumption by AI assistants
- Extract with `--format markdown` for documentation and human review
- Fill in the Projects section with purpose, data sources, data flow, business
  rules, and sensitive data - this is the most valuable curated section
- Document gotchas as you discover them (workspace-specific lessons persist
  across AI sessions)

## Avoid

- Do not rename the notebook (WORKSPACE-CONTEXT is the convention that the CLI
  tool searches for by name)
- Do not delete auto-discovery code cells (they populate item inventory, schemas,
  and AI context on each run)
- Do not hardcode workspace IDs in the notebook (it uses runtime context via
  `sempy.fabric` and `notebookutils` to discover the current workspace)

## Gotchas

- `sempy.fabric.list_items()` returns title-case columns: `Type`,
  `Display Name`, `Id`, `Description` (not snake_case)
- `sempy.fabric.list_tables()` has a known bug with schema-enabled lakehouses -
  the notebook uses `notebookutils.fs.ls()` instead for reliable schema
  discovery
- Workspace settings APIs may return 403 if the user lacks Admin permissions -
  the notebook handles this gracefully and continues
- The notebook uses `notebookutils` which only works inside Fabric - it cannot
  be run locally or in a standard Jupyter environment
- The extract command reads the notebook definition (source cells), not
  execution output - run the notebook first if you need populated auto-discovery
  sections
