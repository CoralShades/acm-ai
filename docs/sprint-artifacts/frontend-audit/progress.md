# Frontend Audit & Fix — Progress

## Date: 2026-03-13

## Session Summary

Frontend UI audit and fix session: 8 tasks, 13 files modified. Addressed label inconsistencies, type misalignment, missing computed metrics, legacy component references, and provenance overlay issues across the V3 frontend.

---

## Tasks

### T1 — Label Renames & Dialog Fix
**Status:** Done
**Files:**
- `frontend/src/app/(dashboard)/jobs/[id]/extract/page.tsx` — "Raw Extracted Records" -> "AI Mapped Records"
- `frontend/src/app/(dashboard)/source/[id]/page.tsx` — `reloadUrl="/sources"` -> `"/jobs"`
- `frontend/src/app/(dashboard)/source/[id]/raw/page.tsx` — `reloadUrl="/sources"` -> `"/jobs"`
- `frontend/src/app/(dashboard)/jobs/[id]/review/records/page.tsx` — replaced raw div modal with ConfirmDialog

### T2 — BuildingReviewGrid Type Alignment
**Status:** Done
**Files:**
- `frontend/src/components/acm/BuildingReviewGrid.tsx` — removed local 22-field BuildingRecord, imported canonical 57-field type from `building.ts`, updated API from legacy `/api/acm/jobs/{id}/buildings` to V3 `/api/acm/buildings?source_id=X`, shared query key with useBuildings hook

### T3 — Overview Metrics Computation
**Status:** Done
**Files:**
- `frontend/src/components/jobs/JobOverviewTab.tsx` — computed `missingFieldsPercent` and `extractionQualityScore` from actual ACM records data (was always null/N/A before)

### T4 — ACM Page V3 Migration
**Status:** Done
**Files:**
- `frontend/src/app/(dashboard)/acm/page.tsx` — replaced legacy `ACMGrid` with V3 `ItemGrid` + `BuildingTabStrip`, unified grid experience

### T5 — Job Cards Metadata
**Status:** Done
**Files:**
- `frontend/src/app/(dashboard)/jobs/page.tsx` — added aggregate Buildings/ACM Records stat cards
- `frontend/src/components/jobs/JobCard.tsx` — showed building/record counts on all job cards (not just published)

### T6 — Document Metadata
**Status:** Done
**Files:**
- `frontend/src/components/jobs/JobOverviewTab.tsx` — wired `GET /api/acm/intelligence/{source_id}` showing consultant, site, date, document type, and building inventory

### T7 — Provider Tab Labels
**Status:** Done
**Files:**
- `frontend/src/components/acm/RawTableGrid.tsx` — added subtitles: Docling ("ML-based table detection"), MinerU ("PDF structure analysis"), Consensus ("Merged provider results")

### T8 — Provenance Bbox Overlay
**Status:** Done
**Files:**
- `frontend/src/components/acm/PDFPageViewer.tsx` — updated bbox overlay to teal color scheme
- `frontend/src/components/acm/ProvenanceViewer.tsx` — added page mismatch and coordinate validation guards

---

## Files Modified (13 total)

| # | File | Tasks |
|---|------|-------|
| 1 | `frontend/src/app/(dashboard)/acm/page.tsx` | T4 |
| 2 | `frontend/src/app/(dashboard)/jobs/[id]/extract/page.tsx` | T1 |
| 3 | `frontend/src/app/(dashboard)/jobs/[id]/page.tsx` | T5 |
| 4 | `frontend/src/app/(dashboard)/jobs/[id]/review/records/page.tsx` | T1 |
| 5 | `frontend/src/app/(dashboard)/jobs/page.tsx` | T5 |
| 6 | `frontend/src/app/(dashboard)/source/[id]/page.tsx` | T1 |
| 7 | `frontend/src/app/(dashboard)/source/[id]/raw/page.tsx` | T1 |
| 8 | `frontend/src/components/acm/BuildingReviewGrid.tsx` | T2 |
| 9 | `frontend/src/components/acm/PDFPageViewer.tsx` | T8 |
| 10 | `frontend/src/components/acm/ProvenanceViewer.tsx` | T8 |
| 11 | `frontend/src/components/acm/RawTableGrid.tsx` | T7 |
| 12 | `frontend/src/components/jobs/JobCard.tsx` | T5 |
| 13 | `frontend/src/components/jobs/JobOverviewTab.tsx` | T3, T6 |

---

## Remaining Gaps (from verification)

| # | Gap | Severity | Notes |
|---|-----|----------|-------|
| 1 | BuildingReviewGrid missing `state` column | LOW | State field exists in canonical type but not rendered as column |
| 2 | BuildingSidebar missing Postcode and State fields | LOW | Sidebar shows building info but omits these address fields |
| 3 | No dynamic Salesforce picklist wiring | MEDIUM | AG Grid cell editors use hardcoded picklist values, not SF schema API |
| 4 | Job cards missing raw extraction counts | LOW | No Docling/MinerU table counts shown on job cards |
| 5 | Job cards missing location/address info | LOW | Building address/suburb not surfaced on job card summaries |

---

## Follow-Up Session: Provenance PDF Viewer Enhancement (2026-03-16)

### T9 — Enhanced PDF Viewer in ProvenanceViewer
**Status:** Done
**Files:**
- `frontend/src/components/acm/PDFPageViewer.tsx` — Major rewrite: zoom (50-300%), page navigation, text search (Ctrl+F with match highlighting), scrollable canvas (65vh), bbox pulse animation, auto-scroll to bbox, crosshair re-scroll button, status bar
- `frontend/src/app/globals.css` — `.pdf-search-highlight`, `.pdf-search-highlight-active`, `@keyframes pdf-bbox-pulse`
- `frontend/src/components/acm/ProvenanceViewer.tsx` — Minor comment update
- `api/routers/acm.py` — **Bug fix**: `table_bbox` added to all 5 `ACMRecordResponse` builders (was missing — bbox overlay never rendered)

**Bug discovered during audit:**
- `table_bbox` field existed on `ACMRecordResponse` model but was never populated in any of the 5 response builder sites (list, get, create, update, provenance endpoints). This meant the bbox overlay in the provenance viewer was always empty — the feature appeared broken but was actually a data omission bug.

---

## Session Status: COMPLETE
