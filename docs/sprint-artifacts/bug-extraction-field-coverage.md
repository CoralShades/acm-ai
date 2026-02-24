# Bug: Extraction Field Coverage — 56% of CSV Columns Mapped

**Status:** drafted
**Priority:** P1 (Medium)
**Discovered:** 2026-02-25 (E2E Test Report + Manual CSV Review)
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
1. [ ] Add `date_of_inspection: Optional[str]` to `ACMExtractionRecord` and `ACMRecord`
2. [ ] Update extraction prompt to capture Date of Inspection from PDF
3. [ ] Add migration for `date_of_inspection` column on `acm_record` table

### Phase 2: Medium Priority (P1)
4. [ ] Add building-level fields: `address`, `suburb`, `postcode`, `building_type` to domain
5. [ ] Add `floor_level` to `ACMRecord` domain model (already in extraction schema)
6. [ ] Add `additional_comments: Optional[str]` to extraction + domain
7. [ ] Add removal tracking: `quantity_removed`, `removal_notification_no`, `epa_certificate_no`

### Phase 3: Quality (P2)
8. [ ] Fix UI column labels to match schema field names (location → location, product → product)
9. [ ] Consider extracting ACM Product Group/Type directly from PDF instead of post-hoc classification

## Technical Notes

- Building-level fields (address, suburb, postcode) should probably be on the `BuildingExtractionPlan` or a new `Building` domain entity, not duplicated per record
- The `floor_level` gap is particularly impactful because it IS already extracted by the LLM but silently dropped when `ACMExtractionRecord` is converted to `ACMRecord`
- The extraction prompt (`building_extraction.jinja`) would need updates to request newly added fields
