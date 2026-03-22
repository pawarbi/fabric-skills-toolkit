# End-to-End Workflow Examples

> Real workflows showing how the toolkit components work together.

---

## Workflow 1: Explore a New Fabric Workspace

**Scenario**: You just got access to a new Fabric workspace and want to understand what's in it.

### Step 1: Find Your Workspace

```bash
# List all workspaces (requires Fabric MCP Server)
fabmcp onelake list_workspaces

# Or use az rest
az rest --method GET \
  --url "https://api.fabric.microsoft.com/v1/workspaces" \
  --resource "https://api.fabric.microsoft.com" \
  | python -c "import sys,json; [print(f'{w[\"id\"]} → {w[\"displayName\"]}') for w in json.load(sys.stdin)['value']]"
```

### Step 2: List Items

```bash
fabmcp onelake list_items --workspace-id "YOUR-WORKSPACE-ID"
```

### Step 3: Explore Lakehouse Schema

```bash
# List tables
fabmcp onelake list_tables \
  --workspace-id "YOUR-WS-ID" \
  --item-id "YOUR-LAKEHOUSE-ID" \
  --schema dbo

# Or query directly with sqlcmd
sqlcmd -S "YOUR-ENDPOINT.datawarehouse.fabric.microsoft.com" \
  -d "YOUR-LAKEHOUSE" -G \
  -Q "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES ORDER BY 1, 2"
```

### Step 4: Save to Memory

Add what you found to `.copilot/memory.json`:

```json
{
  "workspaces": {
    "new_ws": {
      "id": "discovered-guid",
      "note": "Contains sales data"
    }
  },
  "lakehouses": {
    "sales_lh": {
      "sql_endpoint": "discovered-endpoint",
      "schemas": {"dbo": "orders, customers, products (10 tables)"}
    }
  }
}
```

Now every future session starts with this knowledge.

---

## Workflow 2: Debug a Failing Query

**Scenario**: Your AI assistant generated a SQL query that's returning wrong results.

### Step 1: Check the Docs

```bash
# What does Microsoft say about this SQL pattern?
python tools/mslearn.py search "fabric warehouse T-SQL limitations"

# Check specific syntax
python tools/mslearn.py search "fabric lakehouse read-only sql endpoint"
```

### Step 2: Explore the Schema

```bash
# Check column types and names
sqlcmd -S $ENDPOINT -d $DB -G -Q "
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = 'orders'
ORDER BY ORDINAL_POSITION"
```

### Step 3: Analyze Results with DuckDB

```bash
# Export the problematic results
sqlcmd -S $ENDPOINT -d $DB -G \
  -Q "SELECT * FROM orders WHERE order_date > '2024-01-01'" \
  -s "\t" -o results.tsv

# Analyze with DuckDB
python tools/analyze.py query "
SELECT 
  order_status, 
  COUNT(*) as count,
  AVG(total_amount) as avg_amount
FROM read_csv_auto('results.tsv', delim='\t')
GROUP BY order_status
ORDER BY count DESC"
```

### Step 4: Compare Before/After

```bash
# Save the fix
python tools/analyze.py diff query_v1.sql query_v2.sql --type text
```

---

## Workflow 3: Look Up Current API Docs

**Scenario**: You need to use a Python library but aren't sure about the current API.

### Step 1: Find the Library

```bash
python tools/context7.py search "azure identity"
# → Returns: /azure/azure-identity
```

### Step 2: Get Specific Docs

```bash
python tools/context7.py docs "/azure/azure-identity" \
  --topic "DefaultAzureCredential managed identity"
# → Returns current documentation with code examples
```

### Step 3: Cross-Reference with MS Learn

```bash
python tools/mslearn.py search "managed identity fabric workspace"
# → Returns official Microsoft docs for Fabric + managed identity
```

---

## Workflow 4: Analyze Experiment Results

**Scenario**: You ran multiple experiments and want to compare results.

### Step 1: Query Results Files

```bash
# If results are in JSON files
python tools/analyze.py query "
SELECT 
  experiment_name,
  accuracy,
  total_questions,
  correct_answers
FROM read_json_auto('experiments/*/results.json')
ORDER BY accuracy DESC"
```

### Step 2: Generate Comparison Chart

```bash
# Create a CSV from the query
python tools/analyze.py query "
SELECT experiment_name as experiment, accuracy
FROM read_json_auto('experiments/*/results.json')
ORDER BY accuracy DESC" > comparison.csv

# Generate chart
python tools/analyze.py chart bar comparison.csv \
  --x experiment --y accuracy \
  --title "Accuracy by Experiment" \
  --output experiment_comparison.png
```

### Step 3: Generate HTML Report

```python
from tools.analyze import DuckDB, Chart, Report

db = DuckDB()
results = db.query("SELECT * FROM read_json_auto('experiments/*/results.json')")

Chart.bar(results, x="experiment_name", y="accuracy", 
          title="Experiment Comparison", output="chart.png")

Report.from_data("Experiment Results", [
    {"title": "Summary", "content": {
        "Total Experiments": str(len(results)),
        "Best Accuracy": f"{max(r['accuracy'] for r in results):.1%}",
        "Worst Accuracy": f"{min(r['accuracy'] for r in results):.1%}",
    }, "type": "metrics"},
    {"title": "All Results", "content": results, "type": "table"},
    {"title": "Comparison", "content": "chart.png", "type": "image"},
], output="experiment_report.html")
```

### Step 4: Record Best Result in Memory

```json
{
  "experiment_results": {
    "best_config": {
      "date": "2025-03-22",
      "experiment": "structured_headers_v3",
      "accuracy": "96.7%",
      "verdict": "keep — best result so far"
    }
  }
}
```

---

## Workflow 5: Upload Data to OneLake

**Scenario**: You have local CSV files to upload to a Fabric lakehouse.

```bash
# Upload a single file
fabmcp onelake upload_file \
  --workspace-id "YOUR-WS-ID" \
  --item-id "YOUR-LAKEHOUSE-ID" \
  --file-path "Files/raw/sales_2024.csv" \
  --local-file-path "./data/sales_2024.csv"

# Verify it's there
fabmcp onelake list_files \
  --workspace-id "YOUR-WS-ID" \
  --item-id "YOUR-LAKEHOUSE-ID"

# Download to verify content
fabmcp onelake download_file \
  --workspace-id "YOUR-WS-ID" \
  --item-id "YOUR-LAKEHOUSE-ID" \
  --file-path "Files/raw/sales_2024.csv"
```
