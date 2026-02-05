# Open Notebook - Brownfield Project Documentation

> **Generated:** 2025-12-07
> **Scan Level:** Quick
> **Repository Type:** Multi-part (Monorepo)
> **Project Version:** 1.2.3

---

## Project Overview

**Open Notebook** is a privacy-focused, multi-model AI research assistant that enables users to organize research materials, generate AI-powered insights, create podcasts, and chat with context from their documents.

### Quick Reference

| Attribute | Value |
|-----------|-------|
| **Repository Type** | Multi-part Monorepo |
| **Parts** | 2 (Frontend + Backend) |
| **Primary Languages** | TypeScript, Python |
| **Database** | SurrealDB v2 |
| **Deployment** | Docker / Local Development |

---

## Part 1: Frontend (Web)

| Field | Value |
|-------|-------|
| **Part ID** | `frontend` |
| **Root Path** | `/frontend` |
| **Project Type** | Web Application |
| **Framework** | Next.js 15.4.7 + React 19.1.0 |
| **Language** | TypeScript 5.x |
| **UI Library** | Radix UI + Tailwind CSS 4.x |
| **State Management** | Zustand 5.x + React Query (TanStack) 5.x |
| **Build Tool** | Next.js built-in |
| **Package Manager** | npm |

### Frontend Key Dependencies

| Category | Technology | Purpose |
|----------|------------|---------|
| Framework | Next.js 15 | React meta-framework with SSR |
| UI Components | Radix UI | Accessible component primitives |
| Styling | Tailwind CSS 4 | Utility-first CSS |
| State | Zustand | Lightweight state management |
| Data Fetching | React Query | Server state management |
| Forms | React Hook Form + Zod | Form handling with validation |
| Icons | Lucide React | Icon library |
| Markdown | react-markdown, @uiw/react-md-editor | Markdown rendering/editing |

### Frontend Directory Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   ├── components/
│   │   ├── auth/               # Authentication (LoginForm)
│   │   ├── common/             # Shared components (CommandPalette, ModelSelector, etc.)
│   │   ├── errors/             # Error handling components
│   │   ├── layout/             # AppShell, AppSidebar
│   │   ├── notebooks/          # Notebook management
│   │   ├── podcasts/           # Podcast generation UI
│   │   ├── providers/          # React context providers
│   │   ├── search/             # Search functionality
│   │   ├── source/             # Source detail, chat panel
│   │   ├── sources/            # Source list, add dialogs
│   │   └── ui/                 # Base UI components (shadcn/ui style)
│   ├── hooks/                  # Custom React hooks
│   ├── lib/                    # Utilities and API clients
│   └── stores/                 # Zustand stores
├── public/                     # Static assets
├── package.json
├── next.config.ts
├── tailwind.config.ts
└── tsconfig.json
```

---

## Part 2: Backend (Python API)

| Field | Value |
|-------|-------|
| **Part ID** | `backend` |
| **Root Path** | `/` (api/, open_notebook/, commands/) |
| **Project Type** | Backend API |
| **Framework** | FastAPI |
| **Language** | Python 3.11+ |
| **Database** | SurrealDB |
| **AI Framework** | LangChain + LangGraph |
| **Background Jobs** | surreal-commands |

### Backend Key Dependencies

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Web Framework | FastAPI | 0.104+ | REST API |
| ASGI Server | Uvicorn | 0.24+ | HTTP server |
| Validation | Pydantic | 2.9+ | Data validation |
| Database | SurrealDB | 1.0.4+ | Document + Vector DB |
| AI/LLM | LangChain | 0.3+ | LLM orchestration |
| Workflows | LangGraph | 0.2+ | AI workflow graphs |
| Multi-Provider | Esperanto | 2.8+ | Unified AI provider abstraction |
| Content Processing | content-core | 1.0+ | Document extraction (Docling) |
| Podcasts | podcast-creator | 0.7+ | Audio generation |
| Background Jobs | surreal-commands | 1.2+ | Async task processing |

### Backend Directory Structure

```
open-notebook/
├── api/                        # FastAPI Application
│   ├── main.py                 # App entry point, middleware
│   ├── auth.py                 # Authentication
│   ├── models.py               # Pydantic request/response models
│   ├── routers/                # API endpoints
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── commands.py
│   │   ├── config.py
│   │   ├── context.py
│   │   ├── embedding.py
│   │   ├── episode_profiles.py
│   │   ├── insights.py
│   │   ├── models.py
│   │   ├── notebooks.py
│   │   ├── notes.py
│   │   ├── podcasts.py
│   │   ├── search.py
│   │   ├── settings.py
│   │   ├── sources.py
│   │   ├── source_chat.py
│   │   ├── speaker_profiles.py
│   │   └── transformations.py
│   └── *_service.py            # Business logic services
│
├── open_notebook/              # Domain Layer
│   ├── config.py               # Configuration management
│   ├── database/               # Repository pattern, SurrealDB
│   ├── domain/                 # Domain models
│   │   ├── base.py             # Base model with CRUD
│   │   ├── notebook.py         # Notebook, Source, Note entities
│   │   ├── models.py           # AI Model configuration
│   │   ├── podcast.py          # Episode/Speaker profiles
│   │   ├── transformation.py   # Content transformations
│   │   └── content_settings.py # Content configuration
│   ├── graphs/                 # LangGraph AI workflows
│   ├── plugins/                # Extensibility
│   └── utils/                  # Utilities
│
├── commands/                   # Background Job Handlers
│   ├── source_commands.py      # Source processing jobs
│   ├── podcast_commands.py     # Podcast generation jobs
│   └── embedding_commands.py   # Embedding generation jobs
│
├── migrations/                 # Database migrations
├── prompts/                    # AI prompt templates
├── tests/                      # Test suite
├── pyproject.toml              # Python project config
└── run_api.py                  # API startup script
```

---

## Database Schema

### Core Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `notebook` | Research project container | name, description, archived |
| `source` | Content items (PDFs, URLs, etc.) | title, full_text, asset, embedding, notebook_id |
| `note` | User/AI generated notes | title, content, note_type, notebook_id |
| `model` | AI model configurations | name, provider, type |
| `transformation` | Content processing templates | name, prompt, apply_default |
| `episode_profile` | Podcast configuration | speaker_config, outline_model |
| `speaker_profile` | Voice/personality config | tts_provider, speakers[] |

### Relationships

```
notebook (1) ─────────── (N) source
    │
    └──────────────────── (N) note

source (1) ─────────────── embedding (vector)
note (1) ───────────────── embedding (vector)
```

---

## API Endpoints Summary

### Notebooks & Content
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/notebooks` | GET, POST | List/create notebooks |
| `/api/notebooks/{id}` | GET, PUT, DELETE | Notebook CRUD |
| `/api/sources` | GET, POST | List/create sources |
| `/api/sources/{id}` | GET, PUT, DELETE | Source CRUD |
| `/api/notes` | GET, POST | List/create notes |
| `/api/notes/{id}` | GET, PUT, DELETE | Note CRUD |

### AI & Chat
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | General AI chat |
| `/api/source-chat` | POST | Context-aware source chat |
| `/api/search` | GET | Vector + full-text search |
| `/api/insights` | POST | Generate AI insights |

### Podcasts
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/podcasts` | POST | Generate podcast |
| `/api/episode-profiles` | CRUD | Episode templates |
| `/api/speaker-profiles` | CRUD | Voice configurations |

### System
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/models` | GET | Available AI models |
| `/api/transformations` | CRUD | Content transformations |
| `/api/commands` | GET, POST | Background job management |
| `/api/config` | GET | Application configuration |

---

## Integration Points

### Frontend ↔ Backend Communication

```
Browser (8502)
    │
    ▼
Next.js Frontend ──── /api/* proxy ────► FastAPI Backend (5055)
                                              │
                                              ▼
                                         SurrealDB (8000)
```

### External Integrations

| Integration | Purpose | Configuration |
|-------------|---------|---------------|
| OpenAI | LLM, Embeddings, TTS | OPENAI_API_KEY |
| Anthropic | LLM (Claude) | ANTHROPIC_API_KEY |
| Google AI | LLM, Embeddings, TTS | GOOGLE_API_KEY |
| Ollama | Local LLM | OLLAMA_HOST |
| ElevenLabs | TTS | ELEVENLABS_API_KEY |
| Groq | Fast LLM inference | GROQ_API_KEY |

---

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (for SurrealDB)

### Quick Start
```bash
# Start SurrealDB
docker compose -f docker-compose.dev.yml up surrealdb -d

# Backend
uv sync
uv run python run_api.py

# Worker (separate terminal)
uv run surreal-commands-worker --import-modules commands

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

### Ports
| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 8502 | Next.js dev server |
| API | 5055 | FastAPI backend |
| SurrealDB | 8000 | Database |

---

## Existing Documentation

### Core Documentation
| Document | Location | Description |
|----------|----------|-------------|
| README.md | / | Project overview, quick start |
| Architecture | docs/development/architecture.md | System design |
| API Reference | docs/development/api-reference.md | REST API docs |
| Contributing | docs/development/contributing.md | Contribution guide |

### User Documentation
| Document | Location | Description |
|----------|----------|-------------|
| Getting Started | docs/getting-started/ | Installation, tutorials |
| User Guide | docs/user-guide/ | Feature documentation |
| Features | docs/features/ | Advanced capabilities |
| Deployment | docs/deployment/ | Docker, security |
| Troubleshooting | docs/troubleshooting/ | Common issues |

### ACM-AI Project Documentation
| Document | Location | Description |
|----------|----------|-------------|
| System Analysis | docs/acm-ai/01-system-analysis.md | Current architecture review |
| Product Brief | docs/acm-ai/02-product-brief.md | Vision and goals |
| PRD | docs/acm-ai/03-prd.md | Detailed requirements |
| Architecture | docs/acm-ai/04-architecture.md | Technical design |
| Epics & Stories | docs/acm-ai/05-epics-and-stories.md | Implementation plan |

### Test Data
| File | Location | Description |
|------|----------|-------------|
| Sample PDFs | docs/samplePDF/ | 3 Asbestos Register PDFs for ACM extraction testing |

---

## Architecture Patterns

### Backend Patterns
- **Repository Pattern**: Database abstraction in `open_notebook/database/`
- **Domain-Driven Design**: Rich domain models in `open_notebook/domain/`
- **Service Layer**: Business logic in `api/*_service.py`
- **Command Pattern**: Background jobs in `commands/`
- **LangGraph Workflows**: AI pipelines in `open_notebook/graphs/`

### Frontend Patterns
- **App Router**: Next.js 15 file-based routing
- **Component Composition**: Radix UI primitives + custom components
- **React Query**: Server state management with caching
- **Zustand**: Client state management
- **Form Handling**: React Hook Form + Zod validation

---

## ACM-AI Feature Integration Points

For the ACM-AI feature (Asbestos Register extraction + AG Grid), key integration points:

### Backend Extensions Needed
| Location | Extension |
|----------|-----------|
| `open_notebook/domain/acm.py` | NEW: ACMRecord domain model |
| `open_notebook/transformations/acm_extraction.py` | NEW: Docling → ACM parser |
| `api/routers/acm.py` | NEW: ACM REST endpoints |
| `commands/acm_commands.py` | NEW: ACM extraction jobs |
| `migrations/acm_tables.surql` | NEW: Database schema |

### Frontend Extensions Needed
| Location | Extension |
|----------|-----------|
| `frontend/src/components/acm/` | NEW: AG Grid spreadsheet components |
| `frontend/src/lib/api/acm.ts` | NEW: ACM API client |
| `frontend/src/lib/utils/source-references.tsx` | MODIFY: Add `[acm:...]` citation type |
| `frontend/src/components/source/ChatPanel.tsx` | MODIFY: ACM context toggle |

### Existing Code to Leverage
| Component | Reuse For |
|-----------|-----------|
| `content-core` (Docling) | PDF table extraction |
| Citation system | ACM cell-level citations |
| Source processing pipeline | ACM extraction trigger |
| Chat context builder | ACM data in chat |
| React Query patterns | ACM data fetching |

---

## Next Steps for Brownfield PRD

When creating a PRD for new features:

1. **Reference this index** for existing patterns and integration points
2. **Check ACM-AI docs** at `docs/acm-ai/` for the active feature specification
3. **Follow existing patterns** in `api/routers/` and `open_notebook/domain/`
4. **Extend rather than replace** existing components where possible
5. **Use sample PDFs** in `docs/samplePDF/` for testing extraction

---

*Generated by BMAD document-project workflow v1.2.0*
