# ACM-AI Project Context

## Stack Overview

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, LangChain/LangGraph, Esperanto (multi-provider LLM) |
| Frontend | Next.js 15, React 19, Radix UI, Tailwind CSS 4, Zustand, React Query |
| Database | SurrealDB (document + graph + vector) |
| Background Jobs | surreal-commands (command pattern) |
| AI/ML | LangGraph workflows, Ollama (local), OpenRouter (cloud) |
| Testing | pytest (backend), Playwright (E2E planned) |
| Linting | Ruff (Python), ESLint via Next.js (frontend) |

## Folder Purposes

| Directory | Purpose |
|-----------|---------|
| `/api/` | FastAPI routers (`routers/`), services (`*_service.py`), Pydantic models (`models.py`) |
| `/api/routers/` | REST endpoints by domain (acm, chat, notebooks, sources, search, models, etc.) |
| `/open_notebook/` | Domain layer — entities, database, extractors, AI graphs |
| `/open_notebook/domain/` | Pydantic entity models (notebook, source, note, acm, transformation) |
| `/open_notebook/database/` | Repository pattern for SurrealDB access |
| `/open_notebook/extractors/` | Data extraction — ACM extractor, MinerU tables, parsers, validators, normalizers |
| `/open_notebook/graphs/` | LangGraph AI workflows (chat, search, extraction, agents) |
| `/frontend/src/app/` | Next.js App Router pages and layouts |
| `/frontend/src/components/` | React components (ui/, common/, acm/, notebooks/, sources/, etc.) |
| `/frontend/src/hooks/` | Custom React hooks |
| `/frontend/src/lib/` | Utilities, API clients, type definitions |
| `/frontend/src/stores/` | Zustand state management stores |
| `/migrations/` | SurrealDB schema migrations (SurrealQL files, auto-run on API start) |
| `/commands/` | Background job handlers using surreal-commands pattern |
| `/tests/` | pytest test suite (35+ test files) |
| `/prompts/` | Jinja2 AI prompt templates |
| `/_bmad-output/` | BMAD methodology artifacts (stories, tech specs, test reports) |

## SurrealDB Schema

### Core Tables
- `notebook` — Top-level organizational container
- `source` — Uploaded documents with processing status
- `source_embedding` — Vector embeddings for source content
- `note` — User notes linked to notebooks
- `acm_record` — Extracted ACM register data (50+ BAR fields)
- `site_config` — Per-source site configuration
- `model` — LLM model configuration
- `transformation` — Data transformation records
- `podcast_config` — Podcast generation settings

### Key Features
- Full-text BM25 search indexes with custom analyzers
- Vector cosine similarity search functions
- Cascade delete on source deletion (removes related records)
- ACM-specific fields: school_name, building_id, room_id, material_description, risk_status, extraction_confidence, table_bbox

## Key Design Patterns

1. **Repository Pattern** — All DB access through `open_notebook/database/repository.py`
2. **Domain-Driven Design** — Entities in `/domain/` with Pydantic validation
3. **Command Pattern** — Async background jobs in `/commands/` via surreal-commands
4. **Service Layer** — Business logic in `api/*_service.py`, routers call services
5. **LangGraph Workflows** — AI orchestration for extraction, chat, search
6. **Extraction Pipeline** — Modular: Parser detection → Table extraction → Normalization → Validation
7. **React Query + Zustand** — Server state (React Query) + client state (Zustand)
8. **React Hook Form + Zod** — Type-safe form handling with validation

## Service Ports

| Service | Port | URL |
|---------|------|-----|
| FastAPI Backend | 5055 | http://localhost:5055 |
| Next.js Frontend | 8502 | http://localhost:8502 |
| SurrealDB | 8000 | ws://localhost:8000/rpc |

## Test Structure

- **Backend**: 35+ test files in `/tests/`, pytest with `conftest.py` fixtures
- **Key test files**: test_acm_extractor.py (34 tests), test_consultant_parsers.py (40 tests), test_e2e_extraction.py (12 tests)
- **Coverage**: 812+ tests total
- **E2E**: Playwright planned but not yet configured
- **Frontend**: No test runner configured yet (vitest/jest not in package.json)
