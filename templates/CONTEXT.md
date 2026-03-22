# Session Context — My Fabric Project

> **Purpose**: Human-readable preferences and notes for your AI coding assistant.
> Copy to `.copilot/CONTEXT.md` and customize. Your assistant reads this at session start.

---

## User Preferences

- **Always ask before acting** — confirm scope and approach before implementing
- **One step at a time** — don't batch multiple big changes; do them sequentially
- **Backup before changes** — always snapshot current state before modifying resources
- **Show your work** — explain findings before jumping to implementation

## Working Style

- For experiments: state hypothesis → test → analyze → decide (don't just change things)
- Multi-run evaluations (3+) for accuracy claims — single runs are unreliable
- Use structured tables for presenting findings (schema analysis, results, comparisons)

## Key Learnings (Don't Re-learn These)

<!-- Add lessons specific to your project. Examples: -->
1. `updateDefinition` requires ALL files — can't do partial updates
2. Fabric LRO pattern: after polling returns `Succeeded`, must GET `{url}/result` for actual payload
3. `subprocess.run` with `shell=True` on Windows breaks when arguments contain `|` or `&`
4. Always use `-G` flag for Entra ID authentication with sqlcmd

## Tools Available

### Documentation
- `python tools/mslearn.py search "query"` — search official Microsoft Learn docs
- `python tools/mslearn.py fetch "url"` — fetch a specific doc page as markdown
- `python tools/context7.py search "library"` — find a library ID
- `python tools/context7.py docs "id" --topic "topic"` — fetch library docs

### Analysis
- `python tools/analyze.py query "SQL"` — query CSV/JSON/Parquet with DuckDB
- `python tools/analyze.py chart bar data.csv --x col1 --y col2` — generate charts
- `python tools/analyze.py diff file1.json file2.json --type json` — compare files

### Fabric (if installed)
- `fabmcp onelake list_workspaces` — list all Fabric workspaces
- `fabmcp onelake list_items --workspace-id "id"` — list items in workspace
- `sqlcmd -S endpoint -d database -G -Q "SELECT ..."` — direct SQL queries

## Project Notes

<!-- Add project-specific notes here -->
- Main workspace: [name] (ID: [guid])
- Key lakehouse: [name] with schemas [dbo, ...]
- SQL endpoint: [endpoint URL]
