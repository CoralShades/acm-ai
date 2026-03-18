# Session: Set up ACM-AI development environment in WSL2 with all skills, agents, commands, and hooks

## Overview

This prompt sets up a complete ACM-AI development environment in WSL2. The `.claude/` directory (86 skills, 27 agents, 110 commands, 7 rules, 12 hooks) is fully git-tracked on the `ACMV3` branch — cloning the repo gives you everything. This session handles the post-clone steps: installing npm packaged skills, creating `settings.local.json`, and verifying the environment.

---

## Prerequisites

Before starting, ensure:
- WSL2 is installed with Ubuntu (or similar distro)
- Docker Desktop running with WSL2 backend enabled
- Node.js 20+ installed in WSL (`node --version`)
- Python 3.11+ and `uv` installed in WSL (`uv --version`)
- Git configured in WSL
- Claude Code CLI installed in WSL (`claude --version`)

---

## Step 1: Clone and Checkout

```bash
# Clone the repo (adjust URL to your remote)
cd ~/projects  # or wherever you want the repo
git clone <your-remote-url> acm-ai
cd acm-ai
git checkout ACMV3

# Verify .claude/ directory arrived
ls .claude/
# Expected: agents/ commands/ hooks/ planning/ plans/ rules/ settings.json skills/
```

**Verify skill count:**
```bash
ls -d .claude/skills/*/ | wc -l
# Expected: 86 skill directories
```

---

## Step 2: Install npm Packaged Skills

These 9 skills have `package.json` manifests and need `npm install` for their dependencies:

```bash
# ClawSec / OpenClaw security skills (from https://clawsec.prompt.security)
npx skills add clawsec-suite -g -y          # v0.1.3 — includes clawsec-feed
npx skills add clawsec-clawhub-checker -g -y # v0.0.1
npx skills add clawsec-nanoclaw -g -y        # v0.0.1
npx skills add clawtributor -g -y            # v0.0.3
npx skills add openclaw-audit-watchdog -g -y # v0.1.1
npx skills add claw-release -g -y            # v0.0.1
npx skills add prompt-agent -g -y            # v0.0.1
npx skills add soul-guardian -g -y           # v0.0.2

# Playwright skill (npm-based)
cd .claude/skills/playwright-skill && npm install && npx playwright install chromium
cd ~/projects/acm-ai  # return to repo root
```

**Note:** The `-g` flag installs to user-level (`~/.claude/skills/`). Since these skills are also committed to the repo's `.claude/skills/`, you may skip the `npx skills add` if the repo versions are sufficient. The committed versions don't have `node_modules/` — if a skill needs runtime deps, run `npm install` inside its directory.

---

## Step 3: Create settings.local.json (Machine-Specific)

This file is gitignored. Create it with your WSL-specific MCP servers:

```bash
cat > .claude/settings.local.json << 'SETTINGS_EOF'
{
  "permissions": {
    "allow": [
      "mcp__chrome-devtools__*",
      "mcp__filesystem__*"
    ]
  },
  "mcpServers": {
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/chrome-devtools-mcp@latest"],
      "env": {}
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-filesystem"],
      "env": {}
    }
  }
}
SETTINGS_EOF
```

**Optional MCP servers** — add these if you use them:
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-playwright"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/mcp-context7"]
    }
  }
}
```

---

## Step 4: Set Up Python Environment

```bash
cd ~/projects/acm-ai

# Create virtual environment and install all dependencies
uv sync

# Verify
uv run python -c "import open_notebook; print('Backend OK')"
uv run ruff check . --statistics
```

---

## Step 5: Set Up Frontend

```bash
cd frontend
npm install
npm run build  # verify it compiles
cd ..
```

---

## Step 6: Create .env File

```bash
cat > .env << 'ENV_EOF'
# Database
SURREAL_URL=ws://localhost:8000/rpc
SURREAL_USER=root
SURREAL_PASSWORD=root
SURREAL_NAMESPACE=open_notebook
SURREAL_DATABASE=development

# AI Providers (fill in your keys)
OPENAI_API_KEY=sk-...

# ACM Pipeline Keys (separate from Claude Code's keys)
# ACM_ANTHROPIC_API_KEY=sk-ant-...
# ACM_OPENROUTER_API_KEY=sk-or-...

# Ollama (if using local models)
OLLAMA_API_BASE=http://localhost:11434
ACM_ITEM_EXTRACTION_MODE=per_row
ACM_ROW_EXTRACTION_NUM_CTX=2048
ACM_EXTRACTION_MODEL=llama3.1:8b

# Feature flags
DOCLING_DIRECT_TABLE_EXTRACTION=true
MINERU_ENABLED=false

# Observability (optional)
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=ls-...
# LANGFUSE_PUBLIC_KEY=pk-...
# LANGFUSE_SECRET_KEY=sk-...
# LANGFUSE_HOST=http://localhost:3000
ENV_EOF
```

---

## Step 7: Start Services

```bash
# Start SurrealDB
docker compose up -d surrealdb

# Wait for health check
sleep 5
docker compose ps  # should show 'healthy'

# Start API (in tmux pane 1)
uv run python run_api.py

# Start Worker (in tmux pane 2)
uv run python run_worker.py --import-modules commands

# Start Frontend (in tmux pane 3)
cd frontend && npm run dev
```

---

## Step 8: Verify Everything

### 8a. Service Health
```bash
curl http://localhost:5055/health        # API
curl http://localhost:8503               # Frontend (or whatever port)
docker exec acm-ai-db /surreal isready   # SurrealDB
```

### 8b. Skills Verification
```bash
# Count skills
ls -d .claude/skills/*/ | wc -l   # Expected: 86

# Count agents
ls .claude/agents/*.md | wc -l    # Expected: 27

# Count commands
find .claude/commands -name "*.md" | wc -l  # Expected: ~110

# Count rules
ls .claude/rules/*.md | wc -l     # Expected: 7

# Count hooks
ls .claude/hooks/*.sh .claude/hooks/*.md 2>/dev/null | wc -l  # Expected: 12
```

### 8c. Run Tests
```bash
uv run pytest tests/ -x --tb=short
cd frontend && npm run lint && npm run build
```

---

## Step 9: Tmux Session Layout (for prompt pack execution)

```bash
# Create a tmux session with 4 panes
tmux new-session -d -s acm -c ~/projects/acm-ai

# Pane 0: API server
tmux send-keys -t acm:0 'uv run python run_api.py' Enter

# Pane 1: Worker
tmux split-window -h -t acm:0 -c ~/projects/acm-ai
tmux send-keys -t acm:0.1 'uv run python run_worker.py --import-modules commands' Enter

# Pane 2: Frontend
tmux split-window -v -t acm:0.0 -c ~/projects/acm-ai/frontend
tmux send-keys -t acm:0.2 'npm run dev' Enter

# Pane 3: Claude Code (working pane)
tmux split-window -v -t acm:0.1 -c ~/projects/acm-ai
tmux send-keys -t acm:0.3 'claude' Enter

# Attach
tmux attach -t acm
```

---

## Complete Skill Inventory (86 skills on ACMV3 branch)

All of these are git-committed and arrive with `git clone + checkout ACMV3`:

### ACM Project-Specific (5)
`acm-observability`, `dogfood`, `e2e-test`, `flash`, `runpodctl`, `sse-streaming`

### AI/LLM Framework (12)
`claude-api`, `copilotkit`, `deep-agents-core`, `deep-agents-memory`, `deep-agents-orchestration`, `framework-selection`, `langchain-dependencies`, `langchain-fundamentals`, `langchain-middleware`, `langchain-rag`, `langgraph-fundamentals`, `langgraph-human-in-the-loop`, `langgraph-persistence`

### Development Workflow (18)
`brainstorming`, `code-review`, `commit`, `create-pr`, `dispatching-parallel-agents`, `executing-plans`, `find-bugs`, `finishing-a-development-branch`, `planning-with-files`, `prompt-generator`, `prompt-router`, `receiving-code-review`, `request-classifier`, `requesting-code-review`, `skill-creator`, `skill-discovery`, `subagent-driven-development`, `using-superpowers`

### Frontend/UI (16)
`a2a-protocol`, `agent-browser`, `baseline-ui`, `design-system-creation`, `electron`, `fixing-accessibility`, `fixing-metadata`, `fixing-motion-performance`, `frontend-design`, `next-best-practices`, `react-best-practices`, `taste-skill`, `uncodixfy`, `web-artifacts-builder`, `web-design-guidelines`, `webapp-testing`

### Backend/Python (5)
`fastapi-router-py`, `modern-python`, `multi-agent-patterns`, `pydantic-models-py`, `mcp-builder`

### Security (11)
`claw-release`, `clawsec-clawhub-checker`, `clawsec-feed`, `clawsec-nanoclaw`, `clawsec-suite`, `clawtributor`, `codeql`, `differential-review`, `insecure-defaults`, `openclaw-audit-watchdog`, `prompt-agent`, `sarif-parsing`, `security-best-practices`, `semgrep`, `soul-guardian`

### Testing (3)
`systematic-debugging`, `test-driven-development`, `verification-before-completion`

### Documentation/Office (5)
`data-structure-protocol`, `docx`, `pdf`, `pptx`, `xlsx`

### Planning (4)
`context-compression`, `context-optimization`, `using-git-worktrees`, `writing-plans`, `writing-skills`

### Prompt Engineering (1)
`prompt-engineering`

### Playwright (1)
`playwright-skill` (npm package — needs `npm install`)

---

## Agent Inventory (27 agents on ACMV3 branch)

### ACM Domain (12)
`acm-e2e-tester`, `acm-extraction-core`, `acm-extraction-post`, `acm-extraction-pre`, `acm-graph-inspector`, `acm-observability-debugger`, `acm-rag-strategist`, `acm-research-lead`, `acm-schema-expert`, `acm-sprint-lead`, `acm-trace-analyst`, `acm-ui-tester`

### E36 Verification Team (6)
`e36-lead`, `e36-browser-tester`, `e36-log-sentinel`, `e36-devils-advocate`, `e36-bmad-scribe`, `e36-ux-auditor`

### Ralph Loop (4)
`ralph-architect`, `ralph-qa`, `ralph-reviewer`, `ralph-sm`

### General Specialists (5)
`orchestrator`, `backend-specialist`, `frontend-specialist`, `qa-specialist`, `docs-specialist`

---

## WSL-Specific Notes

- **NEVER use `/d/...` or `D:\...` paths** — use the cloned WSL-native path (e.g., `~/projects/acm-ai`)
- **`API_RELOAD=false`** is required on WSL2 — Uvicorn's StatReload blocks the event loop on slow /mnt/* filesystem
- If you mounted from Windows (`/mnt/d/...`), expect 9P overhead. Clone natively to `~/` for best performance
- SurrealDB Docker volume: `acm-ai-surreal-data` (named volume, not bind mount)
- Worker: use `run_worker.py` not `surreal-commands-worker` directly (Unicode fix)

---

## Verification Checklist

- [ ] `git checkout ACMV3` — branch checked out
- [ ] `ls -d .claude/skills/*/ | wc -l` — returns 86
- [ ] `ls .claude/agents/*.md | wc -l` — returns 27
- [ ] `uv sync` — Python deps installed
- [ ] `cd frontend && npm install && npm run build` — frontend builds
- [ ] `.env` created with at least DB credentials
- [ ] `docker compose up -d surrealdb` — DB running
- [ ] `curl http://localhost:5055/health` — API responds
- [ ] `curl http://localhost:8503` — Frontend responds
- [ ] `uv run pytest tests/ -x` — tests pass
- [ ] Tmux session running with 4 panes (API, Worker, Frontend, Claude Code)
- [ ] Claude Code session starts and shows skills in `/help`
