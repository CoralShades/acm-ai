---
description: Set up Claude Code using the framework templates - analyzes project and creates CLAUDE.md, commands, rules, and MCP config
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Task
---

# Self-Setup Claude Code

Use the framework documentation to configure Claude Code for this project.

## Framework Locations
- `docs/claude-framework/` - Claude Code templates (commands, rules, settings)
- `docs/framework/` - OpenCode templates (agents, skills, tools)

## Instructions

### Phase 1: Read Framework Documentation
1. Read `docs/claude-framework/README.md` for overview
2. Read `docs/claude-framework/PROJECT_DETECTION.md` for detection strategy
3. Read `docs/claude-framework/CLAUDE_TEMPLATE.md` for CLAUDE.md structure

### Phase 2: Analyze This Project
Detect the following:

**Documentation:**
- Check if CLAUDE.md exists (merge if yes, create if no)
- Check if AGENTS.md exists
- Check docs/ directory structure
- Look for architecture docs (BMAD, ADR patterns)

**Technology Stack:**
- `package.json` → Node.js/TypeScript
- `pyproject.toml` or `requirements.txt` → Python
- `Cargo.toml` → Rust
- `go.mod` → Go
- Check for frameworks: Next.js, React, FastAPI, Django, etc.

**Infrastructure:**
- `docker-compose*.yml` → Docker setup
- `.github/workflows/` → GitHub Actions
- `supabase/` → Supabase
- Database configurations

### Phase 3: Create/Update CLAUDE.md
1. If CLAUDE.md exists:
   - Read existing content
   - Merge framework sections (commands, rules, MCP)
   - Preserve project-specific content
2. If CLAUDE.md doesn't exist:
   - Copy from `docs/claude-framework/CLAUDE_TEMPLATE.md`
   - Fill in project-specific details based on detection

### Phase 4: Set Up Commands
1. Create `.claude/commands/` if not exists
2. Copy relevant commands from `docs/claude-framework/templates/commands/`:
   - `start.md` - If Docker or dev server detected
   - `stop.md` - If Docker detected
   - `status.md` - For health checks
   - `logs.md` - If Docker detected
3. Customize commands for this project's specific needs

### Phase 5: Set Up Rules
1. Create `.claude/rules/` if not exists
2. Copy relevant rules from `docs/claude-framework/templates/rules/`:
   - `docker-compose.md` - If Docker detected
   - `supabase.md` - If Supabase detected
   - `mcp-servers.md` - Always include
3. Add technology-specific rules based on detection

### Phase 6: Configure MCP Servers
1. Create `.claude/settings.json` if not exists
2. Start with base config from `docs/claude-framework/templates/settings/settings.json`
3. Add project-specific MCP servers:
   - `filesystem` - Always
   - `memory` - Always
   - `github` - If .git exists
   - `supabase` - If supabase/ detected
   - Others based on project needs

### Phase 7: Report Results
Summarize what was created/updated:
- Files created
- Files updated (merged)
- Commands added
- Rules added
- MCP servers configured
- Any manual steps needed (API keys, etc.)

## Detection Commands

```bash
# Check for existing Claude setup
ls -la CLAUDE.md AGENTS.md .claude/ 2>/dev/null

# Detect language/framework
ls package.json pyproject.toml Cargo.toml go.mod 2>/dev/null

# Detect Docker
ls docker-compose*.yml Dockerfile 2>/dev/null

# Detect CI/CD
ls -d .github/workflows .gitlab-ci.yml 2>/dev/null

# Detect docs structure
ls -d docs/ docs/architecture docs/adr 2>/dev/null
```

## Important Notes
- NEVER overwrite existing CLAUDE.md without merging
- NEVER overwrite existing commands without confirmation
- Preserve all project-specific context
- Add `.claude/settings.local.json` to .gitignore
