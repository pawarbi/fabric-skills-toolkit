# Skill Best Practices for Microsoft Fabric

> Distilled from the [microsoft/skills-for-fabric](https://github.com/microsoft/skills-for-fabric) project and 36+ sessions of real-world Fabric skill development.

---

## What Is a Fabric Skill?

A **skill** is a markdown file (`SKILL.md`) that teaches an AI coding assistant how to perform a specific task with Microsoft Fabric. Skills live in the `skills/` folder and are loaded into the assistant's context when triggered.

Skills provide **knowledge and guidance** — not executable code. The AI generates code on-demand based on your guidance.

---

## The 10 Rules of Great Skills

### 1. One Skill = One Job

A skill should do one thing well. If your skill covers both "creating tables" AND "querying data", split it into authoring and consumption skills.

```
✅ sqldw-authoring-cli    → CREATE, ALTER, INSERT, COPY INTO
✅ sqldw-consumption-cli  → SELECT, explore, analyze
❌ sqldw-everything-cli   → Too broad, poor routing
```

### 2. Start With a Clear Description

The YAML frontmatter `description` field is how the AI decides which skill to use. Make it specific:

```yaml
# ✅ Good — specific, actionable, discoverable
description: >
  Execute authoring T-SQL (DDL, DML, data ingestion) against Microsoft Fabric
  Data Warehouse from CLI environments. Use when the user wants to:
  (1) create/alter tables, (2) insert/update data, (3) run COPY INTO.
  Triggers: "create table in warehouse", "insert data via T-SQL".

# ❌ Bad — vague, no routing signals
description: >
  Help with Fabric Warehouse operations.
```

**Rules for descriptions:**
- Start with an action verb (Execute, Create, Run, Query, Deploy)
- Mention specific technologies (T-SQL, PySpark, sqlcmd, Livy)
- List "Use when the user wants to:" with numbered cases
- Include "Triggers:" with quoted phrases

### 3. Use Must/Prefer/Avoid Sections

These guide the AI's behavior — the most impactful part of a skill:

```markdown
### MUST DO
- Always use `-G` flag for Entra ID authentication
- Always run `az login` before first SQL operation
- Include error handling for authentication failures

### PREFER
- `sqlcmd (Go) -G` over curl+token for SQL queries
- `-i file.sql` for complex multi-statement queries
- Structured table output for results

### AVOID
- ODBC sqlcmd (`/opt/mssql-tools/bin/sqlcmd`) — requires driver install
- Hardcoded FQDNs — discover via REST API
- DML on Lakehouse SQL Endpoint — it's read-only
```

### 4. Guidance Over Code Templates

Skills should teach principles, not provide copy-paste implementations:

```markdown
# ✅ Good: Teach WHEN and WHY
**When to define explicit schemas:**
- Production pipelines where data types must be consistent
- Large files where inferSchema adds overhead
- When source schema is known and stable

# ❌ Bad: 100-line implementation to copy
```python
class DataIngestionPipeline:
    def __init__(self, spark_session):
        self.spark = spark_session
    def read_source_data(self, pattern):
        # ... 80 more lines ...
```
```

### 5. Keep Token Count Under Control

Every token in a skill consumes the AI's context window:

| Tokens | Status | Action |
|--------|--------|--------|
| < 5K | ✅ Ideal | Perfect size |
| 5K-10K | ⚠️ OK | Review if everything is needed |
| 10K-15K | ⚠️ Large | Move content to `common/` |
| > 15K | 🚨 Too big | Must split or refactor |

### 6. Reference, Don't Duplicate

Shared patterns (authentication, workspace discovery, REST API basics) belong in `common/`:

```markdown
## Prerequisite Knowledge
- [COMMON-CLI.md](../../common/COMMON-CLI.md) — Authentication patterns
- [COMMON-CORE.md](../../common/COMMON-CORE.md) — Fabric REST API patterns
```

### 7. Tag All Code Blocks

Always specify the language for code blocks — it helps the AI generate the right kind of code:

````markdown
```bash
az login
```

```sql
SELECT TOP 10 * FROM dbo.FactSales
```

```python
df = spark.table("sales")
```
````

### 8. Use Specific Trigger Phrases

Generic triggers cause routing confusion:

```yaml
# ❌ Bad: "query" matches SQL AND Spark AND KQL
Triggers: "query", "sql", "explore"

# ✅ Good: Technology-qualified
Triggers: "T-SQL query", "query warehouse with sqlcmd", "explore warehouse schema"
```

### 9. Include Practical Examples

Show the skill in action with real-world examples:

```markdown
## Examples

### Query Top Products by Revenue
```bash
sqlcmd -S $ENDPOINT -d $DATABASE -G -Q "
SELECT TOP 10 ProductName, SUM(Amount) AS Revenue
FROM dbo.FactSales fs
JOIN dbo.DimProduct dp ON fs.ProductID = dp.ProductID
GROUP BY ProductName
ORDER BY Revenue DESC" -W
```

### Export Results to CSV
```bash
sqlcmd -S $ENDPOINT -d $DATABASE -G -Q "SELECT * FROM dbo.FactSales" -W -s"," -o sales.csv
```
```

### 10. Follow the Naming Convention

```
{endpoint}-{authoring|consumption}-{access}
```

| Type | Pattern | Example |
|------|---------|---------|
| Developer skill | `{endpoint}-authoring-cli` | `sqldw-authoring-cli` |
| Consumer skill | `{endpoint}-consumption-cli` | `spark-consumption-cli` |
| Cross-endpoint | `agents/{persona}.agent.md` | `FabricDataEngineer` |
| End-to-end | `e2e-{pattern}` | `e2e-medallion-architecture` |

---

## Skill Template

```markdown
---
name: my-skill-name
description: >
  [Action verb] [specific task] against Microsoft Fabric [resource]
  from [environment]. Use when the user wants to:
  (1) [use case 1], (2) [use case 2], (3) [use case 3].
  Triggers: "[phrase 1]", "[phrase 2]", "[phrase 3]".
---

> **Update Check — ONCE PER SESSION (mandatory)**
> The first time this skill is used in a session, run the **check-updates** skill
> before proceeding. Skip if already done this session.

# [Skill Title]

## Prerequisite Knowledge
- [COMMON-CLI.md](../../common/COMMON-CLI.md)
- [COMMON-CORE.md](../../common/COMMON-CORE.md)

## Must/Prefer/Avoid

### MUST DO
- [Critical requirement 1]
- [Critical requirement 2]

### PREFER
- [Best practice 1]
- [Best practice 2]

### AVOID
- [Anti-pattern 1]
- [Anti-pattern 2]

## [Topic Sections]

[Your skill content — guidance, patterns, decision frameworks]

## Examples

[Practical examples showing the skill in action]
```

---

## Skills vs. MCP Servers vs. This Toolkit

| Component | Purpose | Content Type |
|-----------|---------|--------------|
| **Skills** | Teach AI what to do | Markdown (knowledge) |
| **MCP Servers** | Execute actions (query, upload, deploy) | Executable servers |
| **This Toolkit** | Bridge gaps (memory, docs, analysis) | Python tools + templates |

They work together:
1. **Skill** tells AI: "Use `sqlcmd -G` for warehouse queries"
2. **Toolkit** provides: Real-time docs, persistent memory, analysis tools
3. **MCP Server** executes: The actual SQL query against OneLake

---

## Quality Checklist

Before shipping a skill:

- [ ] `name` in frontmatter matches folder name
- [ ] Description starts with action verb and mentions technologies
- [ ] Triggers are specific and don't conflict with other skills
- [ ] Update notice is present
- [ ] Must/Prefer/Avoid sections included
- [ ] All code blocks have language tags
- [ ] All cross-references point to existing files
- [ ] Token count is under 10K (ideally under 5K)
- [ ] Content is guidance/principles, not copy-paste code
- [ ] Tested locally with the AI assistant

---

## Further Reading

- [Skill Authoring Guide](https://github.com/microsoft/skills-for-fabric/blob/main/docs/skill-authoring-guide.md)
- [Quality Requirements](https://github.com/microsoft/skills-for-fabric/blob/main/docs/quality-requirements.md)
- [Contributing Guide](https://github.com/microsoft/skills-for-fabric/blob/main/CONTRIBUTING.md)
- [MCP Servers Guide](https://github.com/microsoft/skills-for-fabric/blob/main/docs/mcp-servers-guide.md)
