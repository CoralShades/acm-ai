# Progress: Frontend UI Audit & Fix

## Completed Milestones

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
None — session complete.

## Status
COMPLETE
