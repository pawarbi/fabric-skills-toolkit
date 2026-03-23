---
name: notebook-authoring-cli
description: >
  Create, read, update, and execute Microsoft Fabric Python notebooks via REST
  API from CLI environments using tools/notebook.py. Use when the user wants to:
  (1) create a notebook from .ipynb or scratch, (2) read/extract notebook cells,
  (3) update a notebook definition, (4) execute a notebook and poll for results,
  (5) list notebooks in a workspace.
  Triggers: "create fabric notebook", "run notebook via API", "read notebook cells",
  "update notebook definition", "list notebooks".
version: 1.0.0
tags: [fabric, notebook, crud, rest-api]
tools: [tools/notebook.py]
---

# Notebook Authoring CLI

This skill enables AI assistants to manage Microsoft Fabric Python notebooks
through the REST API. It covers the full lifecycle: create, read, update,
execute, and list. All operations go through `tools/notebook.py`, which handles
authentication, payload encoding, LRO polling, and format conversion.

## Prerequisites

- Python 3.11+
- Azure CLI installed and authenticated (`az login`)
- A Fabric workspace ID (GUID) for all operations
- For read/update/execute: the target notebook ID (use `list` to find it)

## Commands

### List notebooks

Find notebooks in a workspace. Use this to discover notebook IDs before
read/update/execute operations.

```bash
python tools/notebook.py list --workspace-id $WS_ID
python tools/notebook.py list --workspace-id $WS_ID --format json
```

The `--format json` variant returns a JSON array of objects with `id`,
`displayName`, and `description` fields.

### Create a notebook

Create a new notebook in a workspace. Accepts an optional source file.

```bash
# Empty notebook (jupyter/python3.11 kernel)
python tools/notebook.py create --workspace-id $WS_ID --name "My Notebook"

# From a .ipynb file (auto-converted to Fabric source format)
python tools/notebook.py create --workspace-id $WS_ID --name "My Notebook" --from-file analysis.ipynb

# From a notebook-content.py file (Fabric source format)
python tools/notebook.py create --workspace-id $WS_ID --name "My Notebook" --from-file notebook-content.py
```

Under the hood, the CLI:
1. Converts .ipynb to Fabric source format if needed
2. Base64-encodes the notebook-content.py and .platform files
3. POSTs to `/workspaces/{id}/notebooks` with `format: FabricGitSource`
4. Handles 201 (immediate success) or 202 (LRO polling)

### Read a notebook

Extract a notebook's content from the Fabric API.

```bash
# Human-readable markdown (default)
python tools/notebook.py read --workspace-id $WS_ID --notebook-id $NB_ID

# Structured JSON (array of cell objects with type and content)
python tools/notebook.py read --workspace-id $WS_ID --notebook-id $NB_ID --format json

# Raw Fabric source format (notebook-content.py)
python tools/notebook.py read --workspace-id $WS_ID --notebook-id $NB_ID --format raw
```

The read command calls `getDefinition` (which is an LRO), polls for completion,
fetches the result, and extracts `notebook-content.py` from the definition parts.

Output formats:
- `markdown` - renders code cells in fenced blocks and markdown cells as plain
  text; best for human reading
- `json` - returns `[{"type": "code"|"markdown", "content": "..."}]`; best for
  programmatic processing
- `raw` - the verbatim Fabric source format; best for round-trip editing

### Update a notebook

Replace a notebook's definition with content from a local file.

```bash
python tools/notebook.py update --workspace-id $WS_ID --notebook-id $NB_ID --from-file updated.ipynb
python tools/notebook.py update --workspace-id $WS_ID --notebook-id $NB_ID --from-file notebook-content.py --name "Renamed Notebook"
```

The `--name` flag sets the display name in the `.platform` file. If omitted,
defaults to "notebook".

The CLI sends both `notebook-content.py` and `.platform` in the definition
payload. Fabric's `updateDefinition` requires ALL files; partial updates are
not supported.

### Execute a notebook

Trigger a notebook run via the Job Scheduler API.

```bash
# Fire and forget
python tools/notebook.py execute --workspace-id $WS_ID --notebook-id $NB_ID

# Wait for completion (polls every 5s, default 300s timeout)
python tools/notebook.py execute --workspace-id $WS_ID --notebook-id $NB_ID --wait

# Custom timeout
python tools/notebook.py execute --workspace-id $WS_ID --notebook-id $NB_ID --wait --timeout 600
```

The execute command POSTs to the `/items/{id}/jobs/instances?jobType=RunNotebook`
endpoint. Without `--wait`, it returns immediately after the 202. With `--wait`,
it polls the Location header until the run succeeds, fails, or times out.

## Fabric Source Format

Fabric notebooks use a custom Python-file format called `notebook-content.py`
for Git integration and REST API definitions. This is NOT standard `.ipynb`.

Key markers:
- First line: `# Fabric notebook source`
- `# METADATA ********************` - metadata block boundary
- `# META {json}` - metadata lines (prefixed with `# META `)
- `# CELL ********************` - code cell boundary
- `# MARKDOWN ********************` - markdown cell boundary
- `# {text}` - markdown content lines (prefixed with `# `)

See [references/fabric-source-format.md](references/fabric-source-format.md)
for the complete format specification with examples.

## Must

- Always run `az login` before any commands (authentication via Azure CLI)
- Always handle LRO (Long Running Operation) responses: 202 means poll the
  Location header until status is Succeeded, then fetch `/result`
- Always use `format: FabricGitSource` in definition payloads
- The `.platform` file `logicalId` must be `"00000000-0000-0000-0000-000000000000"`
- When converting `.ipynb` to Fabric source, join all source lines first with
  `"".join(cell["source"])`, then split on `"\n"` to avoid trailing blank
  comment lines from line-ending newlines in the source array

## Prefer

- Use `--format markdown` when reading notebooks for human consumption
- Use `--format json` when reading notebooks for programmatic processing
- Use `--wait` when executing notebooks to get completion status
- Use `--from-file` with `.ipynb` files (automatic conversion handled)

## Avoid

- Do not use `synapse_pyspark` kernel; use `jupyter/python3.11`
- Do not include outputs in notebook definitions (they are stripped on import)
- Do not hardcode notebook IDs; use the `list` command to find them
- Do not set `shell=True` on Windows for subprocess calls with special
  characters; it causes `cmd.exe` to interpret `|`, `&`, `>` as operators

## Gotchas

- `sempy.fabric.list_items()` returns title-case columns: `Type`,
  `Display Name`, `Id`, `Description` (not snake_case)
- `sempy.fabric.list_tables()` has a known bug with schema-enabled lakehouses;
  use `notebookutils.fs.ls()` instead
- A 202 response body is literally the string `"null"`; guard with
  `body.strip() in ("", "null", '"null"')` before parsing
- `updateDefinition` requires ALL files (no partial updates); only send
  `draft/` files, not `published/` files (which cause 409 DuplicateDefinitionParts)
- On Windows, use `az.cmd` not `az` for subprocess calls; the CLI detects
  `os.name == "nt"` and handles this automatically
