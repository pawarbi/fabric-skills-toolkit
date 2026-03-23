# Fabric Notebook Source Format

Fabric notebooks are stored as Python files named `notebook-content.py` when
using Git integration or the REST API definition endpoints. This format is
distinct from `.ipynb` and uses comment-based markers to delimit cells and
metadata blocks.

The CLI tool at `tools/notebook.py` handles conversion between `.ipynb` and
this format automatically.

## Structure

A Fabric notebook source file has three parts in order:

1. **Header line** - always `# Fabric notebook source`
2. **Notebook-level metadata** - kernel info, dependencies, lakehouse bindings
3. **Cell blocks** - a sequence of code and markdown cells

## Notebook-level Metadata

Appears once at the top of the file, after the header line.

```python
# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "jupyter",
# META     "jupyter_kernel_name": "python3.11"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse_name": "",
# META       "default_lakehouse_workspace_id": ""
# META     }
# META   }
# META }
```

The `# METADATA ********************` line marks the start of a metadata block.
Each line of JSON is prefixed with `# META `. The JSON object is reconstructed
by stripping the `# META ` prefix from each line and joining.

Use kernel `jupyter` with `python3.11`. Do not use `synapse_pyspark`.

## Markdown Cells

Markdown cells start with the `# MARKDOWN ********************` marker. Each
line of markdown content is prefixed with `# ` (hash, space).

```python
# MARKDOWN ********************

# ## Section Title
#
# This is a paragraph of markdown text.
#
# - Item one
# - Item two
```

Empty markdown lines become `#` (hash with no trailing space). The parser strips
the `# ` prefix when reading, and adds it back when writing.

## Code Cells

Code cells start with the `# CELL ********************` marker. Code lines are
written verbatim (no prefix). Each code cell ends with a cell-level metadata
block.

```python
# CELL ********************

import pandas as pd

df = pd.read_csv("data.csv")
display(df.head())

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }
```

## Cell Metadata

Cell-level metadata uses the same `# METADATA` / `# META` format as
notebook-level metadata, but with a flat structure containing two fields:

```json
{
  "language": "python",
  "language_group": "jupyter_python"
}
```

This is a flat object. Do not wrap it in a `microsoft` or `notebook` key.

## Example

A complete notebook with one markdown cell and two code cells:

```python
# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "jupyter",
# META     "jupyter_kernel_name": "python3.11"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse_name": "",
# META       "default_lakehouse_workspace_id": ""
# META     }
# META   }
# META }

# MARKDOWN ********************

# # Sales Analysis
#
# Load and summarize the sales data.

# CELL ********************

import pandas as pd

df = spark.sql("SELECT * FROM sales.fact_orders").toPandas()
print(f"Rows: {len(df)}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

display(df.describe())

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }
```

## The .platform File

Every notebook definition also requires a `.platform` JSON file alongside
`notebook-content.py`. This file declares the item type and display name:

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
  "metadata": {
    "type": "Notebook",
    "displayName": "Sales Analysis",
    "description": ""
  },
  "config": {
    "version": "2.0",
    "logicalId": "00000000-0000-0000-0000-000000000000"
  }
}
```

The `logicalId` must always be `"00000000-0000-0000-0000-000000000000"`.

## Conversion Notes

When converting `.ipynb` to Fabric source format, the critical step is handling
the `source` array in each cell. In `.ipynb`, cell source is an array of strings
where each string may or may not end with `\n`:

```json
{
  "source": [
    "import pandas as pd\n",
    "df = pd.read_csv('data.csv')\n",
    "print(df.shape)"
  ]
}
```

The correct conversion approach:

1. Join all source lines first: `"".join(cell["source"])`
2. Then split on newlines: `.split("\n")`
3. Write each resulting line to the output

If you skip step 1 and iterate the source array directly, lines ending with
`\n` produce a trailing empty string when split, which creates spurious blank
comment lines in the output.

```python
# Wrong: iterate source lines individually
for line in cell["source"]:
    for sub in line.split("\n"):
        output.append(sub)
# Produces extra blank lines from trailing \n

# Right: join first, then split
for line in "".join(cell["source"]).split("\n"):
    output.append(line)
```
