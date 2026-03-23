# Available Agents

## FabricNotebookDev

Agent concept for Fabric notebook development workflows. Not yet implemented as a standalone agent file.

Intended capabilities:
- Create, read, update, and execute Fabric Python notebooks via REST API
- Convert between .ipynb and Fabric source format
- Deploy and extract WORKSPACE-CONTEXT self-documentation notebooks
- Handle LRO polling for all async Fabric API operations
- Manage notebook definitions with proper base64 encoding and .platform metadata

Delegate to this agent when the user wants to:
- Build or modify Fabric notebooks programmatically
- Deploy workspace documentation
- Extract workspace context for onboarding or governance
- Run notebooks via the Job Scheduler API

## Available Skills

### notebook-authoring-cli

Full lifecycle management for Fabric Python notebooks: create, read, update, execute, list.

Triggers: "create fabric notebook", "run notebook via API", "read notebook cells", "update notebook definition", "list notebooks".

Tool: tools/notebook.py

### workspace-context-cli

Deploy and extract WORKSPACE-CONTEXT notebooks for workspace self-documentation.

Triggers: "deploy workspace context", "extract workspace context", "workspace documentation".

Tool: tools/workspace_context.py

## Available Tools

### tools/notebook.py

Fabric Notebook CRUD operations via REST API.

```bash
python tools/notebook.py list --workspace-id WS_ID [--format json]
python tools/notebook.py create --workspace-id WS_ID --name NAME [--from-file FILE]
python tools/notebook.py read --workspace-id WS_ID --notebook-id NB_ID [--format json|markdown|raw]
python tools/notebook.py update --workspace-id WS_ID --notebook-id NB_ID --from-file FILE [--name NAME]
python tools/notebook.py execute --workspace-id WS_ID --notebook-id NB_ID [--wait] [--timeout SEC]
```

### tools/workspace_context.py

WORKSPACE-CONTEXT notebook deployment and extraction.

```bash
python tools/workspace_context.py deploy --workspace-id WS_ID
python tools/workspace_context.py extract --workspace-id WS_ID [--format json|markdown] [--output FILE]
```

## Prerequisites

- Python 3.11+
- Azure CLI installed and authenticated (`az login`)
- A Fabric workspace ID (GUID) for all operations

## Coordination Notes

- Both tools authenticate via Azure CLI tokens. Ensure `az login` is current before delegating.
- Use `list` to discover notebook IDs before read/update/execute operations.
- The workspace_context.py tool imports from notebook.py (shared auth, API helpers, format conversion).
- All Fabric API calls go through `https://api.fabric.microsoft.com/v1`.
- 202 responses require LRO polling via the Location header.
