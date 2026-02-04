# MCP Server Configuration Template

Model Context Protocol (MCP) servers extend AI capabilities with external tools.

## Server Types

### Local Server (Subprocess)
Runs as a child process managed by OpenCode.

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

### Remote Server (HTTP/SSE)
Connects to external MCP endpoint.

```json
{
  "mcp": {
    "my-server": {
      "type": "remote",
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer {env:API_TOKEN}"
      },
      "enabled": true
    }
  }
}
```

## Common MCP Servers

### Filesystem
```json
{
  "filesystem": {
    "type": "local",
    "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "."],
    "enabled": true
  }
}
```

### PostgreSQL
```json
{
  "postgres": {
    "type": "local",
    "command": ["npx", "-y", "@modelcontextprotocol/server-postgres"],
    "environment": {
      "POSTGRES_CONNECTION_STRING": "{env:DATABASE_URL}"
    },
    "enabled": true
  }
}
```

### GitHub
```json
{
  "github": {
    "type": "local",
    "command": ["npx", "-y", "@modelcontextprotocol/server-github"],
    "environment": {
      "GITHUB_PERSONAL_ACCESS_TOKEN": "{env:GITHUB_TOKEN}"
    },
    "enabled": true
  }
}
```

### Slack
```json
{
  "slack": {
    "type": "local",
    "command": ["npx", "-y", "@modelcontextprotocol/server-slack"],
    "environment": {
      "SLACK_BOT_TOKEN": "{env:SLACK_BOT_TOKEN}",
      "SLACK_TEAM_ID": "{env:SLACK_TEAM_ID}"
    },
    "enabled": true
  }
}
```

### Notion
```json
{
  "notion": {
    "type": "local",
    "command": ["npx", "-y", "@notionhq/notion-mcp-server"],
    "environment": {
      "NOTION_API_KEY": "{env:NOTION_API_KEY}"
    },
    "enabled": true
  }
}
```

### Memory (Persistent Context)
```json
{
  "memory": {
    "type": "local",
    "command": ["npx", "-y", "@modelcontextprotocol/server-memory"],
    "enabled": true
  }
}
```

### n8n MCP (Self-Hosted)
Uses supergateway for streamable HTTP transport.

```json
{
  "n8n-mcp": {
    "command": "npx",
    "args": [
      "-y",
      "supergateway",
      "--streamableHttp",
      "http://localhost:5678/mcp-server/http",
      "--header",
      "authorization:Bearer YOUR_MCP_TOKEN"
    ]
  }
}
```

**Getting the MCP token:**
1. Open n8n at http://localhost:5678
2. Go to Settings → MCP Server
3. Enable MCP Server and copy the token

**Available tools:**
- `search_workflows` - Search workflows with filters
- `execute_workflow` - Execute a workflow by ID
- `get_workflow_details` - Get detailed workflow information

### Supabase MCP (Self-Hosted with Kong)
For self-hosted Supabase running behind Kong proxy.

**Step 1: Enable MCP in Kong**
Edit `supabase/docker/volumes/api/kong.yml`:
```yaml
## MCP endpoint - local access
- name: mcp
  url: http://studio:3000/api/mcp
  routes:
    - name: mcp
      strip_path: true
      paths:
        - /mcp
  plugins:
    # Comment out request-termination
    # - name: request-termination
    #   config:
    #     status_code: 403
    # Enable local access
    - name: cors
    - name: ip-restriction
      config:
        allow:
          - 127.0.0.1
          - ::1
          - 172.0.0.0/8
          - 192.168.0.0/16
        deny: []
```

**Step 2: Restart Kong**
```bash
docker compose -p localai restart kong
```

**Step 3: Configure MCP client**
```json
{
  "supabase-self-hosted": {
    "command": "npx",
    "args": [
      "-y",
      "supergateway",
      "--streamableHttp",
      "http://localhost:8000/mcp"
    ]
  }
}
```

**Available tools:**
- `execute_sql` - Execute raw SQL queries
- `list_tables` - List database tables
- `list_extensions` - List installed extensions
- `list_migrations` - List applied migrations
- `apply_migration` - Apply DDL migrations
- `search_docs` - Search Supabase documentation
- `get_logs` - Get service logs
- `get_advisors` - Get security/performance advisors
- `get_project_url` - Get API URL
- `get_publishable_keys` - Get API keys
- `generate_typescript_types` - Generate TypeScript types

## Environment Variables

Use `{env:VAR_NAME}` syntax to reference environment variables:

```json
{
  "environment": {
    "API_KEY": "{env:SERVICE_API_KEY}",
    "BASE_URL": "{env:SERVICE_URL}"
  }
}
```

Variables are resolved at runtime from:
1. System environment
2. `.env` file in project root
3. `~/.opencode/.env` for global secrets

## Debugging

```bash
# List configured servers
opencode mcp list

# Check server status
opencode mcp status <server-name>

# Test connection
opencode mcp test <server-name>
```

## Creating Custom MCP Servers

For custom integrations, create a tool instead (see TOOL_TEMPLATE.md) or build a full MCP server:

```typescript
// Basic MCP server structure
import { Server } from "@modelcontextprotocol/sdk/server/index.js"
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js"

const server = new Server({
  name: "my-server",
  version: "1.0.0"
}, {
  capabilities: {
    tools: {}
  }
})

// Define tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [{
    name: "my_tool",
    description: "My custom tool",
    inputSchema: { type: "object", properties: {} }
  }]
}))

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  // Implementation
})

// Start server
const transport = new StdioServerTransport()
await server.connect(transport)
```
