# MCP Server Porting Summary

## Overview
This document summarizes the results of porting global MCP servers from your local Claude and VS Code environments into the project-specific workspace (`d:\ailocal\acm-ai-production\.mcp.json`).

## Porting Results

### ✅ Successfully Ported Servers

**1. `xero` (from Windows Claude Desktop Config)**
- **Source:** `C:\Users\User\AppData\Roaming\Claude\claude_desktop_config.json`
- **Command:** `npx -y @xeroapi/xero-mcp-server@latest`
- **Configuration Details:** Migrated alongside its `XERO_CLIENT_ID` and `XERO_CLIENT_SECRET` environment variables.
- **Local Initialization Check:** Successfully started without missing dependencies or local pathing issues.

**2. `n8n-mcp-local` (from Windows Claude Desktop Config)**
- **Source:** `C:\Users\User\AppData\Roaming\Claude\claude_desktop_config.json`
- **Command:** `npx -y supergateway`
- **Configuration Details:** Connects to `http://localhost:5678/mcp-server/http`. This was renamed from `n8n-mcp` to `n8n-mcp-local` in the project settings to prevent conflicts with the production `n8n-mcp` server (`https://n8n-prod.coralshades.ai/mcp-server/http`) that was already defined in the local `.mcp.json`.
- **Local Initialization Check:** Successfully downloaded `supergateway` and started the stdio stream to await requests.

### ❓ Unfound or skipped sources
- **VS Code Global `settings.json` (Windows):** The file at `C:\Users\User\AppData\Roaming\Code\User\settings.json` was analyzed. While it contains some MCP flags (`chat.mcp.autostart`, etc.), it did not contain server definitions mapping (`mcpServers`).
- **WSL Global Settings (`~/.vscode-server/data/Machine/settings.json`, `~/.config/Claude/claude_desktop_config.json`):** Attempted to locate these files in the `Ubuntu` WSL distribution via process checks (`ls`, `find`). The files do not exist at these locations under the active WSL user.

## Implementation Notes
- The Antigravity registry configurations were placed inside `.mcp.json` at the root of the project, observing the standard best practice for Agent tooling configuration.
- The node-based servers were executed via `npx -y`. Testing them dynamically downloaded the remote modules and evaluated them within an isolated environment. None of them surfaced missing local dependencies or fatal pathing breaks.
