# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Critical** : Always use AskUserQuestion Tool when you want to clarify, interview or ask questions from the user.

## CRITICAL PATH RULE (WSL/Windows)

- Never `cd` to `/d/...` or `D:\...` in Bash commands.
- Always use the repo root from `$CLAUDE_PROJECT_DIR`.
- If `$CLAUDE_PROJECT_DIR` is not set, assume WSL mount: `/mnt/d/ailocal/acm-ai`.

Examples:
- `cd "$CLAUDE_PROJECT_DIR"`
- `cd "$CLAUDE_PROJECT_DIR" && uv run ...`
- `ls "$CLAUDE_PROJECT_DIR/docs"`
- `cd /d/ailocal/acm-ai` — WRONG
- `cd D:\ailocal\acm-ai` — WRONG

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
uv run run_worker.py --import-modules commands  # Background worker (Windows-compatible)
cd frontend && npm run dev            # Frontend on port 8502
```

**Note:** Use `run_worker.py` instead of `surreal-commands-worker` directly on Windows to avoid Unicode encoding errors (see Issue #1).

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

## Browser Automation

Use `agent-browser` for web automation. Run `agent-browser --help` for all commands.

Core workflow:
1. `agent-browser open <url>` - Navigate to page
2. `agent-browser snapshot -i` - Get interactive elements with refs (@e1, @e2)
3. `agent-browser click @e1` / `fill @e2 "text"` - Interact using refs
4. Re-snapshot after page changes

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
  extractors/           # Data extraction modules
    acm_extractor.py    # ACM register extraction with MinerU fallback
    mineru_table_extractor.py  # MinerU-based table extraction
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

### Table Extraction

The system uses **MinerU** (via `magic-pdf` library) for advanced table extraction from PDF documents, with automatic fallback to regex-based parsing:

**Features:**
- **Merged cell handling**: Correctly parses HTML tables with `colspan` and `rowspan` attributes
- **Multi-page tables**: Automatically stitches tables spanning multiple pages into a single logical table
- **Bounding box tracking**: Captures table coordinates `{x, y, width, height, page}` for provenance linking
- **Performance**: Processes 20-page PDFs in <30 seconds (estimated 10-25s typical)

**Fallback Strategy:**
```python
# In acm_extractor.py
extract_acm_records(
    markdown_content=None,
    source_id="source:123",
    pdf_path="/path/to/file.pdf",  # Enable MinerU extraction
    use_mineru=True                 # Default: True
)
```

1. **MinerU first** (if `use_mineru=True` and `pdf_path` provided): Uses ML-based table extraction
2. **Regex fallback** (if MinerU fails or unavailable): Falls back to markdown regex parsing

**Configuration:**
- Set `use_mineru=False` to skip MinerU and use regex directly
- MinerU is optional - system works without it via fallback
- Bounding box data is stored in `ACMRecord.table_bbox` field (optional)

**Known Issues:**
- MinerU dependency (`magic-pdf`) has incomplete dependency declarations - may require manual installation of `opencv-python`, `ultralytics`, `doclayout-yolo` for full functionality
- Consider Docker containerization for MinerU isolation in production
- Fallback mechanism ensures data extraction works even if MinerU dependencies are unavailable

## Python Environments: MinerU 2.x (E31-S1 Validated)

MinerU 2.x (`mineru>=2.7.0`) installs directly into the main `.venv/` alongside Docling and PyTorch.
The `paddlepaddle-gpu` conflict that drove the two-venv pattern was specific to MinerU 1.x (`magic-pdf`).

**IMPORTANT — `[all]` extras conflict:** `mineru[all]` includes `vllm` which pins `torchvision` to versions
incompatible with `torchvision>=0.25.0` in the project. Use `mineru>=2.7.0` (without `[all]`) instead.
The `[pipeline]` and `[vlm]` extras can be added individually if specific backends are needed.

### Venv Summary

| Venv | Path | Purpose | Manager |
|------|------|---------|---------|
| Main | `.venv/` | All production services — API, worker, Docling/TableFormer, MinerU 2.x | `uv` (pyproject.toml) |
| MinerU (legacy) | `.venv-mineru/` | MinerU 1.x (`magic-pdf`) — deprecated if MinerU 2.x confirmed in main venv | `pip` (standalone) |

### Interpreter Paths

| Platform | Main venv | MinerU 1.x legacy venv |
|----------|-----------|-------------------------|
| Windows | `.venv\Scripts\python.exe` | `.venv-mineru\Scripts\python.exe` (deprecated) |
| WSL/Linux | `.venv/bin/python` | `.venv-mineru/bin/python` (deprecated) |

### Rules for All AI Coding Tools

- **Always `uv run ...`** for all main project work (API, tests, lint, workers)
- **`import mineru`** directly in main project code — no subprocess bridge needed for MinerU 2.x
- **Never** add `mineru[all]` to `pyproject.toml` — use `mineru>=2.7.0` to avoid `vllm`/`torchvision` conflict
- **Never** `uv pip install magic-pdf` or `paddlepaddle` into the main venv
- `scripts/mineru_runner.py` — legacy bridge for MinerU 1.x, deprecated

### MinerU 2.x API

```python
from mineru import MinerUDocumentConverter

converter = MinerUDocumentConverter()
result = converter.convert("/path/to/file.pdf")
```

Enable via environment variables: `MINERU_ENABLED=true` (no separate venv path needed)

### Legacy Subprocess Bridge (Deprecated)

`scripts/mineru_runner.py` was the MinerU 1.x subprocess bridge via `.venv-mineru/`.
It is deprecated now that MinerU 2.x installs in the main venv.
See E31-S1 validation results at `scripts/research/e31_s1_validation_results.json`.

### One-Time Setup (Windows)

MinerU 2.x installs automatically via `uv sync` — no separate setup step required.
(Legacy: `/e25-setup-mineru` command set up the old `.venv-mineru/` venv.)

## Database

SurrealDB with core tables: `notebook`, `source`, `note`, `model`, `transformation`, `episode_profile`, `speaker_profile`

Relationships:
- `source.notebook_id` → `notebook`
- `note.notebook_id` → `notebook`
- Sources and notes can have vector embeddings for semantic search

**ACM-specific fields:**
- `ACMRecord.table_bbox`: Optional bounding box tracking `{x, y, width, height, page}` for table provenance (populated when using MinerU extraction)

## Environment Variables

Required in `.env`:
```bash
SURREAL_URL=ws://localhost:8000/rpc
SURREAL_USER=root
SURREAL_PASSWORD=root
SURREAL_NAMESPACE=open_notebook
SURREAL_DATABASE=development
OPENAI_API_KEY=sk-...  # At least one AI provider

# ACM pipeline API keys — separate from Claude Code's keys (never use bare ANTHROPIC_API_KEY here)
ACM_ANTHROPIC_API_KEY=sk-ant-...    # ACM extraction only — not read by Claude Code tooling
ACM_OPENROUTER_API_KEY=sk-or-...    # ACM OpenRouter fallback only

# Optional: Ollama-only mode (omit cloud keys above)
OLLAMA_API_BASE=http://localhost:11434
# Content truncation guard for Ollama — auto-sized from model's num_ctx (3.5 chars/token).
# Override only if the auto-size is wrong for your specific model/hardware combo.
OLLAMA_MAX_CONTENT_CHARS=24000  # explicit override (optional; default: num_ctx * 3.5)
```

## Code Style

- **Python**: Ruff for linting/formatting, 88 char line length, type hints required, Google-style docstrings
- **Commits**: Conventional commits (feat:, fix:, docs:, refactor:, test:)

## Sub-Agent Model Selection

When delegating tasks to sub-agents via the Task tool:

- **Default**: Use `model: "sonnet"` for most tasks - provides good speed/quality balance for well-documented codebase areas
- **Complex/Undocumented Tasks**: Use `model: "opus"` when:
  - Task involves areas with minimal documentation or known patterns
  - Requires deep architectural reasoning or cross-cutting concerns
  - Involves novel problem-solving not covered by existing patterns
  - Risk of incomplete understanding with smaller models

### Agent Teams and TeamCreate

**IMPORTANT**: When creating agent teams using `TeamCreate` or spawning teammates via the `Task` tool within a team:

- **Only use `model: "sonnet"` or `model: "haiku"`** - DO NOT use `model: "opus"` for team members
- **Rationale**: Cost control and performance - multiple agents running in parallel can quickly consume resources
- **Default for teams**: Use `model: "sonnet"` for team leads and complex tasks, `model: "haiku"` for simple/focused tasks
- **Exception**: Single-agent Task tool calls (not part of a team) may still use opus when justified by task complexity

**Examples:**
```python
# Single agent - Well-documented feature area → sonnet
Task(description="Add new field to existing table",
     subagent_type="Explore",
     model="sonnet")

# Single agent - Complex, undocumented area → opus (allowed for single agents)
Task(description="Design new RAG strategy for novel extraction pattern",
     subagent_type="acm-rag-strategist",
     model="opus")

# Team creation → ONLY sonnet or haiku
TeamCreate(team_name="implementation-team",
           description="Multi-agent implementation team")

# Team member spawn → ONLY sonnet or haiku
Task(description="Implement backend service",
     subagent_type="acm-extraction-core",
     team_name="implementation-team",
     name="backend-dev",
     model="sonnet")  # ✓ Correct - sonnet for team members

Task(description="Run unit tests",
     subagent_type="general-purpose",
     team_name="implementation-team",
     name="test-runner",
     model="haiku")  # ✓ Correct - haiku for simple tasks in teams

# NEVER do this in teams:
# model="opus"  # ✗ WRONG - do not use opus for team members
```

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

## V3 Architecture Patterns

### Provider Adapter Framework
- Protocol: `ExtractionProvider` in `open_notebook/extractors/providers/base.py`
- Adapters: `DoclingAdapter`, `MinerUAdapter` in `open_notebook/extractors/providers/`
- Registry: `ProviderRegistry` in `open_notebook/extractors/providers/__init__.py`
- Pattern: adapters normalize provider output to common `RawExtraction` domain objects via `NormalizedExtractionResult`

### Consensus Layer
- `RecordMatcher` in `open_notebook/extractors/consensus/matcher.py` -- 3-stage record matching (exact, fuzzy, positional)
- `ConsensusEngine` in `open_notebook/extractors/consensus/engine.py` -- confidence-weighted voting across provider results
- `ConflictResolver` in `open_notebook/extractors/consensus/resolver.py` -- L1-L4 escalation (identical, majority, confidence, flag)

### Salesforce Schema Alignment
- Config loader: `open_notebook/extractors/parsers/config_loader.py` (parses SF field summaries into structured config)
- SF field definitions: `V3/output/building_fields_summary.md`, `V3/output/item_fields_summary.md`
- Dependent picklist validation: `SalesforcePicklistValidator` in config_loader
- Normalizer enums: `open_notebook/extractors/normalizers/enums.py`
- ACM domain model uses SF API names as field aliases: `open_notebook/domain/acm.py`

### Two-View Frontend (Building Grid + Item Grid)
- Route: `/source/[id]` at `frontend/src/app/(dashboard)/source/[id]/page.tsx`
- Components: `BuildingSidebar`, `ItemGrid` in `frontend/src/components/acm/`
- Store: `frontend/src/lib/stores/buildingStore.ts` (Zustand)
- Hooks: `useBuildings`, `useACMItems` in `frontend/src/lib/hooks/`
- AG Grid dynamic columns from `GET /api/acm/field-schema`

### SSE Streaming (PipelineEventBus)
- Backend: `open_notebook/extractors/pipeline_event_bus.py`
- SSE endpoints: `api/routers/v3_streaming.py`
- Frontend hook: `frontend/src/lib/hooks/useV3SSE.ts`
- Zustand store: `frontend/src/lib/stores/streamingStore.ts`
- Event categories: `extraction`, `ai`, `bulk`

### V3 API Endpoints
- `GET /api/acm/buildings?source_id=X` -- Building records with record_count
- `GET /api/acm/field-schema` -- SF field schema config
- `GET /api/acm/raw-extractions/{source_id}` -- Raw extraction records
- `GET /api/acm/provenance/{record_id}` -- Record provenance with consensus data
- `GET /api/acm/intelligence/{source_id}` -- Pre-extraction intelligence
- `GET /api/v3/stream/{category}/{id}` -- SSE streaming endpoints
- `POST /api/acm/bulk-edit` -- Bulk field edit
- `POST /api/acm/bulk-validate` -- Bulk re-validation
- `GET /api/acm/validation-summary/{source_id}` -- Validation summary

### V3 Frontend Type Files
- `frontend/src/lib/types/acm.ts` -- ACMRecord, RawExtraction, Provenance types
- `frontend/src/lib/types/building.ts` -- BuildingRecord, BuildingListResponse
- `frontend/src/lib/types/pipeline.ts` -- PipelineRunState, StageId, StageStatus
- `frontend/src/lib/types/sf-schema.ts` -- SFFieldSchemaConfig, SFFieldDef
- `frontend/src/lib/types/intelligence.ts` -- SourceIntelligence, DocumentMeta, BuildingInventory
- `frontend/src/lib/types/v3-streaming.ts` -- V3EventEnvelope

## Documentation

Extensive documentation exists in `./docs/`. Always review `docs/index.md` before starting new features.

Key docs:
- `docs/development/architecture.md` - System design
- `docs/development/api-reference.md` - REST API
- `docs/development/contributing.md` - Contribution guide
- `docs/bmm-index.md` - Comprehensive project scan/index

## Claude Code Custom Commands

Custom slash commands are available in `.claude/commands/`:

| Command | Description |
|---------|-------------|
| `/start` | Start development services (SurrealDB) |
| `/stop` | Stop all Docker services |
| `/status` | Check service health (SurrealDB, API, Frontend) |
| `/logs [service]` | View service logs |
| `/build [target]` | Build frontend or run backend checks |
| `/test [path]` | Run pytest tests |

BMAD workflow commands are also available in `.claude/commands/bmad/`.

## Claude Code Modular Rules

Domain-specific rules in `.claude/rules/`:

| Rule File | Applies To |
|-----------|------------|
| `docker-compose.md` | `docker-compose*.yml` files |
| `python-backend.md` | `**/*.py`, `api/**/*`, `open_notebook/**/*` |
| `nextjs-frontend.md` | `frontend/**/*.ts`, `frontend/**/*.tsx` |
| `langgraph-ai.md` | `open_notebook/graphs/**/*`, `prompts/**/*` |
| `surrealdb.md` | `migrations/**/*`, `open_notebook/database/**/*` |
| `mcp-servers.md` | `.claude/settings*.json` files |

## MCP Configuration

MCP servers configured in `.claude/settings.json`:

| Server | Purpose | Status |
|--------|---------|--------|
| `filesystem` | File operations | Enabled |
| `memory` | Persistent context | Enabled |
| `playwright` | Browser automation | Enabled (via settings.local.json) |
| `chrome-devtools` | Page snapshots | Enabled (via settings.local.json) |

### Local Overrides
Machine-specific configuration in `.claude/settings.local.json` (gitignored):
- Custom tool permissions
- Additional MCP servers (n8n, etc.)

## Docker Local Overrides

For port conflicts (e.g., Supabase using port 8000), create `docker-compose.override.yml` (gitignored):

```yaml
# Example: Remap SurrealDB to port 8001
services:
  surrealdb:
    ports: !override
      - "8001:8000"
    healthcheck: !override
      test: ["CMD", "/surreal", "isready", "--conn", "http://localhost:8000"]
      interval: 10s
      timeout: 5s
      retries: 5
```

Then update `.env` to match:
```bash
SURREAL_URL=ws://localhost:8001/rpc
```

This file is automatically merged by Docker Compose and keeps machine-specific config separate from the shared base.

## Ralph Loop Configuration

When running a Ralph autonomous loop on this repo:
- **Max iterations**: 40
- **Completion promise**: `<promise>COMPLETE</promise>`
- **Blocked signal**: `<promise>BLOCKED</promise>`

### Test Commands

| Layer | Command |
|-------|---------|
| Backend | `pytest tests/ -x` |
| Frontend | `cd frontend && npm run lint && npm run build` |
| E2E | `npx playwright test` |

### Lint Commands

| Layer | Command |
|-------|---------|
| Python | `ruff check .` |
| Frontend | `cd frontend && npm run lint` |

### Subagent Routing Table

| File Pattern | Route To |
|--------------|----------|
| `/api/**`, `/open_notebook/**`, `/migrations/**`, `/commands/**` | `backend-specialist` |
| `/frontend/**` | `frontend-specialist` |
| `/tests/**`, `/playwright-report/**` | `qa-specialist` |
| Story complete event | `docs-specialist` |

### Agent Teams

Requires environment variable:
```
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

Agent definitions in `.claude/agents/`. The `orchestrator` reads stories from `docs/sprint-artifacts/` and delegates to specialists based on the routing table above.
