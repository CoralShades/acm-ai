# E17-S1: AG-UI Extraction Pipeline Endpoint

## Story Info
- **Epic**: E17 — Live Extraction Intelligence
- **Status**: drafted
- **Priority**: P0
- **Size**: M (Medium)
- **Created**: 2026-02-22
- **Dependencies**: None
- **Blocks**: E17-S2, E17-S3, E17-S4

## Description

Create an AG-UI compliant SSE endpoint for the extraction pipeline. The extraction runs in the surreal-commands worker process, not the API process. A SurrealDB event relay bridges the gap: AGUIEventEmitter in the worker writes events to an `agui_events` table, and a FastAPI SSE endpoint polls and streams them.

## Acceptance Criteria

- [ ] `GET /api/agui/extraction/{command_id}/stream` returns AG-UI compliant SSE
- [ ] Events: RunStarted, StepStarted/Finished per node, StateDelta, ToolCallStart/End, RunFinished/RunError
- [ ] Existing SSE at `/api/acm/extraction-progress/` unchanged
- [ ] 500ms poll interval, heartbeat every 15s
- [ ] Stream auto-closes on RunFinished/RunError

## File Changes

| File | Action | Purpose |
|------|--------|---------|
| `open_notebook/extractors/agui_event_emitter.py` | CREATE | AGUIEventEmitter class — emits AG-UI events to SurrealDB |
| `api/routers/agui_extraction.py` | CREATE | FastAPI SSE endpoint polling agui_events table |
| `migrations/22.surrealql` | CREATE | agui_events table with command_id + sequence index |
| `migrations/22_down.surrealql` | CREATE | Rollback migration |
| `open_notebook/graphs/acm_extraction.py` | MODIFY | Add agui_emitter to ExtractionState; emit events in each node |
| `open_notebook/database/async_migrate.py` | MODIFY | Register migration 22 |
| `api/main.py` | MODIFY | Register agui_extraction router |

## Technical Notes

- AGUIEventEmitter follows the same fire-and-forget pattern as PipelineLogger._schedule_persist()
- SurrealDB relay adds ~500ms latency (acceptable for observability)
- Node-to-event mapping: extract_metadata→StepStarted/Finished, extract→ToolCallStart/End, validate→StepStarted/Finished, etc.
