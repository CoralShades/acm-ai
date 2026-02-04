# Agent Creation Template

Custom agents are specialized AI assistants with specific capabilities and instructions.

## File Structure

Agents are defined in `.opencode/agent/<agent-name>.md`

## Basic Template

```markdown
---
name: my-agent
description: Brief description of what this agent does
model: anthropic/claude-sonnet-4-20250514
tools:
  - tool-name-1
  - tool-name-2
---

# My Agent

## Role
Define the agent's primary role and expertise.

## Capabilities
- Capability 1
- Capability 2
- Capability 3

## Instructions
Detailed instructions for how the agent should behave.

## Workflow
1. Step 1
2. Step 2
3. Step 3

## Constraints
- What the agent should NOT do
- Limitations to be aware of
```

## Frontmatter Options

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Agent identifier (used with @agent-name) |
| `description` | string | Brief description for agent selection |
| `model` | string | LLM model to use (optional, inherits default) |
| `tools` | array | List of tools available to this agent |
| `skills` | array | List of skills to load |
| `mode` | string | `subagent` (default) or `orchestrator` |

## Example: Docker Operations Agent

```markdown
---
name: docker-ops
description: Docker and container operations specialist
tools:
  - service-status
  - start-stack
  - stop-stack
---

# Docker Operations Agent

## Role
Specialist in Docker Compose operations for the local AI stack.

## Capabilities
- Start/stop Docker services
- Check container health
- View container logs
- Manage Docker volumes
- Troubleshoot container issues

## Available Commands
- `docker compose -p localai ps` - List containers
- `docker compose -p localai logs -f <service>` - View logs
- `docker compose -p localai up -d` - Start services
- `docker compose -p localai down` - Stop services

## Workflow
1. Check current stack status
2. Identify requested operation
3. Execute appropriate docker command
4. Verify result and report status
```

## Example: Workflow Builder Agent

```markdown
---
name: workflow-builder
description: n8n workflow creation and management
skills:
  - n8n-workflow
---

# Workflow Builder Agent

## Role
Expert in creating and modifying n8n automation workflows.

## Capabilities
- Design workflow logic
- Configure n8n nodes
- Set up webhooks and triggers
- Integrate with external services
- Debug workflow issues

## Workflow Patterns
- HTTP triggers with JSON parsing
- Scheduled executions
- AI agent nodes with Ollama
- Database operations with Supabase
- Vector store operations with Qdrant
```

## Using Agents

### Mention in Chat
```
@docker-ops check the status of all containers
```

### Programmatic Call
```typescript
// In a tool or plugin
const result = await context.invokeAgent("docker-ops", {
  prompt: "Check container status"
})
```

### In opencode.json
```json
{
  "agent": {
    "docker-ops": {
      "file": ".opencode/agent/docker-ops.md"
    }
  }
}
```

## Best Practices

1. **Single Responsibility** - Each agent should have a focused purpose
2. **Clear Instructions** - Be explicit about what the agent should do
3. **Tool Access** - Only grant access to necessary tools
4. **Skill Integration** - Use skills for reusable knowledge
5. **Error Handling** - Include instructions for handling failures
