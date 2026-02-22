# Findings: ACM-AI Project — Feature Complete

## Last Updated: 2026-02-22
## Status: Feature Complete — All 112 stories done, 10 archived

---

## Final Sprint Reconciliation (2026-02-22)

### Discovery: 7 Stories Already Implemented
All 7 "remaining" stories were implemented in a prior Ralph sprint but tracking artifacts were never updated:
- E10-S1: Navigation config with ACM mode flags (frontend/src/config/navigation.ts)
- E9-S3: Bulk operations API + frontend (api/routers/source_bulk.py, BulkActions.tsx)
- E12-S2: Stage model configuration (ExtractionStageModels.tsx)
- E12-S3: Processing config with presets (migrations/30.surrealql)
- E12-S4: BAR field schema config UI (settings/field-schema/page.tsx)
- E13-S2: Knowledge graph API with dagre layout (api/routers/graph.py)
- E13-S3: React Flow interactive graph (KnowledgeGraph.tsx, graph-nodes/)

### Code Review Results (from .ralph/@review_issues.md)
12 issues found during adversarial review:
- **8 resolved**: Batch size limit, undo-delete errors, graph error exposure, edge set injection, stage model reset safety, partial PUT update, render-phase state, dialog reset
- **3 deferred**: DocumentActions dropdown gap, runtime ACM toggle, test coverage
- **1 not-a-bug**: Navigation useMemo dependencies

### Pre-existing Test Failure
`test_acm_chat_context.py::test_format_acm_context_with_records` — AttributeError: module 'open_notebook.graphs' has no attribute 'source_chat'. This is a module import issue, not a regression from any recent work.

---

## Deferred Items

| Item | Severity | Notes |
|------|----------|-------|
| Test coverage for new endpoints | Major | source_bulk.py, graph.py, settings stage models |
| DocumentActions dropdown | Minor | Functionality exists in BulkActions.tsx |
| Runtime ACM mode toggle | Minor | Env-var control works correctly |
| Favicon conversion | Minor | Needs image processing tools |
| source_chat module import | Minor | Pre-existing test infrastructure issue |

---

## Architecture Summary (as of feature-complete)

### Backend (Python/FastAPI)
- 30+ migrations (SurrealDB)
- 15+ API routers (acm, sources, settings, graph, a2a, agui, etc.)
- LangGraph extraction pipeline with AG-UI event relay
- A2A agent card at /.well-known/agent.json
- 40+ AI models in MODEL_CATALOG (Ollama, Anthropic, OpenAI, OpenRouter)

### Frontend (Next.js 15 / React 19)
- AG Grid with column visibility, bulk actions, field schema config
- React Flow knowledge graph visualization
- CopilotKit chat integration with AG-UI protocol
- Extraction progress panel with reasoning display + tool call feed
- Settings pages: models, processing, field-schema, extraction methods
- Dashboard home with ACM statistics
- Document library with bulk operations

---

## Historical Findings

### Bug Triage (2026-02-21)
- Model ID pattern matching was fundamentally broken (testing SurrealDB record IDs)
- Fixed with model capabilities system (migration 20)
- Anthropic model ID typo: `claude-haiku-3-5-20241022` → `claude-3-5-haiku-20241022`

### Sprint Artifact Location (2026-02-21)
- `docs/sprint-artifacts/` is canonical (not `_bmad-output/implementation-artifacts/`)
- `_bmad/bmm/config.yaml` sets `implementation_artifacts` to `docs/sprint-artifacts`
