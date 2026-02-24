# Bug: Extraction Field Coverage — 56% of CSV Columns Mapped

**Status:** done
**Priority:** P1 (Medium)
**Discovered:** 2026-02-25 (E2E Test Report + Manual CSV Review)
**Completed:** 2026-02-25
**Report:** [docs/reviews/e2e-test-report-20260225.md](../reviews/e2e-test-report-20260225.md)

---

## Description

The ACM extraction schema (`ACMExtractionRecord`) only maps 24 of 43 columns present in the Clutch_Broadmeadows.csv reference file. This means 19 CSV columns — including compliance-critical fields like Date of Inspection, Building Address, and removal tracking — are not captured during extraction.

Additionally, some fields that ARE extracted (e.g., `floor_level`) are lost during persistence because the domain model (`ACMRecord`) doesn't include them.

## Field Gap Summary

### HIGH Priority — Missing Schema Fields (Compliance Critical)

| CSV Column | Impact | Notes |
|-----------|--------|-------|
| **Date of Inspection** | Compliance tracking | No field in extraction or domain schema |

### MEDIUM Priority — Missing Schema Fields

| CSV Column | Impact | Notes |
|-----------|--------|-------|
| Building Address | BAR register export | Building-level field, not per-record |
| Suburb | BAR register export | Building-level field |
| Postcode | BAR register export | Building-level field |
| Building Type | Risk context | "Police Station", "School", etc. |
| Additional Comments | Data completeness | Free-text observations |
| Quantity Removed | Removal compliance | Removal tracking |
| Asbestos Removal Notification No | Regulatory | Removal tracking |
| EPA Waste Transport Certificate No | Regulatory | Removal tracking |

### MEDIUM Priority — Data Loss at Persistence

| Extraction Field | Domain Field | Issue |
|-----------------|-------------|-------|
| `floor_level` | NOT IN ACMRecord | Extracted but lost during save |

### LOW Priority — Not Currently Needed

| CSV Columns | Category |
|------------|----------|
| Department, Agency, Sub Agency | Org hierarchy (3 columns) |
| Owned or Leased, Frequency of use, Public Access? | Building admin (3 columns) |
| Est. Building Size (m2), Number of Levels, Roof Type | Building metadata (3 columns) |

### INFO — Reverse Gaps (Extraction Re-classifies)

| Field | CSV | Extraction | Notes |
|-------|-----|-----------|-------|
| ACM Product Group | Native in CSV | Post-hoc classification (E1-S9) | Extraction ignores CSV value; re-classifies |
| ACM Product Type | Native in CSV | Post-hoc classification (E1-S9) | Same as above |

### LOW — UI Naming Mismatch (Not Real Gaps)

| UI Label | Actual Schema Field | Notes |
|----------|-------------------|-------|
| `location_detail` | `location` | Phantom field — data exists in `location` |
| `item_name` | `product` | Phantom field — data exists in `product` |
| `room_area` (float) | `room_name` (string) | Different semantics — `room_area` is for SAMP numeric area |

## Acceptance Criteria

### Phase 1: High Priority (P0)
1. [x] Add `date_of_inspection: Optional[str]` to `ACMExtractionRecord` and `ACMRecord`
2. [x] Update extraction prompt to capture Date of Inspection from PDF
3. [x] Add migration for `date_of_inspection` column on `acm_record` table

### Phase 2: Medium Priority (P1)
4. [x] Add building-level fields: `address`, `suburb`, `postcode`, `building_type` to domain
5. [x] Add `floor_level` to `ACMRecord` domain model (already in extraction schema)
6. [x] Add `additional_comments: Optional[str]` to extraction + domain
7. [x] Add removal tracking: `quantity_removed`, `removal_notification_no`, `epa_certificate_no`

### Phase 3: Quality (P2)
8. [ ] Fix UI column labels to match schema field names (location → location, product → product)
9. [ ] Consider extracting ACM Product Group/Type directly from PDF instead of post-hoc classification

## Technical Notes

- Building-level fields (address, suburb, postcode) should probably be on the `BuildingExtractionPlan` or a new `Building` domain entity, not duplicated per record
- The `floor_level` gap is particularly impactful because it IS already extracted by the LLM but silently dropped when `ACMExtractionRecord` is converted to `ACMRecord`
- The extraction prompt (`building_extraction.jinja`) would need updates to request newly added fields

---

## Implementation (2026-02-25)

### Phase 1 (CG2): `date_of_inspection` + `floor_level`
- **`open_notebook/domain/acm.py`**: Added `floor_level: Optional[str]` and `date_of_inspection: Optional[str]` to `ACMRecord`
- **`open_notebook/extractors/acm_schemas.py`**: Added `date_of_inspection: Optional[str]` to `ACMExtractionRecord` (`floor_level` was already there)
- **`open_notebook/graphs/acm_extraction.py`**: Updated extraction→domain mapping to pass both fields
- **`prompts/acm/building_extraction.jinja`**: Added report_date hint and `date_of_inspection` to Highly Recommended Fields
- **`migrations/35.surrealql`**: Adds `floor_level` and `date_of_inspection` to `acm_record` table

### Phase 2 (CG3): Building-level + Removal Tracking + Comments
- **`open_notebook/domain/acm.py`**: Added 8 fields: `building_address`, `suburb`, `postcode`, `building_type`, `quantity_removed`, `removal_notification_no`, `epa_certificate_no`, `additional_comments`
- **`open_notebook/extractors/acm_schemas.py`**: Added 4 extraction fields: `quantity_removed`, `removal_notification_no`, `epa_certificate_no`, `additional_comments`
- **`open_notebook/graphs/acm_extraction.py`**: Updated extraction→domain mapping for 4 new extraction fields
- **`prompts/acm/building_extraction.jinja`**: Added guidance for all 4 new extraction fields
- **`migrations/36.surrealql`**: Adds 8 fields to `acm_record` table

### Type Generation
- Fixed `scripts/generate_types.py` for Windows compatibility (`shell=True`, continue-on-error)
- Regenerated `frontend/src/lib/types/generated/ACMRecord.ts` and `ACMExtractionRecord.ts`
- Updated manually-maintained `frontend/src/lib/types/acm.ts` with 10 new fields

### Design Decision (AD-2)
Building-level fields (`building_address`, `suburb`, `postcode`, `building_type`) are denormalized onto `ACMRecord` rather than stored on a separate `Building` entity. This simplifies export and BAR register generation at the cost of some data duplication.
