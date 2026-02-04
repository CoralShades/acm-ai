# Claude Code Initialization Checklist

Step-by-step guide for setting up Claude Code in any project.

## Pre-Flight Checks

- [ ] Claude Code CLI installed (`claude --version`)
- [ ] Project directory exists
- [ ] Git repository initialized (recommended)
- [ ] Node.js installed (for MCP servers via npx)

## Phase 1: Analyze Existing Project

### 1.1 Check for Existing Documentation
```bash
# Check for existing CLAUDE.md
ls -la CLAUDE.md AGENTS.md 2>/dev/null

# Check for docs directory
ls -la docs/ 2>/dev/null

# Check for architecture docs
ls -la docs/architecture/ docs/adr/ 2>/dev/null
```

**Record findings:**
- [ ] CLAUDE.md exists: ___
- [ ] AGENTS.md exists: ___
- [ ] docs/ structure: ___
- [ ] Architecture type: ___ (BMAD, ADR, custom, none)

### 1.2 Identify Project Type
```bash
# Check for common project files
ls package.json pyproject.toml Cargo.toml go.mod 2>/dev/null

# Check for Docker
ls docker-compose*.yml Dockerfile 2>/dev/null

# Check for specific frameworks
ls next.config.* vite.config.* 2>/dev/null
```

**Record project type:**
- [ ] Language: ___ (Node, Python, Rust, Go, etc.)
- [ ] Framework: ___ (Next.js, FastAPI, etc.)
- [ ] Has Docker: ___
- [ ] Has CI/CD: ___

## Phase 2: Create Directory Structure

### 2.1 Create .claude directories
```bash
mkdir -p .claude/commands
mkdir -p .claude/rules
```

### 2.2 Verify structure
```bash
tree .claude/ 2>/dev/null || find .claude/ -type f
```

- [ ] `.claude/` directory created
- [ ] `.claude/commands/` exists
- [ ] `.claude/rules/` exists

## Phase 3: Create Settings File

### 3.1 Create settings.json
```bash
cat > .claude/settings.json << 'EOF'
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
EOF
```

### 3.2 Add project-specific MCP servers

**For GitHub projects:**
```json
"github": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
  }
}
```

**For Supabase projects:**
```json
"supabase": {
  "command": "npx",
  "args": ["-y", "@anthropic/supabase-mcp"],
  "env": {
    "SUPABASE_URL": "${SUPABASE_URL}",
    "SUPABASE_SERVICE_ROLE_KEY": "${SERVICE_ROLE_KEY}"
  }
}
```

- [ ] settings.json created
- [ ] Relevant MCP servers added
- [ ] Environment variables documented

## Phase 4: Create Custom Commands

### 4.1 Copy command templates
```bash
# Copy from framework templates
cp docs/claude-framework/templates/commands/*.md .claude/commands/
```

### 4.2 Customize commands for your project

Edit each command file:
- [ ] `/start` - Customize for your start command
- [ ] `/stop` - Customize for your stop command
- [ ] `/status` - Customize health checks
- [ ] `/logs` - Customize log viewing

### 4.3 Create project-specific commands

Example: `/build` command
```markdown
---
description: Build the project
allowed-tools: Bash
---

# Build Project

Run the build process for this project.

## Instructions
1. Run the build command:
   \`\`\`bash
   npm run build
   \`\`\`
2. Report build status
```

- [ ] Commands customized for project
- [ ] Project-specific commands added

## Phase 5: Create Modular Rules

### 5.1 Copy rule templates
```bash
# Copy from framework templates
cp docs/claude-framework/templates/rules/*.md .claude/rules/
```

### 5.2 Customize rules for your project

Edit path patterns in YAML frontmatter:
```yaml
---
paths:
  - "src/**/*.ts"
  - "lib/**/*.ts"
---
```

### 5.3 Create project-specific rules

Example: API rules
```markdown
---
paths:
  - "src/api/**/*.ts"
  - "src/routes/**/*.ts"
---

# API Development Rules

- All endpoints must have input validation
- Use standard error response format
- Document with OpenAPI comments
```

- [ ] Rules customized for project
- [ ] Path patterns match project structure

## Phase 6: Create or Update CLAUDE.md

### 6.1 If CLAUDE.md doesn't exist

Create from template:
```bash
cp docs/claude-framework/CLAUDE_TEMPLATE.md CLAUDE.md
```

### 6.2 If CLAUDE.md exists

Merge framework sections:
1. Keep existing project context
2. Add "Custom Commands" section
3. Add "Modular Rules" section
4. Add "MCP Configuration" section

### 6.3 Required sections

- [ ] Project Overview
- [ ] Key Commands
- [ ] Architecture (if applicable)
- [ ] Custom Commands reference
- [ ] Modular Rules reference
- [ ] MCP Configuration

## Phase 7: Verification

### 7.1 Verify Claude Code recognizes setup
```bash
# List loaded memory
claude /memory

# List MCP servers
claude mcp list
```

### 7.2 Test custom commands
```bash
# Test each command
claude "/start --help"
claude "/status"
```

### 7.3 Test rules apply correctly
```bash
# Open a file that should trigger rules
# Verify rules shown in context
```

- [ ] `/memory` shows CLAUDE.md loaded
- [ ] MCP servers listed correctly
- [ ] Custom commands work
- [ ] Rules apply to matching files

## Phase 8: Git Configuration

### 8.1 Update .gitignore
```bash
# Add to .gitignore
echo ".claude/settings.local.json" >> .gitignore
```

### 8.2 Commit Claude Code setup
```bash
git add .claude/ CLAUDE.md
git commit -m "feat: add Claude Code configuration"
```

- [ ] settings.local.json in .gitignore
- [ ] Configuration committed

## Troubleshooting

### Commands not appearing
1. Check file names match command names
2. Verify YAML frontmatter syntax
3. Restart Claude Code

### MCP servers not connecting
1. Check environment variables
2. Verify npx can run packages
3. Check network connectivity

### Rules not applying
1. Verify path patterns use correct glob syntax
2. Check YAML frontmatter is valid
3. Rules only apply to matching files

## Completion Checklist

- [ ] Phase 1: Project analyzed
- [ ] Phase 2: Directories created
- [ ] Phase 3: Settings configured
- [ ] Phase 4: Commands created
- [ ] Phase 5: Rules created
- [ ] Phase 6: CLAUDE.md updated
- [ ] Phase 7: Setup verified
- [ ] Phase 8: Git configured

**Setup complete!** Claude Code is now configured for your project.
