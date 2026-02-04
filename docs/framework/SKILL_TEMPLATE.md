# Skill Creation Template

Skills are reusable instruction sets that can be loaded on-demand by agents or commands.

## File Structure

Skills are defined in `.opencode/skill/<skill-name>/SKILL.md`

```
.opencode/skill/
└── my-skill/
    ├── SKILL.md          # Main skill definition
    ├── examples/         # Optional example files
    └── templates/        # Optional template files
```

## Basic Template

```markdown
---
name: my-skill
description: Brief description of what this skill provides
---

# My Skill

## Overview
What this skill is about and when to use it.

## Key Concepts
Important concepts and terminology.

## Patterns
Common patterns and best practices.

## Examples
Code examples and usage patterns.

## Reference
Quick reference information.
```

## Frontmatter Options

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Skill identifier |
| `description` | string | Brief description for skill discovery |
| `tags` | array | Optional tags for categorization |

## Example: Docker Compose Skill

```markdown
---
name: docker-compose
description: Docker Compose patterns for the local AI stack
---

# Docker Compose Skill

## Overview
Patterns and best practices for Docker Compose with the local AI stack.

## Multi-Profile Support
This stack uses Docker Compose profiles for GPU configuration:
- `gpu-nvidia` - NVIDIA GPU acceleration
- `gpu-amd` - AMD GPU acceleration (Linux)
- `cpu` - CPU-only mode
- `none` - External Ollama

## Common Commands
```bash
# Start with profile
docker compose -p localai --profile gpu-nvidia up -d

# Stop all
docker compose -p localai down

# View logs
docker compose -p localai logs -f <service>

# Rebuild single service
docker compose -p localai up -d --build <service>
```

## Volume Management
```bash
# List volumes
docker volume ls | grep localai

# Backup volume
docker run --rm -v localai_data:/data -v $(pwd):/backup alpine tar czf /backup/data.tar.gz /data

# Prune unused
docker volume prune
```
```

## Example: n8n Workflow Skill

```markdown
---
name: n8n-workflow
description: n8n workflow creation and patterns
---

# n8n Workflow Skill

## Overview
Best practices for creating n8n workflows in the local AI stack.

## Workflow Structure
1. **Trigger** - How the workflow starts
2. **Processing** - Data transformation and logic
3. **AI Integration** - LLM calls via Ollama
4. **Output** - Response or side effects

## Ollama Integration
```json
{
  "node": "AI Agent",
  "parameters": {
    "model": "qwen2.5:7b-instruct-q4_K_M",
    "baseUrl": "http://ollama:11434"
  }
}
```

## Webhook Patterns
```json
{
  "node": "Webhook",
  "parameters": {
    "path": "my-endpoint",
    "httpMethod": "POST",
    "responseMode": "responseNode"
  }
}
```
```

## Using Skills

### In Agent Definition
```markdown
---
name: my-agent
skills:
  - docker-compose
  - n8n-workflow
---
```

### Via skill Tool
```
Use the docker-compose skill to help me configure the stack
```

### Programmatic Loading
```typescript
const skill = await context.loadSkill("docker-compose")
```

## Best Practices

1. **Focused Content** - Each skill should cover one topic well
2. **Practical Examples** - Include copy-paste ready examples
3. **Quick Reference** - Add cheat sheets for common operations
4. **Keep Updated** - Update skills as tools and APIs change
5. **Link Related Skills** - Reference other relevant skills
