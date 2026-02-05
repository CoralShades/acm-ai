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

## Common MCP Servers

### Filesystem
```json
"filesystem": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
}
```

### Memory
```json
"memory": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-memory"]
}
```

### GitHub
```json
"github": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
  }
}
```

## Environment Variables
- Use `${VAR_NAME}` syntax for environment variable substitution
- Store sensitive values in environment, not in settings.json
- Use `.claude/settings.local.json` for local overrides (add to .gitignore)

## Best Practices
- Only enable servers you actively use
- Test server connectivity after configuration
- Document required environment variables in README
