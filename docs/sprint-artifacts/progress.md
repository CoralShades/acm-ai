# Progress: Frontend UI Audit & Fix

## Completed Milestones

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
