# Story E16-S2: ACM Record Detail Slide-Out Panel

**Epic:** E16 — UX Enhancement Sprint
**Priority:** P0
**Status:** backlog
**Change Proposal:** SCP-20260220 (2026-02-20)

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
- [ ] Clicking any row in the ACM grid opens a right-side slide-out drawer (380px width)
- [ ] Clicking the same row again, or pressing Escape, closes the panel
- [ ] ← → arrow keys cycle through records (previous/next in current sort order)
- [ ] Panel animates in/out smoothly (slide from right, 200ms)
- [ ] Grid stays interactive while panel is open (user can scroll, filter, etc.)
- [ ] Selected row is highlighted in the grid while panel is open

### Field Display
All 47 fields organized into labeled sections:

- [ ] **Organisation** — department, agency, sub_agency, site_name, building_code
- [ ] **Building** — address, suburb, postcode, state, year_built, floor_count, building_size_sqm, construction_type, roof_type
- [ ] **Location** — area_type, level, room_id, room_name, location, building_name
- [ ] **ACM Details** — product, friable, product_group, product_type, nata_sample_no, sample_result, quantity, floor_level
- [ ] **Assessment** — condition_rating, disturbance_potential, extent, risk_status, identification_company
- [ ] **Documentation** — labelled, label_details, recommendations, comments, photo_reference, acm_labelled
- [ ] **Removal Tracking** — psb_acm_id, date_removed, epa_certificate_no, removal_contractor
- [ ] **Metadata** — page_number, extraction_confidence, created_at, updated_at

- [ ] Empty/null fields shown as "—" (not blank)
- [ ] Extraction confidence shown as `%` badge (e.g., "94%") if available
- [ ] Boolean fields (`friable`, `labelled`, `acm_labelled`) shown as YES / NO badges

### PDF Citation
- [ ] "View in PDF" button visible if `page_number` is set
- [ ] Clicking opens the existing PDF viewer modal (E3) at the stored page_number

### Edit Mode
- [ ] "Edit" toggle button in panel header
- [ ] In edit mode: all fields become inline inputs (text, number, select as appropriate)
- [ ] "Save" button calls `PUT /api/acm/{id}`
- [ ] "Cancel" button reverts to read mode without saving
- [ ] Toast notification on save success / error

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
ACMSpreadsheet
  ├── ACMGrid (AG Grid)
  └── ACMRecordDetailPanel (new, conditional render)
      ├── RecordFieldSection (reusable section header + field list)
      ├── ViewInPDFButton (wraps existing PDFViewer trigger)
      └── RecordEditForm (edit mode fields)
```

---

## Key Files to Create/Modify

| File | Change |
|------|--------|
| `frontend/src/components/acm/ACMRecordDetailPanel.tsx` | New slide-out panel |
| `frontend/src/components/acm/RecordFieldSection.tsx` | New field section component |
| `frontend/src/components/acm/ACMSpreadsheet.tsx` | Mount panel, wire row click |
| `frontend/src/components/acm/ACMGrid.tsx` | `onRowClicked` handler, row highlight |
| `frontend/src/lib/hooks/use-acm-record.ts` | New hook: fetch + update single record |

---

## Dependencies

- **Requires:** E2-S2 (done ✓ — ACMSpreadsheet), E3-S2 (done ✓ — PDF viewer modal)
- **Blocks:** nothing

---

## Estimated Effort

M (Medium) — New panel component + wiring into existing grid. Edit mode adds some complexity. No new backend needed.
