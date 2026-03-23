# MCP Integration Guide

> How to connect MCP (Model Context Protocol) servers to your AI coding assistant for Microsoft Fabric development.

---

## What Is MCP?

MCP is a standard protocol for connecting AI assistants to external tools and data sources. Instead of the AI generating commands for you to run, MCP servers let the AI execute operations directly.

```
Without MCP:  AI -> generates command -> you copy-paste -> terminal -> results -> you paste back
With MCP:     AI -> calls MCP tool -> results -> AI continues
```

---

## MCP Servers for Fabric

### 1. Microsoft Fabric MCP Server (OneLake)

The [official Fabric MCP server](https://github.com/microsoft/mcp) provides 21+ tools for OneLake operations.

**Setup:**

```bash
# Clone and build
git clone https://github.com/microsoft/mcp.git ~/.copilot/fabric-mcp
cd ~/.copilot/fabric-mcp/servers/Fabric.Mcp.Server/src
dotnet build -c Release
```

**Key tools:**

| Tool | What It Does |
|------|-------------|
| `list_workspaces` | List all accessible workspaces |
| `list_items` | List items in a workspace |
| `upload_file` | Upload a file to OneLake |
| `download_file` | Download a file from OneLake |
| `list_tables` | List tables in a lakehouse |
| `get_table` | Get table schema and preview |
| `best-practices` | Get Fabric best practices docs |
| `item-definitions` | Get item definition schemas |

**Authentication:** Uses your Azure CLI token (`az login`).

### 2. MS Learn MCP (via wrapper)

This toolkit includes `tools/mslearn.py` - a wrapper for the public MS Learn MCP endpoint.

**No setup needed** - it's a public HTTP endpoint at `https://learn.microsoft.com/api/mcp`.

**Tools:**

| Tool | What It Does |
|------|-------------|
| `microsoft_docs_search` | Search MS Learn docs |
| `microsoft_docs_fetch` | Fetch a doc page as markdown |
| `microsoft_code_sample_search` | Find official code samples |

### 3. Context7 MCP (via wrapper)

This toolkit includes `tools/context7.py` - a wrapper for the Context7 MCP server.

**Requires:** Node.js 18+, npx

**Tools:**

| Tool | What It Does |
|------|-------------|
| `resolve-library-id` | Find a library by name |
| `query-docs` | Fetch current docs for a library + topic |

---

## MCP Transport Types

Understanding the two transport types helps with troubleshooting:

### stdio Transport (Context7, Fabric MCP Server)

The AI tool spawns the MCP server as a subprocess and communicates via stdin/stdout:

```
AI Tool  ⟷  stdin/stdout  ⟷  MCP Server Process
```

- Server starts/stops with the AI tool
- No network needed
- Uses JSON-RPC line protocol

### Streamable HTTP Transport (MS Learn)

The MCP server runs as an HTTP service:

```
AI Tool  ⟷  HTTP POST  ⟷  https://learn.microsoft.com/api/mcp
```

- Server is always running (hosted by Microsoft)
- Requires internet
- Uses JSON-RPC over HTTP
- Session tracking via `Mcp-Session-Id` header

---

## Registering MCP Servers With Your AI Tool

### GitHub Copilot CLI

Currently, Copilot CLI doesn't natively support MCP configuration. That's why this toolkit uses **Python wrappers** - the AI runs `python tools/mslearn.py search "query"` as a regular command.

To make this seamless, add to your custom instructions:

```markdown
## Available Tools
- `python tools/mslearn.py search "query"` - search Microsoft docs
- `python tools/context7.py docs "id" --topic "topic"` - library docs
- `fabmcp onelake list_workspaces` - list Fabric workspaces
```

### Claude Code

Add to `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "fabric-onelake": {
      "command": "path/to/fabmcp.exe",
      "args": ["onelake"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp@latest"]
    }
  }
}
```

### Cursor / Windsurf

Add MCP server configuration in Settings -> MCP Servers:

```json
{
  "fabric-onelake": {
    "command": "path/to/fabmcp.exe",
    "args": ["onelake"]
  }
}
```

---

## Skills + MCP: Better Together

Skills and MCP servers complement each other:

```markdown
## In Your Skill (SKILL.md)

### With Fabric MCP Server
If `fabmcp` is available, use it directly to list items, upload files, etc.

### Without MCP Server
Generate `az rest` commands for the user to execute manually:
```bash
az rest --method GET \
  --url "https://api.fabric.microsoft.com/v1/workspaces/{id}/items"
```
```

**Best practice**: Always include a non-MCP fallback in your skill. Not everyone has the MCP server set up.

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| "MCP server not found" | Not installed or not in PATH | Verify installation, use full path |
| Authentication fails | Wrong Azure tenant | `az login --tenant YOUR_TENANT_ID` |
| 401 Unauthorized | Wrong token audience | Use `https://storage.azure.com` for OneLake |
| Context7 times out | npx download slow | Run once to cache: `npx @upstash/context7-mcp@latest` |
| MS Learn returns empty | Rate limited | Wait and retry |
| fabmcp shows 0 workspaces | Capacity/permissions | Check workspace access in portal |

---

## Further Reading

- [MCP Specification](https://modelcontextprotocol.io/)
- [Fabric MCP Server (GitHub)](https://github.com/microsoft/mcp)
- [Context7](https://context7.com)
- [skills-for-fabric MCP Guide](https://github.com/microsoft/skills-for-fabric/blob/main/docs/mcp-servers-guide.md)
