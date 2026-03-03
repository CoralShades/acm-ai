# MCP Patterns

> Model Context Protocol servers extending Claude Code capabilities for Ralph loops.

## Server Inventory

| Server | Purpose | Required | Config Location |
|--------|---------|----------|-----------------|
| `filesystem` | Directory tree views, file operations | Optional | `.claude/settings.json` |
| `context7` | Up-to-date library/framework documentation | Optional | `.claude/settings.json` |
| `chrome-devtools` | Page snapshots, screenshots, DOM inspection | Optional | `.claude/settings.local.json` |
| `playwright` | Full browser automation, E2E testing | Optional | `.claude/settings.local.json` |
| `n8n` | Workflow automation, external integrations | Optional | `.claude/settings.local.json` |
| `Atlassian` | Jira issues, Confluence pages | Optional | Claude.ai MCP integration |

## Context7 — Library Documentation

### Purpose
Fetch current documentation for any library/framework instead of relying on training data. Critical for accurate code generation with recent API changes.

### Tool Call Sequence

```
1. resolve-library-id("react", "how to use suspense")
   → Returns: [{ id: "/reactjs/react", name: "React" }, ...]

2. Pick best match (prefer exact names, version-specific IDs)

3. query-docs("/reactjs/react", "how to use suspense")
   → Returns: current docs with code examples

4. Answer using fetched docs, cite version
```

### When to Use
- Any code generation involving specific library APIs
- Setup questions for frameworks
- API reference lookups
- Version-specific behavior questions

### Configuration
```json
{
  "mcpServers": {
    "context7": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@context7/mcp"]
    }
  }
}
```

## Chrome DevTools — Page Inspection

### Purpose
Take DOM snapshots and screenshots for UI story verification. Essential for the Story Verification Protocol.

### Key Tools

| Tool | Purpose | Returns |
|------|---------|---------|
| `navigate_page` | Navigate to URL | Page load confirmation |
| `take_snapshot` | Capture DOM structure | Accessibility tree / DOM tree |
| `take_screenshot` | Visual capture | PNG screenshot |
| `evaluate_script` | Run JS in page | Script output |
| `list_pages` | Show open tabs | Page list with URLs |
| `click` | Click element | Action confirmation |
| `fill` | Fill form field | Action confirmation |

### Story Verification Pattern

```
1. navigate_page({ url: "http://localhost:8502/page" })
2. take_snapshot()   → Verify key elements exist in DOM
3. take_screenshot() → Visual confirmation, save as evidence
4. If 404 or elements missing → story INCOMPLETE
```

### Configuration
```json
{
  "mcpServers": {
    "chrome-devtools": {
      "type": "stdio",
      "command": "npx",
      "args": ["@anthropic/chrome-devtools-mcp@latest"]
    }
  }
}
```

**Note**: Requires Chrome/Chromium running with remote debugging enabled:
```bash
chrome --remote-debugging-port=9222
```

## Playwright — Browser Automation

### Purpose
Full browser automation for E2E testing. More powerful than chrome-devtools but heavier setup.

### Key Capabilities
- Navigate pages, fill forms, click buttons
- Wait for elements, assert content
- Multi-page workflows
- Screenshot and video capture
- Network interception

### When to Use vs Chrome DevTools

| Need | Use |
|------|-----|
| Quick DOM snapshot for verification | chrome-devtools |
| Screenshot for evidence | chrome-devtools |
| Full E2E test flow | playwright |
| Form submission testing | playwright |
| Multi-page navigation | playwright |
| Network request inspection | chrome-devtools |

### Configuration
```json
{
  "mcpServers": {
    "playwright": {
      "type": "stdio",
      "command": "npx",
      "args": ["@anthropic/playwright-mcp@latest"]
    }
  }
}
```

## Filesystem — Directory Operations

### Purpose
Tree views and file operations beyond Claude Code's built-in Read/Write/Glob tools.

### Key Tool
- `directory_tree` — Recursive directory listing with depth control

### When to Use
- Understanding project structure at a glance
- Verifying directory creation after scaffolding
- Checking file counts in directories

## n8n — Workflow Automation

### Purpose
Trigger external workflows from within Claude Code sessions. Useful for CI/CD integration, notifications, and custom pipelines.

### Key Tools
- `search_workflows` — Find available workflows
- `execute_workflow` — Trigger a workflow with parameters
- `get_workflow_details` — Inspect workflow configuration

### Example Use Cases
- Trigger deployment after story completion
- Send notifications to Slack/Discord on loop completion
- Run custom validation pipelines
- Sync status to external project management tools

## Atlassian — Jira/Confluence

### Purpose
Read and update Jira issues and Confluence pages directly from Claude Code.

### Key Tools
- `getJiraIssue` / `editJiraIssue` — Read/update issues
- `searchJiraIssuesUsingJql` — JQL queries
- `getConfluencePage` / `updateConfluencePage` — Read/update pages
- `createJiraIssue` — Create new issues

### Ralph Integration
- Sync story status from prd.json to Jira
- Create Jira issues for blocked stories
- Update Confluence with sprint progress

## Custom MCP Server Wiring

### Project-Level Config (`.claude/settings.json`)
Shared with team (committed to repo):
```json
{
  "mcpServers": {
    "my-server": {
      "type": "stdio",
      "command": "node",
      "args": ["./tools/my-mcp-server.js"],
      "env": {
        "API_KEY": "${MY_API_KEY}"
      }
    }
  }
}
```

### Local Overrides (`.claude/settings.local.json`)
Machine-specific (gitignored):
```json
{
  "mcpServers": {
    "chrome-devtools": {
      "type": "stdio",
      "command": "npx",
      "args": ["@anthropic/chrome-devtools-mcp@latest"]
    }
  }
}
```

### User-Level Config (`~/.claude/settings.json`)
All projects on this machine:
```json
{
  "mcpServers": {
    "context7": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@context7/mcp"]
    }
  }
}
```

## MCP in Ralph Hooks

MCP tools are available within agent-type hooks:
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "agent",
        "prompt": "Check if the written file follows project conventions using MCP tools",
        "timeout": 60
      }]
    }]
  }
}
```

Agent hooks get Read/Grep/Glob tools by default. MCP tools extend this with external capabilities.

## Best Practices

1. **context7 for every library question** — never rely on training data for API specifics
2. **chrome-devtools for UI verification** — take snapshot + screenshot as evidence
3. **Local config for heavy tools** — playwright, chrome-devtools in `.local.json` (gitignored)
4. **Shared config for team tools** — context7, filesystem in `.claude/settings.json`
5. **Environment variables for secrets** — use `${VAR}` syntax, never hardcode keys
6. **Prefer lightweight tools** — chrome-devtools snapshot over full playwright for quick checks
