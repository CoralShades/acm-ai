# E2E Tests: MCP Servers

Test checklist for verifying MCP server connectivity and functionality.

## Prerequisites

- [ ] Claude Code CLI installed
- [ ] `.claude/settings.json` configured
- [ ] Required environment variables set
- [ ] Required services running (if applicable)

## Test: MCP Server List

### Steps
1. Run `claude mcp list`
2. Observe output

### Expected
- Shows all configured servers
- Status indicates connected/disconnected
- No error messages

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: Filesystem Server

### Steps
1. Verify filesystem server in settings.json
2. Ask Claude to list files in current directory
3. Ask Claude to read a specific file

### Expected
- Server connects successfully
- File operations work within project directory
- Respects path restrictions

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: Memory Server

### Steps
1. Verify memory server in settings.json
2. Ask Claude to remember something
3. Start new conversation
4. Ask Claude about remembered item

### Expected
- Server connects successfully
- Items persist between conversations
- Memory can be retrieved

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: GitHub Server (if configured)

### Steps
1. Verify GITHUB_TOKEN is set
2. Ask Claude about a repository
3. Ask Claude to list issues/PRs

### Expected
- Server connects with token
- Repository info retrieved
- Issues/PRs accessible

### Result
- [ ] PASS
- [ ] FAIL (note reason):
- [ ] SKIP (not configured)

---

## Test: Custom MCP Server

### Steps
1. Add custom server to settings.json
2. Restart Claude Code
3. Test server-specific functionality

### Expected
- Server appears in mcp list
- Server tools are available
- Operations work as expected

### Result
- [ ] PASS
- [ ] FAIL (note reason):
- [ ] SKIP (no custom server)

---

## Test: Environment Variables

### Steps
1. Use `${VAR}` syntax in settings.json
2. Set environment variable
3. Restart Claude Code

### Expected
- Variable is substituted
- Server uses correct value
- No plaintext secrets in config

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: Server Reconnection

### Steps
1. Start Claude with all servers
2. Stop a service (if applicable)
3. Restart the service
4. Try to use the server

### Expected
- Handles disconnection gracefully
- Reconnects when service available
- Clear error messages

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Test: Invalid Configuration

### Steps
1. Add invalid server config
2. Restart Claude Code
3. Observe behavior

### Expected
- Invalid server is skipped
- Other servers still work
- Clear error message

### Result
- [ ] PASS
- [ ] FAIL (note reason):

---

## Troubleshooting

### Server not connecting
1. Check settings.json syntax (valid JSON)
2. Verify npx can run the package
3. Check environment variables
4. Check network connectivity

### Server disconnected
1. Check if underlying service is running
2. Verify port availability
3. Check authentication credentials

### Permission denied
1. Check file permissions
2. Verify token scopes
3. Check allowed operations

---

## Test Summary

| Test | Status |
|------|--------|
| MCP Server List | |
| Filesystem Server | |
| Memory Server | |
| GitHub Server | |
| Custom MCP Server | |
| Environment Variables | |
| Server Reconnection | |
| Invalid Configuration | |

**Overall Result**: [ ] PASS / [ ] FAIL

**Tester**: _______________
**Date**: _______________
