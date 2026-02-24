# Story E19-S7: Job Detail Page

**Epic:** E19 — Standard User UX Redesign
**Priority:** P0
**Status:** backlog
**Change Proposal:** SCP-20260224 (2026-02-24)
**Depends on:** E19-S6

---

## User Story

**As a** compliance officer managing a published job,
**I want to** access a permanent detail page for each job with tabs for buildings, ACM records, extraction log, and export actions,
**So that** I can re-review, re-extract, and export my data at any time after initial publication.

---

## Background

After the post-extraction review wizard completes and a job is published, users need a permanent home for that job's data. The current source detail page exists but is not designed for the Jobs mental model. This story creates a purpose-built Job Detail page with the correct tab structure and actions for a compliance officer's workflow.

---

## Acceptance Criteria

### Route & Header
- [x] Route: `/jobs/{source_id}` (replaces or extends current `/sources/{id}`)
- [x] Page header shows:
  - Job name (editable inline)
  - Status pill (`review_status`)
  - Uploaded date + extracted date
  - Record count + building count (if published)
- [x] Breadcrumb: Jobs / {Job Name}

### Tab Structure
- [x] **Overview** tab:
  - Summary cards: record count, building count, missing fields %, extraction quality score
  - Quick actions: [Re-Extract] [Re-Review Buildings] [Re-Review Records]
  - Extraction timeline: when submitted, when extracted, when reviewed, when published
- [x] **Buildings** tab:
  - Same 21-field building grid as Step 1 wizard (editable, auto-saves)
  - [Mark Out of Scope] action still available
- [x] **ACM Records** tab:
  - Same 29-field per-building tab view as Step 2 wizard (editable)
  - Status: "Published" badge
  - [Export CSV] [Export Excel per-building] actions in tab toolbar
- [x] **Extraction Log** tab:
  - Existing `ExtractionProgressPanel` component (stage pills + log terminal)
  - Historical log for completed extractions

### Export Actions
- [x] [Export CSV] — exports all records from this job as 43-column BAR CSV
- [x] [Export Excel per-building] — exports one Excel sheet per building, BAR-compliant
- [x] Export from ACM Records tab is scoped to THIS job only (not global register)
- [x] Both exports use existing `GET /api/acm/export/csv?source_id={id}` and `GET /api/acm/export/excel?source_id={id}` (add source_id filter param if not already supported)

### Re-Review Actions
- [x] [Re-Review Buildings] → navigates to `/jobs/{id}/review/buildings` (Step 1 wizard)
- [x] [Re-Review Records] → navigates to `/jobs/{id}/review/records` (Step 2 wizard)
- [x] [Re-Extract] → triggers re-extraction, sets `review_status = 'pending_review'`, navigates to `/jobs/{id}/extract`

### Skeleton Loading
- [x] All tabs show skeleton while data fetches

---

## Technical Notes

### Existing Components Reused
- `BuildingReviewGrid.tsx` (from E19-S5) — used in Buildings tab
- `ACMReviewGrid.tsx` (from E19-S6) — used in ACM Records tab
- `ExtractionProgressPanel.tsx` (from E17) — used in Extraction Log tab
- `ExtractionLogStream.tsx` — historical log loading

### Export API Extension
Add `source_id` query param to existing export endpoints:
```
GET /api/acm/export/csv?source_id={id}
GET /api/acm/export/excel?source_id={id}
```
If not already supported, add source_id filtering to the export queries.

### Navigation from Jobs Dashboard
Job cards with status `published` show [View] CTA → navigates to `/jobs/{id}` (this page).
Job cards with status `pending_review` / `acm_review` / `building_review` show [Resume Review] CTA → navigates to appropriate wizard step.

---

## Key Files Created/Modified

| File | Change |
|------|--------|
| `frontend/src/app/jobs/[id]/page.tsx` | **New** — Job detail page with tabs |
| `frontend/src/components/jobs/JobDetailHeader.tsx` | **New** — header with status + actions |
| `frontend/src/components/jobs/JobOverviewTab.tsx` | **New** — summary cards + timeline |
| `api/routers/acm.py` | Modified — add source_id filter to export endpoints |

---

## Dev Notes

No API cost risk — no extraction LLM calls.

The [Re-Extract] action reuses the existing extraction trigger (`POST /api/acm/extract`). It should reset `source.review_status = 'extracting'` and navigate to the raw extraction table page (`/jobs/{id}/extract`).

---

## Estimated Effort

M (Medium) — Tabbed page with reused wizard components. Primary new work is the Overview tab and header actions.

---

**Story Status:** ⬜ BACKLOG
