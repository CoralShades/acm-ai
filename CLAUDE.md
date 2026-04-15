# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Critical**: Always use AskUserQuestion Tool when you want to clarify, interview or ask questions from the user.

## User Documentation Location: C:\Users\User\Documents\Obsidian Vault\ACM

## CRITICAL PATH RULE (WSL/Windows)

- Never `cd` to `/d/...` or `D:\...` in Bash commands.
- Always use the repo root from `$CLAUDE_PROJECT_DIR`.
- If `$CLAUDE_PROJECT_DIR` is not set, assume WSL mount: `/mnt/d/ailocal/acm-ai`.

Examples:
- `cd "$CLAUDE_PROJECT_DIR"` — CORRECT
- `cd /d/ailocal/acm-ai` — WRONG
- `cd D:\ailocal\acm-ai` — WRONG

## Project Overview

ACM-AI is an intelligent Asbestos Containing Material (ACM) compliance management system powered by AI. It transforms ARA (Asbestos Register Assessment) documents into structured, queryable data. Monorepo:
- **Backend**: Python 3.11+ with FastAPI, LangChain/LangGraph, SurrealDB
- **Frontend**: Next.js 15 with React 19, Radix UI, Tailwind CSS 4, Zustand, React Query

## Primary User Routes (CRITICAL)

The user's primary workflow is:
1. `/jobs` — Job list (main dashboard after login)
2. `/jobs/{source_id}` — Job detail page (tabs: Overview, Buildings, ACM Records, Content, Raw Tables, Log + Chat sidebar)

**ALL frontend features MUST be built on `/jobs/[id]` first.** This is the canonical page users interact with.

### Route Hierarchy

| Route | Role | Priority |
|-------|------|----------|
| `/jobs` | Primary landing — job cards with status | **P0** |
| `/jobs/[id]` (`/jobs/source:ID`) | Primary detail view — all tabs, SSE streaming, bulk ops, chat | **P0** |
| `/jobs/[id]/extract` | Extraction monitoring (navigated to during extraction) | P1 |
| `/source/[id]` | Secondary ACM Register view — linked from jobs page, NOT primary | P2 |
| `/ai-editor` | AI-Editor list (formerly Notebooks) — auto-created per upload | P2 |
| `/ai-editor/[id]` | AI-Editor detail — sources, notes, chat columns | P2 |

### Rules for Frontend Changes

- When asked to add a feature to "the source page" or "the document view", implement it on `/jobs/[id]` at `frontend/src/app/(dashboard)/jobs/[id]/page.tsx`
- `/source/[id]` is a lightweight secondary view — do NOT add new features there unless explicitly asked
- SSE streaming, bulk operations, validation, search — all belong on `/jobs/[id]`

## Essential Commands

```bash
# Start all services (Windows — ensure Docker Desktop running)
start-all.bat

# Manual start
docker compose up -d surrealdb       # Database on port 8000
uv run run_api.py                    # API on port 5055
uv run run_worker.py --import-modules commands  # Background worker
cd frontend && npm run dev           # Frontend on port 8502

# Backend
uv sync                              # Install dependencies
uv run pytest                        # Run tests
uv run ruff check . --fix && uv run ruff format .  # Lint + format

# Frontend
cd frontend && npm install && npm run dev   # Dev (port 8502)
cd frontend && npm run build                # Production build

# LangGraph dev server (local graph debugging)
uv run langgraph dev --no-browser    # API :2024, Swagger :2024/docs
```

**Gotchas:** Always `uv run langgraph dev` (not bare `langgraph dev`). Use `run_worker.py` on Windows (avoids Unicode errors).

## Architecture

```
Browser (8502) → Next.js Frontend → /api/* proxy → FastAPI Backend (5055) → SurrealDB (8000)
```

- **Backend**: Repository pattern, DDD, Command pattern for async jobs (`commands/`)
- **Frontend**: React Query (server state), Zustand (client state), React Hook Form + Zod
- **AI**: LangGraph workflows in `open_notebook/graphs/` via Esperanto multi-provider abstraction
- **Extraction**: MinerU + Docling providers → consensus engine → SF-aligned output
- **Naming**: "AI-Editor" is the user-facing name; internal code uses `notebook`/`notebookId`

Use `Glob` and `Grep` to explore directory structure — do not rely on memorized file trees.

## Database Gotchas

SurrealDB with tables: `notebook`, `source`, `note`, `model`, `transformation`, `episode_profile`, `speaker_profile`

**Non-obvious patterns (will bite you silently):**
- **`type::thing()` for record refs**: When a column is `record<table>` and you have a string ID, use `type::thing('source:xxx')` in WHERE. Plain string comparison silently returns zero results.
- **RecordID in base.py setattr**: SurrealDB client returns `RecordID` objects. `ObjectModel` setattr must convert to `str()` when the target Pydantic field is `str`.
- **LLM string-to-int coercion**: LLMs return numeric fields as strings. Use Pydantic `BeforeValidator` to coerce `str` → `int`.

## Environment Variables

Required in `.env`:
```bash
SURREAL_URL=ws://localhost:8000/rpc
SURREAL_USER=root
SURREAL_PASSWORD=root
SURREAL_NAMESPACE=open_notebook
SURREAL_DATABASE=development
OPENAI_API_KEY=sk-...               # At least one AI provider
ACM_ANTHROPIC_API_KEY=sk-ant-...    # ACM extraction only (not Claude Code's key)
ACM_OPENROUTER_API_KEY=sk-or-...    # ACM OpenRouter fallback

# Per-row extraction (v3.5)
ACM_ITEM_EXTRACTION_MODE=per_row    # per_row (default) or bulk
ACM_EXTRACTION_MODEL=llama3.1:8b    # Ollama model for extraction
ACM_EXTRACT_TIMEOUT=3600            # Max seconds for extraction job
```

## Code Style

- **Python**: Ruff, 88 char lines, type hints required, Google-style docstrings
- **Commits**: Conventional commits (feat:, fix:, docs:, refactor:, test:)

## Python Environment Rules

- **Always `uv run ...`** for all project work (API, tests, lint, workers)
- MinerU 2.x installs in main `.venv/` — no separate venv needed
- **Never** add `mineru[all]` to `pyproject.toml` — causes `vllm`/`torchvision` conflict. Use `mineru>=2.7.0`
- **Never** install `magic-pdf` or `paddlepaddle` into the main venv

## Sub-Agent Model Selection

- **Default**: `model: "sonnet"` for most tasks
- **Complex/undocumented areas**: `model: "opus"` for single-agent Task calls only
- **Agent teams (TeamCreate)**: Only `"sonnet"` or `"haiku"` — never opus for team members

## Story Verification Protocol

**CRITICAL:** Before marking ANY story as complete, you MUST perform these steps.

### 1. Build Verification (Required for ALL stories)
```bash
cd frontend && npm run build    # Frontend — catches missing files/imports
uv run ruff check .             # Backend lint
uv run pytest                   # Backend tests
```

### 2. File Existence Check (Required)
For each file in the tech spec's "File Changes" table:
- Use `Glob` to verify the file exists
- If ANY expected file is missing → story is INCOMPLETE

### 3. Browser Verification (Required for UI stories)
- Navigate to affected pages via MCP chrome-devtools or playwright
- Verify key elements exist in DOM; 404 or missing elements → INCOMPLETE
- Save screenshot evidence to `sprint-artifacts/`

### Key Rules
- **Never mark "Done" without running these checks**
- **Build failure = incomplete** — fix before continuing
- **Missing files from tech spec = incomplete** — do not skip

## Ralph Loop Configuration

- **Max iterations**: 40
- **Completion**: `<promise>COMPLETE</promise>` | **Blocked**: `<promise>BLOCKED</promise>`

| Layer | Test | Lint |
|-------|------|------|
| Backend | `pytest tests/ -x` | `ruff check .` |
| Frontend | `cd frontend && npm run lint && npm run build` | `cd frontend && npm run lint` |
| E2E | `npx playwright test` | — |

### Subagent Routing

| File Pattern | Route To |
|--------------|----------|
| `/api/**`, `/open_notebook/**`, `/migrations/**`, `/commands/**` | `backend-specialist` |
| `/frontend/**` | `frontend-specialist` |
| `/tests/**` | `qa-specialist` |
| Story complete event | `docs-specialist` |

Agent teams require `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (set in settings.json). Agent definitions in `.claude/agents/`.

## Prompt Generator

Use `/generate-prompt <request>` for optimized session prompts. Flags: `--save`, `--tmux`, `--no-plan`.

## Browser Automation

Use `agent-browser`: `open <url>`, `snapshot -i`, `click @ref` / `fill @ref "text"`. Run `--help` for all commands.

## Documentation

Review `docs/index.md` before starting new features. Key: `docs/development/architecture.md`, `docs/development/api-reference.md`, `docs/bmm-index.md`.

## Salesforce CLI (READ-ONLY)

SF CLI is **read-only** for VAEA sandbox schema discovery. **Never deploy from this repo.** Hard deny entries in `settings.json` enforce blocks. Detailed rules: `.claude/rules/salesforce-cli.md`.

- **Allowed org**: `demi.thathsara@vaea.vic.gov.au.demidev` (read-only)
- **Pre-flight**: Print command → resolve org → classify (SELECT/describe = OK, else STOP and ask)
- **VAEA standards**: `/home/demi/gitrepo/vaea/CLAUDE.md` and `knowledge-base/`
