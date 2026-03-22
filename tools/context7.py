"""
Context7 MCP Wrapper — fetch real-time library docs from the CLI.

Spawns the Context7 MCP server (npx @upstash/context7-mcp) as a subprocess,
communicates via JSON-RPC over stdio, and exposes CLI commands:

    python tools/context7.py search "pandas"
    python tools/context7.py docs "/pandas/pandas" --topic "read_parquet"

Requires: Node.js 18+, npx
Optional: CONTEXT7_API_KEY env var for higher rate limits
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import textwrap
import time
from typing import Any


class McpClient:
    """Minimal MCP client that communicates via JSON-RPC over stdio."""

    def __init__(self, command: list[str]):
        self._command = command
        self._proc: subprocess.Popen | None = None
        self._msg_id = 0

    def start(self) -> None:
        env = os.environ.copy()
        api_key = env.get("CONTEXT7_API_KEY", "")
        if api_key:
            env["CONTEXT7_API_KEY"] = api_key

        self._proc = subprocess.Popen(
            self._command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            shell=True,
        )
        self._initialize()

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            try:
                self._send({"method": "notifications/cancelled", "params": {}})
            except Exception:
                pass
            self._proc.terminate()
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        response = self._request("tools/call", {"name": name, "arguments": arguments})
        if "error" in response:
            raise RuntimeError(f"MCP error: {response['error']}")
        result = response.get("result", {})
        content = result.get("content", [])
        texts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block["text"])
            elif isinstance(block, str):
                texts.append(block)
        return "\n".join(texts) if texts else json.dumps(result, indent=2)

    def list_tools(self) -> list[dict]:
        response = self._request("tools/list", {})
        return response.get("result", {}).get("tools", [])

    def _initialize(self) -> None:
        self._request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "context7-cli", "version": "1.0.0"},
        })
        self._send({
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        })

    def _request(self, method: str, params: dict) -> dict:
        self._msg_id += 1
        msg = {"jsonrpc": "2.0", "id": self._msg_id, "method": method, "params": params}
        self._send(msg)
        return self._receive(self._msg_id)

    def _send(self, msg: dict) -> None:
        if not self._proc or not self._proc.stdin:
            raise RuntimeError("MCP server not running")
        line = json.dumps(msg) + "\n"
        self._proc.stdin.write(line.encode("utf-8"))
        self._proc.stdin.flush()

    def _receive(self, expected_id: int, timeout: float = 30.0) -> dict:
        if not self._proc or not self._proc.stdout:
            raise RuntimeError("MCP server not running")
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self._proc.stdout.readline()
            if not line:
                if self._proc.poll() is not None:
                    stderr = self._proc.stderr.read().decode("utf-8") if self._proc.stderr else ""
                    raise RuntimeError(f"MCP server exited (code {self._proc.returncode}): {stderr[:500]}")
                continue
            line = line.decode("utf-8").strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "id" not in msg:
                continue
            if msg.get("id") == expected_id:
                return msg
        raise TimeoutError(f"No response for request {expected_id} within {timeout}s")


def cmd_search(args: argparse.Namespace) -> None:
    client = McpClient(["npx", "-y", "@upstash/context7-mcp@latest"])
    try:
        client.start()
        result = client.call_tool("resolve-library-id", {
            "libraryName": args.query,
            "query": args.query,
        })
        print(result)
    finally:
        client.stop()


def cmd_docs(args: argparse.Namespace) -> None:
    client = McpClient(["npx", "-y", "@upstash/context7-mcp@latest"])
    try:
        client.start()
        params: dict[str, Any] = {
            "libraryId": args.library_id,
            "query": args.topic or "overview and usage",
        }
        result = client.call_tool("query-docs", params)
        print(result)
    finally:
        client.stop()


def cmd_tools(args: argparse.Namespace) -> None:
    client = McpClient(["npx", "-y", "@upstash/context7-mcp@latest"])
    try:
        client.start()
        tools = client.list_tools()
        for t in tools:
            print(f"  {t['name']}: {t.get('description', '(no description)')[:100]}")
            if "inputSchema" in t:
                props = t["inputSchema"].get("properties", {})
                for pname, pinfo in props.items():
                    req = " (required)" if pname in t["inputSchema"].get("required", []) else ""
                    print(f"    --{pname}: {pinfo.get('description', '?')[:80]}{req}")
    finally:
        client.stop()


def main():
    parser = argparse.ArgumentParser(
        prog="context7",
        description="Fetch real-time library documentation via Context7 MCP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              python tools/context7.py search "fabric rest api"
              python tools/context7.py docs "/pandas/pandas" --topic "read_parquet"
              python tools/context7.py tools
        """),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="Search for a library by name")
    p_search.add_argument("query", help="Library name or keyword to search")
    p_search.set_defaults(func=cmd_search)

    p_docs = sub.add_parser("docs", help="Fetch docs for a library")
    p_docs.add_argument("library_id", help="Context7 library ID (from search)")
    p_docs.add_argument("--topic", "-t", default="overview and usage",
                         help="Topic to focus docs on (default: overview and usage)")
    p_docs.set_defaults(func=cmd_docs)

    p_tools = sub.add_parser("tools", help="List available MCP tools")
    p_tools.set_defaults(func=cmd_tools)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
