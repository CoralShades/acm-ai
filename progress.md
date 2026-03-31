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

---

## UX Mega-Pack (2026-03-20)

Three interconnected UX bugs fixed as a single pack.

### Bug 1: Upload Dialog -- Async Upload Fix (DONE)
- `api/routers/sources.py`: Force `async_processing=True` for uploads, set `review_status='extracting'`
- `commands/acm_commands.py`: Set `review_status='pending_review'` on all terminal paths
- `frontend/src/components/sources/QuickUploadDialog.tsx`: `async_processing: true`, navigate to `/jobs/{id}/extract`
- `frontend/src/components/acm/UploadWizard.tsx`: Same fix
- **review_status lifecycle**: `extracting` -> `pending_review` (set on all terminal paths in acm_commands.py)

### Bug 2: Extract Page -- 3-Panel Progressive Layout (DONE)
- `frontend/src/app/(dashboard)/jobs/[id]/extract/page.tsx`: Rebuilt with 3-panel layout
- NEW: `frontend/src/components/acm/DoclingTablesPanel.tsx` -- raw Docling table cards
- NEW: `frontend/src/components/acm/BuildingsProgressPanel.tsx` -- live building list during extraction
- NEW: `frontend/src/components/acm/LiveRecordsPanel.tsx` -- per-building records table (live)
- `open_notebook/extractors/pipeline_event_bus.py`: New events (`extraction.docling_complete`, `ai.building_saved`)
- `open_notebook/graphs/acm_extraction.py`: Grouped save by building

### Bug 3: Job Card -- Live Dashboard Counters (DONE)
- `frontend/src/components/jobs/JobCard.tsx`: Live counters, elapsed timer, site/consultant names
- NEW: `frontend/src/lib/hooks/useLiveStats.ts` -- polls `GET /api/sources/{id}/live-stats`
- `api/routers/sources.py`: New `/sources/{source_id}/live-stats` endpoint, enriched source list
- `api/models.py`: Added `tables_count`, `records_count`, `site_name`, `consultant_name` to `SourceListResponse`
- `frontend/src/lib/types/api.ts`: Matching TS type additions

### New API Endpoint
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/sources/{source_id}/live-stats` | Lightweight counters for job card polling |

Response: `{ tables_count, buildings_count, records_count, site_name, consultant_name }`

### New SSE Events
| Event | Emitted By | Payload |
|-------|-----------|---------|
| `extraction.docling_complete` | pipeline_event_bus | Docling table extraction finished |
| `ai.building_saved` | pipeline_event_bus | Building record saved to DB |

---

## Pipeline Fix Round: E2E Test Findings (2026-03-20)

Live E2E test with Clutch_Broadmeadows.pdf produced 42 records but surfaced 8 issues.
All fixes applied during test session by parallel agent.

### Errors Found & Fixed

| # | Error | Severity | Fix |
|---|-------|----------|-----|
| 1 | page_start int_type Pydantic error | HIGH | BeforeValidator coercion on int fields |
| 2 | RecordID serialization warning | MEDIUM | Convert RecordID to str in base.py setattr loop |
| 3 | sample_result enum mismatch (78 warnings) | MEDIUM | Expanded enum + synonym mapping |
| 4 | area_type Internal/External rejected (16) | LOW | Added SF picklist values to allowed set |
| 5 | friability "-" warning (10) | LOW | Added dash to friability map |
| 6 | Row extraction failures (3/44) | LOW | Added footer row detection to segmenter |
| 7 | Schema inference invalid response | LOW | Cascade from Error 1 (page_start coercion) |
| 8 | live-stats returns zeros | HIGH | type::thing() cast for SurrealDB record ref comparison |

### Test Results
- **PDF**: Clutch_Broadmeadows.pdf
- **Records**: 42 extracted, 1 building, 9 tables
- **Model**: ollama/llama3.1:8b on RTX 4090 (CUDA 12.6)
- **Pipeline time**: 291s (4m 51s)
- **E2E time**: 424s (7m 4s)
- **Report**: `docs/sprint-artifacts/e2e-evidence/live/final-test-report.md`

---

## Pipeline Accuracy Fixes (2026-03-20 — 2026-03-21)

Three phases of targeted accuracy improvements following live E2E test findings.

### Phase 1: Over-extraction & False Validation Warnings (DONE)

- **Commit**: 1c6026d5
- **Row segmenter header filter**: Added `_is_header_row()` with 37 known column header texts; multi-page table boundaries no longer produce duplicate header records
- **Dedup key normalization**: Strip + whitespace collapse on `product`, `location`, `sample_no` merges near-duplicate records with trivial spacing differences
- **Schema inference fallback parser**: Added handling for flat dict and bare list LLM responses; previously these were discarded entirely
- **SF Picklist validator — needs_user_review routing**: `needs_user_review` issues (Not Sampled, No Access, Unknown) now route to non-blocking `chain_warnings` instead of `all_issues`; eliminates 79 false validation failures per extraction run
- **"Unknown" added to `_LEGACY_VALUES`** in SF picklist validator; no longer triggers validation failure

### Phase 2: Chat System Fixes (DONE)

- **Commit**: dfaf91ee
- **Query/Edit toggle on jobs page**: Added mode toggle to jobs page chat sidebar — SmartChatPanel (Query mode) and JobCrudChatPanel (Edit mode) on both desktop sidebar and mobile drawer
- **CRUD fallback query fix**: `risk_status` renamed to `sample_result` in all `crud_tools.py` fallback queries; added "positive" keyword matching for high-risk queries

- **Commit**: aded56d2
- **SmartChatPanel infinite re-render fix**: Memoized `useCopilotReadable` value object via `useMemo` to break the re-render loop
- **SmartChatErrorBoundary**: Isolates CopilotKit errors so crashes do not take down the entire jobs page
- **Removed problematic hooks**: `useCopilotChatSuggestions` and `useCoAgentStateRender` triggered AG-UI `TEXT_MESSAGE_CONTENT` auto-request errors on connection; removed from SmartChatPanel

### Phase 3: Package Upgrades (DONE)

- **Python packages** (applied at runtime): `ag-ui-langgraph` 0.0.25→0.0.27, `copilotkit` 0.1.78→0.1.81, `ag-ui-protocol` 0.1.11→0.1.14
- **Frontend packages**: `@copilotkit/*` pinned at v1.51.3 — v1.54.0 evaluated and rejected due to breaking API changes

### Benchmark Baseline Established (DONE)

- **Commit**: 1c6026d5 (benchmark-results.json added)
- **Eval harness**: Added F1 metric and `--format markdown` CLI output option to `scripts/eval/prompt_eval_harness.py`
- **Broadmeadows baseline**: P=93.1%, R=87.1%, F1=90.0% (27/31 GT matched, 29 extracted)
- **Alexander baseline**: P=22.2%, R=46.5%, F1=30.1% (20/43 GT matched, 90 extracted — field misalignment on room_name/location columns is primary gap)
- **Evidence**: `docs/sprint-artifacts/e2e-evidence/live/benchmark-results.json`

### Known Open Issues

- AG-UI `TEXT_MESSAGE_CONTENT` errors still occur during chat (non-blocking; upstream `ag-ui-langgraph` run_id mutation bug)
- `/notebooks` redirect when navigating directly to `/jobs/source:...` URLs (client-side routing issue)
- `@copilotkit/*` v1.54.0 has breaking changes; frontend pinned at v1.51.3 until upstream resolves

---

---

## Chat Debug & Fix Session (2026-03-28)

Five bugs in the UnifiedChatPanel (CopilotKit/AG-UI) resolved across 7 files.
PRs #114 (async tools + checkpointer), #115 (token streaming + suggestions),
and #116 (active tab context + mobile) all merged. Branch fix/chat-v2 closed.

### Issues Resolved

| # | Issue | Root Cause | Fix |
|---|-------|-----------|-----|
| #4 | surreal_query failing | LLM SurrealQL used `$params` beyond `$sid`/`$val` — unbound at execution | Auto-bind unmatched `$param` references to `None` in `crud_tools.py` |
| #3 | Agent only queries acm_record | No tools for buildings or source metadata | Added `list_acm_buildings` + `get_source_metadata` tools to `acm_tools.py` |
| #2 | Tool renderers not firing | Tool name mismatch; no renderer for `semantic_search_acm` or new tools | Added 3 renderers; aligned all tool name strings to backend `@tool` names |
| #1 | Thinking messages as full bubbles | AG-UI `TEXT_MESSAGE_CONTENT` for short intermediate steps rendered as full bubbles | `isThinkingContent()` detector in `ACMAssistantMessage.tsx` → compact spinner |
| #5 | Orphaned `ItemDetailCard` / `BuildingSummaryCard` | Components existed but never imported by `UnifiedToolRenderers.tsx` | Wired `ItemDetailCard` → `get_acm_record_detail`; `BuildingSummaryCard` → `list_acm_buildings` |

### Files Modified

| File | Change |
|------|--------|
| `open_notebook/graphs/chat_tools/acm_tools.py` | +2 tools: `list_acm_buildings`, `get_source_metadata` |
| `open_notebook/graphs/chat_tools/__init__.py` | Export new tools via `get_acm_tools()` |
| `open_notebook/graphs/crud_tools.py` | Auto-bind unmatched `$params` in SurrealQL queries |
| `prompts/unified_agent.jinja` | New tools in system prompt + tool selection guide |
| `frontend/src/components/chat/UnifiedToolRenderers.tsx` | 3 new renderers; `ItemDetailCard` wired; total 18 renderers |
| `frontend/src/components/chat/ACMAssistantMessage.tsx` | `isThinkingContent()` compact indicator; null on empty content |
| `frontend/src/components/chat/renderers/ToolStepItem.tsx` | Labels for `get_source_metadata` and `list_acm_buildings` |

Sprint artifact: `docs/sprint-artifacts/chat-debug-2026-03-28.md`

---

## Next Steps
- [ ] MCS11 E2E verification (phases 6.2-6.6)
- [ ] Phase 5.2-5.3: Error row highlighting, validation overview card
- [ ] Phase 3.3-3.4: Per-building data source, building tab strip upgrade
- [ ] Alexander room_name/location field misalignment (root cause of F1=30.1% score)
- [ ] E36-S5..S7: Functional verification, UX audit, devils-advocate review (backlog)
