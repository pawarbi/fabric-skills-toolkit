# Copilot Instructions - Fabric Skills Toolkit

## Project Overview

This is a developer toolkit for AI-assisted Microsoft Fabric skill development. It augments [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric) with persistent memory, real-time documentation wrappers, and a local analysis engine. It is **not** a runnable application - it's a collection of CLI tools, templates, and docs that users copy into their own projects.

## Architecture

```
tools/          Python CLI tools (standalone scripts, also importable as modules)
  analyze.py    DuckDB + matplotlib - query CSV/JSON/Parquet, chart, diff, report
  mslearn.py    MS Learn MCP wrapper (HTTP, no auth, Python stdlib only)
  context7.py   Context7 MCP wrapper (stdio, requires Node.js 18+ / npx)

templates/      Files users copy to ~/.copilot/ or .copilot/ and customize
  memory.json   Machine-readable persistent context (workspace IDs, endpoints, API patterns)
  CONTEXT.md    Human-readable preferences and lessons learned
  WORKSPACE-CONTEXT.ipynb  Fabric notebook template - workspace self-documentation

docs/           Reference guides (not code)
examples/       Workflow walkthroughs
```

### Tool design patterns

- Each tool in `tools/` works both as a **CLI script** (`python tools/analyze.py query "..."`) and as an **importable module** (`from tools.analyze import DuckDB, Chart`).
- `mslearn.py` uses HTTP-based MCP transport (Streamable HTTP) - no external dependencies beyond Python stdlib.
- `context7.py` uses stdio-based MCP transport - it spawns `npx @upstash/context7-mcp@latest` as a subprocess.
- `analyze.py` wraps DuckDB and matplotlib into four classes: `DuckDB`, `Chart`, `Diff`, `Report`.

### Persistent memory pattern

The toolkit's core concept is a two-file persistent memory system:
- `memory.json` - structured JSON for machine lookups (workspace GUIDs, SQL endpoints, API gotchas)
- `CONTEXT.md` - markdown for behavioral guidance (preferences, lessons learned, tool reference)

These live in `~/.copilot/` (user-level) or `.copilot/` (project-level). Templates are in `templates/`.

## Setup & Dependencies

```powershell
# One-click setup (Windows)
.\setup.ps1

# Manual: install Python deps
pip install duckdb matplotlib pandas

# Verify tools
python tools/analyze.py query "SELECT 1+1 AS answer"
python tools/mslearn.py search "fabric lakehouse"
python tools/context7.py search "pandas"          # requires Node.js 18+
```

Prerequisites: Python 3.10+, Node.js 18+ (for Context7), optionally .NET 8+ (for Fabric MCP Server).

## Available CLI Tools

```bash
# DuckDB analysis
python tools/analyze.py query "SELECT * FROM 'data/sales.csv' LIMIT 10"
python tools/analyze.py chart bar results.csv --x experiment --y accuracy --title "Results"
python tools/analyze.py diff file1.json file2.json --type json

# Microsoft Learn docs (no auth needed)
python tools/mslearn.py search "fabric data agent rest api"
python tools/mslearn.py fetch "https://learn.microsoft.com/en-us/fabric/..."
python tools/mslearn.py code "azure openai python"

# Context7 library docs (needs Node.js)
python tools/context7.py search "pandas"
python tools/context7.py docs "/pandas/pandas" --topic "read_parquet"
```

## Fabric API Conventions

When generating code that calls Fabric REST APIs, follow these hard-won rules:

- **LRO /result pattern**: After polling returns `"status": "Succeeded"`, you must make one more `GET {url}/result` to get the actual payload. The Succeeded response body contains only the status.
- **updateDefinition requires ALL files**: No partial updates. Omitting a file deletes it. Only send `draft/` files - including `published/` files causes `409 DuplicateDefinitionParts`.
- **Case-sensitive API paths**: CRUD uses `/dataAgents/` (camelCase), query uses `/dataagents/` (lowercase). Wrong casing -> silent 404.
- **Token audiences**: Fabric REST = `https://api.fabric.microsoft.com`, OneLake = `https://storage.azure.com`, Power BI = `https://analysis.windows.net/powerbi/api`.
- **202 responses**: Body is literally the string `null` - guard with `body.strip() in ("", "null", '"null"')`.
- **Data Agent queries**: Use OpenAI Assistants API format (threads + runs), not Chat Completions.
- **Windows subprocess**: Never use `shell=True` with CLI tools - special characters like `|` get interpreted by cmd.exe.
- **Auth**: Always use `sqlcmd -G` for Entra ID auth. Run `az login` before first SQL operation.
- **`sempy.fabric` column names**: `list_items()` returns columns with title case: `Type`, `Display Name`, `Id` - not snake_case.
- **`list_tables()` bug**: `sempy.fabric.list_tables()` does not work with schema-enabled lakehouses. Use `notebookutils.fs.ls(f"{abfss}/Tables")` instead to discover schemas and tables.

## Skill Authoring Conventions

When writing or editing Fabric skills (SKILL.md files):

- One skill = one job. Split authoring vs. consumption.
- Naming: `{endpoint}-{authoring|consumption}-{access}` (e.g., `sqldw-authoring-cli`).
- Include MUST DO / PREFER / AVOID sections for behavioral guidance.
- Description frontmatter: start with action verb, list numbered use cases, include trigger phrases.
- Keep token count under 10K (ideally under 5K). Move shared patterns to `common/`.
- Provide guidance and principles, not large copy-paste code blocks.
- Always tag code blocks with the language.
