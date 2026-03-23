"""Deploy and extract WORKSPACE-CONTEXT notebooks in Microsoft Fabric workspaces.

Usage:
    python tools/workspace_context.py deploy  --workspace-id WS_ID
    python tools/workspace_context.py extract --workspace-id WS_ID [--format json|markdown] [--output FILE]

Authentication: Uses `az account get-access-token` (Azure CLI must be logged in).
"""

import argparse
import base64
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from notebook import (
    get_token,
    api_request,
    poll_lro,
    ipynb_to_fabric_source,
    fabric_source_to_cells,
    make_platform,
    API_BASE,
)

NOTEBOOK_NAME = "WORKSPACE-CONTEXT"


# -- Helpers -----------------------------------------------------------------

def _find_template() -> str:
    """Locate templates/WORKSPACE-CONTEXT.ipynb relative to this script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    path = os.path.join(repo_root, "templates", "WORKSPACE-CONTEXT.ipynb")
    if not os.path.isfile(path):
        print(f"Error: Template not found at {path}", file=sys.stderr)
        sys.exit(1)
    return path


def _find_notebook(workspace_id: str, token: str) -> dict | None:
    """Find the WORKSPACE-CONTEXT notebook in a workspace. Returns dict or None."""
    url = f"{API_BASE}/workspaces/{workspace_id}/notebooks"
    status, _, body = api_request(url, token)
    if status != 200:
        print(f"Error listing notebooks: HTTP {status}\n{body}", file=sys.stderr)
        sys.exit(1)
    for nb in json.loads(body).get("value", []):
        if nb.get("displayName") == NOTEBOOK_NAME:
            return nb
    return None


def _get_definition(workspace_id: str, notebook_id: str, token: str) -> str:
    """Fetch notebook-content.py via getDefinition LRO. Returns content string."""
    url = f"{API_BASE}/workspaces/{workspace_id}/notebooks/{notebook_id}/getDefinition"
    status, headers, body = api_request(url, token, method="POST", body={})

    if status == 200:
        result_data = json.loads(body)
    elif status == 202:
        location = headers.get("Location", "")
        if not location:
            print("Error: 202 but no Location header", file=sys.stderr)
            sys.exit(1)
        lro_status, _ = poll_lro(location, token, "getDefinition")
        if lro_status != "Succeeded":
            print(f"Error: getDefinition {lro_status}", file=sys.stderr)
            sys.exit(1)
        result_url = (
            location + "/result"
            if "?" not in location
            else location.replace("?", "/result?")
        )
        _, _, result_body = api_request(result_url, token)
        result_data = json.loads(result_body)
    else:
        print(f"Error: HTTP {status}\n{body}", file=sys.stderr)
        sys.exit(1)

    for part in result_data.get("definition", {}).get("parts", []):
        if part["path"] == "notebook-content.py":
            return base64.b64decode(part["payload"]).decode("utf-8")

    print("Error: No notebook-content.py found in definition", file=sys.stderr)
    sys.exit(1)


def _build_payload(nb_content: str, name: str) -> dict:
    """Build the Fabric create/update payload from notebook content."""
    nb_b64 = base64.b64encode(nb_content.encode("utf-8")).decode("utf-8")
    platform_b64 = base64.b64encode(make_platform(name).encode("utf-8")).decode("utf-8")
    return {
        "definition": {
            "format": "FabricGitSource",
            "parts": [
                {"path": "notebook-content.py", "payload": nb_b64, "payloadType": "InlineBase64"},
                {"path": ".platform", "payload": platform_b64, "payloadType": "InlineBase64"},
            ],
        },
    }


# -- Commands ----------------------------------------------------------------

def cmd_deploy(args):
    """Deploy the WORKSPACE-CONTEXT template to a workspace."""
    token = get_token()

    # Read and convert template
    template_path = _find_template()
    with open(template_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
    nb_content = ipynb_to_fabric_source(nb)

    existing = _find_notebook(args.workspace_id, token)

    if existing:
        # Update existing notebook
        nb_id = existing["id"]
        print(f"Updating existing notebook (id: {nb_id})...", file=sys.stderr)
        payload = _build_payload(nb_content, NOTEBOOK_NAME)
        url = f"{API_BASE}/workspaces/{args.workspace_id}/notebooks/{nb_id}/updateDefinition"
        status, headers, body = api_request(url, token, method="POST", body=payload)

        if status == 200:
            print(f"Updated: {NOTEBOOK_NAME} (id: {nb_id})")
        elif status == 202:
            location = headers.get("Location", "")
            if location:
                lro_status, _ = poll_lro(location, token, "update")
                print(f"Update: {lro_status} (id: {nb_id})")
            else:
                print(f"Accepted (202). id: {nb_id}")
        else:
            print(f"Error: HTTP {status}\n{body}", file=sys.stderr)
            sys.exit(1)
    else:
        # Create new notebook
        print(f"Creating {NOTEBOOK_NAME}...", file=sys.stderr)
        payload = _build_payload(nb_content, NOTEBOOK_NAME)
        payload["displayName"] = NOTEBOOK_NAME
        url = f"{API_BASE}/workspaces/{args.workspace_id}/notebooks"
        status, headers, body = api_request(url, token, method="POST", body=payload)

        if status == 201:
            data = json.loads(body)
            print(f"Created: {NOTEBOOK_NAME} (id: {data.get('id', 'unknown')})")
        elif status == 202:
            location = headers.get("Location", "")
            if location:
                lro_status, _ = poll_lro(location, token, "create")
                print(f"Create: {lro_status}")
            else:
                print("Accepted (202). Check Fabric portal.")
        else:
            print(f"Error: HTTP {status}\n{body}", file=sys.stderr)
            sys.exit(1)


def cmd_extract(args):
    """Extract context from an existing WORKSPACE-CONTEXT notebook."""
    token = get_token()

    existing = _find_notebook(args.workspace_id, token)
    if not existing:
        print(f"Error: No notebook named '{NOTEBOOK_NAME}' found in workspace", file=sys.stderr)
        sys.exit(1)

    nb_id = existing["id"]
    print(f"Extracting from {NOTEBOOK_NAME} (id: {nb_id})...", file=sys.stderr)

    raw_content = _get_definition(args.workspace_id, nb_id, token)
    cells = fabric_source_to_cells(raw_content)

    # Build structured output
    sections = []
    for cell in cells:
        title = ""
        content = cell["content"]
        if cell["type"] == "markdown":
            # Use the first heading line as section title
            for line in content.split("\n"):
                stripped = line.strip().lstrip("#").strip()
                if stripped:
                    title = stripped
                    break
        sections.append({
            "type": cell["type"],
            "title": title,
            "content": content,
        })

    if args.format == "json":
        output = json.dumps(sections, indent=2)
    else:
        # markdown
        parts = []
        for section in sections:
            if section["type"] == "markdown":
                parts.append(section["content"])
            else:
                parts.append("```python")
                parts.append(section["content"])
                parts.append("```")
            parts.append("")
        output = "\n".join(parts)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Saved to {args.output}")
    else:
        print(output)


# -- CLI ---------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Deploy and extract WORKSPACE-CONTEXT notebooks in Fabric workspaces."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # deploy
    p_deploy = sub.add_parser("deploy", help="Deploy WORKSPACE-CONTEXT template to a workspace")
    p_deploy.add_argument("--workspace-id", required=True, help="Fabric workspace ID")

    # extract
    p_extract = sub.add_parser("extract", help="Extract context from WORKSPACE-CONTEXT notebook")
    p_extract.add_argument("--workspace-id", required=True, help="Fabric workspace ID")
    p_extract.add_argument("--format", choices=["json", "markdown"], default="markdown",
                           help="Output format (default: markdown)")
    p_extract.add_argument("--output", help="Save output to file instead of stdout")

    args = parser.parse_args()

    commands = {
        "deploy": cmd_deploy,
        "extract": cmd_extract,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
