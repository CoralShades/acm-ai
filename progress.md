# Sprint Progress Log — MCS Series (2026-03-18 to 2026-03-19)

## MCS1-MCS7: Multi-Consultant Format Adaptability (2026-03-18)

### Completed Stories

| Story | Commit | Summary |
|-------|--------|---------|
| SAMP→ARA rename | 0febe5f9, 513790dd | Complete terminology rename across codebase |
| MCS1 — Detector rename/fix | 35abe382 | ClutchDetector→PipeTableDetector, broken import fixed |
| MCS2 — Schema inference node | 167f0c43 | LangGraph node for auto column-mapping from PDF headers |
| MCS3 — Format profile registry | 881f04f1 | SurrealDB cache for consultant column mappings |
| MCS4 — Adaptive row segmenter | 6ab5abb3 | Row segmenter adapts to InferredSchema |
| MCS5 — Format-agnostic prompts | cd5f919b | Extraction prompts use dynamic field lists |
| MCS6 — HITL mapping UI | 80267917 | Confirmation dialog for low-confidence schema inference |
| MCS7 — 3-format validation | fa1ff9a4 | 4 PDFs validated, 246 records, 3 consultant formats |
| Live extraction UX | 5d560d06 | SSE streaming, job lifecycle, real-time building display |
| Prompt-pack docs | 14d188dc | 6 post-validation fix prompts from MCS7 audit |

### MCS7 Validation Results
| Source | Format | Records | Target | Status |
|--------|--------|---------|--------|--------|
| Broadmeadows | Standard DET | 32 | 31 | PASS |
| Alexander | ARA/Prensa | 95 | ≥36 | PASS |
| Clutch_Alexander | Pipe-table/Greencap | 90 | N/A | PASS |
| Clutch_BM_2 | Pipe-table/Greencap | 29 | N/A | PASS |

---

## MCS8-MCS10: Pipeline Persistence Timing Fixes (2026-03-19)

### MCS8 — Ghost Save Fix (DONE)
- Commit: 31ede390
- Root cause: SurrealDB Python client auto-parses `"table:id"` strings as RecordIDs, causing TYPE mismatch errors that base.py swallowed silently
- Fixed `repo_create()` to raise on non-dict results (not swallow)
- Removed 5 MCS7 workarounds from acm_extraction.py (query-back hacks, null FKs, disabled checkpointer)
- Re-enabled `MemorySaver()` LangGraph checkpointer with serializable state

### MCS9 — SSE Save Events (IN PROGRESS)
- Prompt pack: `docs/sprint-artifacts/prompt-packs/2026-03-19-mcs9-sse-save-events-realtime.md`
- Adding: `ai.save_started`, `ai.save_progress`, `ai.save_complete` events to `save_records` node
- Moving terminal event from `ai.validation_complete` → `ai.save_complete`
- Frontend: `useV3BuildingStream` to close stream and invalidate queries on `ai.save_complete`

### MCS10 — Building Query Invalidation Fix (DONE)
- Buildings query now invalidated on `ai.building_extracted` (buildings ARE in DB at that point)
- Items query deferred to `ai.save_complete` (items don't exist until after save)
- Added `'saving'` to `BuildingStreamStatus` union type
- Wired `ai.save_progress.current_building` to per-building save badge
- Updated 3 `Record<BuildingStreamStatus>` maps (source/[id], BuildingSidebar)
- All tests pass: 32/33 E2E (1 pre-existing), frontend build clean

### Pipeline Persistence Timing Audit — 6 Gaps
| Gap | Pack | Priority | Status |
|-----|------|----------|--------|
| Ghost save (base.py) | MCS8 | P0 | Done |
| Terminal event race (save node blind) | MCS9 | P0 | In Progress |
| Buildings query too late | MCS10 | P1 | Done |
| Items query too early | MCS10 | P1 | Done |
| building_record_id FK always NULL | MCS11 | P1 | Backlog |
| extraction.* dead SSE endpoint | MCS12 | P2 | Done |
| schema_inference DocumentMeta bug | MCS13 | P1 | Backlog |

---

# MCS11 (Jobs/Source Unification) Progress Log

## Session 1: 2026-03-19

### 01:00 — MCS10 Implementation Complete
- Fixed buildings query invalidation timing (Gap 2: `ai.building_extracted`)
- Fixed items query deferred to `ai.save_complete` (Gap 3)
- Added `'saving'` status to `BuildingStreamStatus` union
- Wired `ai.save_progress.current_building` to per-building save badge
- Updated 3 `Record<BuildingStreamStatus>` maps (source/[id], BuildingSidebar)
- All tests pass: 32/33 E2E (1 pre-existing), frontend build clean

### 01:30 — Visual Audit Started
- Took screenshots of both pages with same source data
- Discovered Buildings tab "No Rows To Show" bug on `/jobs/[id]`
- Root cause: V3 `building_record` table empty for old pipeline extractions
- `useBuildings` → V3 API → 0 results, but legacy API → 2 buildings

### 02:00 — Comprehensive Feature Audit
- Spawned Explore agent for full code analysis of both pages
- Produced 15-category feature comparison matrix
- Identified 7 P0/P1 feature gaps on the primary jobs page
- Documented in findings.md

### 02:15 — Buildings Bug Fixed (Quick Win)
- Created `JobBuildingResponse` interface in `acm.ts`
- Added `acmApi.listJobBuildings()` — adapts legacy API to `BuildingRecord` shape
- Created `useJobBuildings.ts` hook
- Updated `/jobs/[id]` page to try V3 first, fall back to legacy
- **Verified via browser**: Buildings tab now shows "1 to 2 of 2" with "Broadmeadows Poli..."
- Frontend build passes

### 02:30 — Planning Phase
- Created task_plan.md with 6 phases (SP 13 total)
- Created findings.md with audit results
- Created progress.md (this file)
- Ready for user review before implementation

## MCS12 — Extraction Events SSE Wiring (DONE — 2026-03-20)

### Backend
- Added `ExtractionCompleteEvent` + `ExtractionFailedEvent` to `pipeline_event_bus.py`
- Emit `extraction.started` from `acm_commands.py` (instant) and `acm_extraction.py` (with page count)
- Emit `extraction.complete` after `save_records` node with records_saved, buildings_count, duration_ms
- Emit `extraction.failed` on all error paths (timeout, pipeline failure, exception) with stage info
- Added both to `_TERMINAL_EVENT_TYPES` in `v3_streaming.py`
- `/v3/stream/extraction/{op_id}` endpoint now delivers real events

### Frontend
- Created `useExtractionStream` hook — wraps `useV3SSE` with typed extraction phase state machine
- Created `ExtractionStatusBanner` — compact status banner with phase-specific icons, metrics, auto-dismiss
- Integrated on `/jobs/[id]` below `JobDetailHeader`

### Files Modified
| File | Change |
|------|--------|
| `open_notebook/extractors/pipeline_event_bus.py` | +2 event types (ExtractionComplete, ExtractionFailed) |
| `api/routers/v3_streaming.py` | +2 terminal event types |
| `open_notebook/graphs/acm_extraction.py` | +6 imports, emit started/complete/failed |
| `commands/acm_commands.py` | +5 imports, emit started/failed on all paths |
| `frontend/src/lib/hooks/useExtractionStream.ts` | NEW — extraction SSE hook |
| `frontend/src/components/jobs/ExtractionStatusBanner.tsx` | NEW — status banner |
| `frontend/src/app/(dashboard)/jobs/[id]/page.tsx` | +banner integration |
| `frontend/src/lib/types/v3-streaming.ts` | +2 payload interfaces |

---

## Next Steps
- [ ] User reviews and approves plan
- [ ] Phase 1: Wire SSE streaming into /jobs/[id] (SP 3)
- [ ] Phase 2: Add bulk operations to ACM Records tab (SP 3)
- [ ] Phase 3: Search, filter, grid enhancements (SP 2)
- [ ] Phase 4: Job card status on /jobs list (SP 2)
- [ ] Phase 5: Validation error display (SP 2)
- [ ] Phase 6: Verification & polish (SP 1)
