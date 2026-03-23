# How to Use Persistent Memory Effectively

> The persistent memory pattern is the highest-impact, lowest-effort improvement you can make to your AI-assisted Fabric development workflow.

---

## The Problem

Every AI coding session starts from scratch. Session 1 you teach your assistant your workspace ID, SQL endpoint, and schema layout. Session 2... you do it all over again.

After 36 sessions, I was spending the first 5-10 minutes of every session re-explaining the same context. That's ~3-6 hours wasted total.

---

## The Solution: Two Files

### memory.json - Structured Data for Machine Lookups

```json
{
  "workspaces": {
    "dev": {"id": "82ad2591-...", "note": "Development workspace"}
  },
  "lakehouses": {
    "sales": {
      "sql_endpoint": "xxx.datawarehouse.fabric.microsoft.com",
      "schemas": {"dbo": "10 tables", "analytics": "3 views"}
    }
  }
}
```

Your AI assistant reads this and immediately knows:
- Which workspace to target
- How to connect to SQL endpoints
- What schemas exist

### CONTEXT.md - Behavioral Guidance for the AI

```markdown
## Preferences
- Always ask before modifying production resources
- Multi-run evaluations (3+) for accuracy claims

## Lessons Learned
- updateDefinition requires ALL files
- DAX tool ignores agent instructions
```

This prevents the AI from making the same mistakes it made in previous sessions.

---

## Where to Put Them

### Option A: Project-Level (Recommended for Teams)

```
my-fabric-project/
├── .copilot/
│   ├── memory.json    ← Project-specific context
│   └── CONTEXT.md     ← Team preferences
└── ...
```

Benefits: Shared across the team via git. Everyone's AI assistant has the same context.

### Option B: User-Level (Personal Preferences)

```
~/.copilot/
├── memory.json    ← All your Fabric projects
└── CONTEXT.md     ← Your personal preferences
```

Benefits: Applies to all your projects. Good for tool paths and personal preferences.

### Option C: Both (Recommended)

```
~/.copilot/
├── memory.json    ← Personal: tool paths, global preferences
└── CONTEXT.md     ← Personal: working style

my-fabric-project/.copilot/
├── memory.json    ← Project: workspace IDs, endpoints, schemas
└── CONTEXT.md     ← Project: team conventions, learnings
```

---

## What to Store in memory.json

### Essential (Add These First)

```json
{
  "workspaces": {
    "name": {"id": "guid", "note": "description"}
  },
  "lakehouses": {
    "name": {"sql_endpoint": "url", "schemas": {"dbo": "tables..."}}
  },
  "api_patterns": {
    "gotchas": ["lessons learned from debugging"]
  }
}
```

### Helpful (Add Over Time)

```json
{
  "tools_installed": {
    "tool_name": "path or install info"
  },
  "experiment_results": {
    "experiment_name": {"result": "finding", "date": "when"}
  },
  "preferences": {
    "ask_user_before_acting": true
  }
}
```

### Advanced (Power Users)

```json
{
  "api_patterns": {
    "fabric_base": "https://api.fabric.microsoft.com/v1",
    "token_audiences": {
      "fabric": "https://api.fabric.microsoft.com",
      "onelake": "https://storage.azure.com"
    },
    "supported_datasource_types": ["lakehouse_tables", "data_warehouse", "..."]
  }
}
```

---

## What to Store in CONTEXT.md

### Behavioral Guidance

```markdown
## Preferences
- Always ask before acting on production resources
- One step at a time - sequential, not batched
- Show findings before implementing changes
```

### Lessons Learned

```markdown
## Key Learnings
1. Fabric LRO: after Succeeded, must GET {url}/result for actual data
2. updateDefinition requires ALL files - no partial updates
3. subprocess.run with shell=True breaks on Windows with special chars
```

### Tool Reference

```markdown
## Tools
- `python tools/mslearn.py search "query"` - Microsoft docs
- `sqlcmd -S endpoint -d db -G -Q "..."` - Direct SQL
```

---

## How to Tell Your AI to Read Them

### Custom Instructions (Copilot CLI)

Add to `.copilot/instructions.md`:

```markdown
At session start, read `.copilot/memory.json` and `.copilot/CONTEXT.md` 
for persistent context about this project's Fabric environment.
```

### CLAUDE.md (Claude Code)

```markdown
## Session Setup
Read `.copilot/memory.json` for workspace IDs, endpoints, and API patterns.
Read `.copilot/CONTEXT.md` for preferences and lessons learned.
```

### .cursorrules (Cursor)

```
Before starting work, load context from .copilot/memory.json and .copilot/CONTEXT.md.
```

---

## Maintenance Tips

1. **Update after discoveries**: Found a new API quirk? Add it immediately
2. **Prune stale data**: Old experiment results with wrong conclusions -> remove them
3. **Version control it**: Commit memory.json and CONTEXT.md so the team benefits
4. **Keep it concise**: 50-100 lines in memory.json is ideal. Over 200 lines -> prune
5. **Date your entries**: Add `"_updated": "2025-03-22"` so you know what's current

---

## Before & After

### Before (Session Start Without Memory)

```
User: "Query my Fabric lakehouse"
AI: "What's your workspace ID?"
User: "82ad2591-974a-..."
AI: "What's the SQL endpoint?"
User: "xpkymsttihxelp6..."
AI: "What schema should I use?"
User: "dbo"
AI: "What tables are in dbo?"
... 5 minutes later, you can start working
```

### After (Session Start With Memory)

```
User: "Query my Fabric lakehouse"
AI: [reads memory.json - knows workspace, endpoint, schemas, table names]
AI: "I see your sales lakehouse has 10 tables in dbo and 3 views in analytics. 
     What would you like to query?"
... 0 minutes wasted, start working immediately
```
