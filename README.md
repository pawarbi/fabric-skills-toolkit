# Fabric Skills Toolkit

Skills, tools, and agents for AI-assisted Microsoft Fabric notebook development. Python notebooks only (for now).

## Why This Exists

AI coding assistants are powerful but they start blind in Fabric workspaces. They don't know what items exist, what IDs they have, what schemas the lakehouses use, what Spark runtime is configured, or what naming conventions the team follows. Every session starts with the developer manually feeding context or the AI making repeated API calls just to orient itself.

This plugin solves that with two things:

**1. WORKSPACE-CONTEXT notebook** - A notebook that lives in every workspace and serves two purposes:

- **For AI assistants**: It provides structured, machine-readable context (item IDs, schemas, settings, conventions) so the AI can start working immediately without discovery calls. The AI reads one notebook and knows everything about the workspace.
- **For human developers**: It's a living document that the team edits directly in the Fabric workspace. Developers update project mappings, document gotchas as they find them, record architecture decisions, and maintain conventions. It travels with the workspace - when someone branches off, the context comes with them. When a new team member joins, they open it and see everything without asking anyone.

The notebook auto-discovers what it can (items, schemas, Spark settings, Git connection) and leaves curated sections for the team to fill in (projects, conventions, architecture, gotchas, ownership).

**2. CLI tools for notebook CRUD** - Instead of the AI (or the developer) manually constructing REST API calls, handling Fabric source format conversion, polling long-running operations, and debugging 202 responses, the tools handle all of that. `notebook.py` gives you list/read/create/update/execute in one command. `workspace_context.py` deploys the template and extracts context without running the notebook.

### Workspace context vs repo context

WORKSPACE-CONTEXT is not a replacement for repo-level context files (like `.github/copilot-instructions.md` in GitHub or similar files in ADO repos). They serve different levels:

| | WORKSPACE-CONTEXT (workspace) | Repo context (GitHub/ADO) |
|---|---|---|
| **Lives in** | Fabric workspace (visible to all workspace users) | Git repo (visible to repo collaborators) |
| **Scope** | One workspace - its items, schemas, settings, conventions | One codebase - its architecture, patterns, build/test/deploy |
| **Updates** | Edited in Fabric UI, auto-discovers live metadata on each run | Edited in IDE, committed to version control |
| **Audience** | Fabric developers + AI assistants working in that workspace | Code developers + AI assistants working in that repo |
| **Travels with** | Workspace branches (Fabric "Branch out" feature) | Git branches |
| **Examples** | "Lakehouse uses schema-enabled tables", "Gold layer naming: dim_*, fact_*" | "Run tests with pytest", "API routes follow REST conventions" |

They complement each other. The repo context tells the AI how to write code. The workspace context tells the AI what's in the environment the code runs against. A developer working in Copilot CLI has repo context from the repo and can pull workspace context via `workspace_context.py extract`.

### What this means in practice

Without this plugin, a typical AI-assisted session starts with:
- "What's the workspace ID?" (developer looks it up)
- "What notebooks exist?" (AI calls list API, parses response)
- "What tables are in the lakehouse?" (AI calls another API)
- "What naming convention do you use?" (developer explains again)
- "What's the Spark runtime version?" (another API call)

With this plugin:
- AI reads WORKSPACE-CONTEXT and has the full picture: items, IDs, schemas, settings, conventions, project context
- AI uses `notebook.py` to create/read/update/execute without manual REST calls
- New developers open WORKSPACE-CONTEXT and see everything without asking anyone
- Branched workspaces carry the context with them
- UAT/PROD workspaces get context generated programmatically

### One instruction to rule them all

If every workspace has a WORKSPACE-CONTEXT notebook, developers only need one line in their repo-level instructions (e.g., `.github/copilot-instructions.md`):

> Always read the WORKSPACE-CONTEXT notebook first before writing any Fabric code.

That single instruction means the AI starts every session by pulling item IDs, schemas, settings, and conventions. No more "what's the workspace ID?", no more "what naming convention do you use?". The context is already there, maintained by the team, refreshed on each run.

### Cross-workspace projects

Many Fabric projects span multiple workspaces (ingestion, transformation, analytics, reporting). Each workspace has its own WORKSPACE-CONTEXT. The AI can extract context from all of them:

```bash
python tools/workspace_context.py extract --workspace-id INGEST_WS --format json --output ingest-context.json
python tools/workspace_context.py extract --workspace-id ANALYTICS_WS --format json --output analytics-context.json
```

Now the AI has item IDs, schemas, and conventions for both workspaces. It can write code that creates cross-workspace shortcuts, references tables in other lakehouses, or builds pipelines that span environments - all without asking the developer to look up a single ID.

### Freshness

Auto-discovered data goes stale as items are added, schemas change, and settings are updated. The notebook records a `last_refreshed` UTC timestamp every time it runs, so both AI assistants and developers know how current the data is. If the context is weeks old, re-run the notebook or deploy fresh via pipeline.

### How each component helps

| Component | What it does |
|-----------|-------------|
| WORKSPACE-CONTEXT.ipynb | Auto-discovers items, schemas, settings. Captures conventions, projects, architecture. Outputs structured JSON for AI consumption. |
| notebook.py | List, read, create, update, execute notebooks via CLI. Handles Fabric source format, LRO polling, auth. No manual REST calls. |
| workspace_context.py | Deploy the template to any workspace. Extract context without running the notebook. |
| Skills (SKILL.md) | Teach AI assistants the correct patterns: format conversion, API gotchas, naming conventions. |
| FabricNotebookDev agent | Orchestrates skills for end-to-end workflows: setup workspace, create notebooks, read context. |
| Compatibility files | Same capabilities in Claude, Cursor, Windsurf - not just Copilot. |

## What This Is

A standalone skill collection that gives AI coding assistants (GitHub Copilot, Claude, Cursor, Windsurf) the ability to work with Microsoft Fabric workspaces and notebooks. Follows the [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric) pattern: SKILL.md files teach the AI what to do, Python CLI tools do the work, and an agent orchestrates end-to-end workflows.

> **Note**: The WORKSPACE-CONTEXT notebook currently supports Python notebooks only. Scala/R/SQL notebook support may be added later.

## Quick Start

### Install as Plugin (GitHub Copilot CLI)

```
/plugin marketplace add pawarbi/fabric-skills-toolkit
/plugin install fabric-notebook-toolkit@fabric-skills-toolkit
```

### Install Manually

```powershell
# Clone and install
git clone https://github.com/pawarbi/fabric-skills-toolkit.git
cd fabric-skills-toolkit

# Windows
.\install.ps1

# macOS/Linux
chmod +x install.sh && ./install.sh
```

Installs to `~/.copilot/skills/fabric/`.

### Verify

```bash
python tools/notebook.py --help
python tools/workspace_context.py --help
```

## What's Included

### Skills (SKILL.md)

| Skill | Description |
|-------|-------------|
| notebook-authoring-cli | Create, read, update, execute Fabric notebooks via REST API |
| workspace-context-cli | Deploy and extract WORKSPACE-CONTEXT notebooks for workspace self-documentation |

### Tools (Python CLI)

| Tool | Description |
|------|-------------|
| tools/notebook.py | Notebook CRUD - list, read, create, update, execute |
| tools/workspace_context.py | Context deploy and extract |

### Agent

| Agent | Description |
|-------|-------------|
| FabricNotebookDev | Orchestrates both skills for end-to-end notebook development |

### Templates

| Template | Description |
|----------|-------------|
| WORKSPACE-CONTEXT.ipynb | Self-documenting workspace notebook (15 cells: auto-discovery + curated knowledge) |

### Compatibility

| File | Target |
|------|--------|
| CLAUDE.md | Claude Code / Claude Projects |
| .cursorrules | Cursor IDE |
| AGENTS.md | GitHub Copilot agents |
| .windsurfrules | Windsurf / Codeium |

## Project Structure

```
fabric-skills-toolkit/
├── README.md
├── package.json
├── install.ps1                              # Windows installer
├── install.sh                               # macOS/Linux installer
├── requirements.txt
│
├── skills/
│   ├── notebook-authoring-cli/
│   │   ├── SKILL.md                         # Notebook CRUD skill definition
│   │   └── references/                      # Fabric source format spec, etc.
│   └── workspace-context-cli/
│       ├── SKILL.md                         # Workspace context skill definition
│       └── references/
│
├── agents/
│   └── FabricNotebookDev.agent.md           # End-to-end agent definition
│
├── tools/
│   ├── notebook.py                          # Notebook list/read/create/update/execute
│   ├── workspace_context.py                 # Context deploy/extract
│   ├── analyze.py                           # DuckDB + matplotlib analysis
│   ├── context7.py                          # Context7 MCP wrapper (library docs)
│   └── mslearn.py                           # MS Learn MCP wrapper (Microsoft docs)
│
├── templates/
│   ├── WORKSPACE-CONTEXT.ipynb              # Workspace self-documentation notebook
│   ├── memory.json                          # Persistent memory template
│   └── CONTEXT.md                           # Human-readable context template
│
├── compatibility/
│   ├── CLAUDE.md                            # Claude Code / Claude Projects
│   ├── .cursorrules                         # Cursor IDE
│   ├── AGENTS.md                            # GitHub Copilot agents
│   └── .windsurfrules                       # Windsurf / Codeium
│
├── docs/
│   ├── workspace-context-guide.md           # WORKSPACE-CONTEXT deep dive
│   ├── skill-best-practices.md              # How to write Fabric skills
│   ├── fabric-api-gotchas.md                # Fabric API lessons learned
│   └── mcp-integration-guide.md             # MCP server integration
│
└── examples/
    ├── workspace-context-usage.md           # Multi-environment usage
    ├── workflow-examples.md                 # End-to-end workflows
    └── memory-usage.md                      # Persistent memory patterns
```

## CLI Reference

### notebook.py

```bash
# List notebooks in a workspace
python tools/notebook.py list --workspace-id WS_ID

# List notebooks as JSON (returns id, displayName, description)
python tools/notebook.py list --workspace-id WS_ID --format json

# Read notebook content (default: markdown)
python tools/notebook.py read --workspace-id WS_ID --notebook-id NB_ID

# Read as structured JSON (array of cell objects)
python tools/notebook.py read --workspace-id WS_ID --notebook-id NB_ID --format json

# Read as raw Fabric source format
python tools/notebook.py read --workspace-id WS_ID --notebook-id NB_ID --format raw

# Create empty notebook
python tools/notebook.py create --workspace-id WS_ID --name "My Notebook"

# Create from .ipynb file (auto-converts to Fabric source format)
python tools/notebook.py create --workspace-id WS_ID --name "My Notebook" --from-file analysis.ipynb

# Update notebook definition from file
python tools/notebook.py update --workspace-id WS_ID --notebook-id NB_ID --from-file updated.ipynb

# Execute notebook (fire and forget)
python tools/notebook.py execute --workspace-id WS_ID --notebook-id NB_ID

# Execute and wait for completion (polls every 5s, default 300s timeout)
python tools/notebook.py execute --workspace-id WS_ID --notebook-id NB_ID --wait

# Execute with custom timeout
python tools/notebook.py execute --workspace-id WS_ID --notebook-id NB_ID --wait --timeout 600
```

### workspace_context.py

```bash
# Deploy WORKSPACE-CONTEXT to a workspace (creates or updates)
python tools/workspace_context.py deploy --workspace-id WS_ID

# Extract context as JSON
python tools/workspace_context.py extract --workspace-id WS_ID --format json

# Extract context as markdown, save to file
python tools/workspace_context.py extract --workspace-id WS_ID --format markdown --output context.md
```

## WORKSPACE-CONTEXT Notebook

A Fabric notebook that serves as a workspace's self-documentation. It combines executable code cells that auto-discover workspace metadata with curated markdown cells that capture conventions, ownership, and architecture.

### What it auto-discovers

- Workspace identity (name, ID, capacity)
- Workspace settings (Git status, Spark settings)
- Item inventory via `sempy.fabric.list_items()`
- Lakehouse schemas via `notebookutils.fs.ls()`

### What developers curate

- Projects (purpose, items, data sources, data flow, business rules, sensitive data)
- Architecture and data flow (bronze -> silver -> gold -> semantic model)
- Schema conventions (naming, column standards, data types)
- Coding standards and naming patterns
- Gotchas and lessons learned
- Ownership and contacts
- Changelog

### Multi-environment strategy

- **DEV** (read-write) - fully interactive, developers maintain curated sections and run auto-discovery. This is the source of truth.
- **UAT/PROD** (read-only) - deploy via pipeline (lakehouse auto-binding rebinds to target workspace) or generate programmatically. Run the notebook in the target stage to get that environment's metadata.
- **Branched workspaces** - when a developer uses Fabric's "Branch out" feature, the notebook travels with the branch. Auto-discovery cells re-run against the branched workspace; curated sections carry over.

For the full guide, see [docs/workspace-context-guide.md](docs/workspace-context-guide.md).

## Prerequisites

- Python 3.x
- Azure CLI (`az login`)
- Access to a Fabric workspace

## Cross-Tool Support

Copy the appropriate file from `compatibility/` to your project root:

| AI Tool | What to copy |
|---------|-------------|
| Claude Code / Claude Projects | `compatibility/CLAUDE.md` -> `CLAUDE.md` |
| Cursor IDE | `compatibility/.cursorrules` -> `.cursorrules` |
| Windsurf / Codeium | `compatibility/.windsurfrules` -> `.windsurfrules` |
| GitHub Copilot agents | `compatibility/AGENTS.md` -> `.github/AGENTS.md` |

## Links

- [Workspace Context Guide](docs/workspace-context-guide.md)
- [Usage Examples](examples/workspace-context-usage.md)
- [Skill Best Practices](docs/skill-best-practices.md)
- [Fabric API Gotchas](docs/fabric-api-gotchas.md)
- [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric)

## License

MIT
