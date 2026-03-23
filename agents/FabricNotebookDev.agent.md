---
name: FabricNotebookDev
description: End-to-end Fabric notebook development - create, deploy, manage notebooks and workspace context
skills:
  - notebook-authoring-cli
  - workspace-context-cli
---

# FabricNotebookDev Agent

This agent orchestrates the notebook-authoring-cli and workspace-context-cli
skills to handle end-to-end Microsoft Fabric notebook development. It combines
notebook CRUD operations (create, read, update, execute, list) with workspace
context management (deploy and extract WORKSPACE-CONTEXT notebooks) so that AI
assistants can work with full awareness of the target workspace before creating
or modifying notebooks.

## When to Use

- Setting up a new Fabric workspace with self-documentation
- Creating notebooks that follow workspace conventions
- Reading existing notebooks for code review or understanding
- Deploying workspace context to DEV, UAT, or PROD environments
- Running notebooks and validating execution results
- Auditing workspace contents (items, schemas, ownership)

## Workflow: New Workspace Setup

1. Deploy the WORKSPACE-CONTEXT notebook to the target workspace:
   ```bash
   python tools/workspace_context.py deploy --workspace-id WS_ID
   ```
2. Execute the notebook to populate auto-discovered sections (item inventory,
   schemas, workspace settings, AI context JSON):
   ```bash
   python tools/notebook.py execute --workspace-id WS_ID --notebook-id NB_ID --wait
   ```
3. Extract the context to understand what the workspace contains:
   ```bash
   python tools/workspace_context.py extract --workspace-id WS_ID --format json
   ```
4. Create or update project notebooks as needed, using the extracted context to
   follow naming conventions, schema patterns, and architecture decisions.

## Workflow: Read Workspace State

1. Extract WORKSPACE-CONTEXT to get the full workspace inventory:
   ```bash
   python tools/workspace_context.py extract --workspace-id WS_ID --format json
   ```
2. Read specific notebooks for code review or analysis:
   ```bash
   python tools/notebook.py read --workspace-id WS_ID --notebook-id NB_ID --format markdown
   ```
3. Use the context JSON to make informed decisions about what to create, update,
   or how to structure new code.

## Workflow: Create and Deploy a Notebook

1. Extract workspace context first to understand conventions, naming patterns,
   schemas, and architecture:
   ```bash
   python tools/workspace_context.py extract --workspace-id WS_ID --format json
   ```
2. Create the notebook locally as a .ipynb file following the workspace
   conventions discovered in step 1.
3. Deploy via the create command:
   ```bash
   python tools/notebook.py create --workspace-id WS_ID --name "My Notebook" --from-file notebook.ipynb
   ```
4. Execute to validate that it runs without errors:
   ```bash
   python tools/notebook.py execute --workspace-id WS_ID --notebook-id NB_ID --wait
   ```

## Workflow: Multi-Environment

1. Deploy WORKSPACE-CONTEXT to the DEV workspace:
   ```bash
   python tools/workspace_context.py deploy --workspace-id DEV_WS_ID
   ```
2. Customize the curated sections (Projects, Conventions, Gotchas, Ownership,
   Changelog) in the Fabric portal.
3. For UAT/PROD: deploy the notebook programmatically via pipeline or use the
   deploy command with the target workspace ID. Run the notebook in the target
   environment to populate auto-discovered sections for that stage.

## Tool Reference

| Task | Command |
|------|---------|
| List notebooks | `python tools/notebook.py list --workspace-id WS_ID` |
| Read notebook | `python tools/notebook.py read --workspace-id WS_ID --notebook-id NB_ID --format markdown` |
| Create notebook | `python tools/notebook.py create --workspace-id WS_ID --name NAME --from-file FILE` |
| Update notebook | `python tools/notebook.py update --workspace-id WS_ID --notebook-id NB_ID --from-file FILE` |
| Execute notebook | `python tools/notebook.py execute --workspace-id WS_ID --notebook-id NB_ID --wait` |
| Deploy context | `python tools/workspace_context.py deploy --workspace-id WS_ID` |
| Extract context | `python tools/workspace_context.py extract --workspace-id WS_ID --format json` |

## Decisions

- Always extract workspace context before creating new notebooks (understand
  conventions first)
- Use WORKSPACE-CONTEXT (all caps) as the notebook name for the context notebook
- Prefer --format markdown for human review, --format json for programmatic use
- Always use --wait when executing notebooks to confirm success
- Use the list command to discover notebook IDs rather than hardcoding them
- Run the WORKSPACE-CONTEXT notebook after deploying to populate auto-discovered
  sections (item inventory, schemas, workspace settings)
