# Story E15-S1: Extraction Log Panel in Document Library

**Epic:** E15 — Extraction Monitor & Live Logging UI
**Priority:** P0
**Status:** backlog
**Change Proposal:** SCP-20260220 (2026-02-20)

---

## User Story

**As a** compliance officer reviewing document processing,
**I want to** click any document in the library and see the full extraction log with stage-by-stage progress,
**So that** I can understand exactly what the AI extracted, identify failures, and retry without re-uploading.

---

## Background

E1-S21 (Extraction Pipeline Observability) fully implemented the backend SSE streaming, PipelineLogger, and frontend log components (`ExtractionProgressPanel`, `ExtractionLogStream`, `StageProgressPill`, `use-extraction-progress.ts`). These components are currently only surfaced during the active upload wizard flow. This story wires them into the Document Library view.

**Existing infrastructure (no new backend work needed):**
- `api/routers/extraction_events.py` — SSE at `/api/acm/extraction-progress/{commandId}/stream`
- `api/routers/extraction_events.py` — REST fallback `GET /api/acm/extraction-progress/{commandId}`
- `open_notebook/extractors/pipeline_events.py` — StageId, StageState, PipelineRunState
- `frontend/src/components/acm/ExtractionProgressPanel.tsx`
- `frontend/src/components/acm/ExtractionLogStream.tsx`
- `frontend/src/components/acm/StageProgressPill.tsx`
- `frontend/src/lib/hooks/use-extraction-progress.ts`

---

## Acceptance Criteria

- [ ] Each document row in the Document Library (Documents page / Source list) has an expand/collapse chevron
- [ ] Clicking the chevron expands an inline panel showing `ExtractionProgressPanel`
- [ ] The panel is populated via `commandId` stored on the source record
- [ ] For **completed** documents: loads historical log from REST endpoint (polling fallback)
- [ ] For **active/in-progress** documents: connects live SSE stream
- [ ] Stage pills show all 7 stages: `STRUCTURE`, `PREFLIGHT`, `ORCHESTRATOR`, `EXTRACT`, `VALIDATE`, `CORRECT`, `STORE`
- [ ] Log terminal is scrollable, monospace, with Copy All button
- [ ] Failed/partial extractions show a **Retry Extraction** button
- [ ] Panel can be collapsed by clicking chevron again
- [ ] Works for both success and failure states
- [ ] Accessible: keyboard operable (Enter/Space to expand, Escape to collapse)
- [ ] Only one panel open at a time (expanding another collapses previous)

---

## Technical Notes

### commandId retrieval
The `Source` record in SurrealDB stores the `command_id` of the extraction job. The frontend must pass this to `use-extraction-progress.ts`.

Check `api/routers/sources.py` and `open_notebook/domain/source.py` for the `command_id` / `job_id` field — may need to be exposed in `SourceResponse`.

### Historical log fetch
For completed documents, call:
```
GET /api/acm/extraction-progress/{commandId}
```
This returns `{ status, state: PipelineRunState, log_entries }` from the `extraction_progress` SurrealDB table.

### Component reuse
Import and mount `ExtractionProgressPanel` directly. Pass `commandId` as prop — the panel handles SSE vs polling logic internally via `use-extraction-progress.ts`.

---

## Key Files to Modify

| File | Change |
|------|--------|
| `frontend/src/components/documents/DocumentRow.tsx` (or equivalent) | Add expand chevron + panel mount |
| `frontend/src/lib/types/source.ts` | Ensure `commandId` / `jobId` exposed |
| `api/models.py` | Expose `command_id` in `SourceResponse` if not already |

---

## Dependencies

- **Requires:** E1-S21 (done ✓), E9-S1 (done ✓)
- **Blocks:** E15-S2

---

## Estimated Effort

S (Small) — All backend infrastructure exists. Frontend is primarily wiring existing components into an existing list view.
