# MCS9-Gap1+6: Add SSE Events to Save Node + Fix Terminal Event Timing
# Generated from MCS7 validation audit — 2026-03-19

**SP: 5 | Priority: P0 | Dependencies: MCS8 (ghost save fix)**
**Audit ref: Pipeline Persistence Timing Audit — Gap 1 (save node blind) + Gap 6 (race condition)**
**Related commits: 5d560d06 (Live extraction UX), fa1ff9a4 (validation)**

## Skills to Load

/langgraph-fundamentals — LangGraph node patterns for event emission
/planning-with-files — persistent markdown plan
/frontend-design — SSE-driven UI progress indicators
/ui-ux-pro-max — progress bar, loading states, completion animations
/uncodixfy — prevent generic AI UI patterns in the progress display
/sse-streaming — SSE implementation best practices
/e2e-test — browser verification of real-time updates
/acm-observability — trace SSE event flow
/verification-before-completion — verify events fire at correct times

---

## Problem Statement

The `save_records` node (`acm_extraction.py:2625`) emits **zero SSE events**. The frontend receives `ai.validation_complete` (terminal event) 4 nodes BEFORE records are saved to DB. This creates a race condition: frontend closes the SSE stream and refetches, but records don't exist yet.

### Audit Evidence

```
validate [ai.validation_complete emitted here — TERMINAL]
  → deduplicate (no events)
  → recover_no_access (no events)
  → save (no events — frontend BLIND, records saved HERE)
  → END
```

The frontend's `useV3BuildingStream` hook closes the SSE connection on `ai.validation_complete` and invalidates queries. But records aren't in DB until the `save` node completes — potentially seconds later for large documents.

---

## Key Files

**Read:**
- `open_notebook/extractors/pipeline_event_bus.py` — event types + PipelineEventBus
- `open_notebook/graphs/acm_extraction.py` — lines 2625-2828 (`save_records` node), 2832-2880 (graph wiring)
- `api/routers/v3_streaming.py` — SSE endpoints
- `frontend/src/lib/hooks/useV3SSE.ts` — generic SSE hook
- `frontend/src/lib/hooks/useV3BuildingStream.ts` — building extraction progress hook
- `frontend/src/lib/types/v3-streaming.ts` — event envelope types

**Modify (Backend):**
- `open_notebook/extractors/pipeline_event_bus.py` — add `ai.save_started`, `ai.save_progress`, `ai.save_complete` events
- `open_notebook/graphs/acm_extraction.py` — emit events in `save_records`, move terminal event to AFTER save
- `open_notebook/graphs/acm_extraction.py` — emit events in `deduplicate` and `recover_no_access` nodes

**Modify (Frontend):**
- `frontend/src/lib/hooks/useV3BuildingStream.ts` — handle new save events, move stream close to `ai.save_complete`
- `frontend/src/lib/types/v3-streaming.ts` — add new event type definitions
- `frontend/src/components/acm/` — progress UI for save phase

---

## Plan

### Phase 1: Define New SSE Events (Backend)
- [ ] Add to `pipeline_event_bus.py`:
  - `ai.save_started` — `{total_records, total_sections}`
  - `ai.save_progress` — `{saved, total, current_building}`
  - `ai.save_complete` — `{records_saved, sections_saved, duration_ms}` (**new terminal event**)
  - `ai.dedup_complete` — `{merged, unique, total_before}`
- [ ] Change `ai.validation_complete` from terminal to non-terminal
- [ ] Set `ai.save_complete` as the new terminal event for the `ai` category

### Phase 2: Emit Events in Graph Nodes (Backend)
- [ ] `deduplicate_records` node — emit `ai.dedup_complete` after merging
- [ ] `save_records` node — emit `ai.save_started` before loop
- [ ] `save_records` node — emit `ai.save_progress` every N records (batch of 10)
- [ ] `save_records` node — emit `ai.save_complete` after all saves done

### Phase 3: Update Frontend Event Handling
- [ ] `useV3BuildingStream.ts` — handle `ai.save_started` (show "Saving records..." state)
- [ ] `useV3BuildingStream.ts` — handle `ai.save_progress` (update progress bar)
- [ ] `useV3BuildingStream.ts` — handle `ai.save_complete` (invalidate queries, close stream)
- [ ] Remove `ai.validation_complete` as stream-close trigger
- [ ] Add save progress UI component (progress bar with record count)

### Phase 4: Fix Premature Query Invalidation (Gap 3)
- [ ] Remove items query invalidation from `ai.building_extracted` handler (items don't exist yet)
- [ ] Add items query invalidation to `ai.save_complete` handler instead
- [ ] Keep building status updates on `ai.building_extracted` (building IS in DB at that point)

### Phase 5: Verification
- [ ] Upload a PDF and verify SSE events fire in correct order
- [ ] Verify `ai.save_complete` fires AFTER records are queryable in DB
- [ ] Verify frontend progress bar shows save progress
- [ ] Verify no race condition between stream close and query refetch
- [ ] Run /e2e-test for full extraction → display flow
- [ ] Run /acm-observability to verify event timing

---

## Agent Strategy: Agent Team (Opus)

Create team `mcs9-sse-save` with 3 agents:

| Agent | Role | Model | Tasks |
|-------|------|-------|-------|
| `backend-events` | Add SSE events to pipeline_event_bus + graph nodes | opus | Phase 1-2 |
| `frontend-ux` | Update hooks, types, progress UI | opus | Phase 3-4 |
| `e2e-verifier` | Browser tests + observability traces | opus | Phase 5 |

---

## Context7 Directives

Fetch latest docs for:
- `langgraph` — node event emission patterns
- `react-query` / `@tanstack/react-query` — query invalidation timing

---

## Verification Checklist

- [ ] `ai.save_started` event fires before record save loop
- [ ] `ai.save_progress` events fire during save (batched every 10 records)
- [ ] `ai.save_complete` fires after ALL records saved — is the new terminal event
- [ ] `ai.validation_complete` is no longer terminal
- [ ] Frontend shows save progress with record count
- [ ] No query invalidation until `ai.save_complete`
- [ ] No race condition: records exist in DB before frontend queries
- [ ] `/e2e-test` passes: upload PDF → see buildings → see progress → see records
- [ ] `/acm-observability` traces show correct event sequence

---

## Commit Template

```
feat(streaming): add SSE events to save node and fix terminal event race condition

- Add ai.save_started, ai.save_progress, ai.save_complete events
- Move terminal event from ai.validation_complete to ai.save_complete
- Fix premature query invalidation (items query fired before items exist)
- Add save progress UI with record count and progress bar
- MCS9 — Pipeline Persistence Timing Audit Gap 1 + Gap 6

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
```
