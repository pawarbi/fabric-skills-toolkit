# Fabric Skills Toolkit

Skills, tools, and agents for AI-assisted Microsoft Fabric notebook development. Python notebooks only (for now).

## Why This Exists

AI coding assistants are powerful but they start blind in Fabric workspaces. They don't know what items exist, what IDs they have, what schemas the lakehouses use, what Spark runtime is configured, or what naming conventions the team follows. Every session starts with the developer manually feeding context or the AI making repeated API calls just to orient itself.

This plugin solves that with two things:

**1. WORKSPACE-CONTEXT notebook** - A notebook that lives in every workspace and builds a complete picture automatically. It calls the Fabric APIs to discover items, schemas, workspace settings, Spark configuration, and Git connection. Developers add curated sections for conventions, project mappings, architecture, and gotchas. The result: any AI assistant can read this one notebook and immediately know what's in the workspace, how things connect, and how the team works.

**2. CLI tools for notebook CRUD** - Instead of the AI (or the developer) manually constructing REST API calls, handling Fabric source format conversion, polling long-running operations, and debugging 202 responses, the tools handle all of that. `notebook.py` gives you list/read/create/update/execute in one command. `workspace_context.py` deploys the template and extracts context without running the notebook.

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
