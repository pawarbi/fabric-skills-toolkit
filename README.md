# Supercharging Microsoft Fabric Skills: A Developer Toolkit for AI-Assisted Development

> **TL;DR**: After 36+ Copilot sessions building Fabric skills, I kept hitting the same problems: the AI assistant forgets workspace IDs every session, hallucinates deprecated APIs, and can't query live data. So I built a toolkit that fixes all of it — persistent memory, real-time doc wrappers, and an analysis engine. This repo has everything you need to use it with [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric).

---

## Table of Contents

- [The Problem](#the-problem)
- [The Toolkit](#the-toolkit)
- [Project Structure](#project-structure)
- [Setup Guide](#setup-guide)
- [Tool Deep Dives](#tool-deep-dives)
  - [Persistent Memory](#1-persistent-memory)
  - [MS Learn MCP Wrapper](#2-ms-learn-mcp-wrapper)
  - [Context7 MCP Wrapper](#3-context7-mcp-wrapper)
  - [Analysis Toolkit (DuckDB)](#4-analysis-toolkit-duckdb)
  - [Fabric MCP Server (OneLake)](#5-fabric-mcp-server-onelake)
- [Skill Best Practices](#skill-best-practices)
- [Fabric API Lessons Learned](#fabric-api-lessons-learned)
- [How This Works with Skills-for-Fabric](#how-this-works-with-skills-for-fabric)
- [Contributing](#contributing)

---

## The Problem

If you use AI coding assistants (GitHub Copilot CLI, Claude Code, Cursor, etc.) with [Microsoft Fabric skills](https://github.com/microsoft/skills-for-fabric), you've probably hit these walls:

### 1. The Amnesia Problem
Every new session starts from zero. Your AI assistant:
- Forgets which workspace you're using (`82ad2591-974a-4ad4-ace6-...what?`)
- Rediscovers the same API patterns you taught it yesterday
- Loses track of what worked and what didn't

### 2. The Hallucination Problem
Fabric APIs evolve fast. Your AI assistant:
- Suggests deprecated API parameters
- Generates wrong authentication patterns
- Uses outdated SDK methods that no longer exist

### 3. The "Skills Teach, Tools Do" Gap
Skills tell the AI *what to do* (use `sqlcmd -G` for auth, prefer T-SQL for warehouse queries). But the AI still needs *tools to do it* — query OneLake files, analyze data, compare configurations. Skills provide knowledge; tools provide capability.

### 4. The Scattered Context Problem
Your Fabric environment context lives in your head:
- SQL endpoint URLs, lakehouse IDs, schema names
- Which tables have Portuguese column names vs. English
- Which API quirks you've already worked around

**This toolkit solves all four problems.**

---

## The Toolkit

| Component | What It Does | Why You Need It |
|-----------|-------------|-----------------|
| **[Persistent Memory](#1-persistent-memory)** | Stores workspace IDs, API patterns, preferences across sessions | No more re-explaining your environment every session |
| **[MS Learn Wrapper](#2-ms-learn-mcp-wrapper)** | Searches official Microsoft docs in real-time | Always-current Fabric API docs, zero hallucination |
| **[Context7 Wrapper](#3-context7-mcp-wrapper)** | Fetches real-time library docs (9000+ libraries) | Current SDK docs for pandas, PySpark, azure-identity, etc. |
| **[Analysis Toolkit](#4-analysis-toolkit-duckdb)** | DuckDB + matplotlib for data analysis | Query CSV/JSON/Parquet directly, generate charts |
| **[Fabric MCP Server](#5-fabric-mcp-server-onelake)** | OneLake file/table operations | Upload, download, list, query OneLake data programmatically |

---

## Project Structure

```
fabric-skills-toolkit/
├── README.md                          # This file (the guide)
├── requirements.txt                   # Python dependencies
├── setup.ps1                          # One-click setup (Windows)
│
├── tools/
│   ├── context7.py                    # Context7 MCP wrapper (real-time library docs)
│   ├── mslearn.py                     # MS Learn MCP wrapper (official Microsoft docs)
│   └── analyze.py                     # DuckDB + matplotlib analysis toolkit
│
├── templates/
│   ├── memory.json                    # Template: persistent machine-readable memory
│   └── CONTEXT.md                     # Template: human-readable preferences & notes
│
├── docs/
│   ├── skill-best-practices.md        # How to write great Fabric skills
│   ├── fabric-api-gotchas.md          # Hard-won Fabric API lessons
│   └── mcp-integration-guide.md       # How to integrate MCP servers with skills
│
└── examples/
    ├── memory-usage.md                # How to use persistent memory effectively
    └── workflow-examples.md           # End-to-end workflow examples
```

### Where This Fits With Skills-for-Fabric

```
~/.copilot/                            # Your AI assistant's home
├── skills/                            # Symlinked skills from microsoft/skills-for-fabric
│   ├── sqldw-authoring-cli/
│   ├── spark-authoring-cli/
│   └── ...
├── memory.json                        # ← From this toolkit (persistent memory)
└── CONTEXT.md                         # ← From this toolkit (preferences)

your-project/
├── tools/                             # ← From this toolkit (copy these in)
│   ├── context7.py
│   ├── mslearn.py
│   └── analyze.py
└── ...
```

---

## Setup Guide

### Prerequisites

- **Python 3.10+** with pip
- **Node.js 18+** with npx (for Context7 MCP)
- **Azure CLI** (`az login` for Fabric authentication)
- Optional: **.NET 8+** (for Fabric MCP Server / OneLake tools)

### Quick Setup (Windows)

```powershell
# Clone this repo
git clone https://github.com/yourusername/fabric-skills-toolkit.git
cd fabric-skills-toolkit

# Run setup
.\setup.ps1
```

### Manual Setup

#### Step 1: Install Python Dependencies

```bash
pip install duckdb matplotlib pandas
```

#### Step 2: Copy Tools to Your Project

```bash
# Copy the tools/ folder to your project
cp -r tools/ /path/to/your/project/tools/
```

Or use them directly from this repo:

```bash
python fabric-skills-toolkit/tools/mslearn.py search "fabric data warehouse"
python fabric-skills-toolkit/tools/context7.py search "pyspark"
python fabric-skills-toolkit/tools/analyze.py query "SELECT 1+1 AS answer"
```

#### Step 3: Set Up Persistent Memory

```bash
# Copy templates to your .copilot folder
mkdir -p ~/.copilot
cp templates/memory.json ~/.copilot/memory.json
cp templates/CONTEXT.md ~/.copilot/CONTEXT.md
```

Then edit `~/.copilot/memory.json` with your actual workspace IDs, endpoints, etc.

#### Step 4 (Optional): Install Fabric MCP Server

```bash
# Requires .NET 8+
git clone https://github.com/microsoft/mcp.git ~/.copilot/fabric-mcp
cd ~/.copilot/fabric-mcp/servers/Fabric.Mcp.Server/src
dotnet build -c Release
```

The binary will be at `bin/Release/fabmcp.exe`.

#### Step 5: Verify Everything Works

```bash
# Test MS Learn docs
python tools/mslearn.py search "fabric lakehouse"

# Test Context7 docs  
python tools/context7.py search "pandas"

# Test DuckDB
python tools/analyze.py query "SELECT 'hello world' AS greeting"

# Test Fabric MCP (if installed)
fabmcp onelake list_workspaces
```

---

## Tool Deep Dives

### 1. Persistent Memory

**The single most impactful thing you can do for your AI-assisted Fabric development.**

Every AI session starts fresh — no memory of what you did before. The persistent memory pattern gives your assistant a "cheat sheet" to load at session start.

#### How It Works

Two files in your project's `.copilot/` folder (or `~/.copilot/`):

| File | Format | Purpose | Who Reads It |
|------|--------|---------|--------------|
| `memory.json` | JSON | Machine-readable: IDs, endpoints, API patterns, tool paths | AI assistant (structured lookups) |
| `CONTEXT.md` | Markdown | Human-readable: preferences, working style, lessons learned | AI assistant (behavioral guidance) |

#### memory.json — What Goes In It

```json
{
  "_description": "Persistent memory for Copilot sessions. Auto-maintained.",
  "_updated": "2025-03-22T00:00:00Z",

  "tools_installed": {
    "analyze": "tools/analyze.py",
    "context7": "tools/context7.py",
    "mslearn": "tools/mslearn.py",
    "duckdb": "pip: duckdb 1.5.0"
  },

  "workspaces": {
    "my_dev_workspace": {
      "id": "YOUR-WORKSPACE-GUID-HERE",
      "note": "Primary development workspace"
    }
  },

  "lakehouses": {
    "sales_lakehouse": {
      "sql_endpoint": "YOUR-SQL-ENDPOINT.datawarehouse.fabric.microsoft.com",
      "schemas": {
        "dbo": "5 tables: orders, customers, products, ...",
        "analytics": "3 views: monthly_summary, top_products, ..."
      }
    }
  },

  "api_patterns": {
    "fabric_base": "https://api.fabric.microsoft.com/v1",
    "token_audiences": {
      "fabric": "https://api.fabric.microsoft.com",
      "onelake": "https://storage.azure.com"
    },
    "gotchas": [
      "CRUD uses /dataAgents/ (camelCase), query uses /dataagents/ (lowercase)",
      "updateDefinition requires ALL files, not partial updates"
    ]
  },

  "preferences": {
    "ask_user_before_acting": true,
    "backup_before_changes": true
  }
}
```

#### CONTEXT.md — What Goes In It

```markdown
# Session Context — My Fabric Project

## User Preferences
- Always ask before modifying production resources
- One step at a time — don't batch big changes
- Show findings before implementing

## Working Style
- For experiments: hypothesis → test → analyze → decide
- Multi-run evaluations (3+) for accuracy claims
- Use structured tables for presenting schema/results

## Key Learnings (Don't Re-learn These)
1. DAX tool ignores agent-level instructions → use Prep for AI
2. Few-shot retrieval is keyword-based, not semantic → exact wording matters
3. updateDefinition requires ALL files → can't do partial updates

## Tools Available
- `tools/analyze.py` — DuckDB queries, charts, JSON diff
- `tools/context7.py` — Real-time library docs
- `tools/mslearn.py` — Official MS Learn docs
```

#### Pro Tips for Memory

1. **Update after discoveries**: Found a new API quirk? Add it to `api_patterns.gotchas`
2. **Record experiment results**: Your AI assistant can reference past results instead of re-running
3. **Store tool paths**: So the assistant doesn't search for tools every session
4. **Keep it pruned**: Remove outdated info — stale memory is worse than no memory

> **How to instruct your AI assistant to use it**: Add to your custom instructions or SKILL.md:  
> *"At session start, read `.copilot/memory.json` and `.copilot/CONTEXT.md` for persistent context."*

---

### 2. MS Learn MCP Wrapper

**Real-time access to official Microsoft documentation — zero hallucination risk.**

Uses the public MS Learn MCP endpoint (`https://learn.microsoft.com/api/mcp`). No API key needed. No authentication required.

#### Commands

```bash
# Search docs
python tools/mslearn.py search "fabric lakehouse sql endpoint"

# Fetch a specific page as markdown
python tools/mslearn.py fetch "https://learn.microsoft.com/en-us/fabric/data-engineering/lakehouse-overview"

# Search code samples
python tools/mslearn.py code "azure openai python chat completion"

# List available tools (debug)
python tools/mslearn.py tools
```

#### Example Output

```
$ python tools/mslearn.py search "fabric data warehouse create table"

- **Create tables in Microsoft Fabric Data Warehouse**
  https://learn.microsoft.com/en-us/fabric/data-warehouse/create-table
  Learn how to create tables in your Fabric Data Warehouse using T-SQL...

- **Data types in Microsoft Fabric**
  https://learn.microsoft.com/en-us/fabric/data-warehouse/data-types
  Supported data types for tables in Fabric Data Warehouse...
```

#### How It Works

The MS Learn MCP server uses **Streamable HTTP transport** — the wrapper sends JSON-RPC requests directly to the endpoint over HTTP. No subprocess, no npm packages, no external dependencies (just Python stdlib).

```
Your CLI  →  mslearn.py  →  HTTP POST  →  learn.microsoft.com/api/mcp
                                              ↓
                                        JSON-RPC response
                                              ↓
                                        Formatted output
```

#### Integration with Skills

Add to your AI assistant's custom instructions:

```markdown
## Documentation Lookup
When you need current Fabric API docs, use:
  python tools/mslearn.py search "your query"
  python tools/mslearn.py fetch "https://learn.microsoft.com/..."
Never guess API parameters — always verify with mslearn first.
```

---

### 3. Context7 MCP Wrapper

**Real-time docs for 9,000+ libraries — pandas, PySpark, azure-identity, and more.**

Uses the [Context7](https://context7.com) MCP server via npx. Fetches documentation that is always up-to-date with the latest library versions.

#### Commands

```bash
# Search for a library
python tools/context7.py search "pyspark"

# Fetch docs for a specific topic
python tools/context7.py docs "/apache/spark" --topic "read_parquet"
python tools/context7.py docs "/pandas/pandas" --topic "merge dataframes"
python tools/context7.py docs "/azure/azure-identity" --topic "DefaultAzureCredential"

# List available MCP tools (debug)
python tools/context7.py tools
```

#### Workflow: Find Library → Fetch Docs

```bash
# Step 1: Search for the library
$ python tools/context7.py search "azure identity"
# → Returns library IDs like "/azure/azure-identity"

# Step 2: Fetch specific docs
$ python tools/context7.py docs "/azure/azure-identity" --topic "ManagedIdentityCredential"
# → Returns current documentation with code examples
```

#### How It Works

Context7 uses **stdio transport** — the wrapper spawns the MCP server as a subprocess (`npx @upstash/context7-mcp`), communicates via JSON-RPC over stdin/stdout, gets the response, and shuts down.

```
Your CLI  →  context7.py  →  subprocess (npx)  →  Context7 MCP Server
                                                        ↓
                                                   JSON-RPC over stdio
                                                        ↓
                                                   Documentation text
```

> **Note**: Each invocation starts/stops the MCP server. This keeps it stateless and simple. The first call takes ~3-5 seconds for npx to start; subsequent calls are faster if npm has cached the package.

#### Requirements

- Node.js 18+
- npx (comes with npm)
- Optional: `CONTEXT7_API_KEY` env var for higher rate limits

---

### 4. Analysis Toolkit (DuckDB)

**SQL analytics on any file format, directly from the CLI.**

DuckDB can query CSV, JSON, and Parquet files without loading them into a database first. Combined with matplotlib for charts and a JSON differ, this is your Swiss Army knife for data analysis.

#### Commands

```bash
# Query any file with SQL
python tools/analyze.py query "SELECT * FROM 'data/sales.csv' LIMIT 10"
python tools/analyze.py query "SELECT count(*) FROM 'data/*.parquet'"
python tools/analyze.py query "SELECT * FROM read_json_auto('results.json')"

# Generate charts
python tools/analyze.py chart bar sales.csv --x product --y revenue --title "Revenue by Product"
python tools/analyze.py chart line metrics.csv --x date --y accuracy --title "Accuracy Over Time"

# Compare JSON files (e.g., before/after config changes)
python tools/analyze.py diff config_v1.json config_v2.json --type json
python tools/analyze.py diff old_instructions.txt new_instructions.txt --type text
```

#### Use as a Python Module

```python
from tools.analyze import DuckDB, Chart, Diff, Report

# Query data
db = DuckDB()
results = db.query("SELECT product, SUM(amount) as total FROM 'sales.csv' GROUP BY product")
print(db.query_table("SELECT * FROM 'sales.csv' LIMIT 5"))

# Generate chart
Chart.bar(results, x="product", y="total", title="Sales by Product", output="sales_chart.png")

# Compare configurations
changes = Diff.json_diff("before.json", "after.json")
print(f"Added: {len(changes['added'])}, Removed: {len(changes['removed'])}, Changed: {len(changes['changed'])}")

# Generate HTML report
Report.from_data("Weekly Report", [
    {"title": "Summary", "content": {"Total Sales": "$1.2M", "Orders": "5,430"}, "type": "metrics"},
    {"title": "Top Products", "content": results, "type": "table"},
    {"title": "Trend", "content": "trend_chart.png", "type": "image"},
])
```

#### DuckDB Power Features

```sql
-- Query multiple files with glob patterns
SELECT * FROM 'experiments/*/results.json'

-- Cross-file joins
SELECT a.question, b.accuracy 
FROM 'eval_run1.json' a 
JOIN 'eval_run2.json' b ON a.id = b.id

-- Parquet files (great for lakehouse exports)
SELECT * FROM 'lakehouse_export/*.parquet' WHERE year = 2024
```

---

### 5. Fabric MCP Server (OneLake)

**Programmatic access to OneLake files, tables, and workspace metadata.**

This uses the [official Microsoft Fabric MCP Server](https://github.com/microsoft/mcp) — a .NET tool that exposes 21 OneLake operations.

#### Setup

```bash
# Requires .NET 8+
git clone https://github.com/microsoft/mcp.git ~/.copilot/fabric-mcp
cd ~/.copilot/fabric-mcp/servers/Fabric.Mcp.Server/src
dotnet build -c Release

# Add to PATH or create alias
alias fabmcp="$HOME/.copilot/fabric-mcp/servers/Fabric.Mcp.Server/src/bin/Release/fabmcp.exe"
```

#### Key Commands

```bash
# List all workspaces
fabmcp onelake list_workspaces

# List items in a workspace
fabmcp onelake list_items --workspace-id "YOUR-WORKSPACE-ID"

# Upload a file to OneLake
fabmcp onelake upload_file \
  --workspace-id "YOUR-WS-ID" \
  --item-id "YOUR-LAKEHOUSE-ID" \
  --file-path "Files/data/input.csv" \
  --local-file-path "./input.csv"

# Download a file from OneLake
fabmcp onelake download_file \
  --workspace-id "YOUR-WS-ID" \
  --item-id "YOUR-LAKEHOUSE-ID" \
  --file-path "Files/data/input.csv"

# List tables in a lakehouse
fabmcp onelake list_tables \
  --workspace-id "YOUR-WS-ID" \
  --item-id "YOUR-LAKEHOUSE-ID" \
  --schema dbo

# Get Fabric best practices docs
fabmcp docs best-practices --topic data-agent
```

> **Authentication**: Uses your Azure CLI token (`az login`). Make sure you're logged into the right tenant.

---

## Skill Best Practices

If you're writing or customizing Fabric skills (for [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric)), here are the patterns that work.

### The Skill Authoring Checklist

For the full guide, see [docs/skill-best-practices.md](docs/skill-best-practices.md). Quick summary:

| ✅ Do | ❌ Don't |
|--------|----------|
| Start description with action verb | Vague descriptions ("helps with data") |
| Include specific trigger phrases | Generic triggers ("query", "sql") |
| Add Must/Prefer/Avoid sections | Skip behavioral guidance |
| Reference common/ for shared content | Duplicate auth patterns in every skill |
| Keep skills under 10K tokens | Mega-skills that cover everything |
| Provide guidance and principles | Copy-paste code templates |
| Tag all code blocks with language | Untagged code blocks |

### Skill Structure Template

```markdown
---
name: my-skill-name
description: >
  Execute [specific action] against Microsoft Fabric [resource type] 
  from CLI environments. Use when the user wants to:
  (1) first use case, (2) second use case.
  Triggers: "trigger phrase 1", "trigger phrase 2".
---

> **Update Check — ONCE PER SESSION (mandatory)**
> First time this skill is used, run **check-updates** skill before proceeding.

# Skill Title

## Prerequisite Knowledge
- [COMMON-CLI.md](../../common/COMMON-CLI.md) — Authentication
- [COMMON-CORE.md](../../common/COMMON-CORE.md) — Fabric REST patterns

## Must/Prefer/Avoid

### MUST DO
- Critical requirements for this skill

### PREFER  
- Best practice patterns

### AVOID
- Known anti-patterns

## [Your Skill Content]
Guidance, patterns, decision frameworks...

## Examples
Practical examples showing the skill in action
```

### Key Principles

1. **Skills = Knowledge, MCP = Tools**  
   Skills teach the AI *what* to do. MCP servers *do* it. Don't put executable code in skills.

2. **Guidance Over Code**  
   Tell the AI *when* and *why* to use an approach, not *how* (it can generate code). Instead of a 100-line Python class, provide principles:
   ```markdown
   **When to define explicit schemas:**
   - Production pipelines where types must be consistent
   - Large files where inferSchema adds overhead
   ```

3. **Disambiguation Matters**  
   If two skills have similar triggers, the AI can't route correctly. Use specific technology qualifiers:
   ```yaml
   # ❌ Bad: "query data" matches SQL AND Spark
   # ✅ Good: "T-SQL query warehouse with sqlcmd"
   ```

4. **Token Budget**  
   Every token in a skill consumes context window. Move reference material to `common/` and keep skills focused:
   - Under 5K tokens: ✅ Ideal
   - 5K-10K: ⚠️ Acceptable  
   - Over 10K: 🚨 Split or refactor

---

## Fabric API Lessons Learned

These are hard-won discoveries from 36+ sessions. They apply to anyone writing tools or skills that interact with Fabric APIs.

For the full list, see [docs/fabric-api-gotchas.md](docs/fabric-api-gotchas.md). Highlights:

### 1. The LRO /result Pattern (Critical)

When calling Fabric REST APIs that return `202 Accepted` (Long Running Operations):

```
POST /workspaces/{id}/items/{id}/getDefinition
→ 202 Accepted + Location header

GET {Location URL}                  ← Poll this
→ {"status": "Succeeded"}          ← Body has NO payload!

GET {Location URL}/result           ← MUST call this
→ {"definition": {"parts": [...]}} ← Actual data is here
```

**The trap**: The polling response body says `Succeeded` but contains no data. You must append `/result` to the Location URL and make one more GET request.

### 2. Case Sensitivity in API Paths

```
CRUD operations:  /workspaces/{id}/dataAgents/{id}     ← camelCase
Query operations: /workspaces/{id}/dataagents/{id}     ← lowercase
```

Yes, really. The same resource uses different casing depending on the operation.

### 3. The `null` Body Trap

A `202 Accepted` response body is literally the string `"null"` — not empty string, not `{}`, but the four characters n-u-l-l. If you `json.loads("null")`, you get Python `None`, not an error. Guard against it:

```python
if resp_body and resp_body.strip() not in ("", "null"):
    data = json.loads(resp_body)
```

### 4. updateDefinition Requires ALL Files

You can't do partial updates. Every call must include the complete set of definition files. If you forget one, it gets deleted.

### 5. subprocess.run + shell=True on Windows

If you're calling CLI tools from Python on Windows:

```python
# ❌ This breaks — cmd.exe interprets | in arguments as pipe
subprocess.run(["sqlcmd", "-s", "|", "-Q", query], shell=True)

# ✅ This works — use shell=False and tab separator instead
subprocess.run(["sqlcmd", "-s", "\t", "-Q", query])
```

---

## How This Works with Skills-for-Fabric

This toolkit is designed to complement [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric), not replace it.

```
┌─────────────────────────────────────────────────────┐
│                  Your AI Assistant                    │
│                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Fabric Skills │  │  This Toolkit │  │  MCP Servers│ │
│  │              │  │              │  │            │ │
│  │ "What to do" │  │ "Remember &  │  │  "Do it"   │ │
│  │              │  │  look up"    │  │            │ │
│  └──────────────┘  └──────────────┘  └────────────┘ │
│         │                 │                │         │
│    Knowledge         Context &          Actions      │
│    (SKILL.md)       Documentation      (OneLake,    │
│                     (memory, docs)      SQL, etc.)   │
└─────────────────────────────────────────────────────┘
```

### Setup for Skills-for-Fabric Users

1. **Install skills** following the [official guide](https://github.com/microsoft/skills-for-fabric#installation)
2. **Add this toolkit** by copying tools and templates
3. **Configure memory** with your workspace details
4. **Instruct your AI** to read memory at session start

### Custom Instructions to Add

Add this to your AI assistant's custom instructions (e.g., `.copilot/instructions.md`, `CLAUDE.md`, `.cursorrules`):

```markdown
## Session Setup
At session start, read these files for persistent context:
- `.copilot/memory.json` — workspace IDs, endpoints, API patterns
- `.copilot/CONTEXT.md` — preferences, learnings, tool reference

## Documentation
When unsure about Fabric APIs, check real-time docs:
- `python tools/mslearn.py search "<query>"` — official Microsoft docs
- `python tools/context7.py search "<library>"` — library docs (pandas, PySpark, etc.)

## Analysis
For data analysis tasks:
- `python tools/analyze.py query "<SQL>"` — query CSV/JSON/Parquet with DuckDB
- `python tools/analyze.py chart <type> <file> --x <col> --y <col>` — generate charts
```

---

## Contributing

Found this useful? Here's how to contribute:

1. **Star the repo** ⭐ to show interest
2. **Open issues** for bugs or feature requests
3. **Submit PRs** for improvements

### Ideas for Contribution

- Templates for more Fabric workloads (Eventhouse, Power BI, Spark)
- Additional MCP wrappers (Azure DevOps, GitHub, etc.)
- More analysis patterns and chart types
- CI/CD integration examples

---

## License

MIT License — use it however you want.

---

*Built with ❤️ during 36+ Copilot sessions building Fabric Data Agent skills. Every tool in this toolkit exists because something broke in production and I got tired of fixing it manually.*
