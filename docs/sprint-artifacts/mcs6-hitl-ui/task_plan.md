# MCS6: HITL Mapping Confirmation UI — Task Plan

## Architecture Decision

**LangGraph `interrupt()` + asyncio.Event hybrid:**
- Add `MemorySaver` checkpointer to extraction graph
- `schema_inference_node` calls `interrupt()` when LLM confidence < 0.8
- `extract_acm_from_source()` detects `__interrupt__`, emits SSE, waits on asyncio.Event
- Resume API endpoint receives user decision, signals the Event, graph resumes via `Command(resume=...)`
- Frontend `ColumnMappingDialog` shows mapping table, submits decision

## Tasks

- [x] 1. Create `open_notebook/extractors/hitl_registry.py` — asyncio.Event wait/signal registry
- [x] 2. Add SSE types: `SchemaMappingReviewEvent` in pipeline_event_bus.py + frontend types
- [x] 3. Add `interrupt()` in `schema_inference_node` when confidence < 0.8
- [x] 4. Add `MemorySaver` checkpointer + HITL handling in `extract_acm_from_source()`
- [x] 5. Add `POST /api/acm/hitl/resume` endpoint
- [x] 6. Build `ColumnMappingDialog.tsx` component
- [x] 7. Create `useColumnMapping.ts` hook
- [x] 8. Write backend tests: `tests/test_hitl_schema_inference.py` (21 tests, all pass)
- [x] 9. Run full verification: build + pytest + ruff — ALL PASS

## Key Files

| Action | File |
|--------|------|
| CREATE | `open_notebook/extractors/hitl_registry.py` |
| CREATE | `frontend/src/components/acm/ColumnMappingDialog.tsx` |
| CREATE | `frontend/src/lib/hooks/useColumnMapping.ts` |
| CREATE | `tests/test_hitl_schema_inference.py` |
| MODIFY | `open_notebook/extractors/schema_inference.py` |
| MODIFY | `open_notebook/graphs/acm_extraction.py` |
| MODIFY | `open_notebook/extractors/pipeline_event_bus.py` |
| MODIFY | `api/routers/v3_streaming.py` |
| MODIFY | `api/routers/format_profiles.py` |
| MODIFY | `frontend/src/lib/types/v3-streaming.ts` |
| MODIFY | `frontend/src/lib/hooks/useV3SSE.ts` |
| MODIFY | `frontend/src/lib/stores/streamingStore.ts` |

## Verification Results

- `uv run ruff check .` — All checks passed
- `cd frontend && npm run build` — Build successful
- `uv run pytest tests/test_hitl_schema_inference.py tests/test_schema_inference.py -v` — 45 passed
