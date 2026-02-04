# OpenCode Setup Guide

Complete guide to setting up OpenCode for any project. This template can be copied to new projects.

## Prerequisites

- Node.js 18+ or Bun
- OpenCode CLI installed: `npm install -g opencode` or `bun install -g opencode`

## Quick Start

1. **Initialize OpenCode**
   ```bash
   opencode init
   ```

2. **Create directory structure**
   ```
   your-project/
   ├── .opencode/
   │   ├── agent/       # Custom agents
   │   ├── command/     # Custom commands
   │   ├── skill/       # Reusable skills
   │   ├── tool/        # Custom tools
   │   └── plugin/      # Plugins
   ├── opencode.json    # Main configuration
   └── AGENTS.md        # Agent instructions
   ```

3. **Configure opencode.json**
   ```json
   {
     "$schema": "https://opencode.ai/config.json",
     "model": "anthropic/claude-sonnet-4-20250514",
     "instructions": ["AGENTS.md"],
     "mcp": {},
     "permission": {
       "*": "allow"
     }
   }
   ```

4. **Start OpenCode**
   ```bash
   opencode
   ```

## Directory Structure

### `.opencode/agent/`
Custom AI agents with specific capabilities. Each agent is a markdown file with frontmatter.

### `.opencode/command/`
Slash commands for common tasks. Markdown files with instructions.

### `.opencode/skill/`
Reusable instruction sets. Each skill is a directory with `SKILL.md`.

### `.opencode/tool/`
TypeScript/JavaScript functions that extend AI capabilities.

### `.opencode/plugin/`
Event hooks and lifecycle extensions.

## Configuration Reference

See [CONFIG_REFERENCE.md](./CONFIG_REFERENCE.md) for full configuration options.

## Component Templates

- [AGENT_TEMPLATE.md](./AGENT_TEMPLATE.md) - Create custom agents
- [SKILL_TEMPLATE.md](./SKILL_TEMPLATE.md) - Create reusable skills
- [TOOL_TEMPLATE.md](./TOOL_TEMPLATE.md) - Create custom tools
- [MCP_TEMPLATE.md](./MCP_TEMPLATE.md) - Configure MCP servers
- [INTEGRATIONS.md](./INTEGRATIONS.md) - Integration patterns

## Common Patterns

### Multi-Provider Setup
```json
{
  "provider": {
    "anthropic": { "options": {} },
    "openai": { "options": {} },
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "options": { "baseURL": "http://localhost:11434/v1" }
    }
  }
}
```

### Permission Configuration
```json
{
  "permission": {
    "*": "allow",
    "bash": {
      "*": "ask",
      "docker *": "allow",
      "git *": "allow"
    },
    "mcp": {
      "*": "ask"
    }
  }
}
```

### Multiple Instruction Files
```json
{
  "instructions": [
    "AGENTS.md",
    "CLAUDE.md",
    "docs/CONTRIBUTING.md"
  ]
}
```
