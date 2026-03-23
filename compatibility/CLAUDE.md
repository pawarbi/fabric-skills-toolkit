# Fabric Skills Toolkit

Tools for managing Microsoft Fabric notebooks and workspace context via REST API.
All operations authenticate through Azure CLI (`az login`).

## Tools Available

### Notebook CRUD (tools/notebook.py)

Create, read, update, execute, and list Fabric Python notebooks.

```bash
# List notebooks in a workspace
python tools/notebook.py list --workspace-id WS_ID
python tools/notebook.py list --workspace-id WS_ID --format json

# Create a notebook (empty or from file)
python tools/notebook.py create --workspace-id WS_ID --name "My Notebook"
python tools/notebook.py create --workspace-id WS_ID --name "My Notebook" --from-file analysis.ipynb

# Read notebook content
python tools/notebook.py read --workspace-id WS_ID --notebook-id NB_ID
python tools/notebook.py read --workspace-id WS_ID --notebook-id NB_ID --format json
python tools/notebook.py read --workspace-id WS_ID --notebook-id NB_ID --format raw

# Update notebook definition
python tools/notebook.py update --workspace-id WS_ID --notebook-id NB_ID --from-file updated.ipynb

# Execute a notebook
python tools/notebook.py execute --workspace-id WS_ID --notebook-id NB_ID --wait
python tools/notebook.py execute --workspace-id WS_ID --notebook-id NB_ID --wait --timeout 600
```

Read formats: `markdown` (default, human-readable), `json` (structured cells), `raw` (Fabric source).

### Workspace Context (tools/workspace_context.py)

Deploy and extract WORKSPACE-CONTEXT notebooks - a self-documentation pattern for Fabric workspaces.

```bash
# Deploy template to a workspace (creates or updates)
python tools/workspace_context.py deploy --workspace-id WS_ID

# Extract context as JSON (for programmatic use)
python tools/workspace_context.py extract --workspace-id WS_ID --format json

# Extract context as markdown (for human review)
python tools/workspace_context.py extract --workspace-id WS_ID --format markdown --output context.md
```

The WORKSPACE-CONTEXT notebook auto-discovers workspace items, schemas, and settings,
and combines them with curated markdown sections (projects, conventions, gotchas, ownership).

## Key Conventions

- Authenticate via `az login` before any operations
- All API calls go through `https://api.fabric.microsoft.com/v1`
- Notebook definitions use Fabric source format (`notebook-content.py`), not `.ipynb`
- Definition payloads require `format: FabricGitSource` with base64-encoded parts
- The `.platform` file `logicalId` must be `"00000000-0000-0000-0000-000000000000"`
- Use `jupyter/python3.11` kernel, not `synapse_pyspark`
- 202 responses are Long Running Operations (LRO) - poll the `Location` header until status is `Succeeded`, then fetch `/result`
- `updateDefinition` requires ALL files (both `notebook-content.py` and `.platform`); partial updates are not supported
- Only send `draft/` files, not `published/` files (causes 409 DuplicateDefinitionParts)
- The WORKSPACE-CONTEXT notebook name must be all caps

## Gotchas

- `sempy.fabric.list_items()` returns title-case columns: `Type`, `Display Name`, `Id`, `Description` (not snake_case)
- `sempy.fabric.list_tables()` has a known bug with schema-enabled lakehouses; use `notebookutils.fs.ls()` instead
- A 202 response body may be the literal string `"null"`; guard with `body.strip() in ("", "null", '"null"')` before parsing
- On Windows, use `az.cmd` not `az` for subprocess calls; the CLI handles this automatically via `os.name == "nt"` check
- Workspace settings APIs may return 403 if the user lacks Admin permissions
- The extract command reads notebook source cells, not execution output - run the notebook first to populate auto-discovery sections
- When converting `.ipynb` to Fabric source, join source lines with `"".join(cell["source"])` then split on `"\n"` to avoid trailing blank comment lines
