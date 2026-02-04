# OpenCode Configuration Reference

Complete reference for `opencode.json` configuration.

## Schema

```json
{
  "$schema": "https://opencode.ai/config.json"
}
```

## Full Configuration Structure

```json
{
  "$schema": "https://opencode.ai/config.json",

  "model": "anthropic/claude-sonnet-4-20250514",

  "instructions": ["AGENTS.md", "CLAUDE.md"],

  "provider": {
    "anthropic": {
      "options": {}
    },
    "openai": {
      "options": {}
    },
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "http://localhost:11434/v1"
      }
    }
  },

  "mcp": {
    "server-name": {
      "type": "local",
      "command": ["npx", "-y", "package-name"],
      "args": [],
      "environment": {},
      "enabled": true
    }
  },

  "agent": {
    "agent-name": {
      "file": ".opencode/agent/agent-name.md"
    }
  },

  "permission": {
    "*": "allow",
    "bash": {
      "*": "ask",
      "pattern *": "allow"
    },
    "mcp": {
      "*": "ask"
    }
  }
}
```

## Configuration Options

### model
Default model for conversations.

```json
{
  "model": "anthropic/claude-sonnet-4-20250514"
}
```

Available formats:
- `anthropic/claude-sonnet-4-20250514`
- `openai/gpt-4`
- `ollama/llama3.1:8b`

### instructions
Array of markdown files loaded as system context.

```json
{
  "instructions": [
    "AGENTS.md",
    "CLAUDE.md",
    "docs/CONTEXT.md"
  ]
}
```

### provider
Configure LLM providers.

```json
{
  "provider": {
    "anthropic": {
      "options": {
        "apiKey": "{env:ANTHROPIC_API_KEY}"
      }
    },
    "openai": {
      "options": {
        "apiKey": "{env:OPENAI_API_KEY}"
      }
    },
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "http://localhost:11434/v1"
      }
    }
  }
}
```

### mcp
MCP server configuration. See [MCP_TEMPLATE.md](./MCP_TEMPLATE.md).

#### Local Server
```json
{
  "mcp": {
    "my-server": {
      "type": "local",
      "command": ["npx", "-y", "@package/mcp-server"],
      "args": ["--flag", "value"],
      "environment": {
        "API_KEY": "{env:MY_API_KEY}"
      },
      "enabled": true
    }
  }
}
```

#### Remote Server
```json
{
  "mcp": {
    "my-server": {
      "type": "remote",
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer {env:TOKEN}"
      },
      "enabled": true
    }
  }
}
```

### agent
Agent configuration. See [AGENT_TEMPLATE.md](./AGENT_TEMPLATE.md).

```json
{
  "agent": {
    "docker-ops": {
      "file": ".opencode/agent/docker-ops.md"
    },
    "workflow-builder": {
      "file": ".opencode/agent/workflow-builder.md"
    }
  }
}
```

### permission
Permission rules for tools and operations.

```json
{
  "permission": {
    "*": "allow",
    "bash": {
      "*": "ask",
      "docker *": "allow",
      "git *": "allow",
      "npm *": "allow",
      "python *": "allow"
    },
    "mcp": {
      "*": "ask",
      "filesystem": "allow"
    },
    "write": {
      "*": "ask",
      "*.md": "allow"
    }
  }
}
```

Permission values:
- `allow` - Always allow
- `ask` - Ask user for confirmation
- `deny` - Always deny

Pattern matching:
- `*` - Wildcard match
- `pattern *` - Match commands starting with pattern
- `*.ext` - Match file extensions

## Environment Variables

Use `{env:VAR_NAME}` syntax to reference environment variables:

```json
{
  "environment": {
    "API_KEY": "{env:SERVICE_API_KEY}"
  }
}
```

## File Locations

| File | Purpose |
|------|---------|
| `opencode.json` | Main configuration |
| `AGENTS.md` | Agent instructions |
| `.opencode/agent/*.md` | Custom agents |
| `.opencode/command/*.md` | Custom commands |
| `.opencode/skill/*/SKILL.md` | Skills |
| `.opencode/tool/*.ts` | Custom tools |
| `.opencode/plugin/*.ts` | Plugins |

## CLI Commands

```bash
# Start OpenCode
opencode

# List MCP servers
opencode mcp list

# Check configuration
opencode config

# Initialize new project
opencode init
```
