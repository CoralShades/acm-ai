# Claude Code Framework

A comprehensive, reusable framework for setting up Claude Code in any project. Copy this directory to quickly enable custom commands, modular rules, and MCP servers.

## Quick Start

```bash
# 1. Copy framework to your project
cp -r docs/claude-framework/ /path/to/your/project/

# 2. Run initialization script
cd /path/to/your/project
python docs/claude-framework/scripts/init-claude-code.py

# 3. Verify setup
claude mcp list
```

## What's Included

```
docs/claude-framework/
├── README.md                    # This file
├── INIT_CHECKLIST.md           # Step-by-step manual setup
├── PROJECT_DETECTION.md        # How to analyze existing projects
├── CLAUDE_TEMPLATE.md          # CLAUDE.md template with all sections
├── templates/
│   ├── commands/               # Slash command templates
│   │   ├── _template.md        # Command template
│   │   ├── start.md           # /start command
│   │   ├── stop.md            # /stop command
│   │   ├── status.md          # /status command
│   │   └── logs.md            # /logs command
│   ├── rules/                  # Modular rule templates
│   │   ├── _template.md        # Rule template
│   │   ├── docker-compose.md  # Docker rules
│   │   ├── supabase.md        # Supabase rules
│   │   └── mcp-servers.md     # MCP rules
│   └── settings/
│       ├── settings.json       # MCP server config template
│       └── settings.local.json # Local overrides template
├── scripts/
│   ├── init-claude-code.py     # Main initialization script
│   ├── detect-project.py       # Project structure analyzer
│   └── sync-framework.py       # Update framework in projects
└── tests/
    └── e2e/
        ├── test_commands.md    # Command test checklist
        └── test_mcp.md         # MCP server tests
```

## Framework Features

### 1. Custom Slash Commands
Define project-specific commands in `.claude/commands/`:
- `/start` - Start services
- `/stop` - Stop services
- `/status` - Check health
- `/logs` - View logs

### 2. Modular Rules
Path-specific rules in `.claude/rules/`:
- Apply only to matching file patterns
- Use YAML frontmatter for path filtering
- Keep CLAUDE.md focused on project context

### 3. MCP Servers
Configure in `.claude/settings.json`:
- filesystem - File operations
- memory - Persistent context
- github - GitHub integration
- Custom servers for your stack

### 4. Project Detection
The framework respects existing:
- CLAUDE.md files (merges, doesn't overwrite)
- Documentation structure (/docs)
- Architecture files (BMAD, ADR, etc.)
- Existing configurations

## Usage Patterns

### New Project Setup
```bash
# Initialize new project with framework
python scripts/init-claude-code.py --new

# This creates:
# - .claude/commands/
# - .claude/rules/
# - .claude/settings.json
# - CLAUDE.md (if not exists)
```

### Existing Project Integration
```bash
# Analyze existing project first
python scripts/detect-project.py

# Then initialize with detected patterns
python scripts/init-claude-code.py --existing

# This:
# - Detects existing CLAUDE.md
# - Finds existing documentation
# - Merges framework with existing setup
```

### Update Framework
```bash
# Sync framework updates to existing setup
python scripts/sync-framework.py --dry-run  # Preview changes
python scripts/sync-framework.py            # Apply changes
```

## Customization

### Adding Commands
1. Copy `templates/commands/_template.md` to `.claude/commands/your-command.md`
2. Edit YAML frontmatter (description, allowed-tools)
3. Add instructions

### Adding Rules
1. Copy `templates/rules/_template.md` to `.claude/rules/your-rule.md`
2. Set `paths:` pattern in frontmatter
3. Add rules content

### Adding MCP Servers
1. Edit `.claude/settings.json`
2. Add server configuration
3. Set required environment variables

## Integration with Existing Architectures

### BMAD v6 Architecture
The framework detects and integrates with BMAD:
- Respects `/docs/architecture/` structure
- Links to existing ADRs
- Preserves BMAD conventions

### Monorepo Projects
For monorepos, the framework supports:
- Root-level CLAUDE.md for shared rules
- Package-level overrides
- Workspace-aware commands

### Standard Projects
Default setup for typical projects:
- Single CLAUDE.md at root
- Commands for common tasks
- Rules for detected file types

## Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `GITHUB_TOKEN` | GitHub MCP server | For GitHub features |
| `ANON_KEY` | Supabase anonymous key | For Supabase MCP |
| `SERVICE_ROLE_KEY` | Supabase service role | For Supabase MCP |

## Troubleshooting

### Commands not showing
- Check `.claude/commands/` exists
- Verify YAML frontmatter syntax
- Run `claude` to reload

### MCP servers not connecting
- Check environment variables set
- Verify service is running
- Check `.claude/settings.json` syntax

### Rules not applying
- Check `paths:` pattern matches files
- Verify YAML frontmatter valid
- Rules load on Claude start

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-12 | Initial framework release |

## Contributing

To improve this framework:
1. Test changes in a sample project
2. Update templates as needed
3. Update this README
4. Add E2E tests for new features
