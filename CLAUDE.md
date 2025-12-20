# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ACM-AI is an intelligent Asbestos Containing Material (ACM) compliance management system powered by AI. It transforms SAMP (School Asbestos Management Plan) documents into structured, queryable data. It's a monorepo with two parts:
- **Backend**: Python 3.11+ with FastAPI, LangChain/LangGraph, SurrealDB
- **Frontend**: Next.js 15 with React 19, Radix UI, Tailwind CSS 4, Zustand, React Query

## Essential Commands

### Development Setup (Windows)
```batch
# Ensure Docker Desktop is running first!

# Start all services (SurrealDB + API + Worker + Frontend)
start-all.bat

# Stop all services
stop-all.bat
```

### Development Setup (macOS/Linux)
```bash
# Start all services
make start-all

# Stop all services
make stop-all

# Check service status
make status
```

### Manual Setup (All Platforms)
```bash
docker compose up -d surrealdb        # Database on port 8000
uv run run_api.py                     # API on port 5055
uv run surreal-commands-worker --import-modules commands  # Background worker
cd frontend && npm run dev            # Frontend on port 8502
```

### Docker-Only Development
```bash
# Full containerized development with hot-reload:
docker compose -f docker-compose.dev-local.yml up
```

### Backend Commands
```bash
uv sync                              # Install dependencies
uv run pytest                        # Run all tests
uv run pytest tests/test_specific.py # Run single test file
uv run pytest --cov=open_notebook    # Run with coverage
uv run ruff check . --fix            # Lint and fix
uv run ruff format .                 # Format code
uv run mypy .                        # Type check
```

### Frontend Commands
```bash
cd frontend
npm install                          # Install dependencies
npm run dev                          # Development server (port 8502)
npm run build                        # Production build
npm run lint                         # Lint
```

## Architecture

### Service Communication
```
Browser (8502) → Next.js Frontend → /api/* proxy → FastAPI Backend (5055) → SurrealDB (8000)
```

### Backend Structure
```
api/                    # FastAPI routers and services
  routers/              # REST endpoints by domain
  *_service.py          # Business logic
open_notebook/          # Domain layer
  domain/               # Entity models (Notebook, Source, Note, etc.)
  database/             # Repository pattern for SurrealDB
  graphs/               # LangGraph AI workflows (chat, search, transformations)
commands/               # Background job handlers (surreal-commands)
prompts/                # Jinja2 AI prompt templates
migrations/             # SurrealDB schema migrations (auto-run on API start)
```

### Frontend Structure
```
frontend/src/
  app/                  # Next.js App Router pages
  components/           # React components
    ui/                 # Base shadcn/ui-style components
    common/             # Shared (CommandPalette, ModelSelector)
    notebooks/, sources/, notes/  # Feature components
  hooks/                # Custom React hooks
  lib/                  # Utilities and API clients
  stores/               # Zustand stores
```

### Key Patterns
- **Backend**: Repository pattern, Domain-Driven Design, Command pattern for async jobs
- **Frontend**: React Query for server state, Zustand for client state, React Hook Form + Zod for forms
- **AI**: LangGraph workflows in `open_notebook/graphs/` using Esperanto for multi-provider abstraction

## Database

SurrealDB with core tables: `notebook`, `source`, `note`, `model`, `transformation`, `episode_profile`, `speaker_profile`

Relationships:
- `source.notebook_id` → `notebook`
- `note.notebook_id` → `notebook`
- Sources and notes can have vector embeddings for semantic search

## Environment Variables

Required in `.env`:
```bash
SURREAL_URL=ws://localhost:8000/rpc
SURREAL_USER=root
SURREAL_PASSWORD=root
SURREAL_NAMESPACE=open_notebook
SURREAL_DATABASE=development
OPENAI_API_KEY=sk-...  # At least one AI provider
```

## Code Style

- **Python**: Ruff for linting/formatting, 88 char line length, type hints required, Google-style docstrings
- **Commits**: Conventional commits (feat:, fix:, docs:, refactor:, test:)

## Story Verification Protocol

**CRITICAL:** Before marking ANY story as complete, you MUST perform these verification steps. Never trust task checkmarks alone.

### 1. Build Verification (Required for ALL stories)
```bash
# Frontend changes
cd frontend && npm run build    # Must pass - catches missing files/imports

# Backend changes
uv run ruff check .             # Lint check
uv run pytest                   # Tests must pass
```

### 2. File Existence Check (Required)
For each file listed in the tech spec's "File Changes" table:
- Use `Glob` tool to verify the file actually exists
- If ANY expected file is missing, the story is INCOMPLETE - create it before continuing

### 3. Browser Verification (Required for UI stories)
For stories involving frontend/UI changes:
```
1. Use MCP chrome-devtools or playwright to navigate to affected page(s)
2. Take snapshot to verify key elements exist in DOM
3. If page returns 404 or elements missing → story is INCOMPLETE
4. Take screenshot as evidence and save to sprint-artifacts/
```

### 4. Evidence Collection
Add to the story's Dev Agent Record:
- Build status: PASS/FAIL
- Files verified: [list of files checked]
- Pages verified: [list of URLs tested] (for UI stories)
- Screenshot path: [path to evidence]

### Key Rules
- **Never mark a story "Done" without running these checks**
- **A build failure = incomplete implementation** - fix before continuing
- **A 404 error = missing page/route** - create required files
- **Missing files from tech spec = incomplete** - do not skip any files
- **Code review cannot catch files that don't exist** - verify BEFORE review

## Documentation

Extensive documentation exists in `./docs/`. Always review `docs/index.md` before starting new features.

Key docs:
- `docs/development/architecture.md` - System design
- `docs/development/api-reference.md` - REST API
- `docs/development/contributing.md` - Contribution guide
- `docs/bmm-index.md` - Comprehensive project scan/index
