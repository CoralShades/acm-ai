# Story E19-S5: Building Review Wizard — Step 1

**Epic:** E19 — Standard User UX Redesign
**Priority:** P0
**Status:** backlog
**Change Proposal:** SCP-20260224 (2026-02-24)
**Depends on:** E19-S4

---

## User Story

**As a** compliance officer reviewing an extraction result,
**I want to** see a list of all detected buildings with their 21 metadata fields in an editable grid,
**So that** I can verify, correct, and confirm building-level information before it appears in the ACM Register.

---

## Background

After extraction, raw records exist in the database but building metadata (address, type, year, etc.) may be incomplete or incorrectly detected. Step 1 of the review wizard presents all buildings detected in the document as an editable table using the 21-field building schema (`docs/samplePDF/building_data-schema.md`). Building data maps to existing `site_config` table fields and `acm_record` building fields — no new DB table needed.

---

## Acceptance Criteria

### Wizard Navigation
- [x] Route: `/jobs/{source_id}/review/buildings`
- [x] Wizard step indicator: "Step 1 of 2: Review Buildings" with progress bar
- [x] [← Cancel] button: returns to raw extraction table without saving
- [x] [Next: Review Records →] button: saves building data, advances to Step 2 (E19-S6)
- [x] Sets `source.review_status = 'building_review'` when step opens
- [x] Sets `source.review_status = 'acm_review'` when user clicks [Next]

### Building Grid (21 fields from building_data-schema.md)
- [x] Each detected building shown as an editable row
- [x] Columns (mapped to existing DB fields):

| Schema Field | DB Field | Source Table |
|-------------|----------|-------------|
| Organisation | department + agency | site_config |
| Site Name | site_name | acm_record (from source config) |
| Building Name | building_name | acm_record |
| Building Type | building_type | site_config |
| Building Address | building_address | acm_record |
| Suburb | suburb | acm_record |
| Postcode | postcode | acm_record |
| Owned or Leased | owned_or_leased | site_config |
| Building Unique ID | building_unique_id | site_config |
| Frequency of use | frequency_of_use | site_config |
| Public Access? | public_access | site_config |
| Date of Audit Report | date_of_inspection | acm_record |
| Estimated Year Built | building_year | acm_record |
| Est. Building Size (m2) | building_size_m2 | acm_record |
| Number of Levels | number_of_levels | acm_record |
| Construction Type | building_construction | acm_record |
| Roof Type | roof_type | acm_record |
| PSB District/Region | sub_agency | site_config |
| Building Out of Scope | (new site_config flag) | site_config |
| Building Out of Scope Comments | (new site_config field) | site_config |
| Additional Comments | additional_comments | site_config |

- [x] All fields inline-editable (text input, date picker, number input as appropriate)
- [x] Changes auto-saved to `site_config` and `acm_record` building fields in real time (debounced 500ms)

### Building Actions
- [x] [+ Add Building] — adds a blank building row (for buildings the AI missed)
- [x] [Mark Out of Scope] — sets `building_out_of_scope = true` flag; building's records move to "Unassigned" tab in Step 2
- [x] [Remove Building] — removes a mis-detected building row (records become unassigned)

### Unassigned Records Indicator
- [x] Counter badge: "X records not assigned to any building" shown in header
- [x] [View Unassigned Records] link opens a modal showing unassigned raw records

---

## Technical Notes

### New API Endpoint
```
GET /api/acm/jobs/{source_id}/buildings
```
Returns distinct buildings for a source, merging `site_config` and unique `building_id` values from `acm_record`:
```json
[
  {
    "building_id": "broadmeadows_police_main",
    "building_name": "Broadmeadows Police Station",
    "building_type": "Police Station",
    "department": "DJCS",
    "agency": "Victoria Police",
    ...
  }
]
```

```
PUT /api/acm/jobs/{source_id}/buildings/{building_id}
```
Updates site_config and/or building fields on all acm_record rows with that building_id.

### site_config Schema Extension
Add two new fields to `site_config`:
```surql
DEFINE FIELD building_out_of_scope ON site_config TYPE option<bool> DEFAULT false;
DEFINE FIELD building_out_of_scope_comments ON site_config TYPE option<string>;
```
These do NOT require a new migration number — can be bundled into Migration 032 (E19-S1) or as an addendum.

### Existing Components to Extend
- `SiteConfigForm.tsx` — extend to handle the full 21-field set
- `SiteConfigPanel.tsx` — wire into wizard step layout

---

## Key Files Created/Modified

| File | Change |
|------|--------|
| `frontend/src/app/jobs/[id]/review/buildings/page.tsx` | **New** — Step 1 wizard page |
| `frontend/src/components/acm/BuildingReviewGrid.tsx` | **New** — 21-field editable building grid |
| `frontend/src/components/acm/WizardStepHeader.tsx` | **New** — reusable step indicator + progress bar |
| `api/routers/acm.py` | Modified — add /jobs/{id}/buildings GET + PUT |
| `migrations/032_review_status.surql` | Modified — add out_of_scope fields to site_config |

---

## Dev Notes

No API cost risk — this story has no extraction LLM calls.

The building aggregation query in SurrealDB:
```surql
SELECT DISTINCT building_id, building_name, building_address, building_year
FROM acm_record
WHERE source_id = $source_id;
```
Then merge with `site_config` for the site_config fields. Return the merged result as the 21-field building object.

---

## Estimated Effort

L (Large) — New wizard page, new editable building grid, new API endpoints, schema extension.

---

**Story Status:** ⬜ BACKLOG
