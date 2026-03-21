# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Critical** : Always use AskUserQuestion Tool when you want to clarify, interview or ask questions from the user.

## User Documetation Location : C:\Users\User\Documents\Obsidian Vault\ACM

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

ACM-AI is an intelligent Asbestos Containing Material (ACM) compliance management system powered by AI. It transforms ARA (Asbestos Register Assessment) documents into structured, queryable data. It's a monorepo with two parts:
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
| `/dashboard` | Notebooks overview (legacy) | P3 |

### Rules for Frontend Changes

- When asked to add a feature to "the source page" or "the document view", implement it on `/jobs/[id]` page at
`frontend/src/app/(dashboard)/jobs/[id]/page.tsx`
- `/source/[id]` is a lightweight secondary view — do NOT add new features there unless explicitly asked
- SSE streaming, bulk operations, validation, search — all belong on `/jobs/[id]`
- The jobs page component is at: `frontend/src/app/(dashboard)/jobs/[id]/page.tsx`

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

### LangGraph Dev Server (Local Graph Debugging)
```bash
uv run langgraph dev --no-browser     # Both graphs: acm_extraction, supervisor
# API: http://127.0.0.1:2024          # Invoke graphs, inspect thread state
# Docs: http://127.0.0.1:2024/docs    # Swagger UI — fully local, no cloud
```
**Important:** Always use `uv run langgraph dev`, not bare `langgraph dev` — the latter uses global Python which lacks project deps.
**Note:** LangGraph Studio UI now requires LangSmith cloud. Use the local API + Swagger UI at `:2024/docs` for fully-local debugging, combined with Langfuse traces for visualization.

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
    acm/                # ACM domain (BuildingGrid, ACMGrid, BuildingViewDialog, ProvenanceViewer, DoclingTablesPanel, BuildingsProgressPanel, LiveRecordsPanel, etc.)
    chat/               # Chat components (SmartChatPanel, renderers/)
    jobs/               # Job-related components (JobCard with live counters, ExtractionStatusBanner)
    notebooks/, sources/, notes/  # Feature components
  hooks/                # Custom React hooks (useLiveStats, useExtractionStream, useV3SSE, etc.)
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

**SurrealDB Query Patterns:**
- **`type::thing()` for record ref comparison**: When a column is typed as `record<table>` and you have a string ID (e.g., `"source:xxx"`), use `type::thing('source:xxx')` in the WHERE clause. Plain string comparison silently returns zero results.
- **RecordID in base.py setattr**: SurrealDB Python client returns `RecordID` objects in query results. The `ObjectModel` setattr loop must convert these to `str()` when the target Pydantic field is typed as `str`, otherwise downstream serialization fails.
- **LLM string-to-int coercion**: LLMs frequently return numeric fields (e.g., `page_start`, `page_end`) as strings. Use Pydantic `BeforeValidator` to coerce `str` to `int` rather than rejecting with a validation error.

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

# Per-row extraction (v3.5)
ACM_ITEM_EXTRACTION_MODE=per_row    # per_row (default) or bulk
ACM_ROW_EXTRACTION_NUM_CTX=2048     # Context window for per-row extraction
ACM_EXTRACTION_MODEL=llama3.1:8b    # Ollama model for extraction (configurable)

# Extraction timeout
ACM_EXTRACT_TIMEOUT=3600            # Max seconds for full extraction job (default 3600; large Ollama docs need >30min)
```

## Code Style

- **Python**: Ruff for linting/formatting, 88 char line length, type hints required, Google-style docstrings
- **Commits**: Conventional commits (feat:, fix:, docs:, refactor:, test:)

## Prompt Generator System

### Quick Start
Use `/generate-prompt <request>` to auto-generate optimized Claude Code prompts.

Examples:
- `/generate-prompt "Fix the extraction pipeline timeout error"`
- `/generate-prompt "Add a new extraction provider" --save --tmux`
- `/generate-prompt "Update the README" --no-plan`

### How It Works
The prompt generator is a 4-skill pipeline:
1. **Discovery** (`/skill-discovery`): Scans `.claude/skills/`, `.agents/skills/`, `commands/`, and `CLAUDE.md` to build `skills-registry.json`
2. **Classification** (`/request-classifier`): Parses your request → type (feature/bug/research/...), complexity (1-10), plan mode (on/off)
3. **Routing** (`/prompt-router`): Maps classification → skill bundle, agent strategy (solo/subagent/tmux), Context7 directives
4. **Generation** (`/prompt-generator`): Assembles a complete prompt with glossary, verification checklist, and files summary

### Plan Mode
Automatically activated for features, bug fixes, research, and improvements. Creates:
- `task_plan.md` — Numbered steps with file paths
- `findings.md` — Research template
- `progress.md` — Checkbox tracker

Override: add `--no-plan` to skip, or `--with-plan` to force.

### Agent Strategies
- **Solo**: Simple tasks, 1 skill, direct execution
- **Subagent Dispatch**: Medium tasks, parallel subtasks via `/dispatching-parallel-agents`
- **Tmux Agent Team**: Complex tasks, 3+ panes for implementation/testing/research

### Skills Registry
Auto-updated on session start (via pre-session hook). Manual refresh: `/skill-discovery`.
Location: `skills-registry.json` at repo root.

### Available Skills
Run `/skill-discovery` to see the current catalog.

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

### Two-Tab Frontend (Building Grid + ACM Records Grid)
- Route: `/source/[id]` at `frontend/src/app/(dashboard)/source/[id]/page.tsx`
- Layout: Two-tab — "Buildings" tab (`BuildingGrid`) + "ACM Records" tab (`BuildingTabStrip` + `ACMGrid`)
- `BuildingGrid` in `frontend/src/components/acm/BuildingGrid.tsx` — AG Grid with 13 default building columns, autoHeight, localStorage column state, View button
- `BuildingViewDialog` in `frontend/src/components/acm/BuildingViewDialog.tsx` — Dialog modal wrapping `BuildingDetailForm`
- `ACMGrid` column defs: 13 required Item__c fields (Building Code, Item Name, Friability, etc.)
- Per-building export dropdown: "Export Current Building" + "Export All" (Excel/CSV)
- Same layout applied to `/jobs/[id]` page
- Store: `frontend/src/lib/stores/buildingStore.ts` (Zustand)
- Column visibility presets: `frontend/src/lib/stores/column-visibility-store.ts`
- Hooks: `useBuildings`, `useACMItems` in `frontend/src/lib/hooks/`
- AG Grid dynamic columns from `GET /api/acm/field-schema`

### Observability Stack
Six tools, each with a distinct role:

| Tool | When to Use | Key Feature | Data Location |
|------|------------|-------------|---------------|
| **Langfuse** (self-hosted) | Production monitoring, cost tracking, trace archive | Per-provider cost breakdown, unlimited retention | Local Docker (`localhost:3000`) |
| **LangSmith** (cloud) | Dev prompt iteration, auto-tracing all graphs | Prompt playground (edit + re-run), side-by-side comparison | Cloud (smith.langchain.com) |
| **LangGraph API** (local) | Debug graph state, invoke/inspect threads | Swagger UI at `:2024/docs`, state inspection via REST | Local (`127.0.0.1:2024`) |
| **Logfire SDK** (dev) | Pydantic validation traces → Langfuse via OTel | See every `model_validate()`, parse error, coercion as a span | Routes to Langfuse (no cloud) |
| **erdantic** (dev CLI) | Static ER diagrams of Pydantic model relationships | `pip install erdantic` + Graphviz, then `python scripts/generate_model_diagrams.py` → `docs/diagrams/*.svg` | Local SVG files |
| **JSON Crack** (Docker) | Interactive JSON tree viewer for graph state debugging | Paste JSON or upload `state_dump.json` at `localhost:8888` | Local Docker (`localhost:8888`) |

**When to use which:**
- **"Why did this extraction produce wrong data?"** → LangSmith (trace the LLM call, edit prompt in playground)
- **"How much is this costing across all runs?"** → Langfuse (self-hosted, cost/token dashboards)
- **"What's the graph state right now for thread X?"** → LangGraph API (`GET /threads/{id}/state`)
- **"Is the pipeline healthy across many documents?"** → Langfuse (historical traces, score trends)
- **"What did Pydantic do with the LLM output?"** → Logfire (validation spans in Langfuse)
- **"How do our 60+ models relate?"** → erdantic (`docs/diagrams/*.svg`)
- **"Let me explore this nested JSON interactively"** → JSON Crack (`localhost:8888`)
- **Production** → Langfuse only (self-hosted, data stays local — required for government data)

**Code patterns:**
- Langfuse config: `open_notebook/observability/langfuse_config.py`
- Logfire config: `open_notebook/observability/logfire_config.py`
- Use `langfuse_tracing()` context manager + `merge_langfuse_into_config()` for all new graph invocations in routers
- Do NOT modify `acm_extraction.py` or `source_commands.py` Langfuse wiring (pre-existing, working)
- All tracing is non-fatal — app works with Langfuse/Logfire disabled
- LangSmith auto-traces via `LANGCHAIN_TRACING_V2=true` env var (zero code changes)
- Logfire auto-instruments Pydantic v2 when `LOGFIRE_ENABLED=true` (requires Langfuse keys)
- JSON Crack: `docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d jsoncrack`
- State dump: `uv run python scripts/dump_state_json.py <thread_id>` → paste into JSON Crack

### Per-Row Extraction Pipeline (v3.5)

Item__c extraction supports two modes controlled by `ACM_ITEM_EXTRACTION_MODE` env var:

**Per-row mode** (default): One LLM call per table row → 13 fields → deterministic post-processing
- Row segmenter: `open_notebook/extractors/row_segmenter.py` (RawTableRow, 8 edge case types)
- Row extractor: `open_notebook/extractors/row_extractor.py` (KV prompt, extract_all_rows)
- Schema: `open_notebook/domain/acm_row_schemas.py` (ACMItemRow, 13 fields)
- Mapper: `open_notebook/domain/acm_row_mappers.py` (ACMItemRow → ACMExtractionRecord)
- Prompts: `prompts/acm/row_extraction.jinja`, `prompts/acm/row_split.jinja`
- Ollama config: `ACM_ROW_EXTRACTION_NUM_CTX=2048`, `ACM_EXTRACTION_MODEL=llama3.1:8b`

**Bulk mode**: Original V3 path — one LLM call per building, all items at once
- Activated by `ACM_ITEM_EXTRACTION_MODE=bulk` or automatic fallback when no DoclingDocument JSON

**Truncation protection**: TruncationError detection → cloud model retry, 30% output budget reservation

### SSE Streaming (PipelineEventBus)
- Backend: `open_notebook/extractors/pipeline_event_bus.py`
- SSE endpoints: `api/routers/v3_streaming.py`
- Frontend hook: `frontend/src/lib/hooks/useV3SSE.ts`
- Zustand store: `frontend/src/lib/stores/streamingStore.ts`
- Event categories: `extraction`, `ai`, `bulk`
- Key events: `extraction.started`, `extraction.docling_complete`, `extraction.complete`, `extraction.failed`, `ai.building_extracted`, `ai.building_saved`, `ai.save_started`, `ai.save_progress`, `ai.save_complete`

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
- `GET /api/sources/{source_id}/live-stats` -- Live extraction counters for job card polling

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
| `/observability-status` | Health check observability services |
| `/trace-inspect` | Inspect Langfuse traces for a source extraction |
| `/trace-cleanup` | Delete Langfuse traces by tag/name/date |
| `/debug-extraction` | Root-cause debug failed extraction |
| `/provider-costs` | Analyze costs by provider/model |
| `/graph-inspect` | Inspect LangGraph thread state |
| `/debug-pydantic` | Debug Pydantic validation failures |
| `/regenerate-diagrams` | Regenerate erdantic ER diagrams |
| `/benchmark-compare` | Compare benchmark results across models |
| `/prompt-test` | Test prompt template changes |

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
| `observability-ops.md` | `open_notebook/observability/**/*`, `scripts/observability/**/*` |

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

#### E36 Verification Team

The `e36-lead` agent orchestrates E2E verification, benchmarking, and auditing:

| Agent | Model | Role |
|-------|-------|------|
| `e36-lead` | sonnet | Pure orchestrator — delegates all work, manages state files |
| `e36-browser-tester` | sonnet | UI testing via agent-browser CLI |
| `e36-log-sentinel` | sonnet | Log monitoring during extraction runs |
| `e36-devils-advocate` | sonnet | Adversarial code/test review |
| `e36-bmad-scribe` | haiku | BMAD documentation updates |
| `e36-ux-auditor` | sonnet | Visual/responsive/a11y audit |

State files: `docs/sprint-artifacts/e36/` (task_plan.md, progress.md, findings.md)

#### Observability Agents

| Agent | Model | Role |
|-------|-------|------|
| `acm-observability-debugger` | sonnet | Root-cause extraction failures via trace analysis |
| `acm-trace-analyst` | sonnet | Bulk cost/performance analysis across runs |
| `acm-graph-inspector` | sonnet | LangGraph thread state inspection |
