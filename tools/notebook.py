"""Fabric Notebook CRUD - Create, Read, Update, Execute Python notebooks via REST API.

Usage:
    python tools/notebook.py create --workspace-id WS_ID --name NAME [--from-file FILE]
    python tools/notebook.py read   --workspace-id WS_ID --notebook-id NB_ID [--format json|markdown|raw]
    python tools/notebook.py update --workspace-id WS_ID --notebook-id NB_ID --from-file FILE
    python tools/notebook.py execute --workspace-id WS_ID --notebook-id NB_ID [--wait] [--timeout SEC]
    python tools/notebook.py list   --workspace-id WS_ID

Authentication: Uses `az account get-access-token` (Azure CLI must be logged in).
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error

API_BASE = "https://api.fabric.microsoft.com/v1"


# ── Authentication ──────────────────────────────────────────────────────────

def get_token() -> str:
    """Get Fabric API token via Azure CLI."""
    cmd = ["az", "account", "get-access-token", "--resource",
           "https://api.fabric.microsoft.com", "--query", "accessToken", "-o", "tsv"]
    # On Windows, az is az.cmd
    if os.name == "nt":
        cmd[0] = "az.cmd"
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=(os.name == "nt"))
        return r.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error getting token. Ensure `az login` has been run.\n{e}", file=sys.stderr)
        sys.exit(1)


# ── HTTP Helpers ────────────────────────────────────────────────────────────

def api_request(url: str, token: str, method: str = "GET", body: dict | None = None) -> tuple:
    """Make an authenticated Fabric API request. Returns (status, headers, body_text)."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, dict(resp.headers), resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8")


def poll_lro(url: str, token: str, label: str = "operation", max_wait: int = 300) -> tuple:
    """Poll a long-running operation until completion."""
    for i in range(max_wait // 5):
        time.sleep(5)
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {token}")
        try:
            resp = urllib.request.urlopen(req)
            body = resp.read().decode("utf-8")
            data = json.loads(body) if body else {}
            status = data.get("status", "Unknown")
            print(f"  [{label}] {status} ({(i + 1) * 5}s)", file=sys.stderr)
            if status in ("Succeeded", "Completed", "Failed"):
                return status, data
        except urllib.error.HTTPError as e:
            if e.code == 200:
                return "Succeeded", {}
            print(f"  [{label}] HTTP {e.code} ({(i + 1) * 5}s)", file=sys.stderr)
        except (urllib.error.URLError, OSError):
            print(f"  [{label}] Network retry ({(i + 1) * 5}s)", file=sys.stderr)
    return "Timeout", {}


# ── Format Conversion ──────────────────────────────────────────────────────

def ipynb_to_fabric_source(nb: dict) -> str:
    """Convert .ipynb JSON to Fabric notebook-content.py source format."""
    lines = ["# Fabric notebook source", "", "# METADATA ********************", ""]
    nb_meta = {
        "kernel_info": {"name": "jupyter", "jupyter_kernel_name": "python3.11"},
        "dependencies": {
            "lakehouse": {
                "default_lakehouse_name": "",
                "default_lakehouse_workspace_id": "",
            }
        },
    }
    for ml in json.dumps(nb_meta, indent=2).split("\n"):
        lines.append("# META " + ml)

    for cell in nb.get("cells", []):
        lines.append("")
        if cell["cell_type"] == "markdown":
            lines.append("# MARKDOWN ********************")
            lines.append("")
            for line in "".join(cell.get("source", [])).split("\n"):
                lines.append("# " + line)
        elif cell["cell_type"] == "code":
            lines.append("# CELL ********************")
            lines.append("")
            for line in "".join(cell.get("source", [])).split("\n"):
                lines.append(line)
            lines.extend(["", "# METADATA ********************", ""])
            cell_meta = {"language": "python", "language_group": "jupyter_python"}
            for ml in json.dumps(cell_meta, indent=2).split("\n"):
                lines.append("# META " + ml)
    lines.append("")
    return "\n".join(lines)


def fabric_source_to_cells(content: str) -> list:
    """Parse Fabric notebook-content.py into a list of cell dicts."""
    lines = content.split("\n")
    cells = []
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        if line == "# MARKDOWN ********************":
            i += 1
            # Skip blank line after marker
            if i < len(lines) and lines[i].strip() == "":
                i += 1
            md_lines = []
            while i < len(lines):
                cur = lines[i].rstrip()
                if cur.startswith("# CELL ********************") or cur.startswith("# MARKDOWN ********************"):
                    break
                if cur.startswith("# META ") or cur == "# METADATA ********************":
                    break
                # Strip the "# " prefix
                if cur.startswith("# "):
                    md_lines.append(cur[2:])
                elif cur == "#":
                    md_lines.append("")
                else:
                    md_lines.append(cur)
                i += 1
            # Remove trailing empty lines
            while md_lines and md_lines[-1] == "":
                md_lines.pop()
            cells.append({"type": "markdown", "content": "\n".join(md_lines)})

        elif line == "# CELL ********************":
            i += 1
            if i < len(lines) and lines[i].strip() == "":
                i += 1
            code_lines = []
            while i < len(lines):
                cur = lines[i].rstrip()
                if cur == "# METADATA ********************":
                    # Skip metadata block
                    i += 1
                    while i < len(lines):
                        if lines[i].rstrip().startswith("# META "):
                            i += 1
                        elif lines[i].strip() == "":
                            i += 1
                        else:
                            break
                    break
                if cur.startswith("# CELL ********************") or cur.startswith("# MARKDOWN ********************"):
                    break
                code_lines.append(cur)
                i += 1
            # Remove trailing empty lines
            while code_lines and code_lines[-1] == "":
                code_lines.pop()
            cells.append({"type": "code", "content": "\n".join(code_lines)})
        else:
            i += 1

    return cells


def make_platform(name: str) -> str:
    """Create the .platform JSON for a notebook."""
    return json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Notebook", "displayName": name, "description": ""},
        "config": {"version": "2.0", "logicalId": "00000000-0000-0000-0000-000000000000"},
    })


# ── Commands ────────────────────────────────────────────────────────────────

def cmd_list(args):
    """List notebooks in a workspace."""
    token = get_token()
    url = f"{API_BASE}/workspaces/{args.workspace_id}/notebooks"
    status, _, body = api_request(url, token)
    if status != 200:
        print(f"Error: HTTP {status}\n{body}", file=sys.stderr)
        sys.exit(1)
    data = json.loads(body)
    notebooks = data.get("value", [])
    if args.format == "json":
        print(json.dumps(notebooks, indent=2))
    else:
        print(f"Notebooks in workspace ({len(notebooks)}):\n")
        for nb in notebooks:
            desc = nb.get("description", "")
            desc_str = f" - {desc}" if desc else ""
            print(f"  {nb['displayName']}  (id: {nb['id']}){desc_str}")


def cmd_read(args):
    """Read/extract a notebook's content."""
    token = get_token()
    # Step 1: getDefinition (LRO)
    url = f"{API_BASE}/workspaces/{args.workspace_id}/notebooks/{args.notebook_id}/getDefinition"
    status, headers, body = api_request(url, token, method="POST", body={})

    if status == 200:
        result_data = json.loads(body)
    elif status == 202:
        location = headers.get("Location", "")
        if not location:
            print("Error: 202 but no Location header", file=sys.stderr)
            sys.exit(1)
        lro_status, lro_data = poll_lro(location, token, "getDefinition")
        if lro_status != "Succeeded":
            print(f"Error: getDefinition {lro_status}", file=sys.stderr)
            sys.exit(1)
        # Fetch result
        result_url = location + "/result" if "?" not in location else location.replace("?", "/result?")
        _, _, result_body = api_request(result_url, token)
        result_data = json.loads(result_body)
    else:
        print(f"Error: HTTP {status}\n{body}", file=sys.stderr)
        sys.exit(1)

    # Step 2: Extract notebook-content.py
    defn = result_data.get("definition", {})
    nb_content = ""
    for part in defn.get("parts", []):
        if part["path"] == "notebook-content.py":
            nb_content = base64.b64decode(part["payload"]).decode("utf-8")
            break

    if not nb_content:
        print("Error: No notebook-content.py found in definition", file=sys.stderr)
        sys.exit(1)

    # Step 3: Output in requested format
    if args.format == "raw":
        print(nb_content)
    elif args.format == "json":
        cells = fabric_source_to_cells(nb_content)
        print(json.dumps(cells, indent=2))
    elif args.format == "markdown":
        cells = fabric_source_to_cells(nb_content)
        for cell in cells:
            if cell["type"] == "markdown":
                print(cell["content"])
                print()
            else:
                print("```python")
                print(cell["content"])
                print("```")
                print()


def cmd_create(args):
    """Create a new notebook in a workspace."""
    token = get_token()

    if args.from_file:
        with open(args.from_file, "r", encoding="utf-8") as f:
            if args.from_file.endswith(".ipynb"):
                nb = json.load(f)
                nb_content = ipynb_to_fabric_source(nb)
            else:
                nb_content = f.read()
    else:
        # Create an empty notebook
        nb_content = "# Fabric notebook source\n\n# METADATA ********************\n\n"
        nb_content += '# META {\n# META   "kernel_info": {\n# META     "name": "jupyter",\n'
        nb_content += '# META     "jupyter_kernel_name": "python3.11"\n# META   },\n'
        nb_content += '# META   "dependencies": {\n# META     "lakehouse": {}\n# META   }\n# META }\n'

    nb_b64 = base64.b64encode(nb_content.encode("utf-8")).decode("utf-8")
    platform_b64 = base64.b64encode(make_platform(args.name).encode("utf-8")).decode("utf-8")

    payload = {
        "displayName": args.name,
        "definition": {
            "format": "FabricGitSource",
            "parts": [
                {"path": "notebook-content.py", "payload": nb_b64, "payloadType": "InlineBase64"},
                {"path": ".platform", "payload": platform_b64, "payloadType": "InlineBase64"},
            ],
        },
    }

    url = f"{API_BASE}/workspaces/{args.workspace_id}/notebooks"
    status, headers, body = api_request(url, token, method="POST", body=payload)

    if status == 201:
        data = json.loads(body)
        print(f"Created: {data.get('displayName', args.name)} (id: {data.get('id', 'unknown')})")
    elif status == 202:
        location = headers.get("Location", "")
        if location:
            lro_status, _ = poll_lro(location, token, "create")
            print(f"Create: {lro_status}")
        else:
            print("Accepted (202). Check Fabric portal for the new notebook.")
    else:
        print(f"Error: HTTP {status}\n{body}", file=sys.stderr)
        sys.exit(1)


def cmd_update(args):
    """Update a notebook's definition."""
    token = get_token()

    with open(args.from_file, "r", encoding="utf-8") as f:
        if args.from_file.endswith(".ipynb"):
            nb = json.load(f)
            nb_content = ipynb_to_fabric_source(nb)
        else:
            nb_content = f.read()

    nb_b64 = base64.b64encode(nb_content.encode("utf-8")).decode("utf-8")
    platform_b64 = base64.b64encode(make_platform(args.name or "notebook").encode("utf-8")).decode("utf-8")

    payload = {
        "definition": {
            "format": "FabricGitSource",
            "parts": [
                {"path": "notebook-content.py", "payload": nb_b64, "payloadType": "InlineBase64"},
                {"path": ".platform", "payload": platform_b64, "payloadType": "InlineBase64"},
            ],
        },
    }

    url = f"{API_BASE}/workspaces/{args.workspace_id}/notebooks/{args.notebook_id}/updateDefinition"
    status, headers, body = api_request(url, token, method="POST", body=payload)

    if status == 200:
        print("Updated successfully.")
    elif status == 202:
        location = headers.get("Location", "")
        if location:
            lro_status, _ = poll_lro(location, token, "update")
            print(f"Update: {lro_status}")
        else:
            print("Accepted (202).")
    else:
        print(f"Error: HTTP {status}\n{body}", file=sys.stderr)
        sys.exit(1)


def cmd_execute(args):
    """Execute a notebook via Job Scheduler API."""
    token = get_token()
    url = f"{API_BASE}/workspaces/{args.workspace_id}/items/{args.notebook_id}/jobs/instances?jobType=RunNotebook"
    status, headers, body = api_request(url, token, method="POST", body={})

    if status == 202:
        print("Notebook run triggered.", file=sys.stderr)
        if args.wait:
            location = headers.get("Location", "")
            if location:
                lro_status, _ = poll_lro(location, token, "run", max_wait=args.timeout)
                print(f"Run result: {lro_status}")
            else:
                print("No Location header for polling. Check Fabric portal.")
        else:
            print("Use --wait to poll for completion.")
    else:
        print(f"Error: HTTP {status}\n{body}", file=sys.stderr)
        sys.exit(1)


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Fabric Notebook CRUD - Create, Read, Update, Execute notebooks via REST API."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = sub.add_parser("list", help="List notebooks in a workspace")
    p_list.add_argument("--workspace-id", required=True, help="Workspace ID")
    p_list.add_argument("--format", choices=["text", "json"], default="text")

    # read
    p_read = sub.add_parser("read", help="Read/extract notebook content")
    p_read.add_argument("--workspace-id", required=True, help="Workspace ID")
    p_read.add_argument("--notebook-id", required=True, help="Notebook ID")
    p_read.add_argument("--format", choices=["json", "markdown", "raw"], default="markdown",
                        help="Output format (default: markdown)")

    # create
    p_create = sub.add_parser("create", help="Create a new notebook")
    p_create.add_argument("--workspace-id", required=True, help="Workspace ID")
    p_create.add_argument("--name", required=True, help="Notebook display name")
    p_create.add_argument("--from-file", help="Source .ipynb or notebook-content.py file")

    # update
    p_update = sub.add_parser("update", help="Update notebook definition")
    p_update.add_argument("--workspace-id", required=True, help="Workspace ID")
    p_update.add_argument("--notebook-id", required=True, help="Notebook ID")
    p_update.add_argument("--name", help="Notebook display name (for .platform)")
    p_update.add_argument("--from-file", required=True, help="Source .ipynb or notebook-content.py file")

    # execute
    p_exec = sub.add_parser("execute", help="Execute a notebook")
    p_exec.add_argument("--workspace-id", required=True, help="Workspace ID")
    p_exec.add_argument("--notebook-id", required=True, help="Notebook ID")
    p_exec.add_argument("--wait", action="store_true", help="Wait for completion")
    p_exec.add_argument("--timeout", type=int, default=300, help="Max wait seconds (default: 300)")

    args = parser.parse_args()

    commands = {
        "list": cmd_list,
        "read": cmd_read,
        "create": cmd_create,
        "update": cmd_update,
        "execute": cmd_execute,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
