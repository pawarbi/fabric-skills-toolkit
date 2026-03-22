"""
Microsoft Learn MCP Wrapper — fetch official MS docs from the CLI.

Uses the public MS Learn MCP HTTP endpoint (https://learn.microsoft.com/api/mcp).
No authentication required. No external dependencies (Python stdlib only).

    python tools/mslearn.py search "fabric data agent rest api"
    python tools/mslearn.py fetch "https://learn.microsoft.com/en-us/fabric/..."
    python tools/mslearn.py code "azure openai python"

Tools exposed by the server:
  - microsoft_docs_search: Semantic search across MS Learn docs
  - microsoft_docs_fetch: Fetch a full doc page as markdown
  - microsoft_code_sample_search: Search official code samples
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
import urllib.request
import urllib.error
import uuid
from typing import Any

MCP_ENDPOINT = "https://learn.microsoft.com/api/mcp"


class McpHttpClient:
    """Minimal MCP client for Streamable HTTP transport."""

    def __init__(self, endpoint: str = MCP_ENDPOINT):
        self.endpoint = endpoint
        self._session_id: str | None = None
        self._initialized = False

    def initialize(self) -> None:
        resp = self._rpc("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mslearn-cli", "version": "1.0.0"},
        })
        self._session_id = resp.get("_session_id")
        self._notify("notifications/initialized", {})
        self._initialized = True

    def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        if not self._initialized:
            self.initialize()
        result = self._rpc("tools/call", {"name": name, "arguments": arguments})
        content = result.get("content", [])
        texts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block["text"])
            elif isinstance(block, str):
                texts.append(block)
        return "\n".join(texts) if texts else json.dumps(result, indent=2)

    def list_tools(self) -> list[dict]:
        if not self._initialized:
            self.initialize()
        result = self._rpc("tools/list", {})
        return result.get("tools", [])

    def _rpc(self, method: str, params: dict) -> dict:
        msg = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": method,
            "params": params,
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id

        data = json.dumps(msg).encode("utf-8")
        req = urllib.request.Request(self.endpoint, data=data, headers=headers, method="POST")

        try:
            resp = urllib.request.urlopen(req, timeout=30)
            sid = resp.getheader("Mcp-Session-Id")
            if sid:
                self._session_id = sid
            body = resp.read().decode("utf-8")

            if "text/event-stream" in (resp.getheader("Content-Type") or ""):
                return self._parse_sse(body)

            parsed = json.loads(body)
            if isinstance(parsed, list):
                for item in parsed:
                    if "result" in item:
                        return item["result"]
                    if "error" in item:
                        raise RuntimeError(f"MCP error: {item['error']}")
                return parsed[0] if parsed else {}
            elif "result" in parsed:
                return parsed["result"]
            elif "error" in parsed:
                raise RuntimeError(f"MCP error: {parsed['error']}")
            return parsed

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"HTTP {e.code}: {body[:300]}") from e

    def _notify(self, method: str, params: dict) -> None:
        msg = {"jsonrpc": "2.0", "method": method, "params": params}
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        data = json.dumps(msg).encode("utf-8")
        req = urllib.request.Request(self.endpoint, data=data, headers=headers, method="POST")
        try:
            urllib.request.urlopen(req, timeout=10)
        except Exception:
            pass

    @staticmethod
    def _parse_sse(body: str) -> dict:
        for line in body.split("\n"):
            line = line.strip()
            if line.startswith("data:"):
                data_str = line[5:].strip()
                if data_str:
                    try:
                        parsed = json.loads(data_str)
                        if "result" in parsed:
                            return parsed["result"]
                    except json.JSONDecodeError:
                        continue
        return {}


def cmd_search(args: argparse.Namespace) -> None:
    client = McpHttpClient()
    raw = client.call_tool("microsoft_docs_search", {"query": args.query})
    try:
        data = json.loads(raw)
        results = data.get("results", [])
        if results:
            for r in results:
                title = r.get("title", "(no title)")
                url = r.get("url", "")
                snippet = r.get("content", "")[:200].replace("\n", " ").strip()
                print(f"- **{title}**")
                if url:
                    print(f"  {url}")
                if snippet:
                    print(f"  {snippet}...")
                print()
        else:
            print("No results found.")
    except (json.JSONDecodeError, TypeError):
        print(raw)


def cmd_fetch(args: argparse.Namespace) -> None:
    client = McpHttpClient()
    result = client.call_tool("microsoft_docs_fetch", {"url": args.url})
    print(result)


def cmd_code(args: argparse.Namespace) -> None:
    client = McpHttpClient()
    raw = client.call_tool("microsoft_code_sample_search", {"query": args.query})
    try:
        data = json.loads(raw)
        results = data.get("results", [])
        if results:
            for r in results[:10]:
                desc = r.get("description", "").split("\n")[0][:120]
                lang = r.get("language", "?")
                link = r.get("link", "")
                print(f"- [{lang}] {desc}")
                if link:
                    print(f"  {link}")
                snippet = r.get("codeSnippet", "")
                if snippet:
                    lines = snippet.replace("\r\n", "\n").split("\n")[:5]
                    for line in lines:
                        print(f"    {line}")
                    if len(snippet.split("\n")) > 5:
                        print(f"    ... ({len(snippet)} chars total)")
                print()
        else:
            print("No code samples found.")
    except (json.JSONDecodeError, TypeError):
        print(raw)


def cmd_tools(args: argparse.Namespace) -> None:
    client = McpHttpClient()
    tools = client.list_tools()
    for t in tools:
        print(f"  {t['name']}: {t.get('description', '(no description)')[:120]}")
        if "inputSchema" in t:
            props = t["inputSchema"].get("properties", {})
            for pname, pinfo in props.items():
                req = " (required)" if pname in t["inputSchema"].get("required", []) else ""
                print(f"    --{pname}: {pinfo.get('description', '?')[:80]}{req}")


def main():
    parser = argparse.ArgumentParser(
        prog="mslearn",
        description="Fetch official Microsoft documentation via MS Learn MCP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python tools/mslearn.py search "fabric data agent configuration"
              python tools/mslearn.py fetch "https://learn.microsoft.com/en-us/fabric/..."
              python tools/mslearn.py code "azure openai python chat completion"
              python tools/mslearn.py tools
        """),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="Search MS Learn docs")
    p_search.add_argument("query", help="Search query")
    p_search.set_defaults(func=cmd_search)

    p_fetch = sub.add_parser("fetch", help="Fetch a doc page as markdown")
    p_fetch.add_argument("url", help="Full URL of the MS Learn page")
    p_fetch.set_defaults(func=cmd_fetch)

    p_code = sub.add_parser("code", help="Search official code samples")
    p_code.add_argument("query", help="Code sample search query")
    p_code.set_defaults(func=cmd_code)

    p_tools = sub.add_parser("tools", help="List available MCP tools")
    p_tools.set_defaults(func=cmd_tools)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
