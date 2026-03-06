# Observability Setup — Progress

## Session 1: 2026-03-06

### Completed
- [x] Audited all 3 observability tools (LangGraph Studio, LangSmith, Langfuse)
- [x] Inventoried all 13 open GitHub issues + 15 local issue files
- [x] Mapped each issue to which tool(s) help observe, validate, and fix it
- [x] Created findings.md with full head-to-head comparison
- [x] Created task_plan.md with phased rollout

### Key Decisions
- **Production**: Langfuse self-hosted only (data privacy for government data)
- **Development**: LangSmith + Langfuse + Studio (all three, complementary)
- **LangSmith free tier budget**: ~380 full extractions/month — sufficient for dev iteration

### Current State
- Langfuse: code exists, wired into acm_extraction + source_commands only
- LangSmith: zero code, just env vars needed
- Studio: langgraph.json exists, only acm_extraction registered

---

## Session 2: 2026-03-06 — Phase 2 Implementation

### Completed
- [x] Created `docker-compose.observability.yml` (Langfuse v3: PostgreSQL 17 + ClickHouse + Redis + MinIO + Worker + Web)
- [x] Wired Langfuse callbacks into all active graph invocation sites:
  - `api/routers/chat.py` — chat graph `.invoke()`
  - `api/routers/source_chat.py` — source_chat graph `.invoke()`
  - `api/routers/transformations.py` — transformation graph `.ainvoke()`
  - `api/routers/sources.py` — transformation graph `.ainvoke()` (insight creation)
  - `api/routers/search.py` — ask graph `.astream()` (both streaming + simple endpoints)
  - `api/routers/notes.py` — prompt graph `.ainvoke()` (note title generation)
- [x] Registered `supervisor` graph in `langgraph.json` (now 2 graphs: acm_extraction, supervisor)
- [x] Added `langgraph-cli[inmem]` to dev dependency-group in `pyproject.toml`
- [x] Updated `.env.example` with comprehensive observability docs
- [x] Ruff lint passes on all modified files

### Investigation Answers
- **LANGCHAIN_API_KEY vs LANGSMITH_API_KEY**: Same key. LangSmith settings page shows `LANGCHAIN_API_KEY`. No separate `LANGSMITH_API_KEY` needed.
- **LANGSMITH_PROJECT auto-creates**: Yes — first trace to a project name creates it automatically.
- **Checkpointed graphs in Studio**: `chat`, `source_chat`, `doc_search_graph`, `acm_analyst_graph` all compile with `MemorySaver` at module level. They import directly but would need studio entry wrappers to avoid side effects. Deferred to Phase 4.

### Files Modified
| File | Action |
|------|--------|
| `docker-compose.observability.yml` | CREATED |
| `api/routers/chat.py` | EDITED — Langfuse callbacks |
| `api/routers/source_chat.py` | EDITED — Langfuse callbacks |
| `api/routers/transformations.py` | EDITED — Langfuse callbacks |
| `api/routers/sources.py` | EDITED — Langfuse callbacks |
| `api/routers/search.py` | EDITED — Langfuse callbacks (2 sites) |
| `api/routers/notes.py` | EDITED — Langfuse callbacks |
| `langgraph.json` | EDITED — added supervisor graph |
| `pyproject.toml` | EDITED — added langgraph-cli to dev deps |
| `.env.example` | EDITED — observability docs |
| `docs/sprint-artifacts/observability/progress.md` | EDITED — this file |

### Verification Results
- [x] **7A — Import smoke test**: All 6 routers import cleanly, Langfuse handler creates successfully
- [x] **7B — Langfuse cloud**: `LANGFUSE_ENABLED=true` with cloud keys — handler creates, callbacks append, flush works
- [x] **7D — Langfuse self-hosted**: `docker compose -f docker-compose.yml -f docker-compose.observability.yml up -d` — all 7 containers healthy, `http://localhost:3000/api/public/health` returns `{"status":"OK","version":"3.155.1"}`
- [ ] **7C — LangSmith traces**: `LANGCHAIN_TRACING_V2=true` + key set — needs API running with real request to confirm
- [ ] **7E — LangGraph Studio**: `langgraph dev` deferred (needs API + DB running)

### Langfuse v3 Self-Hosted Architecture
Initial attempt with v2-style compose (just PostgreSQL + Langfuse) failed: Langfuse v3 requires ClickHouse.
Updated to official v3 architecture with 7 services:

| Service | Container | Port | Purpose |
|---------|-----------|------|---------|
| PostgreSQL 17 | acm-ai-langfuse-postgres | 5433 | User data, auth |
| ClickHouse | acm-ai-langfuse-clickhouse | 8123, 9002 | Trace storage |
| Redis 7 | acm-ai-langfuse-redis | 6379 | Queue/cache |
| MinIO | acm-ai-langfuse-minio | 9090, 9091 | S3-compatible events/media |
| MinIO init | acm-ai-langfuse-minio-init | — | One-shot bucket creation |
| Worker | acm-ai-langfuse-worker | 3030 | Background processing |
| Web UI | acm-ai-langfuse | 3000 | Dashboard |

### Files Modified (Updated)
| File | Action |
|------|--------|
| `docker-compose.observability.yml` | CREATED (Langfuse v3 full stack) |
| `.env.example.acm` | CREATED (ACM project-specific env template) |
| `api/routers/chat.py` | EDITED — Langfuse callbacks |
| `api/routers/source_chat.py` | EDITED — Langfuse callbacks |
| `api/routers/transformations.py` | EDITED — Langfuse callbacks |
| `api/routers/sources.py` | EDITED — Langfuse callbacks |
| `api/routers/search.py` | EDITED — Langfuse callbacks (2 sites) |
| `api/routers/notes.py` | EDITED — Langfuse callbacks |
| `langgraph.json` | EDITED — added supervisor graph |
| `pyproject.toml` | EDITED — added langgraph-cli to dev deps |
| `.env.example` | EDITED — observability docs, defaults to false |
| `.env` | EDITED — improved observability section comments |

### Next Steps
1. Start API + create account at `http://localhost:3000` for self-hosted keys
2. **LangGraph Studio**: `langgraph dev` to verify both graphs load
3. Phase 3: Use observability to fix complex issues (#100, #99, #84)

### Reboot Check
1. Last milestone: Phase 2 implementation + verification complete
2. Current task: Phase 2 done — ready for Phase 3
3. Blockers: None
4. Files modified: see table above
5. Next action: Visit http://localhost:3000 to create Langfuse self-hosted account + API keys

---

## Session 3: 2026-03-06 — Phase 2B: Fix LangGraph Studio + Enrich Traces

### Completed
- [x] **LangGraph Studio fix**: Documented `uv run langgraph dev` (not bare `langgraph dev`) in `.env`, `.env.example`, `.env.example.acm`, and CLAUDE.md
- [x] **Created `langfuse_tracing()` context manager** in `langfuse_config.py` — yields `(callbacks, metadata)`, auto-flushes on exit
- [x] **Created `merge_langfuse_into_config()` helper** — merges callbacks/metadata into RunnableConfig dict, no-op when disabled
- [x] **Enriched trace metadata in all 6 routers** — replaced inline boilerplate with context manager:
  - `chat.py` — `operation_type="chat"`
  - `source_chat.py` — passes real `source_id`, `operation_type="source_chat"`
  - `transformations.py` — passes `transformation_id` as source_id, `operation_type="transformation"`
  - `sources.py` — passes real `source_id`, `operation_type="insight"`
  - `search.py` (2 sites) — `operation_type="search"`, extra_tags `["streaming"]` / `["simple"]`
  - `notes.py` — `operation_type="note_title"`
- [x] **Context7 research** — confirmed Langfuse v3 metadata pattern: `langfuse_user_id`, `langfuse_session_id`, `langfuse_tags` in metadata dict
- [x] **CLAUDE.md updated** — added LangGraph Studio command, Observability architecture section
- [x] **Ruff lint passes** on all modified files
- [x] **Import smoke test passes** — all routers + new helpers import cleanly
- [x] **Backward compatibility verified** — with `LANGFUSE_ENABLED=false`, context manager yields empty callbacks and `merge_langfuse_into_config` returns config unchanged

### Context7 Findings (Langfuse Best Practices)
- `langfuse_session_id` in metadata groups traces by session (already implemented in `build_langfuse_metadata`)
- `langfuse_user_id` in metadata tracks user identity (already implemented)
- `langfuse_tags` in metadata enables tag-based filtering (now enriched with operation_type)
- `run_name` in config names individual spans (available for future use)
- Cost tracking is automatic when Langfuse receives model/token data from LangChain callbacks

### Files Modified
| File | Action |
|------|--------|
| `open_notebook/observability/langfuse_config.py` | EDITED — added `langfuse_tracing()` + `merge_langfuse_into_config()` |
| `api/routers/chat.py` | EDITED — use context manager |
| `api/routers/source_chat.py` | EDITED — use context manager |
| `api/routers/transformations.py` | EDITED — use context manager |
| `api/routers/sources.py` | EDITED — use context manager |
| `api/routers/search.py` | EDITED — use context manager (2 sites) |
| `api/routers/notes.py` | EDITED — use context manager |
| `.env` | EDITED — fix langgraph dev command |
| `.env.example` | EDITED — fix langgraph dev command |
| `.env.example.acm` | EDITED — fix langgraph dev command |
| `CLAUDE.md` | EDITED — LangGraph Studio command + Observability section |
| `docs/sprint-artifacts/observability/progress.md` | EDITED — this file |

### Key Decision: LangGraph Studio Cloud UI Dropped
- Studio visual UI now requires LangSmith cloud session (no standalone desktop app)
- Conflicts with data-privacy requirement for Victorian Government data
- **Replacement**: LangGraph local API at `:2024` (Swagger UI at `/docs`) + Langfuse traces + LangSmith playground
- See findings.md Section 5 for full mitigation assessment

### Files Modified (Updated)
| File | Action |
|------|--------|
| `open_notebook/observability/langfuse_config.py` | EDITED — added `langfuse_tracing()` + `merge_langfuse_into_config()` |
| `api/routers/chat.py` | EDITED — use context manager |
| `api/routers/source_chat.py` | EDITED — use context manager |
| `api/routers/transformations.py` | EDITED — use context manager |
| `api/routers/sources.py` | EDITED — use context manager |
| `api/routers/search.py` | EDITED — use context manager (2 sites) |
| `api/routers/notes.py` | EDITED — use context manager |
| `.env` | EDITED — LangGraph dev server docs |
| `.env.example` | EDITED — LangGraph dev server docs |
| `.env.example.acm` | EDITED — LangGraph dev server docs |
| `CLAUDE.md` | EDITED — Observability stack guide, when-to-use-which |
| `docs/sprint-artifacts/observability/findings.md` | EDITED — Studio dropped, mitigation table |
| `docs/sprint-artifacts/observability/progress.md` | EDITED — this file |

### Next Steps
1. Phase 3: Use observability to debug complex issues (#100, #99, #84)
2. Start API + trigger chat/transformation to verify enriched traces in Langfuse dashboard
3. `uv run langgraph dev` to access local API Swagger UI for graph state debugging
