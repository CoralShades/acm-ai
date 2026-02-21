# Story E16-S2: ACM Record Detail Slide-Out Panel

**Epic:** E16 — UX Enhancement Sprint
**Priority:** P0
**Status:** done
**Completed:** 2026-02-21
**Change Proposal:** SCP-20260220 (2026-02-20)
**Implementation Method:** Ralph autonomous loop (ralph_loop.sh --max 10, 1 iteration, 967s)

---

## User Story

**As a** compliance officer reviewing records,
**I want to** click an ACM record row to see all its fields in a readable panel,
**So that** I can review full record details without horizontal scrolling or opening separate pages.

---

## Background

The ACM grid has 47 fields but only a fraction are visible at any time. E3 (Cell Citations & PDF Viewer) allows clicking a cell to jump to the PDF, but there's no way to read the full record in one place. Users must scroll horizontally or use column visibility to find fields they need.

---

## Acceptance Criteria

### Panel Behaviour
- [x] Clicking any row in the ACM grid opens a right-side slide-out drawer (380px width)
- [x] Clicking the same row again, or pressing Escape, closes the panel
- [x] ← → arrow keys cycle through records (previous/next in current sort order)
- [x] Panel animates in/out smoothly (slide from right, 200ms)
- [x] Grid stays interactive while panel is open (user can scroll, filter, etc.)
- [x] Selected row is highlighted in the grid while panel is open

### Field Display
All 47 fields organized into labeled sections:

- [x] **Organisation** — department, agency, sub_agency, site_name, building_code
- [x] **Building** — address, suburb, postcode, state, year_built, floor_count, building_size_sqm, construction_type, roof_type
- [x] **Location** — area_type, level, room_id, room_name, location, building_name
- [x] **ACM Details** — product, friable, product_group, product_type, nata_sample_no, sample_result, quantity, floor_level
- [x] **Assessment** — condition_rating, disturbance_potential, extent, risk_status, identification_company
- [x] **Documentation** — labelled, label_details, recommendations, comments, photo_reference, acm_labelled
- [x] **Removal Tracking** — psb_acm_id, date_removed, epa_certificate_no, removal_contractor
- [x] **Metadata** — page_number, extraction_confidence, created_at, updated_at

- [x] Empty/null fields shown as "—" (not blank)
- [x] Extraction confidence shown as `%` badge (e.g., "94%") if available
- [x] Boolean fields (`friable`, `labelled`, `acm_labelled`) shown as YES / NO badges

### PDF Citation
- [x] "View in PDF" button visible if `page_number` is set
- [x] Clicking opens the existing PDF viewer modal (E3) at the stored page_number

### Edit Mode
- [x] "Edit" toggle button in panel header
- [x] In edit mode: all fields become inline inputs (text, number, select as appropriate)
- [x] "Save" button calls `PUT /api/acm/{id}`
- [x] "Cancel" button reverts to read mode without saving
- [x] Toast notification on save success / error

---

## Technical Notes

### AG Grid Row Click
AG Grid fires `onRowClicked` event. Extract `data.id` and use it to:
1. Set selected record ID in component state
2. Fetch full record: `GET /api/acm/{id}` (to get all 47 fields, not just grid columns)

### Existing API
`GET /api/acm/{id}` and `PUT /api/acm/{id}` both exist in `api/routers/acm.py`. Verify they return/accept all 47 fields.

### Component Architecture
```
ACMTab (parent)
  ├── ACMGrid (AG Grid)
  └── ACMRecordDetailPanel (new, conditional render)
      ├── RecordFieldSection (reusable section header + field list)
      └── EditableFields (inline edit mode, local to panel)
```

Note: `ACMSpreadsheet` is not a separate component — `ACMTab` is the parent that was wired to mount the panel.

---

## Key Files Created/Modified

| File | Change | Lines |
|------|--------|-------|
| `frontend/src/components/acm/ACMRecordDetailPanel.tsx` | **New** — slide-out panel with inline editing | +545 |
| `frontend/src/components/acm/RecordFieldSection.tsx` | **New** — field section header + list component | +82 |
| `frontend/src/lib/hooks/use-acm-record.ts` | **New** — fetch + update single record hook | +62 |
| `frontend/src/components/acm/ACMGrid.tsx` | Modified — row highlighting via `getRowClass` | +33 |
| `frontend/src/components/acm/ACMTab.tsx` | Modified — mounted panel, replaced dialog with panel | +80 |

**Total:** 653 insertions, 54 deletions across 5 files

---

## Dev Agent Record

### Implementation Summary

Implemented by Ralph autonomous loop in a single 967-second iteration (2026-02-21 04:37–04:53 UTC). Two commits:

1. **`4e8277e`** — Stub files created (ACMRecordDetailPanel returning null, RecordFieldSection, use-acm-record)
2. **`e929926`** — Full implementation (545-line panel replacing stub)

### Key Design Decisions

**Panel structure:** Uses shadcn/ui `Sheet` component with `side="right"` and fixed 380px width. CSS translate animation (200ms ease-in-out) provides smooth slide-in/out. z-index 40 ensures panel overlays grid without blocking toolbar.

**Toggle semantics:** Clicking the same row that is already selected closes the panel (handled in `ACMTab.handleRowClick` by comparing `panelRecordId === data.id`). This mirrors Outlook/Gmail convention.

**Keyboard navigation:** Arrow key listeners use `document.activeElement` to check whether focus is inside an input — arrow keys only trigger record navigation when focus is NOT in a text/number/select field. Escape first exits edit mode before closing the panel.

**Edit state:** Controlled `editData` state object, reset on `recordId` change, uses merge semantics for partial updates. Save dispatches `PUT /api/acm/{id}` via the `updateRecord` mutation from `useACMRecordDetail`.

**Row highlighting:** `getRowClass` callback on AG Grid compares each row's `data.id` with `selectedRecordId`. CSS uses HSL oklch variables: `--primary` with 12% opacity fill + 3px left border (20% opacity in dark mode). `redrawRows()` triggered via `useEffect` on `selectedRecordId` change.

**Navigation state:** `panelIndex` is a `useMemo` over `filteredRecords` (the visible AG Grid data after filtering). `hasPrev`/`hasNext` disable navigation buttons at list boundaries.

**PDF citation:** When "View in PDF" is clicked, `ACMTab.handlePanelViewInPDF` constructs a `CellSelectionDetails` object and invokes the existing `ACMCellViewer` modal — no new backend needed.

### Notes & Deviations from Tech Spec

1. **`ACMSpreadsheet.tsx` not used** — the tech spec listed this file but it doesn't exist as a separate component. `ACMTab.tsx` is the actual parent component; integration was done there instead.
2. **`RecordEditForm` not a separate file** — edit mode UI (`EditableFields`) lives inline in `ACMRecordDetailPanel.tsx` rather than as a standalone component, keeping co-location and reducing file proliferation.
3. **8 sections, not 7** — Metadata is displayed as a final section (8th), not embedded in other sections. This improves clarity.

---

## Verification

### Build Verification (2026-02-21)

| Check | Result |
|-------|--------|
| `cd frontend && npm run build` | ✅ PASS — 21/21 pages generated |
| `cd frontend && npm run lint` | ✅ PASS — 0 ESLint errors |
| `uv run ruff check .` | ✅ PASS (7 auto-fixed I001 in `tests/test_ara_format.py`, pre-existing) |
| `uv run pytest` | ✅ 496 passed, 2 xfailed, 1 infra failure (no SurrealDB) |

### Pytest Failure Note
`tests/test_field_config_api.py::TestUpdateFieldConfig::test_update_field_config_toggle_active` fails because the test calls `PUT /api/acm/field-config` which requires a live SurrealDB connection (port 8000). This is a **pre-existing infrastructure issue** unrelated to E16-S2 (test added in E1-S11 commit `3834f23`).

### Files Verified
- [x] `frontend/src/components/acm/ACMRecordDetailPanel.tsx` — exists, 545 lines
- [x] `frontend/src/components/acm/RecordFieldSection.tsx` — exists, 82 lines
- [x] `frontend/src/lib/hooks/use-acm-record.ts` — exists
- [x] `frontend/src/components/acm/ACMGrid.tsx` — row highlighting added
- [x] `frontend/src/components/acm/ACMTab.tsx` — panel wired in

---

## Dependencies

- **Requires:** E2-S2 (done ✓ — ACMSpreadsheet), E3-S2 (done ✓ — PDF viewer modal)
- **Blocks:** nothing

---

## Estimated Effort

M (Medium) — New panel component + wiring into existing grid. Edit mode adds some complexity. No new backend needed.

---

**Story Status:** ✅ DONE
**Completion Date:** 2026-02-21
**Implementation:** Ralph autonomous loop (1 iteration / 967s)
**Commits:** `4e8277e`, `e929926` (feat), `3e4d7b0` (lint fix), `9b9c97e` (tracking)
**Next Recommended Stories:** E15-S1 Extraction Log Panel, E16-S1 Dashboard Home, E16-S3 Empty States
