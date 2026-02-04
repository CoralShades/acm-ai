# Integration Patterns

Patterns for integrating external services with OpenCode via MCP servers.

## GitHub Integration

### Configuration
```json
{
  "mcp": {
    "github": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-github"],
      "environment": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "{env:GITHUB_TOKEN}"
      },
      "enabled": true
    }
  }
}
```

### Required Token Scopes
- `repo` - Full repository access
- `read:org` - Read organization data
- `read:user` - Read user profile

### Available Tools
- `list_repos` - List repositories
- `get_repo` - Get repository details
- `list_issues` - List issues
- `create_issue` - Create new issue
- `list_pull_requests` - List PRs
- `create_pull_request` - Create PR
- `get_file_contents` - Read file from repo
- `search_code` - Search code across repos

---

## GitLab Integration

### Configuration
```json
{
  "mcp": {
    "gitlab": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-gitlab"],
      "environment": {
        "GITLAB_PERSONAL_ACCESS_TOKEN": "{env:GITLAB_TOKEN}",
        "GITLAB_URL": "https://gitlab.com"
      },
      "enabled": true
    }
  }
}
```

### Required Token Scopes
- `api` - Full API access
- `read_repository` - Read repository content

---

## Slack Integration

### Configuration
```json
{
  "mcp": {
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
}
```

### Setup Steps
1. Create Slack App at https://api.slack.com/apps
2. Add Bot Token Scopes:
   - `channels:history`
   - `channels:read`
   - `chat:write`
   - `users:read`
3. Install to workspace
4. Copy Bot User OAuth Token

### Available Tools
- `list_channels` - List workspace channels
- `post_message` - Send message to channel
- `get_channel_history` - Read channel messages
- `search_messages` - Search messages

---

## Notion Integration

### Configuration
```json
{
  "mcp": {
    "notion": {
      "type": "local",
      "command": ["npx", "-y", "@notionhq/notion-mcp-server"],
      "environment": {
        "NOTION_API_KEY": "{env:NOTION_API_KEY}"
      },
      "enabled": true
    }
  }
}
```

### Setup Steps
1. Create integration at https://www.notion.so/my-integrations
2. Copy Internal Integration Token
3. Share pages/databases with integration

### Available Tools
- `search` - Search pages and databases
- `get_page` - Get page content
- `create_page` - Create new page
- `update_page` - Update page properties
- `query_database` - Query database

---

## PostgreSQL Integration

### Configuration
```json
{
  "mcp": {
    "postgres": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-postgres"],
      "environment": {
        "POSTGRES_CONNECTION_STRING": "{env:DATABASE_URL}"
      },
      "enabled": true
    }
  }
}
```

### Connection String Format
```
postgresql://user:password@host:5432/database
```

### For Supabase
```
postgresql://postgres:your-password@localhost:5432/postgres
```

### Available Tools
- `query` - Execute SQL query
- `list_tables` - List database tables
- `describe_table` - Get table schema

---

## Memory (Persistent Context)

### Configuration
```json
{
  "mcp": {
    "memory": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-memory"],
      "enabled": true
    }
  }
}
```

### Available Tools
- `save_memory` - Store key-value pair
- `load_memory` - Retrieve stored value
- `list_memories` - List all stored keys

### Use Cases
- Store project context between sessions
- Save user preferences
- Cache API responses
- Track conversation state

---

## n8n Integration

### Configuration
```json
{
  "mcp": {
    "n8n": {
      "type": "local",
      "command": ["npx", "-y", "n8n-mcp"],
      "environment": {
        "MCP_MODE": "stdio",
        "LOG_LEVEL": "error",
        "DISABLE_CONSOLE_OUTPUT": "true",
        "N8N_API_URL": "http://localhost:5678",
        "N8N_API_KEY": "{env:N8N_API_KEY}",
        "WEBHOOK_SECURITY_MODE": "moderate"
      },
      "enabled": true
    }
  }
}
```

### Setup Steps
1. Start your n8n instance
2. Go to n8n Settings → API
3. Create a new API Key
4. Add to `.env`: `N8N_API_KEY=your-api-key`

### Available Capabilities
- Access to 1,084+ n8n node documentation (537 core + 547 community)
- Workflow creation and management
- Execution monitoring and history
- Credential management
- Node property schemas for all nodes

### Environment Variables
| Variable | Description |
|----------|-------------|
| `MCP_MODE` | Must be `stdio` for Claude compatibility |
| `N8N_API_URL` | URL of your n8n instance |
| `N8N_API_KEY` | API key from n8n settings |
| `WEBHOOK_SECURITY_MODE` | Set to `moderate` for local instances |

### Docker Configuration
For Docker-based n8n instances, you can also use:
```json
{
  "n8n": {
    "type": "local",
    "command": ["docker", "run", "-i", "--rm", "--init",
      "-e", "MCP_MODE=stdio",
      "-e", "LOG_LEVEL=error",
      "-e", "DISABLE_CONSOLE_OUTPUT=true",
      "-e", "N8N_API_URL=http://host.docker.internal:5678",
      "-e", "N8N_API_KEY={env:N8N_API_KEY}",
      "ghcr.io/czlonkowski/n8n-mcp:latest"
    ],
    "enabled": true
  }
}
```

### Sources
- [n8n-mcp GitHub](https://github.com/czlonkowski/n8n-mcp)
- [n8n-mcp npm](https://www.npmjs.com/package/n8n-mcp)

---

## Custom REST API Integration

For services without MCP servers, create a custom tool.

### Example: Generic REST Tool
```typescript
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Call external REST API",
  args: {
    baseUrl: tool.schema.string().describe("API base URL"),
    endpoint: tool.schema.string().describe("API endpoint"),
    method: tool.schema.enum(["GET", "POST", "PUT", "DELETE"]).default("GET"),
    body: tool.schema.string().optional(),
    headers: tool.schema.string().describe("JSON headers").optional()
  },
  async execute({ baseUrl, endpoint, method, body, headers }) {
    const url = `${baseUrl}${endpoint}`
    const options: RequestInit = {
      method,
      headers: headers ? JSON.parse(headers) : {}
    }

    if (body && method !== "GET") {
      options.body = body
      options.headers["Content-Type"] = "application/json"
    }

    const response = await fetch(url, options)
    return {
      status: response.status,
      data: await response.json()
    }
  }
})
```

---

## Shopify Integration (Custom)

### Tool Example
```typescript
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Query Shopify store data",
  args: {
    query: tool.schema.string().describe("GraphQL query"),
    shop: tool.schema.string().describe("Shop domain")
  },
  async execute({ query, shop }) {
    const response = await fetch(
      `https://${shop}/admin/api/2024-01/graphql.json`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Shopify-Access-Token": process.env.SHOPIFY_ACCESS_TOKEN
        },
        body: JSON.stringify({ query })
      }
    )
    return await response.json()
  }
})
```

---

## WordPress Integration (Custom)

### Tool Example
```typescript
import { tool } from "@opencode-ai/plugin"

export default tool({
  description: "Interact with WordPress REST API",
  args: {
    endpoint: tool.schema.string().describe("API endpoint (e.g., /wp/v2/posts)"),
    method: tool.schema.enum(["GET", "POST", "PUT", "DELETE"]).default("GET"),
    body: tool.schema.string().optional()
  },
  async execute({ endpoint, method, body }) {
    const siteUrl = process.env.WP_SITE_URL
    const auth = Buffer.from(
      `${process.env.WP_USERNAME}:${process.env.WP_APPLICATION_PASSWORD}`
    ).toString("base64")

    const response = await fetch(`${siteUrl}/wp-json${endpoint}`, {
      method,
      headers: {
        "Authorization": `Basic ${auth}`,
        "Content-Type": "application/json"
      },
      body: body || undefined
    })
    return await response.json()
  }
})
```

---

## Environment Variables Summary

| Service | Variable | Description |
|---------|----------|-------------|
| GitHub | `GITHUB_TOKEN` | Personal access token |
| GitLab | `GITLAB_TOKEN` | Personal access token |
| Slack | `SLACK_BOT_TOKEN` | Bot OAuth token |
| Slack | `SLACK_TEAM_ID` | Workspace ID |
| Notion | `NOTION_API_KEY` | Integration token |
| PostgreSQL | `DATABASE_URL` | Connection string |
| n8n | `N8N_API_KEY` | API key from n8n settings |
| Shopify | `SHOPIFY_ACCESS_TOKEN` | Admin API token |
| WordPress | `WP_APPLICATION_PASSWORD` | App password |
| WordPress | `WP_SITE_URL` | Site URL |
| WordPress | `WP_USERNAME` | Admin username |
