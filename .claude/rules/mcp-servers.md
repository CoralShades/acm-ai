---
paths:
  - ".claude/settings.json"
  - ".claude/settings.local.json"
---

# MCP Server Configuration Rules

## Settings Structure
```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "@package/server-name"],
      "env": {
        "API_KEY": "${ENV_VAR}"
      }
    }
  }
}
```

## Configured Servers for ACM-AI

### Playwright (Browser Automation)
Used for UI testing and verification.

### Chrome DevTools
Used for page snapshots and interaction.

## Environment Variables
- Use `${VAR_NAME}` syntax for environment variable substitution
- Store sensitive values in environment, not in settings.json
- Use `.claude/settings.local.json` for local overrides (gitignored)

## Best Practices
- Only enable servers you actively use
- Test server connectivity after configuration
- Document required environment variables

## Local Overrides
Add to `.claude/settings.local.json` for machine-specific configuration:
- Personal API keys
- Custom tool permissions
- Machine-specific MCP servers
