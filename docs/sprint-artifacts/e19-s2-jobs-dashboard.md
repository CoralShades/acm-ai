# Story E19-S2: Jobs Dashboard

**Epic:** E19 — Standard User UX Redesign
**Priority:** P0
**Status:** backlog
**Change Proposal:** SCP-20260224 (2026-02-24)
**Depends on:** E19-S1

---

## User Story

**As a** compliance officer,
**I want to** see my uploaded documents as a list of "Jobs" with clear status and actions,
**So that** I can immediately understand what has been processed, what needs review, and what is published.

---

## Background

The current "Documents" page displays uploaded files in a generic file-management pattern. Compliance officers think in terms of extraction *jobs* — not file libraries. Each uploaded SAMP/BAR document is one job: it gets submitted, processed, reviewed, and published. This story renames the UX vocabulary and redesigns the document list as a Jobs dashboard.

**Important:** The backend `source` table and all APIs remain unchanged. This is a frontend UI/UX change only.

---

## Acceptance Criteria

### Route & Navigation
- [x] New route `/jobs` replaces current `/documents` route (redirect `/documents` → `/jobs`)
- [x] Sidebar navigation item reads "Jobs" with 📋 icon (replace "Documents")
- [x] Page title: "Jobs"

### Job Cards / List
- [x] Each source rendered as a "Job card" showing:
  - Job name (filename, editable inline — existing behaviour)
  - Status pill: `Extracting` (blue, pulsing) | `Pending Review` (amber) | `Review in Progress` (amber) | `Published` (green) | `Failed` (red)
  - Uploaded date (relative: "2 days ago")
  - Record count (if published, e.g. "32 records")
  - Building count (if published, e.g. "3 buildings")
  - Primary CTA: [Review] (if pending_review/building_review/acm_review) or [View] (if published)
- [x] Status pill maps to `source.review_status` field
- [x] Empty state: "No jobs yet. Upload your first SAMP document." + [+ New Job] button

### New Job Button
- [x] Prominent [+ New Job] button in page header opens existing upload wizard
- [x] Upload wizard completion redirects to Building Review Wizard (E19-S5) instead of source detail

### Actions per Job Card
- [x] Three-dot menu (or action buttons) per job card:
  - Download PDF (original upload)
  - Re-extract (re-triggers extraction)
  - Delete job
- [x] For published jobs: [Export CSV] and [Export Excel] quick actions visible

### Skeleton Loading
- [x] Job cards show skeleton placeholder while `GET /api/sources` fetches
- [x] Uses existing skeleton system (E14-S4 shimmer animation)

---

## Technical Notes

### Status Mapping
```typescript
const statusLabel = {
  extracting: 'Extracting',
  pending_review: 'Pending Review',
  building_review: 'Review: Buildings',
  acm_review: 'Review: Records',
  published: 'Published',
};

const statusColor = {
  extracting: 'blue',
  pending_review: 'amber',
  building_review: 'amber',
  acm_review: 'amber',
  published: 'green',
};
```

### Existing Components to Reuse
- Upload wizard (existing) — unchanged
- Skeleton loading (E14-S4) — reuse pattern
- Toast system (E14-S5) — for delete confirmation

### API
No new API endpoints. Use existing `GET /api/sources` which now returns `review_status`. Add query filter support: `GET /api/sources?review_status=pending_review`.

---

## Key Files Created/Modified

| File | Change |
|------|--------|
| `frontend/src/app/jobs/page.tsx` | **New** — Jobs dashboard page |
| `frontend/src/components/jobs/JobCard.tsx` | **New** — Job card component |
| `frontend/src/components/jobs/JobStatusPill.tsx` | **New** — Status badge component |
| `frontend/src/app/documents/page.tsx` | Modified — redirect to /jobs |
| `frontend/src/components/layout/AppSidebar.tsx` | Modified — rename Documents → Jobs |

---

## Dev Notes

No API cost risk — no extraction calls.

Do not use `review_status` until E19-S1 migration has run. If `review_status` is null on an existing source, treat as `'published'` in the UI (fallback for any data that survived migration).

---

## Estimated Effort

S (Small) — Primarily UI rename + new JobCard component. No new APIs.

---

**Story Status:** ⬜ BACKLOG
