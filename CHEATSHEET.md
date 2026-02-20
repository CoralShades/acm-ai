# ACM-AI Cheatsheet

Quick reference for Ralph Loop, agent teams, and common operations.

---

## Slash Commands

| Command | Usage | Description |
|---------|-------|-------------|
| `/ralph-init` | `/ralph-init [story-file]` | Initialize Ralph loop for a story |
| `/sprint-status` | `/sprint-status` | Show sprint board from BMAD stories |
| `/story-complete` | `/story-complete` | Verify ACs + tests, commit and push |
| `/start` | `/start` | Start development services |
| `/stop` | `/stop` | Stop all Docker services |
| `/status` | `/status` | Check service health |
| `/build` | `/build [frontend\|backend]` | Build frontend or check backend |
| `/test` | `/test [path]` | Run pytest tests |
| `/logs` | `/logs [service]` | View service logs |

---

## Test Commands

| Layer | Command | Notes |
|-------|---------|-------|
| Backend (all) | `pytest tests/ -x` | Stop on first failure |
| Backend (file) | `pytest tests/test_acm_api.py` | Single file |
| Backend (coverage) | `pytest --cov=open_notebook` | With coverage |
| Python lint | `ruff check .` | Lint check |
| Python format | `ruff format .` | Auto-format |
| Python types | `mypy .` | Type check |
| Frontend lint | `cd frontend && npm run lint` | ESLint |
| Frontend build | `cd frontend && npm run build` | Production build |
| E2E | `npx playwright test` | Playwright tests |

---

## Agent Team

```
                    ┌─────────────────┐
                    │   ORCHESTRATOR   │
                    │  (never codes)   │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
    ┌───────▼──────┐  ┌─────▼──────┐  ┌──────▼──────┐
    │   BACKEND    │  │  FRONTEND  │  │     QA      │
    │  SPECIALIST  │  │ SPECIALIST │  │ SPECIALIST  │
    │              │  │            │  │             │
    │ /api/**      │  │ /frontend/ │  │ /tests/**   │
    │ /open_note/**│  │            │  │ playwright  │
    │ /migrations/ │  │            │  │             │
    │ /commands/   │  │            │  │             │
    └──────────────┘  └────────────┘  └─────────────┘
                             │
                    ┌────────▼────────┐
                    │     DOCS        │
                    │   SPECIALIST    │
                    │                 │
                    │ /docs/**        │
                    │ README.md       │
                    │ progress.md     │
                    └─────────────────┘
```

All agents: `model: claude-sonnet-4-6` | Definitions: `.claude/agents/`

---

## Ralph Loop Quick Start

```bash
# Initialize for a story
/ralph-init e8-s11-acm-register-grid-ui-polish.md

# Run the loop (max 40 iterations)
.ralph/ralph_loop.sh

# Or with custom max
.ralph/ralph_loop.sh --max 20

# Check progress
cat .ralph/@fix_plan.md    # Task checklist
cat .ralph/logs/metrics.log # Timing/metrics

# When done
/story-complete
```

---

## Service Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend | 8502 | http://localhost:8502 |
| FastAPI | 5055 | http://localhost:5055 |
| SurrealDB | 8000 | ws://localhost:8000/rpc |

---

## Environment

```bash
# Required for agent teams
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# Already set in .claude/settings.json — no manual action needed
```

---

## Top 5 Troubleshooting Fixes

### 1. Ralph loop stuck (not completing or blocking)

```bash
# Check the last iteration log
cat .ralph/logs/iteration-$(ls .ralph/logs/iteration-*.md | wc -l).md

# Check metrics for patterns
cat .ralph/logs/metrics.log | tail -20

# Common fix: the fix_plan has an AC that can't be verified
# Edit .ralph/@fix_plan.md to clarify the task, then re-run
```

### 2. Agent teams not activating

```bash
# Verify the env var is set
echo $CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS
# Should output: 1

# Check settings.json has it
cat .claude/settings.json | grep AGENT_TEAMS

# If missing, add to .claude/settings.json:
# "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" }
```

### 3. Tests fail locally but pass in web VM

```bash
# Usually a dependency version mismatch
uv sync          # Re-sync Python deps
cd frontend && npm install  # Re-sync Node deps

# Or a missing .env variable
cat .env         # Check all required vars are set
```

### 4. Frontend build fails after backend changes

```bash
# Often caused by type mismatches after API changes
# Regenerate TypeScript types from Pydantic models
cd frontend && npm run generate:types

# Then rebuild
npm run build
```

### 5. Merge conflict on progress.md

```bash
# progress.md is auto-generated — safe to take either version
git checkout --theirs progress.md
# Then regenerate
/sprint-status
```
