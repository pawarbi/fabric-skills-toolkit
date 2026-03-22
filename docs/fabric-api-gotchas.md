# Fabric API Gotchas — Hard-Won Lessons

> These discoveries came from 36+ real sessions working with Fabric REST APIs. Each one caused at least one debugging session. Save yourself the pain.

---

## 1. The LRO /result Pattern (Critical)

**The #1 trap in Fabric REST APIs.**

Many Fabric APIs use Long Running Operations (LRO). The pattern is:

```
Step 1: POST /workspaces/{id}/items/{id}/getDefinition
        → 202 Accepted
        → Location: https://api.fabric.microsoft.com/v1/operations/{op-id}

Step 2: GET {Location URL}          ← Poll this repeatedly
        → 200 OK
        → {"status": "Running"}     ← Keep polling
        ...
        → {"status": "Succeeded"}   ← Done! But...

Step 3: GET {Location URL}/result   ← MUST call this!
        → 200 OK
        → {"definition": {"parts": [...]}}   ← Actual data
```

**The trap**: When polling returns `"status": "Succeeded"`, the response body contains ONLY the status. The actual payload requires one more GET request to `{Location URL}/result`.

**Code pattern:**

```python
import time
import requests

def poll_lro(poll_url: str, headers: dict, timeout: int = 120) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = requests.get(poll_url, headers=headers)
        body = resp.json()
        status = body.get("status", "")
        
        if status == "Succeeded":
            # Don't return body — it has no payload!
            result_resp = requests.get(f"{poll_url}/result", headers=headers)
            return result_resp.json()
        elif status in ("Failed", "Cancelled"):
            raise RuntimeError(f"LRO failed: {body}")
        
        time.sleep(2)
    
    raise TimeoutError(f"LRO did not complete within {timeout}s")
```

---

## 2. The `null` Body Trap

When a Fabric API returns `202 Accepted`, the response body is literally the string `"null"` — not an empty string, not `{}`, but the four characters n-u-l-l.

```python
# What you get:
resp.text  # → '"null"' (the string, including quotes)
resp.text  # → 'null'   (sometimes without quotes)

# The trap:
import json
json.loads("null")  # → None (not an error!)
json.loads("")      # → JSONDecodeError

# Safe pattern:
def safe_parse(body: str):
    if not body or body.strip() in ("", "null", '"null"'):
        return None
    return json.loads(body)
```

---

## 3. Case Sensitivity in API Paths

The same resource type uses **different casing** depending on the operation:

```
CRUD operations:    /workspaces/{id}/dataAgents/{id}     ← camelCase
Query operations:   /workspaces/{id}/dataagents/{id}     ← all lowercase

# And the query endpoint has an extra suffix:
Query URL:          /workspaces/{id}/dataagents/{id}/aiassistant/openai/
```

This isn't documented. If you use the wrong casing, you get a 404 with no helpful error message.

**Other case-sensitive paths:**

```
/workspaces/{id}/lakehouses/{id}    ← lowercase
/workspaces/{id}/dataAgents/{id}    ← camelCase for CRUD
/workspaces/{id}/semanticModels/    ← camelCase
```

---

## 4. updateDefinition Requires ALL Files

When updating an item's definition via the REST API, you must include **every** file in the definition — not just the ones you changed.

```python
# ❌ Wrong: Only sending the file you changed
body = {
    "definition": {
        "parts": [
            {"path": "stage_config.json", "payload": new_config_b64}
        ]
    }
}

# ✅ Right: Send ALL files
body = {
    "definition": {
        "parts": [
            {"path": "stage_config.json", "payload": config_b64},
            {"path": "lakehouse-tables-001.json", "payload": ds1_b64},
            {"path": "lakehouse-tables-001-schema-tables.json", "payload": schema_b64},
            # ... every other file
        ]
    }
}
```

If you forget a file, it gets deleted from the definition. There's no "partial update" mode.

**Also important**: `getDefinition` returns both `draft/` and `published/` files. When calling `updateDefinition`, only include the `draft/` files. Including `published/` files causes a `409 DuplicateDefinitionParts` error.

---

## 5. subprocess.run + shell=True on Windows

If you're calling CLI tools (sqlcmd, az, etc.) from Python on Windows:

```python
# ❌ BREAKS: cmd.exe interprets | as a pipe operator
subprocess.run(
    ["sqlcmd", "-S", endpoint, "-d", db, "-G", "-s", "|", "-Q", query],
    shell=True  # ← the problem
)

# ✅ WORKS: Don't use shell=True, use tab as separator
subprocess.run(
    ["sqlcmd", "-S", endpoint, "-d", db, "-G", "-s", "\t", "-Q", query]
    # shell=False is the default
)
```

`shell=True` causes `cmd.exe` to process the arguments, and special characters like `|`, `&`, `>`, `<` get interpreted as shell operators.

---

## 6. Token Audience Confusion

Fabric uses different OAuth token audiences for different services:

| Service | Audience | When to Use |
|---------|----------|-------------|
| Fabric REST API | `https://api.fabric.microsoft.com` | CRUD, definitions, management |
| Power BI API | `https://analysis.windows.net/powerbi/api` | Semantic models, reports |
| OneLake storage | `https://storage.azure.com` | File upload/download, DFS |

Using the wrong audience gives a 401 or 403 with an unhelpful error message.

```bash
# Get a Fabric API token
az account get-access-token --resource "https://api.fabric.microsoft.com" --query accessToken -o tsv

# Get a OneLake storage token
az account get-access-token --resource "https://storage.azure.com" --query accessToken -o tsv
```

---

## 7. Workspace Visibility Differences

Not all workspaces are visible through all APIs:

```
Fabric REST API:    GET /workspaces     → Shows workspaces you have access to
OneLake DFS API:    filesystem list     → May show FEWER workspaces
Fabric MCP Server:  list_workspaces     → Uses OneLake, same visibility as DFS
```

If a workspace appears in the Fabric portal but not in OneLake API calls, it may be a capacity or permission issue. Personal workspaces and workspaces on shared capacity sometimes behave differently.

---

## 8. The Published vs. Draft Distinction

Fabric items have two states: **draft** and **published**. The REST API returns both:

```json
{
  "definition": {
    "parts": [
      {"path": "files/config/draft/stage_config.json", "payload": "..."},
      {"path": "files/config/published/stage_config.json", "payload": "..."}
    ]
  }
}
```

**Rules:**
- `getDefinition` returns both draft AND published files
- `updateDefinition` must only include draft files
- There is NO publish API — you must publish manually in the Fabric UI
- Draft and published configs can differ (that's the point)

---

## 9. Data Agent Query Format

Data Agents use the OpenAI Assistants API format, NOT the Chat Completions API:

```python
# ❌ Wrong: Chat Completions format
requests.post(url, json={"messages": [{"role": "user", "content": "..."}]})

# ✅ Right: Assistants API format
# Step 1: Create a thread
thread = requests.post(f"{base}/threads", headers=headers)

# Step 2: Add a message
requests.post(f"{base}/threads/{thread_id}/messages", json={
    "role": "user",
    "content": "How many orders do we have?"
})

# Step 3: Create a run
run = requests.post(f"{base}/threads/{thread_id}/runs", json={
    "assistant_id": agent_id
})

# Step 4: Poll until complete, then get messages
```

---

## 10. Rate Limits and Throttling

Fabric APIs have undocumented rate limits:

- **Definition operations**: ~10 per minute
- **Query operations**: ~60 per minute  
- **OneLake file operations**: Higher limits but varies

When throttled, you get a `429 Too Many Requests` with a `Retry-After` header. Always respect it:

```python
if resp.status_code == 429:
    retry_after = int(resp.headers.get("Retry-After", 30))
    time.sleep(retry_after)
```

---

## Summary Table

| Gotcha | Impact | Workaround |
|--------|--------|------------|
| LRO /result | Silent data loss | Always GET `{url}/result` after Succeeded |
| null body | Crash or None | Guard with `body.strip() != "null"` |
| Case sensitivity | 404 errors | Use exact casing per operation type |
| Partial update | Deleted files | Always send ALL definition files |
| shell=True | Broken commands | Use `shell=False` (default) |
| Token audience | 401/403 | Match audience to service |
| Workspace visibility | Missing items | Check capacity/permissions |
| Draft vs published | 409 errors | Only send draft files in updates |
| Query format | Wrong API | Use Assistants API, not Chat |
| Rate limits | 429 errors | Respect Retry-After header |
