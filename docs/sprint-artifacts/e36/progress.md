# E36 Progress Journal

## 2026-03-05 — E36-S1: Agent Team Creation & Orchestration Setup

- **Status**: DONE
- **What completed**:
  - Created 6 agent files: e36-lead, e36-browser-tester, e36-log-sentinel, e36-devils-advocate, e36-bmad-scribe, e36-ux-auditor
  - Edited 3 existing agents: acm-e2e-tester (benchmark workflow), qa-specialist (browser verification), docs-specialist (e36 scope)
  - Created directory structure: docs/sprint-artifacts/e36/ with evidence/, benchmark-results/, adversarial-reviews/, logs/
  - Created state files: task_plan.md, progress.md, findings.md
  - Updated prd.json with E36 epic (8 stories, 26 SP)
  - Updated sprint-status.yaml with E36 entries
  - Added 8 missing DYNAMIC_ROUTES to route-walker.ts (4 -> 12 total)
- **Next**: Phase 2 — E36-S2 (E35 re-verify) + E36-S3 (route gaps) in parallel

## 2026-03-05 — E36-S2: E35 Fix Re-verification

- **Status**: DONE
- **What completed**:
  - V1 (E35-S1): Sync upload — no asyncio.run() in commands/source_commands.py. PASS
  - V2 (E35-S2): Model defaults — PUT /api/models/defaults persists via defaults.update(). PASS
  - V3 (E35-S3): Ollama hardening — format="json", character-based multi-chunking, num_ctx=32768. PASS
  - V4 (E35-S4): Provider priority — Ollama->Anthropic->OpenRouter chain, ACM-namespaced keys. PASS
  - V5 (E35-S5): SSE terminal — all endpoints emit terminal events and close streams. PASS
  - V6 (E35-S6): Building backfill — POST /backfill-buildings endpoint, GET /buildings returns empty array. PASS
  - V7 (E35-S7): SF-first validation — field freezing, sf_valid_fields(), filtered correction prompts. PASS
  - V8 (E35-S8): Frontend empty state — BuildingSidebar, BuildingReviewGrid, SourceIntelligencePanel all show empty states. PASS
  - Unit tests: 315 passed, 1 skipped across all E35-related test files
  - All 8 evidence files created in docs/sprint-artifacts/e36/evidence/
- **Next**: E36-S3 (route coverage gaps)

## 2026-03-05 — E36-S3: Route/Coverage Gap Fixes

- **Status**: DONE
- **What completed**:
  - Verified 12 DYNAMIC_ROUTES entries in route-walker.ts (AC1)
  - Updated smoke-walker.spec.ts with static + dynamic route tests and 36/36 coverage assertion (AC2)
  - Confirmed 36/36 route coverage: 24 static + 12 dynamic (AC3)
  - Updated cheat-sheet.md Dynamic Routes section from 4 to 12 entries (AC4)
  - All static routes return 200/307, dynamic routes work in browser with real entity IDs
  - 10 screenshots captured as evidence in docs/sprint-artifacts/e36/evidence/e36-s3/
  - npm run build passes
- **Next**: E36-S4 (Ollama Multi-Model Benchmark)

## 2026-03-13 — Bug Fix: Frontend Navigation Performance (ACMV3 branch)

- **Status**: DONE
- **What completed**:
  - Fixed ConnectionGuard (`frontend/src/components/common/ConnectionGuard.tsx`) — replaced `return null` during API health check with a full app-shell skeleton. Eliminated blank white screen on cold start.
  - Created 17 new `loading.tsx` files across all data-fetching routes that were missing them: `(dashboard)/loading.tsx`, `notebooks/loading.tsx`, `notebooks/[id]/loading.tsx`, `sources/[id]/loading.tsx`, `source/[id]/loading.tsx`, `source/[id]/raw/loading.tsx`, `source/[id]/building/[buildingId]/loading.tsx`, `source/[id]/provenance/[recordId]/loading.tsx`, `settings/loading.tsx`, `settings/models/loading.tsx`, `settings/processing/loading.tsx`, `settings/field-schema/loading.tsx`, `settings/extraction/loading.tsx`, `extraction-monitor/loading.tsx`, `extraction/[id]/loading.tsx`, `transformations/loading.tsx`, `jobs/[id]/chat/loading.tsx`
  - Created navigation timing E2E test at `tests/e2e/specs/navigation-timing.spec.ts`
  - Findings report at `docs/temp/frontend-nav-audit-report.md`
  - `npm run build` passes clean
- **Root cause**: All 34 pages are Client Components (not async Server Components). 27/34 routes had no `loading.tsx` so Next.js kept old page visible during transitions. `ConnectionGuard` rendered null on cold start.
- **Next**: E36-S5 (Functional Verification)

## 2026-03-16 — CRUD Chat + Grid Audit Fix E2E Verification

- **Status**: DONE
- **What completed**:
  - Created `docs/sprint-artifacts/crud-audit-fix/audit-fix-report.md` documenting all 23 audit fixes across P0/P1/P2 tiers
  - Fixed missing `EventEncoder` in `/api/agui/crud-chat` SSE endpoint (`api/routers/agui_chat.py`) — this was blocking all SSE streaming for the CRUD chat panel
  - E2E verified 11/11 planned tests: page load, source ID injection, count query, buildings query, full HITL write flow (T10), SSE streaming, Record ID column visibility (F2)
  - HITL write flow (T10) confirmed PASS: backend interrupt fires, `HITLApprovalDialog` renders, user approve action confirmed, DB write reflected
  - Record ID column confirmed visible in both Buildings tab and ACM Records tab
  - Added Findings 016-018 to e36/findings.md: SurrealDB v2.6.3 wire protocol issue, ACM Records grid empty state, EventEncoder missing
- **Pre-existing issues documented** (not caused by audit fix):
  - SurrealDB v2.6.3 CBOR incompatibility (Finding 016 — BLOCKER)
  - ACM Records grid empty due to building_id vs building_record_id mismatch (Finding 017 — CONCERN)
  - validation-summary endpoint 500 (downstream of Finding 016)
- **Next**: E36-S5 (Functional Verification)

## 2026-03-05 — E36-S4: Ollama Multi-Model Benchmark

- **Status**: DONE
- **What completed**:
  - Created benchmark script `scripts/benchmark_ollama.py` with dual completion detection
  - Registered mistral:7b model in the system (was missing)
  - Executed 12 benchmark runs (6 models x 2 PDFs): 5 completed, 7 timed out
  - Discovered extraction_progress status bug (Finding 012) — pipeline logger doesn't write terminal status
  - Discovered Alexander field misalignment (Finding 013) — room_name contains material descriptions
  - Reconfirmed correction stage JSON failure (Finding 014) — format="json" not applied to correction LLM
  - Identified qwen2.5:7b as best Ollama model (Finding 015): fastest, highest extraction rate
  - Created 12 per-run detail files + summary.md + raw_results.json in benchmark-results/
  - Log sentinel report at evidence/log-sentinel-e36s4.md
  - Updated findings.md with 4 new findings (012-015)
- **Key metrics**:
  - Best model: qwen2.5:7b (64.5% Broadmeadows, 86.0% Alexander extraction rate)
  - Worst: llama3.1:8b (9.7% Broadmeadows, timeout Alexander)
  - Average extraction time (completed): 167s (qwen2.5:7b) to 403s (llama3.1:8b)
- **Next**: E36-S5 (Functional Verification)

## 2026-03-20 to 2026-03-21 — Pipeline Accuracy Fixes + Chat System

- **Status**: DONE
- **Commits**: 1c6026d5, dfaf91ee, aded56d2
- **Pipeline accuracy (Phase 1)**:
  - Row segmenter: `_is_header_row()` with 37 known header texts prevents duplicate header records at multi-page table boundaries
  - Dedup key normalization: strip + whitespace collapse on product/location/sample_no
  - Schema inference fallback parser for flat dict and bare list LLM responses
  - SF Picklist validator: `needs_user_review` routing changed to non-blocking `chain_warnings` (was causing 79 false validation failures)
  - Added "Unknown" to `_LEGACY_VALUES` in SF picklist validator
  - Eval harness: F1 metric + `--format markdown` CLI option
- **Benchmark baseline established**:
  - Broadmeadows: P=93.1%, R=87.1%, F1=90.0%
  - Alexander: P=22.2%, R=46.5%, F1=30.1% (room_name/location field misalignment is primary gap)
  - Evidence: `docs/sprint-artifacts/e2e-evidence/live/benchmark-results.json`
- **Chat fixes (Phase 2)**:
  - Query/Edit mode toggle added to jobs page chat sidebar (SmartChatPanel + JobCrudChatPanel)
  - CRUD fallback query field `risk_status` renamed to `sample_result` in `crud_tools.py`
  - SmartChatPanel infinite re-render fixed (useMemo on useCopilotReadable value)
  - SmartChatErrorBoundary added to isolate CopilotKit crashes from the page
  - Removed `useCopilotChatSuggestions` and `useCoAgentStateRender` (caused AG-UI TEXT_MESSAGE_CONTENT errors)
- **Package upgrades**: ag-ui-langgraph 0.0.25→0.0.27, copilotkit 0.1.78→0.1.81, ag-ui-protocol 0.1.11→0.1.14 (Python); @copilotkit/* pinned at v1.51.3 (v1.54.0 has breaking changes)
- **Known open issues (non-blocking)**:
  - AG-UI TEXT_MESSAGE_CONTENT errors during chat (upstream ag-ui-langgraph run_id mutation bug)
  - /notebooks redirect on direct navigation to /jobs/source:... (client-side routing)
- **Next**: E36-S5 (Functional Verification)

## 2026-03-17 — Dogfood Session: Live Extraction + Bug Fixes

- **Status**: DONE
- **What completed**:
  - Live extraction run on Broadmeadows Police Station PDF (18 pages, 31 ground truth records)
  - Fresh SurrealDB volume, model provisioning, full UX dogfood via browser automation
  - **Commit 6fd92aaf**: `_get_db_extraction_model()` rejects non-Ollama models; `validate_records_strict()` auto-fills material_description from product. Result: 0→28/31 records
  - **Commit c0832fa8**: `ACMItemRecord.quantity` `Optional[float]`→`Optional[str]` (prevents entire building discard); `JobOverviewTab.tsx` optional chaining crash fix
  - **Commit 0785f1b8**: Source delete cascade (file on disk, reference edges, command+agui_events, chat edges); `POST /api/sources/cleanup-orphaned-files` endpoint (deleted 92 orphaned files, 149MB)
  - Audit findings: building inventory cross-validation merge produces phantom buildings (deferred)
  - Full report: `dogfood-output/extraction-run-report.md`
- **Key metrics**:
  - Records: 28/31 (90% ground truth match)
  - Extraction time: 232.8s (bulk mode, ollama/qwen2.5:7b)
  - Confidence: 25 high, 0 medium, 3 low (no-access recovery)
  - Orphaned files cleaned: 92 files, 149MB→0MB
- **Next**: E36-S5 (Functional Verification)
