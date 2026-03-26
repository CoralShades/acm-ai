# Progress: Frontend UI Audit & Fix

## Completed Milestones

### Chat Pipeline Audit + Fix (2026-03-23) — IN PROGRESS (Phases 2-4 remaining)

Root cause fix for chat tools ignoring `source_id` context. Python 3.11 `ThreadPoolExecutor` does not propagate `contextvars`, so the `_run_async()` threadpool hack caused all tools to return stale data regardless of which job was active.

| Session | Description | Status |
|---------|-------------|--------|
| S1 | Async tool conversion — all 16 tools in `acm_tools`, `crud_tools`, `search_tools` converted from sync to async. `_run_async()` and `_run_in_thread()` helpers removed. Graph nodes `call_unified_agent` + `approval_node` made async. | Done |
| S2 | Persistent checkpointer — `MemorySaver` replaced with `AsyncSqliteSaver` (`data/chat_checkpoints.db`). Deferred graph compilation via `get_unified_graph()` lazy accessor, initialized in FastAPI lifespan. `thread_id` (UUID) added to `ChatSession` model and API responses. Migration 56 adds `thread_id` field + unique index. Legacy HITL nodes (`route_entry`, `legacy_execute_write_node`) removed — graph is now interrupt-only. | Done |
| S3 | Streaming improvements, tool registry, copilot suggestions | Pending |
| S4 | Polish, final E2E, documentation | Pending |

**Tests:** 57 pass (all updated to async `.ainvoke()` pattern) | **PR:** #114 | **Branch:** `fix/chat-v2` | **Commit:** `beedf620`

**Files changed (16):** `api/main.py`, `api/routers/agui_chat.py`, `api/routers/unified_sessions.py`, `frontend/src/lib/types/chat-session.ts`, `migrations/56.surrealql`, `migrations/56_down.surrealql`, `open_notebook/domain/notebook.py`, `open_notebook/graphs/chat_tools/__init__.py`, `open_notebook/graphs/chat_tools/acm_tools.py`, `open_notebook/graphs/chat_tools/search_tools.py`, `open_notebook/graphs/checkpointer.py`, `open_notebook/graphs/crud_tools.py`, `open_notebook/graphs/studio_entry_unified.py`, `open_notebook/graphs/unified_agent.py`, `tests/test_crud_tools_enhanced.py`, `tests/test_crud_tools_v2.py`

---

### Bug Fix 15: Broadmeadows Page 8 Missing Records (2026-03-23) — COMPLETE
Three compounding failures caused 2 ACM records to be permanently excluded from Broadmeadows extraction.

| Task | Description | Status |
|------|-------------|--------|
| T1 | Add page_end expansion to LLM success path in compile_building_inventory() | Done |
| T2 | Add Docling gap-detection warning in source_commands.py | Done |
| T3 | 3 new unit tests for page_end expansion in test_building_inventory.py | Done |

**Root Causes:**
- Docling TableFormer skips page 8 (only 2 sparse "no access" rows — not detected as a valid table)
- LLM sets page_end=7 (visually correct but misses continuation page); heuristic expansion only ran on LLM failure, not success
- With page_end=7, both _extract_building_content() and _get_docling_tables() excluded page 8 entirely

**Files changed:** `open_notebook/extractors/building_inventory.py`, `commands/source_commands.py`, `tests/test_building_inventory.py`
**Expected result:** 29/31 → 31/31 Broadmeadows (recovers "Lift Foyer — Internal lining" and "Main Foyer — Room adjacent disabled toilet")

---

### Unified Chat Phase 3: Polish + Testing (2026-03-22) — COMPLETE

| Task | Description | Status |
|------|-------------|--------|
| S1 | LLM intent router (`open_notebook/graphs/llm_router.py`) — rule-based fast-path + LLM fallback, entity extraction (buildings, rooms, risk_levels, materials, record_ids), injected into `unified_agent.py` system prompt | Done |
| S2 | Legacy chat deprecation — 14 files deleted (8 backend: `supervisor_agent.py`, `crud_agent.py`, `chat.py`, `source_chat.py`, `acm_analyst_agent.py`, `doc_search_agent.py`, `api/routers/chat.py`, `api/routers/source_chat.py`; 6 frontend: `SmartChatPanel.tsx`, `ChatModeSwitch.tsx`, `CrudToolRenderers.tsx`, `useSmartChat.ts`, `smart-chat.ts`, `copilot-crud/route.ts`). `api/main.py` + `langgraph.json` cleaned up | Done |
| S3 | E2E live testing (4 queries, screenshots via chrome-devtools MCP), prompt hardening for schema tool forcing, session store 404 graceful degradation, Playwright specs + mobile/dark/a11y audit | Done |

**Tests:** 2477 backend pass | **S1 unit tests:** 17/17 pass (`tests/test_llm_router.py`)

**Unified Chat Epic complete:** 13 stories across 3 phases, 21 files created, 14 legacy files deleted, 2477 tests passing.

---

### Unified Chat Phase 1: Backend (2026-03-22) — COMPLETE
Replaced separate supervisor + CRUD graphs with a single unified LangGraph agent.

| Task | Description | Status |
|------|-------------|--------|
| T1 | Thread-safe `contextvars` tool context replacing module-level globals (`tool_context.py`) | Done |
| T2 | SqliteSaver singleton for persistent chat sessions (`checkpointer.py`) | Done |
| T3 | Unified LangGraph graph — 6 nodes, 15 tools, interrupt-based HITL (`unified_agent.py`) | Done |
| T4 | Comprehensive system prompt covering all 7 DB tables + 15 tools (`prompts/unified_agent.jinja`) | Done |
| T5 | Rewritten AG-UI endpoint with single unified path + `session_id` support (`api/routers/agui_chat.py`) | Done |
| T6 | Session CRUD REST endpoints — list/create/update/delete (`api/routers/unified_sessions.py`) | Done |
| T7 | Delegate tool context in `acm_tools.py` and `crud_tools.py` to `tool_context.py` | Done |
| T8 | Expand `guardrails.py` with 4 missing table schemas (source, source_intelligence, acm_table_section, raw_extraction_table) | Done |
| T9 | Add 6 new SurrealQL query examples to `prompts/crud/surrealql_query.jinja` | Done |
| T10 | Register `unified_sessions` router in `api/main.py` | Done |
| T11 | Fix stale import of removed `_crud_context` in `test_crud_tools_enhanced.py` + `test_crud_tools_v2.py` | Done |

**Files created:** 6  **Files modified:** 7  **Tests:** 2452 pass (4 pre-existing failures)

---

### Auto-Notebook + AI-Editor Rename (2026-03-22) — COMPLETE
Auto-create Notebook on PDF upload, rename "Notebooks" to "AI-Editor", cascade delete.

| Task | Description | Status |
|------|-------------|--------|
| T1 | Auto-create Notebook in POST /sources (name from cleaned filename, editable in wizard) | Done |
| T2 | Enrich notebook name post-extraction with site/consultant metadata | Done |
| T3 | Show notebook name badge on JobCards | Done |
| T4 | Move /notebooks route to /ai-editor, update all user-facing labels | Done |
| T5 | Animated Sparkles icon with rotate+pulse hover for sidebar | Done |
| T6 | Cascade-delete notebooks + chat sessions on source/job deletion | Done |
| T7 | Frontend sources API client + UploadWizard + QuickUploadDialog notebook_name field | Done |
| T8 | Fix all cross-file imports after directory move (ModalProvider, ContextToggle, SourceCard, useNotebookChat) | Done |

**Files changed:** 28 frontend + 3 backend = 31 total
**Commit:** `33bf5aed`


### Building Grid + ACM Records Grid Rework (2026-03-16) — COMPLETE
Two-tab layout on `/source/[id]` and `/jobs/[id]` pages: "Buildings" tab (BuildingGrid) + "ACM Records" tab (BuildingTabStrip + ACMGrid). New `BuildingGrid.tsx` component — AG Grid with 13 default columns (Asset Name, Address, Suburb, Postcode, State, Asset Type, Category, Construction, Year, Levels, Ownership, Frequency, Records), View button opening `BuildingViewDialog`, autoHeight layout, column state persisted to localStorage. ACMGrid column defs reordered to 13 required Item__c fields. Per-building export dropdown ("Export Current Building" + "Export All"). DependentPicklistEditor, BuildingDetailForm, RecordWizard styling improvements. 3 commits, 8 files changed.

### Provenance PDF Viewer Enhancement (2026-03-16) — COMPLETE
PDFPageViewer rewrite: zoom (50-300%), page navigation, text search (Ctrl+F), scrollable canvas (65vh), bbox pulse animation, auto-scroll to highlighted record, crosshair re-scroll button, status bar. Bug fix: table_bbox missing from all 5 ACMRecordResponse builders (bbox overlay was never rendering). 4 files changed.

### Frontend Audit & Fix Session (2026-03-13) — COMPLETE
8 tasks, 13 files modified across the frontend. All tasks completed in a single session.

| Task | Description | Status |
|------|-------------|--------|
| T1 | Label renames: "Raw Extracted Records" -> "AI Mapped Records", reloadUrl fix, ConfirmDialog | Done |
| T2 | BuildingReviewGrid type alignment: canonical 57-field type from building.ts, V3 API endpoint | Done |
| T3 | Overview metrics: computed missingFieldsPercent + extractionQualityScore from real data | Done |
| T4 | ACM page migration: replaced legacy ACMGrid with V3 ItemGrid + BuildingTabStrip | Done |
| T5 | Job cards metadata: aggregate building/record stat cards on jobs page | Done |
| T6 | Document metadata: intelligence API wired into JobOverviewTab (consultant, site, date) | Done |
| T7 | Provider tab labels: subtitles for Docling/MinerU/Consensus tabs | Done |
| T8 | Provenance bbox overlay: teal color scheme + page mismatch guard | Done |

**Remaining gaps (from verification):**
- BuildingReviewGrid missing `state` column
- BuildingSidebar missing Postcode and State fields
- No dynamic Salesforce picklist wiring (uses hardcoded values)
- Job cards missing raw extraction counts (Docling/MinerU table counts)
- Job cards missing location/address info

See: `docs/sprint-artifacts/frontend-audit/progress.md` for full details.

## Blockers
None.

## Status
IN PROGRESS — Chat Pipeline Fix (fix/chat-v2): Sessions 1-2 done (async tools + AsyncSqliteSaver). Sessions 3-4 pending (streaming, tool registry, copilot suggestions, polish). Bug Fix 15 done (Broadmeadows page 8). Unified Chat Epic done (all 3 phases).
