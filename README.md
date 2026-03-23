# Fabric Skills Toolkit

Skills, tools, and agents for AI-assisted Microsoft Fabric notebook development.

## What This Is

A standalone skill collection that gives AI coding assistants (GitHub Copilot, Claude, Cursor, Windsurf) the ability to work with Microsoft Fabric workspaces and notebooks. Follows the [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric) pattern: SKILL.md files teach the AI what to do, Python CLI tools do the work, and an agent orchestrates end-to-end workflows.

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
