# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Open Notebook is a privacy-focused, multi-model AI research assistant. It's a monorepo with two parts:
- **Backend**: Python 3.11+ with FastAPI, LangChain/LangGraph, SurrealDB
- **Frontend**: Next.js 15 with React 19, Radix UI, Tailwind CSS 4, Zustand, React Query

## Essential Commands

### Development Setup
```bash
# Start all services (SurrealDB + API + Worker + Frontend)
make start-all

# Or start services individually:
docker compose up -d surrealdb        # Database on port 8000
uv run run_api.py                     # API on port 5055
uv run surreal-commands-worker --import-modules commands  # Background worker
cd frontend && npm run dev            # Frontend on port 8502

# Stop all services
make stop-all

# Check service status
make status
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

## Documentation

Extensive documentation exists in `./docs/`. Always review `docs/index.md` before starting new features.

Key docs:
- `docs/development/architecture.md` - System design
- `docs/development/api-reference.md` - REST API
- `docs/development/contributing.md` - Contribution guide
- `docs/bmm-index.md` - Comprehensive project scan/index
