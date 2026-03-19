# MCS12-Gap5: Wire extraction.* SSE Events to Main Pipeline
# Generated from MCS7 validation audit — 2026-03-19

**SP: 3 | Priority: P2 | Dependencies: MCS9 (SSE save events)**
**Audit ref: Pipeline Persistence Timing Audit — Gap 5 (extraction.* events never emitted)**
**Related commits: 5d560d06 (Live extraction UX)**

## Skills to Load

/langgraph-fundamentals — node event patterns
/sse-streaming — SSE event architecture
/frontend-design — extraction progress dashboard
/ui-ux-pro-max — overall extraction progress visualization
/uncodixfy — prevent generic progress bars
/planning-with-files — persistent markdown plan
/e2e-test — browser verification
/acm-observability — trace event flow
/verification-before-completion — verify events fire

---

## Problem Statement

The `PipelineEventBus` defines `extraction.started`, `extraction.provider_complete`, and `extraction.consensus_complete` event types. The SSE endpoint `/v3/stream/extraction/{op_id}` exists and listens for these events. But the main LangGraph extraction pipeline (`acm_extraction.py`) **never emits any `extraction.*` events**. The endpoint is dead.

The pipeline only emits `ai.*` events. There is no top-level progress indication that tells the frontend "extraction has started", "extraction is X% complete", or "extraction finished successfully".

---

## Key Files

**Read:**
- `open_notebook/extractors/pipeline_event_bus.py` — `extraction.*` event definitions
- `api/routers/v3_streaming.py` — `/v3/stream/extraction/{op_id}` endpoint
- `open_notebook/graphs/acm_extraction.py` — `extract_acm_from_source()` entry point (line 2887+)
- `frontend/src/lib/hooks/useV3SSE.ts` — SSE subscription

**Modify (Backend):**
- `open_notebook/graphs/acm_extraction.py` — emit `extraction.started` at graph entry, `extraction.complete` at end
- `open_notebook/extractors/pipeline_event_bus.py` — add `extraction.complete` event type (distinct from consensus)
- `commands/acm_commands.py` — emit `extraction.started` when command begins

**Modify (Frontend):**
- `frontend/src/lib/hooks/` — add `useExtractionStream` hook for top-level progress
- `frontend/src/components/acm/` — add extraction status banner/indicator
- `frontend/src/lib/stores/streamingStore.ts` — track overall extraction state

---

## Plan

### Phase 1: Backend — Emit Extraction Events
- [ ] In `extract_acm_from_source()`, emit `extraction.started` with source_id, page_count
- [ ] In `acm_commands.py:acm_extract_command()`, emit `extraction.started` when command begins
- [ ] Add `extraction.complete` event to pipeline_event_bus (records_saved, duration_ms, buildings_count)
- [ ] Emit `extraction.complete` in `save_records` node after successful save
- [ ] Emit `extraction.failed` on graph exception

### Phase 2: Frontend — Extraction Status Display
- [ ] Create `useExtractionStream` hook subscribing to `extraction` category
- [ ] Show extraction status banner: "Extraction started" → "Processing" → "Complete"
- [ ] Show overall timing and record count on completion
- [ ] Apply /ui-ux-pro-max + /uncodixfy — contextual progress, no generic spinners

### Phase 3: Verification
- [ ] Upload PDF, verify `/v3/stream/extraction/{op_id}` delivers events
- [ ] Verify `extraction.started` fires immediately on upload
- [ ] Verify `extraction.complete` fires after records saved
- [ ] Run /e2e-test for extraction status display
- [ ] Run /acm-observability to verify event timing

---

## Agent Strategy: Agent Team (Opus)

Create team `mcs12-extraction-events` with 3 agents:

| Agent | Role | Model | Tasks |
|-------|------|-------|-------|
| `backend-events` | Wire extraction.* events to pipeline + commands | opus | Phase 1 |
| `frontend-status` | Extraction status hook + UI with /ui-ux-pro-max | opus | Phase 2 |
| `verifier` | E2E tests + observability traces | opus | Phase 3 |

---

## Verification Checklist

- [ ] `/v3/stream/extraction/{op_id}` delivers events (no longer dead)
- [ ] `extraction.started` fires within 1s of extraction trigger
- [ ] `extraction.complete` fires after all records saved
- [ ] Frontend shows extraction status banner
- [ ] `/e2e-test` passes for extraction status display

---

## Commit Template

```
feat(streaming): wire extraction.* SSE events to main pipeline

- Emit extraction.started from acm_extract_command and graph entry
- Add extraction.complete event after save_records node
- Emit extraction.failed on graph exception
- /v3/stream/extraction/{op_id} endpoint now delivers real events
- Add useExtractionStream hook + status banner component
- MCS12 — Pipeline Persistence Timing Audit Gap 5

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
```
