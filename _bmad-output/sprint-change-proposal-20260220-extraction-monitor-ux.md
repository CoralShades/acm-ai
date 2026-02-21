# Sprint Change Proposal — Extraction Monitor UI & UX Enhancement Sprint

**Date:** 2026-02-20
**Status:** APPROVED
**Approved by:** Demi
**Priority:** P0 (E15-S1, E15-S2, E16-S2) / P1 (E16-S1, E16-S3)
**Scope:** Moderate
**Risk:** Low
**Path:** Epic Additions (2 new epics, 5 new stories)

---

## 1. Motivation

Following the E2E gap-fix sprint (PR #30, Feb 16) and a full project state reconciliation (Feb 20), two capability gaps remain unaddressed:

### Gap 1: Extraction visibility is buried in the upload wizard

The backend SSE pipeline, pipeline logger, and frontend log components were fully implemented in E1-S21, but they are only accessible during the active upload flow. Once an upload completes, there is no way for users to:
- Review the detailed stage-by-stage progress of any past extraction
- Monitor multiple concurrent extractions from one place
- Debug or retry a failed extraction without re-uploading the document

This is a usability gap — the infrastructure exists, it just needs to be surfaced.

### Gap 2: Key UX entry points are missing

Despite E14 completing enterprise readiness (WCAG, breadcrumbs, skeleton loading, etc.), three high-impact UX patterns remain unimplemented:

- No **dashboard home** — users land directly on Documents with no system overview
- No **record detail panel** — the ACM grid has 47 fields but users can only see a few columns at once; there's no way to read a full record without scrolling
- No **empty states** — blank grids with no guidance when there are no records

Additionally, **E9-S3** (bulk document operations) is drafted but hasn't been promoted to ready-for-dev despite being critical for document management workflows.

---

## 2. Project State Reconciliation (Feb 20)

### Planning Doc Discrepancy Resolved

The file `_bmad-output/implementation-artifacts/sprint-status.yaml` (updated Feb 9) was stale. The canonical file `docs/sprint-artifacts/sprint-status.yaml` (updated Feb 16) shows 11 stories as **done** that were previously listed as "backlog" or "review" in older planning documents:

| Story | Old Status | Actual Status |
|-------|-----------|---------------|
| E1-S11 | review | done |
| E1-S12 | ready-for-dev | done |
| E1-S14 | backlog | done |
| E1-S15 | backlog | done |
| E1-S16 | backlog | done |
| E1-S17 | backlog | done |
| E1-S18 | backlog | done |
| E1-S19 | backlog | done |
| E1-S20 | backlog | done |
| E1-S21 | backlog | done |
| E11-S1 | review | done |

**Actual completion: 72/94 stories done (77%)**, not 50/74 (68%) as shown in stale docs.

### PR #30 Deliverables Not Reflected in PRD/Epics

The following features shipped in PR #30 (Feb 16) are not yet documented in `03-prd.md` or `05-epics-and-stories.md`:
- 7 BAR compliance columns in ACMGrid
- Extraction accuracy fixes (dedup key, assumed positive, false positive guards)
- GitHub Actions E2E CI/CD pipeline (`e2e-ci-github-actions-setup: done`)

These are covered by existing stories (E2-S12, E1-S24..S27, e2e-ci) already tracked in the canonical sprint-status.yaml. No new PRD changes needed for these — they are implementation improvements within existing approved stories.

---

## 3. Change Proposals

### CP-1: New Epic 15 — Extraction Monitor & Live Logging UI

**Rationale:** Surface existing SSE infrastructure (E1-S21 done) to the Document Library and a dedicated monitoring page.

**New Stories:**

#### E15-S1: Extraction Log Panel in Document Library

- **As a:** compliance officer reviewing document processing
- **I want to:** click any document in the library and see the full extraction log with stage-by-stage progress
- **So that:** I can understand exactly what the AI extracted, identify failures, and retry without re-uploading

**Acceptance Criteria:**
- Each document row in the Document Library has an expand chevron
- Expanding shows `ExtractionProgressPanel` component with stage pills and log terminal
- For completed documents: loads historical log from `extraction_progress` SurrealDB table via REST fallback endpoint
- For active/in-progress documents: connects live SSE stream via `/api/acm/extraction-progress/{commandId}/stream`
- Stage pills show: STRUCTURE, PREFLIGHT, ORCHESTRATOR, EXTRACT, VALIDATE, CORRECT, STORE
- Log terminal scrollable with Copy All button
- Retry button shown for failed/partial extractions
- Works for both success and failure states

**Backend dependencies:** Already complete (E1-S21: `api/routers/extraction_events.py`, `extraction_progress` table)
**Frontend dependencies:** Already complete (`ExtractionProgressPanel.tsx`, `ExtractionLogStream.tsx`, `use-extraction-progress.ts`)
**New frontend work:** Wire into Document Library component, handle historical log fetch

#### E15-S2: Dedicated Extraction Monitor Page

- **As a:** system administrator
- **I want to:** a single page showing all active and historical extractions with full log detail
- **So that:** I can monitor system health, debug failures, and manage the extraction queue

**Acceptance Criteria:**
- New route: `/extraction-monitor`
- Two tabs: **Active** (live SSE streams for in-progress) and **History** (paginated past extractions)
- Each extraction card shows: document name, started_at, duration, final status, stage pills
- Expandable log terminal per extraction
- Filter by status: running / completed / failed / partial
- Filter by date range
- Retry button for failed/partial extractions
- Navigation entry: CONFIGURE section > "Extraction Monitor"
- Accessible via keyboard navigation (Tab/Enter to expand logs)

**Backend dependencies:** Already complete
**Frontend dependencies:** Reuses E15-S1 panel components

---

### CP-2: New Epic 16 — UX Enhancement Sprint

**Rationale:** Three high-impact UX patterns absent after E14; bulk operations drafted but not promoted.

#### Promote E9-S3: Document Actions & Bulk Operations

Change status from `drafted` → `ready-for-dev`.

The tech-spec at `docs/sprint-artifacts/tech-spec-e9-s3-document-actions-bulk-operations.md` (drafted) covers:
- Multi-select documents with checkboxes
- Bulk actions: delete, re-extract, export
- Individual actions: rename, view details, download source PDF

No story scope changes — just status promotion.

#### E16-S1: Dashboard Home Page with ACM Stats

- **As a:** user opening ACM-AI
- **I want to:** see a dashboard overview with system metrics and quick actions
- **So that:** I understand the system state at a glance without navigating to multiple pages

**Acceptance Criteria:**
- New `/` home route replaces current landing page
- Summary cards (skeleton loading while fetching):
  - Total ACM records in system
  - Total buildings managed
  - Documents processed (total + this month)
  - Risk breakdown: % High/Medium/Low/Unknown
- Charts (Recharts or similar):
  - Risk status distribution (donut chart)
  - Records by building (horizontal bar, top 10)
  - Extraction quality trend (line chart, last 7 days if data available)
- Recent activity section: last 5 extractions with name, date, status, record count
- Quick action buttons: "Upload SAMP", "View ACM Register", "Extraction Monitor"
- Responsive: works on 1280px+ (desktop focus, degrades gracefully on tablet)
- Skeleton loading for all charts while data fetches

**Backend work:** New `GET /api/acm/stats` endpoint returning aggregate counts and risk breakdown

#### E16-S2: ACM Record Detail Slide-Out Panel

- **As a:** compliance officer reviewing records
- **I want to:** click an ACM record row to see all its fields in a readable panel
- **So that:** I can review full record details without horizontal scrolling or opening separate pages

**Acceptance Criteria:**
- Click any row in ACM grid → right-side slide-out drawer (380px width)
- Organized field sections with section headers:
  - Organisation Hierarchy (department, agency, sub_agency, site_name)
  - Building Information (address, suburb, postcode, year_built, floor_count, etc.)
  - Location (area_type, level, room_id, room_name, location)
  - ACM Details (product, friable, product_group, product_type, nata_sample_no, sample_result)
  - Assessment (condition_rating, disturbance_potential, extent, risk_status)
  - Documentation (labelled, label_details, recommendations, comments, photo)
  - Removal Tracking (psb_acm_id, date_removed, epa_certificate_no)
- PDF citation button: opens existing PDF viewer at stored page_number
- Edit mode toggle: inline field editing with Save / Cancel
- Keyboard navigation: ← → arrow keys cycle through records
- Escape key closes panel
- Empty/null fields shown as "—" (not blank)
- Extraction confidence shown as percentage badge if available

**Backend work:** No new endpoints — uses existing `GET /api/acm/{id}` and `PUT /api/acm/{id}`

#### E16-S3: Empty States & Onboarding Hints

- **As a:** new user opening ACM-AI for the first time
- **I want to:** see helpful guidance when there are no documents or records
- **So that:** I know what to do next and the app doesn't feel broken

**Acceptance Criteria:**
- **Documents page empty state:** illustration + "No SAMPs uploaded yet" + "Upload your first SAMP" button → opens upload wizard
- **ACM Register empty state:** "No ACM records extracted yet" + "Upload a SAMP document to extract records" link
- **Chat empty state:** "Add a SAMP document first to enable AI chat" + link to Documents
- **Extraction Monitor empty state:** "No extraction history found" + "Upload a document to start"
- All empty states use consistent ACM-AI design system (same card style, muted palette)
- **Onboarding hints** (dismissable per-user via localStorage):
  - First time on Documents page: callout explaining drag-drop upload
  - First time on ACM Register: callout explaining column visibility and search
  - One-time only (localStorage `acm-hint-{page}: dismissed`)
- Empty state illustrations: simple SVG icons (no external image dependencies)

---

## 4. Impact Analysis

### Dependencies

| Story | Depends On | Blocks |
|-------|-----------|--------|
| E15-S1 | E1-S21 (done), E9-S1 (done) | E15-S2 |
| E15-S2 | E15-S1 | — |
| E16-S1 | New `/api/acm/stats` endpoint | — |
| E16-S2 | E3-S1 (done — PDF viewer) | — |
| E16-S3 | E9-S1 (done), E4-S1 (done) | — |

### No Breaking Changes

All new stories are additive — no existing APIs, components, or database schemas are modified in ways that could break current functionality.

### Database Changes

- E16-S1 requires new `GET /api/acm/stats` endpoint (read-only aggregation, no schema changes)
- No SurrealDB migration files needed

---

## 5. Updated Story Counts

| Category | Before | After |
|----------|--------|-------|
| Total stories | 94 | 99 |
| Done | 72 | 72 |
| Ready-for-dev | 5 | 7 (+ E9-S3, E10-S1 promoted) |
| Backlog | 8 | 13 (+ E15-S1, E15-S2, E16-S1, E16-S2, E16-S3) |
| Drafted | 2 | 0 (E9-S3, E10-S1 promoted) |
| Total epics | 14 | 16 |

---

## 6. Implementation Order (Recommended)

```
Sprint A — Quick wins and promotions:
  E9-S3  (Bulk Operations — already drafted, promote to ready-for-dev)
  E10-S1 (Navigation Simplification — already drafted, promote to ready-for-dev)
  E16-S3 (Empty States — low risk, high polish value)

Sprint B — High-value new stories:
  E15-S1 (Extraction Log Panel in Document Library)
  E16-S2 (ACM Record Detail Panel)

Sprint C — Larger scope new stories:
  E15-S2 (Dedicated Extraction Monitor Page)
  E16-S1 (Dashboard Home Page)

Sprint D — Remaining backlog:
  E2-S8, E2-S11, E5-S3, E5-S4, E1-S23
  E11-S2, E12-S1..S4, E13-S1..S3
```

---

## 7. Files Changed by This Proposal

| File | Change |
|------|--------|
| `docs/sprint-artifacts/sprint-status.yaml` | Add E15, E16 sections; promote E9-S3, E10-S1; update summary |
| `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` | Fix done statuses; add E15, E16 |
| `_bmad-output/bmm-workflow-status.yaml` | Add Feb 20 change log entry |
| `docs/sprint-artifacts/e15-s1-extraction-log-panel.md` | New story file |
| `docs/sprint-artifacts/e15-s2-extraction-monitor-page.md` | New story file |
| `docs/sprint-artifacts/e16-s1-dashboard-home.md` | New story file |
| `docs/sprint-artifacts/e16-s2-record-detail-panel.md` | New story file |
| `docs/sprint-artifacts/e16-s3-empty-states.md` | New story file |
