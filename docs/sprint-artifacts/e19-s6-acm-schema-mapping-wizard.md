# Story E19-S6: ACM Schema Mapping Wizard — Step 2

**Epic:** E19 — Standard User UX Redesign
**Priority:** P0
**Status:** backlog
**Change Proposal:** SCP-20260224 (2026-02-24)
**Depends on:** E19-S5

---

## User Story

**As a** compliance officer reviewing extracted ACM records,
**I want to** see all records organised by building in per-building tabs with all 29 ACM fields editable,
**So that** I can verify, correct, and approve records before publishing them to the official ACM Register.

---

## Background

After building review (Step 1), all extracted records are assigned to buildings (or flagged as unassigned). Step 2 presents records using the 29-field ACM schema (`docs/samplePDF/acm_data-schema.md`) in per-building tabs with an inline-editable AG Grid. This is the final human checkpoint before records are published to the global register.

---

## Acceptance Criteria

### Wizard Navigation
- [x] Route: `/jobs/{source_id}/review/records`
- [x] Wizard step indicator: "Step 2 of 2: Review ACM Records" with progress bar
- [x] [← Back: Buildings] button: returns to Step 1 without losing changes
- [x] [Publish to Register →] button: sets `source.review_status = 'published'`, records visible in global register
- [x] Sets `source.review_status = 'acm_review'` when step opens
- [x] Confirmation dialog before publishing: "Publish 32 records to ACM Register? This cannot be undone."

### Per-Building Tab Navigation
- [x] Building tabs rendered at top (reuse existing `BuildingTabs.tsx` component)
- [x] One tab per building detected in Step 1
- [x] Additional tabs: "Unassigned Records" (if any records have no building), "All Records"
- [x] Tab badge shows record count: "Broadmeadows PS (28)"
- [x] "Unassigned (4)" tab shown in amber if unassigned records exist

### ACM Records Grid (29 fields from acm_data-schema.md)
- [x] Inline-editable AG Grid per building tab
- [x] Default visible columns (editable inline):

| Schema Field | DB Field |
|-------------|----------|
| Building Code | building_id |
| Internal/External | area_type |
| No Access | (new flag field — see below) |
| Level | level |
| Room Or Area | room_name |
| Location in Room/Area | location |
| ACM Name | product |
| Friability Of Material | friable |
| ACM Product Group | acm_product_group |
| ACM Product Type | acm_product_type |
| SMF Present | (new optional field) |
| Sample no | nata_sample_number |
| Sample Result | sample_result |
| Identifying Company | identifying_company |
| Condition | material_condition |
| Disturbance Potential | disturbance_potential |
| Quantity | quantity |
| ACM Labelled | acm_labelled |
| ACM Label Details | acm_label_details |
| Hygienist Recommendations | hygienist_recommendations |
| Additional Comments | additional_comments |
| PSB Supplied ACM ID | psb_acm_id |
| Removal Status | assumed_removed |
| Date Of Removal | date_of_removal |
| Quantity Removed | quantity_removed |
| Clearance Certificates Available | epa_certificate_no |
| Asbestos Removal Notification No | removal_notification_no |
| EPA Waste Record | (maps to epa_certificate_no or new field) |

- [x] All fields inline-editable with appropriate input types
- [x] Changes saved immediately via `PUT /api/acm/records/{id}` (debounced 500ms)
- [x] Enum fields use dropdown select (Sample Result, Condition, Disturbance Potential, Friability)
- [x] "Not Sampled" and "No Access" records shown with distinct amber row highlight

### Record Actions
- [x] [+ Add Record] — adds a blank record row assigned to current building tab
- [x] [Delete] — removes a mis-extracted record
- [x] [Merge Duplicate] — opens a merge modal comparing two similar rows; merges fields and deletes duplicate

### Live Updates
- [x] Grid updates immediately when a field is saved (no page reload)
- [x] Record count badges on building tabs update as records are added/deleted

---

## Technical Notes

### New Fields Required
Two new fields on `acm_record` not currently in the schema:
```surql
DEFINE FIELD no_access ON acm_record TYPE option<bool> DEFAULT false;
DEFINE FIELD smf_present ON acm_record TYPE option<string>;  -- "Yes" / "No" / "Unknown"
```
Add to Migration 032 or as a new Migration 033.

### Publish API
```
POST /api/acm/jobs/{source_id}/publish
```
Sets `source.review_status = 'published'`. After this:
- `GET /api/acm/records` (no source_id filter) returns records from all published sources
- Existing global register view remains unaffected

### BuildingTabs.tsx Integration
Existing `BuildingTabs.tsx` component renders tabs per building. Pass building list from Step 1 review as props. Add "Unassigned" and "All Records" tabs programmatically.

### Existing Enum Dropdown Values
Use `register_enums.json` from `docs/samplePDF/instructions-sample/register_enums.json` as the source for dropdown options. These are already loaded in the system via field schema config (E1-S11).

---

## Key Files Created/Modified

| File | Change |
|------|--------|
| `frontend/src/app/jobs/[id]/review/records/page.tsx` | **New** — Step 2 wizard page |
| `frontend/src/components/acm/ACMReviewGrid.tsx` | **New** — 29-field editable records grid |
| `frontend/src/components/acm/BuildingTabs.tsx` | Modified — add Unassigned + All Records tabs |
| `frontend/src/components/acm/RecordMergeModal.tsx` | **New** — duplicate merge modal |
| `api/routers/acm.py` | Modified — add POST /jobs/{id}/publish |
| `migrations/032_review_status.surql` | Modified — add no_access and smf_present fields |

---

## Dev Notes

No API cost risk — no extraction LLM calls.

The publish action is irreversible in the current flow. After publishing, `source.review_status = 'published'` and records appear in the global register. Re-extraction is possible from the Job Detail page (E19-S7) which will set `review_status = 'pending_review'` again and require a new review cycle.

---

## Estimated Effort

L (Large) — New wizard page, adapted AG Grid for 29 fields, per-building tab integration, merge modal, publish API.

---

**Story Status:** ⬜ BACKLOG
