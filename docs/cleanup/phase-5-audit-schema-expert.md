# Phase 5 Audit — Schema Expert Report

**Agent:** SCHEMA-EXPERT
**Date:** 2026-04-11
**Branch:** `feat/sf-reconciliation-20260411`
**Scope:** SurrealDB migrations, Pydantic domain models, field_schema config, E38-S2 migration plan
**Mode:** READ-ONLY — no code changes made

---

## 1. Scope

Files inspected:
- `open_notebook/domain/acm.py` — `ACMRecord`, `BuildingRecord`
- `migrations/10–56.surrealql` — table definitions and field additions
- `config/sf-schema-snapshot.json` — new extractable-only snapshot (25 Building, 27 Item fields)
- `V3/output/building_fields_summary.md`, `V3/output/item_fields_summary.md` — stale V3 markdown
- `open_notebook/extractors/parsers/config_loader.py` — runtime schema loader
- `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260411-sf-reconciliation.md` — E38-S2 scope
- `docs/cleanup/assumptions-and-decisions.md` — DEC-001 through DEC-020

Governing rule: **DEC-001** — only fields literally extractable from ARA PDFs are in scope. Fields that exist in SF but are populated by SF workflows, formula engines, or admin input are excluded.

---

## 2. Findings

### 2.1 Dead Fields on `BuildingRecord` — 21 fields

These are Pydantic fields on `open_notebook/domain/acm.py:BuildingRecord` whose SF aliases either do not exist in the live describe or are outside the extractable set per `config/sf-schema-snapshot.json`.

#### 2.1.1 Fully fabricated (no live SF backing — confirmed against `sf-describe/Building__c.json`)

| Python field | SF alias (used) | Reason |
|---|---|---|
| `building_code` | `Building_Code__c` | `Building_Code__c` does not exist on `Building__c` — it exists on `Item__c` as the master-detail parent reference. Wrong object entirely. |
| `building_sub_category` | `Building_Sub_Category__c` | Not found in live SF describe (grep returns 0 hits in `sf-describe/Building__c.json`). Fully fabricated. |

#### 2.1.2 Real SF fields, but outside the extractable snapshot (not populatable from ARA PDFs)

| Python field | SF alias | SF field type | Why excluded |
|---|---|---|---|
| `building_address_lga` | `Building_Address_LGA__c` | restricted picklist | Auto-populated by Meshblock geocoding; not in PDF |
| `building_address_region` | `Building_Address_Region__c` | restricted picklist | Auto-populated by geocoding; not in PDF |
| `est_building_size_m2` | `Est_Building_Size_m2__c` | string(255) | Real SF field (V3 row 56), but not in extractable snapshot. Phase 2b incorrectly stated "no SF field" — the field exists. It was correctly excluded from export, but the label "fabricated" in the session log was wrong. |
| `daily_duration` | `Daily_Duration__c` | picklist | Hours of daily access — not in ARA PDFs |
| `level_of_activity` | `Level_of_Activity__c` | picklist | Activity intensity — not in ARA PDFs |
| `mobile_plant` | `Mobile_Plant__c` | picklist | Forklift/scissor lift flag — not in ARA PDFs |
| `no_identified_acms` | `No_Identified_ACMs__c` | boolean (default=false) | Operational boolean; not extractable |
| `no_identified_acms_note` | `No_Identified_ACMs_Note__c` | textarea(255) | Operational note; not extractable |
| `building_out_of_scope` | `Building_Out_Of_Scope_New__c` | picklist | Operational flag; not in ARA PDFs |
| `building_out_of_scope_comments` | `Building_Out_Of_Scope_Comments__c` | textarea | Operational; not in ARA PDFs |
| `demolished_status` | `Demolished_Status__c` | restricted picklist | Operational; not in ARA PDFs |
| `demolition_date` | `Demolition_Date__c` | date | Operational; not in ARA PDFs |
| `demolition_type` | `Demolition_Type__c` | restricted picklist | Operational; not in ARA PDFs |
| `demolition_comments` | `Demolition_Comments__c` | textarea | Operational; not in ARA PDFs |
| `psb_district_region` | `PSB_District_Region__c` | string(255) | District designation; not in ARA PDFs |
| `country` | `Country__c` | string(255) | Real SF field but not in snapshot; value is always "Australia", no extraction value |
| `capital_works_project_details` | `Capital_Works_Project_Provide_Details__c` | textarea | Operational; not in ARA PDFs |
| `possible_capital_works_project` | `Possible_Capital_Works_Project__c` | boolean | Operational boolean; not extractable |
| `building_risk_rating` | `Building_Risk_Rating__c` | string(255) | System-generated asset rating; not extractable |

**BuildingRecord dead field count: 21**

Missing from `BuildingRecord` but IS in extractable snapshot: `responsible_agency_department` → `Responsible_Agency_Department__c` (gap, not dead field).

---

### 2.2 Dead Fields on `ACMRecord` — 25 fields

#### 2.2.1 Fully fabricated (no live SF backing — confirmed against `sf-describe/Item__c.json` and `V3/output/item_fields_summary.md`)

| Python field | SF alias | Reason |
|---|---|---|
| `school_name` | (none) | No `Item__c` field for school name. School is a Building__c-level concept. |
| `school_code` | (none) | Same — no Item__c field. |
| `building_year` | `Building_Year__c` | `Building_Year__c` does not exist in SF. Building year is `Estimated_Year_Build_New__c` on `Building__c`, not on `Item__c`. |
| `building_construction` | (none) | Denormalized building-level field on Item record. No Item__c field for this. |
| `building_address` | (none) | Denormalized; belongs on `BuildingRecord`. Not on Item__c. |
| `suburb` | (none) | Denormalized; belongs on `BuildingRecord`. Not on Item__c. |
| `postcode` | (none) | Denormalized; belongs on `BuildingRecord`. Not on Item__c. |
| `building_type` | (none) | Denormalized; belongs on `BuildingRecord`. Not on Item__c. |
| `room_id` | `Room_ID__c` | Not found in live SF describe. Phase 2b confirmed deletion from export: "no equivalent". |
| `room_area` | `Room_Area__c` | Not found in live SF describe. No Item__c field for room area. |
| `material_description` | `Material_Description__c` | Not found in live SF describe. BAR-only field (the PDF text column). No SF equivalent. |
| `sample_result` | (none) | No SF alias defined. Redundant with `result` which maps to `Sample_Analysis_Result_Material_Status__c`. Standalone orphan. |
| `acm_labelled` | `ACM_Labelled__c` | `ACM_Labelled__c` does not exist in SF. The real field is `Labelled__c` → `labelled_sf`. Boolean superseded by string picklist. |

#### 2.2.2 Real SF fields, but outside the extractable snapshot

| Python field | SF alias | SF field type | Why excluded |
|---|---|---|---|
| `risk_status` | `Risk_Rating__c` | string(255) | Real SF field "ACM Removal Priority" — but system-assigned, not extractable from ARA PDF rows |
| `hygienist_recommendations` | `Hygienist_Recommendations__c` | textarea(1000) | Real SF field — Phase 2b stated "not a SF field" which was INCORRECT. This IS a real SF field, but currently not in `config/sf-schema-snapshot.json`. Candidate for re-inclusion in E38 schema extension. |
| `psb_supplied_acm_id` | `ID_provided_by_metro__c` | string(100) | Real SF field "PSB Supplied Item ID" — not in extractable snapshot |
| `removal_status` | `Removal_Status__c` | restricted picklist | Real but belongs to Removal_Job__c workflow — out of scope per DEC-001 |
| `date_of_removal` | `Removed_Date__c` | date | Real but Removal_Job__c domain — out of scope |
| `quantity_removed` | `Quantity_Removed__c` | double | Real but Removal_Job__c domain — out of scope |
| `removal_notification_no` | `Asbestos_Removal_Notification_No__c` | string(255) | Real but Removal_Job__c domain — out of scope |
| `epa_certificate_no` | `EPA_Waste_Transport_Certificate_No__c` | string(255) | Real but Removal_Job__c domain — out of scope |
| `no_access` | `No_Access__c` | boolean (default=false) | Real but operational boolean; not extractable from PDF |
| `smf_present` | `SMF_Present__c` | boolean | Real but operational boolean; not extractable from PDF |
| `assea_risk_level` | `ASSEA_Survey_Guide_Risk_Level__c` | restricted picklist | Real SF field but not in extractable snapshot. Could be in some PDFs — worth reviewing for E38 schema extension. |
| `date_identified` | `Date_Identified__c` | (not found in item_fields_summary.md) | Not found in V3 describe output; possibly non-existent in live SF |

**ACMRecord dead field count: 25**

**Grand total dead Pydantic fields: 46** (21 BuildingRecord + 25 ACMRecord)

**Note on E38-S2 scope:** The SCP lists 25 specific fields to delete. This audit finds 46. The gap (21 extra) consists mainly of the denormalized building fields on ACMRecord (`school_name`, `school_code`, `building_year`, `building_construction`, `building_address`, `suburb`, `postcode`, `building_type`) and several ACMRecord fields the SCP overlooked (`room_area`, `material_description`, `sample_result`, `acm_labelled`, `no_access`, `smf_present`, `assea_risk_level`, `date_identified`). E38-S2 scope should be expanded accordingly.

---

### 2.3 SurrealDB Schema Drift

The `building_record` table (defined in migration 40, extended in migration 47) contains all 21 dead BuildingRecord fields as explicit `DEFINE FIELD` columns. The `acm_record` table (migrations 10-39) contains the 25 dead ACMRecord fields.

Because both tables are `SCHEMAFULL`, columns must be explicitly defined — they will not auto-drop when the Pydantic model changes. Each dead field requires a `REMOVE FIELD <name> ON TABLE <table>` statement in an E38-S2 migration.

Specific migration origin of dead columns:

| Table | Dead fields | Source migration(s) |
|---|---|---|
| `building_record` | `est_building_size_m2`, `daily_duration`, `level_of_activity`, `mobile_plant`, `no_identified_acms`, `no_identified_acms_note`, `building_out_of_scope`, `building_out_of_scope_comments`, `demolished_status`, `demolition_date`, `demolition_type`, `demolition_comments`, `psb_district_region`, `country`, `capital_works_project_details`, `possible_capital_works_project`, `building_address_lga`, `building_address_region`, `building_code`, `building_risk_rating` | Migration 40 |
| `building_record` | `building_sub_category` | Migration 47 |
| `acm_record` | `school_name`, `school_code`, `room_id`, `room_area`, `material_description`, `risk_status` | Migration 10 |
| `acm_record` | `sample_result`, `acm_labelled`, `hygienist_recommendations`, `psb_supplied_acm_id`, `removal_status`, `date_of_removal` | Migration 11 |
| `acm_record` | `no_access`, `smf_present` | Migration 32 |
| `acm_record` | `building_address`, `suburb`, `postcode`, `building_type`, `quantity_removed`, `removal_notification_no`, `epa_certificate_no` | Migration 36 |
| `acm_record` | `assea_risk_level`, `date_identified` | Migration 39 |
| `acm_record` | `building_year`, `building_construction` | Migration 10 (implicit — no separate column, but Pydantic writes them) |

---

### 2.4 `field_schema` Table vs `config/sf-schema-snapshot.json` — CRITICAL CONFLICT

**Runtime behaviour at `open_notebook/extractors/parsers/config_loader.py:409`:**

```python
SF_SCHEMA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "V3", "output")

def load_sf_field_schema() -> SFSchemaBundle:
    building_path = os.path.join(SF_SCHEMA_DIR, "building_fields_summary.md")
    item_path = os.path.join(SF_SCHEMA_DIR, "item_fields_summary.md")
    ...
```

The loader reads `V3/output/building_fields_summary.md` and `V3/output/item_fields_summary.md` — the stale V3 markdown files that enumerate ALL 132+ Building__c fields and ALL 144+ Item__c fields, including formulas, rollups, geocode fields, and all the fabricated ones.

`config/sf-schema-snapshot.json` is **never read by any runtime code path**. It was committed as a reference document in Phase 2a but no wiring was done to connect it to `load_sf_field_schema()`, the picklist validator, or the normalizer.

**Consequence:** The `SalesforcePicklistValidator` and `sf_normalizer.py` are validating against the stale V3 schema, not the current verified extractable set. Any picklist value that the Phase 2a snapshot added or corrected is NOT enforced at runtime.

**Canonicity verdict:**
- `config/sf-schema-snapshot.json` — the authoritative extractable-only snapshot per SCP, but INERT at runtime
- `V3/output/*.md` — stale, over-inclusive (all fields including non-extractable), but ACTIVE at runtime
- `field_schema:sf_v1` in SurrealDB — populated by migration 38 column additions; actual data population status unknown (no seeding script exists on this branch)

**This is a blocker for E38-S2:** deleting fields without updating `load_sf_field_schema()` will leave the picklist validator referencing deleted field names from stale markdown. The snapshot wiring must be part of E38-S2 or a separate prerequisite story.

---

### 2.5 E38-S2 Migration Safety: Rollback Plan

**Data risk assessment:**
- Pre-production system — no VAEA production deployment
- Migration 32 already ran `DELETE acm_record` (destroyed all rows) — existing `acm_record` data is empty or test-only
- `building_record` rows may exist from test extractions but are not VAEA production records

**Rollback design for E38-S2:**
```sql
-- UP: drop dead columns
REMOVE FIELD est_building_size_m2 ON TABLE building_record;
-- (repeat for all 21+25 dead fields)

-- DOWN: restore columns (no data recovery possible)
DEFINE FIELD IF NOT EXISTS est_building_size_m2 ON TABLE building_record TYPE option<float>;
-- (repeat for all dropped fields)
```

**Key constraints:**
1. SurrealDB `REMOVE FIELD` on a SCHEMAFULL table permanently drops the column and any stored data in it
2. The down migration can restore the schema but cannot recover the data
3. Any live `DEFINE INDEX` referencing a dead field must also be removed (e.g., `acm_fulltext` BM25 index on `acm_record` references `hygienist_recommendations` — migration 27)
4. The BM25 full-text search index at migration 27 includes `hygienist_recommendations` — dropping that field requires rebuilding the index without it
5. `acm_embedding_idx` (migration 12) and related indexes are safe — they reference `embedding` which is an internal field, not a dead SF field

**Recommended migration sequence for E38-S2:**
1. REMOVE dead indexes that reference dying fields (especially migration 27 BM25 index)
2. REMOVE dead fields from `acm_record`
3. REMOVE dead fields from `building_record`
4. REDEFINE the full-text BM25 index with only surviving fields

---

### 2.6 Pydantic Validators with BAR-Only Rules

Validators that encode BAR-specific logic, not SF schema rules:

| Validator | Location | Rule | BAR-only? |
|---|---|---|---|
| `validate_internal_id` | `BuildingRecord:acm.py:953` | `internal_id must start with 'BLD#'` | YES — pure BAR internal ID format |
| `validate_school_name` | `ACMRecord:acm.py:413` | Strip + null empty | Partial — guards `school_name` which is a dead field |
| `validate_material_description` | `ACMRecord:acm.py:436` | Raises if empty | YES — `material_description` has no SF equivalent; guards a dead field |
| `validate_result` | `ACMRecord:acm.py:443` | Raises if empty; `result: str = Field(...)` (required) | Partial — `result` maps to real SF field `Sample_Analysis_Result_Material_Status__c`, but SF treats it as optional (nillable). Treating it as REQUIRED is a BAR-derived constraint. |
| `validate_product` | `ACMRecord:acm.py:429` | Raises if empty; `product: str = Field(...)` (required) | Partial — `product` maps to `Item_Name__c`, which is a picklist in SF but not required. |
| `validate_normalized_action` | `ACMRecord:acm.py:464` | Checks against `CANONICAL_ACTIONS` | YES — `normalized_action` is internal BAR recommendation normalization; no SF equivalent. |
| `validate_extraction_confidence` | `ACMRecord:acm.py:450` | Validates 'high'/'medium'/'low' | Internal — no SF equivalent. Acceptable internal tracking field, not a dead-SF issue. |

**Additional dead-field references in methods:**
- `ACMEmbeddingConfig.include_fields` (`acm.py:38`): includes `risk_status`, `hygienist_recommendations` — both are dead-field references in the embedding config
- `ACMRecord.get_embedding_text()` (`acm.py:635`): references `self.risk_status`, `self.hygienist_recommendations` — will silently emit blank when those fields are dropped

---

## 3. Recommendations

1. **Expand E38-S2 scope from 25 to 46 dead fields.** The SCP's field list was incomplete. Annex the full 21+25 list from this report into the E38-S2 acceptance criteria.

2. **Correct Phase 2b error re: `Est_Building_Size_m2__c` and `Hygienist_Recommendations__c`.** Both ARE real SF fields. `hygienist_recommendations` should be considered for re-inclusion in the extractable snapshot for E38 schema extension (hygienist notes DO appear in ARA PDFs). `Est_Building_Size_m2__c` remains correctly excluded from export as non-extractable, but the session log's claim that it was "fabricated" was wrong.

3. **Wire `config/sf-schema-snapshot.json` into `load_sf_field_schema()` before E38-S2 deletes fields.** Without this, the picklist validator will reference stale schema. Suggested approach: add a JSON loader path in `config_loader.py` that reads `config/sf-schema-snapshot.json` and converts it to `SFSchemaBundle` format; remove the dependency on `V3/output/*.md`.

4. **Include migration 27 BM25 index rebuild in E38-S2.** The `acm_fulltext` index on `acm_record` includes `hygienist_recommendations`. Dropping that field without rebuilding the index will leave a broken index definition in the schema.

5. **Delete `_llm_correct_records()` dead function** (`acm_extraction.py:1853` area). Already deferred in SCP; should be bundled with E38-S2 since the single caller was removed in commit `5dc3ef30`.

6. **BAR-only validators on dead fields** (`validate_school_name`, `validate_material_description`, `validate_normalized_action`) should be removed when their guarded fields are dropped in E38-S2.

---

## 4. References

- `open_notebook/domain/acm.py:60` — ACMRecord definition
- `open_notebook/domain/acm.py:676` — BuildingRecord definition
- `open_notebook/domain/acm.py:953` — `validate_internal_id` BAR-only rule
- `open_notebook/extractors/parsers/config_loader.py:402` — stale V3 schema loader
- `migrations/10.surrealql` — initial acm_record table
- `migrations/40.surrealql` — building_record table (all 40+ columns)
- `migrations/47.surrealql` — building_sub_category, building_risk_rating
- `migrations/27.surrealql` — BM25 full-text index referencing hygienist_recommendations
- `config/sf-schema-snapshot.json` — authoritative extractable snapshot (INERT at runtime)
- `V3/output/building_fields_summary.md`, `V3/output/item_fields_summary.md` — stale but ACTIVE at runtime
- `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260411-sf-reconciliation.md` — E38-S2 story
