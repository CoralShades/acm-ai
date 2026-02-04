# Project Detection Guide

How to analyze existing projects before integrating the Claude Code framework.

## Detection Strategy

The framework uses a multi-layer detection approach:

1. **Documentation Layer** - Existing CLAUDE.md, AGENTS.md, docs/
2. **Architecture Layer** - BMAD, ADR, design docs
3. **Technology Layer** - Languages, frameworks, tools
4. **Infrastructure Layer** - Docker, CI/CD, deployment

## Documentation Detection

### Existing Claude Files

| File | Action |
|------|--------|
| `CLAUDE.md` exists | Merge framework sections, preserve project content |
| `AGENTS.md` exists | Keep as-is, reference from CLAUDE.md |
| `.claude/` exists | Analyze existing setup, extend don't replace |
| None exist | Create from templates |

### Documentation Structure

| Pattern | Type | Action |
|---------|------|--------|
| `docs/architecture/` | Architecture docs | Link from CLAUDE.md |
| `docs/adr/` | ADR pattern | Reference decisions |
| `docs/api/` | API docs | Create API rules |
| `docs/guides/` | User guides | Reference in context |
| `README.md` only | Minimal docs | Create full structure |

## Architecture Detection

### BMAD v6 Architecture

**Indicators:**
- `docs/architecture/` with structured folders
- `docs/adr/` for Architecture Decision Records
- `bmad.config.js` or similar config
- Specific folder structure patterns

**Integration:**
```markdown
# In CLAUDE.md
See @docs/architecture/README.md for system architecture.
See @docs/adr/ for architecture decisions.
```

### Clean Architecture

**Indicators:**
- `src/domain/`, `src/application/`, `src/infrastructure/`
- Clear layer separation
- Interface-based design

**Rules to create:**
```yaml
---
paths:
  - "src/domain/**/*"
---
# Domain layer - no external dependencies
```

### Microservices

**Indicators:**
- Multiple `docker-compose.yml` services
- `services/` or `packages/` directory
- Inter-service communication patterns

**Rules to create:**
- Per-service rules
- Shared rules for common patterns

## Technology Detection

### Language Detection

```bash
# Detection commands
ls package.json 2>/dev/null && echo "Node.js"
ls pyproject.toml requirements.txt 2>/dev/null && echo "Python"
ls Cargo.toml 2>/dev/null && echo "Rust"
ls go.mod 2>/dev/null && echo "Go"
ls pom.xml build.gradle 2>/dev/null && echo "Java"
```

### Framework Detection

| Files | Framework | Suggested Rules |
|-------|-----------|-----------------|
| `next.config.*` | Next.js | React, Next.js conventions |
| `nuxt.config.*` | Nuxt | Vue conventions |
| `angular.json` | Angular | Angular conventions |
| `vite.config.*` | Vite | Vite patterns |
| `manage.py` | Django | Django conventions |
| `main.py` + `requirements.txt` | FastAPI/Flask | Python API rules |

### Build Tool Detection

| Files | Tool | Command Templates |
|-------|------|-------------------|
| `package.json` | npm/yarn/pnpm | npm scripts |
| `Makefile` | Make | make targets |
| `justfile` | Just | just recipes |
| `taskfile.yml` | Task | task commands |

## Infrastructure Detection

### Docker Detection

```bash
# Check for Docker files
ls docker-compose*.yml Dockerfile .dockerignore 2>/dev/null
```

**If Docker found:**
- Create `/start`, `/stop`, `/logs` commands
- Create `docker-compose.md` rules
- Configure service URLs

### CI/CD Detection

| Files | Platform | Action |
|-------|----------|--------|
| `.github/workflows/` | GitHub Actions | Reference in commands |
| `.gitlab-ci.yml` | GitLab CI | Reference in commands |
| `Jenkinsfile` | Jenkins | Reference in commands |
| `.circleci/` | CircleCI | Reference in commands |

### Database Detection

| Indicators | Database | MCP Server |
|------------|----------|------------|
| `prisma/` | Prisma/SQL | `@modelcontextprotocol/server-postgres` |
| `supabase/` | Supabase | `@anthropic/supabase-mcp` |
| `mongodb.conf` | MongoDB | Custom or community |
| `redis.conf` | Redis | Custom or community |

## Detection Script Output

Run `detect-project.py` to generate:

```json
{
  "documentation": {
    "claude_md": true,
    "agents_md": false,
    "docs_structure": "bmad",
    "existing_rules": []
  },
  "architecture": {
    "type": "bmad-v6",
    "layers": ["domain", "application", "infrastructure"],
    "patterns": ["clean-architecture", "ddd"]
  },
  "technology": {
    "language": "typescript",
    "framework": "next.js",
    "build_tool": "npm",
    "test_framework": "jest"
  },
  "infrastructure": {
    "docker": true,
    "ci_cd": "github-actions",
    "database": "supabase",
    "deployment": "vercel"
  },
  "recommendations": {
    "commands": ["start", "stop", "build", "test", "deploy"],
    "rules": ["typescript.md", "nextjs.md", "supabase.md"],
    "mcp_servers": ["filesystem", "github", "supabase"]
  }
}
```

## Integration Strategies

### Strategy 1: Minimal Integration
For projects with existing, well-structured documentation:
- Only add MCP servers
- Create minimal commands
- Reference existing docs from CLAUDE.md

### Strategy 2: Standard Integration
For projects with basic documentation:
- Create full command set
- Add relevant rules
- Merge CLAUDE.md sections
- Configure MCP servers

### Strategy 3: Full Integration
For projects with no Claude Code setup:
- Create from templates
- Generate project-specific content
- Full MCP configuration
- Complete documentation structure

## Preserving Existing Setup

### What to Preserve
- All existing CLAUDE.md content
- Custom project context
- Architecture documentation
- Team conventions
- Project-specific patterns

### What to Add
- Custom commands section (if missing)
- Modular rules reference
- MCP configuration section
- Framework templates link

### What Never to Overwrite
- Existing commands without confirmation
- Custom rules
- Project-specific settings
- Team configurations

## Post-Detection Actions

After running detection:

1. **Review recommendations**
   - Check suggested commands match project needs
   - Verify rules apply to correct paths
   - Confirm MCP servers needed

2. **Customize templates**
   - Edit command templates for project specifics
   - Adjust rule path patterns
   - Configure MCP server endpoints

3. **Merge with existing**
   - If CLAUDE.md exists, merge sections
   - If rules exist, extend don't replace
   - If settings exist, add new servers

4. **Test setup**
   - Run E2E tests from `tests/e2e/`
   - Verify commands work
   - Confirm MCP servers connect
