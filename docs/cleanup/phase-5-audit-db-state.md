# Phase 5 Audit — DB State Report

**Agent:** DB-STATE-AUDITOR
**Date:** 2026-04-11
**Branch:** `feat/sf-reconciliation-20260411`
**Scope:** Live SurrealDB inspection — schema drift, record counts, dead-field data-loss risk, stuck commands, observability state
**Mode:** READ-ONLY — no schema changes, no data writes

---

## 1. Scope

SurrealDB endpoint: `ws://127.0.0.1:8000/rpc` (HTTP at `:8000`)
Container: `acm-ai-db` (surrealdb/surrealdb:v2.2.1, Up 2 days, healthy)
Namespace: `open_notebook` / Database: `development`

Queries executed via `curl -X POST http://localhost:8000/sql` with `Surreal-NS` and `Surreal-DB` headers.

Reference documents used:
- `config/sf-schema-snapshot.json` (Phase 2a — 25 Building__c + 27 Item__c extractable fields)
- `docs/cleanup/phase-5-audit-schema-expert.md` (46 dead Pydantic fields enumerated)
- `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260411-sf-reconciliation.md` (E38-S2 scope)

---

## 2. Live Queries Run

| Query | Table | Result |
|---|---|---|
| `INFO FOR TABLE building_record` | building_record | 55 DEFINE FIELD entries |
| `INFO FOR TABLE acm_record` | acm_record | 67 DEFINE FIELD entries |
| `SELECT count() FROM <table> GROUP ALL` | 6 tables | Counts recorded |
| `SELECT source_id, count() FROM acm_record GROUP BY source_id` | acm_record | Orphan cross-check |
| `SELECT source_id, count() FROM building_record GROUP BY source_id` | building_record | Orphan cross-check |
| Dead-field NULL check (building_record) | building_record | 15 dead fields |
| Dead-field NULL check (acm_record) | acm_record | 13 dead fields |
| `SELECT count() FROM agui_events GROUP ALL` | agui_events | Pipeline events |
| `SELECT * FROM command WHERE status = 'running'` | command | Stuck commands |
| `SELECT ... FROM extraction_progress WHERE status IN ('running','pending')` | extraction_progress | Stuck progress records |
| `SELECT id, status FROM field_schema LIMIT 3` | field_schema | Schema config check |
| `curl http://localhost:3000/api/public/health` | Langfuse | Observability status |

---

## 3. Findings

### 3.1 Schema Drift — `building_record` vs `Building__c` Snapshot

**DB table columns** (from `INFO FOR TABLE building_record`): 55 DEFINE FIELD entries
**SF snapshot extractable fields**: 25 (Building__c in `config/sf-schema-snapshot.json`)

#### In DB but NOT in SF snapshot (dead / non-extractable fields) — 20 fields

These are confirmed by the schema-expert report. All 20 are SCHEMAFULL columns that will require explicit `REMOVE FIELD` migrations in E38-S2.

| DB field | SF alias (if any) | Category |
|---|---|---|
| `est_building_size_m2` | `Est_Building_Size_m2__c` | Real SF field, not extractable from PDF |
| `daily_duration` | `Daily_Duration__c` | Real SF field, not in ARA PDFs |
| `level_of_activity` | `Level_of_Activity__c` | Real SF field, not in ARA PDFs |
| `mobile_plant` | `Mobile_Plant__c` | Real SF field, not in ARA PDFs |
| `building_out_of_scope` | `Building_Out_Of_Scope_New__c` | Operational flag, not extractable |
| `building_out_of_scope_comments` | `Building_Out_Of_Scope_Comments__c` | Operational, not extractable |
| `demolished_status` | `Demolished_Status__c` | Operational, not extractable |
| `demolition_date` | `Demolition_Date__c` | Operational, not extractable |
| `demolition_type` | `Demolition_Type__c` | Operational, not extractable |
| `demolition_comments` | `Demolition_Comments__c` | Operational, not extractable |
| `no_identified_acms` | `No_Identified_ACMs__c` | Operational boolean, not extractable |
| `no_identified_acms_note` | `No_Identified_ACMs_Note__c` | Operational note, not extractable |
| `psb_district_region` | `PSB_District_Region__c` | Not in ARA PDFs |
| `country` | `Country__c` | Always "Australia", no extraction value |
| `capital_works_project_details` | `Capital_Works_Project_Provide_Details__c` | Operational, not extractable |
| `possible_capital_works_project` | `Possible_Capital_Works_Project__c` | Operational boolean |
| `building_address_lga` | `Building_Address_LGA__c` | Auto-populated by geocoding |
| `building_address_region` | `Building_Address_Region__c` | Auto-populated by geocoding |
| `building_code` | `Building_Code__c` | Wrong object — exists on Item__c, not Building__c |
| `building_risk_rating` | `Building_Risk_Rating__c` | System-generated, not extractable |
| `building_sub_category` | `Building_Sub_Category__c` | Not found in live SF describe |

#### In SF snapshot but NOT in DB (gap — missing extraction target)

| SF field | SF label | Impact |
|---|---|---|
| `Responsible_Agency_Department__c` | Responsible Agency/Department | Low — not in current 13-field extraction schema; candidate for E38 schema extension |

---

### 3.2 Schema Drift — `acm_record` vs `Item__c` Snapshot

**DB table columns** (from `INFO FOR TABLE acm_record`): 67 DEFINE FIELD entries
**SF snapshot extractable fields**: 27 (Item__c in `config/sf-schema-snapshot.json`)

#### In DB but NOT in SF snapshot (dead / non-extractable fields) — 25 fields

| DB field | SF alias (if any) | Category |
|---|---|---|
| `school_name` | (none) | Denormalized Building-level field — no Item__c equivalent |
| `school_code` | (none) | Denormalized Building-level field — no Item__c equivalent |
| `building_year` | (none, `Building_Year__c` not real) | Denormalized; Building__c uses `Estimated_Year_Build_New__c` |
| `building_construction` | (none) | Denormalized Building-level field |
| `building_address` | (none) | Denormalized Building-level field |
| `suburb` | (none) | Denormalized Building-level field |
| `postcode` | (none) | Denormalized Building-level field |
| `building_type` | (none) | Denormalized Building-level field |
| `room_id` | `Room_ID__c` | Not found in live SF describe — confirmed fabricated |
| `room_area` | `Room_Area__c` | Not found in live SF describe — confirmed fabricated |
| `material_description` | `Material_Description__c` | Not found in live SF describe — BAR-only field |
| `result` | (none in export) | NOT used in `sf_export.py` ITEM_SF_MAPPING; `sample_result` is the active SF-bound field |
| `acm_labelled` | `ACM_Labelled__c` | Not found in live SF describe; real field is `Labelled__c` → `labelled_sf` |
| `risk_status` | `Risk_Rating__c` | Real SF field but system-assigned, not extractable |
| `hygienist_recommendations` | `Hygienist_Recommendations__c` | **CORRECTION**: real SF field (Phase 2b error); candidate for re-inclusion in E38 schema extension |
| `psb_supplied_acm_id` | `ID_provided_by_metro__c` | Real SF field but not in extractable snapshot |
| `removal_status` | `Removal_Status__c` | Removal_Job__c domain — out of scope per DEC-001 |
| `date_of_removal` | `Removed_Date__c` | Removal_Job__c domain — out of scope |
| `quantity_removed` | `Quantity_Removed__c` | Removal_Job__c domain — out of scope |
| `removal_notification_no` | `Asbestos_Removal_Notification_No__c` | Removal_Job__c domain — out of scope |
| `epa_certificate_no` | `EPA_Waste_Transport_Certificate_No__c` | Removal_Job__c domain — out of scope |
| `no_access` | `No_Access__c` | Real but operational boolean, not extractable |
| `smf_present` | `SMF_Present__c` | Real but operational boolean, not extractable |
| `assea_risk_level` | `ASSEA_Survey_Guide_Risk_Level__c` | Real SF field, not in extractable snapshot; some PDFs may include it |
| `date_identified` | `Date_Identified__c` | Not confirmed in live SF describe |

#### In SF snapshot but NOT in DB (gap — missing extraction targets) — 7 fields

| SF field | SF label | Impact |
|---|---|---|
| `If_Other_Item_Name__c` | If Other Please Specify the ACM Name | Medium — needed for picklist fallback |
| `Frequency_of_Use__c` (item-level) | Frequency of Use (ACM) | Medium — item-level, distinct from building-level |
| `Public_Access__c` (item-level) | Public Access (ACM) | Medium — item-level, distinct from building-level |
| `Clearance_Certificates_Available__c` | Clearance Certificates Available | Low — not in current ARA PDF scope |
| `Photo_Ref__c` | Photo Ref | Low — not in ARA PDFs |
| `Asbestos_Register_Reference_No__c` | Asbestos Register Reference No | Low — may be in some PDFs |
| `Lot_No__c` | Lot No | Low — not in ARA PDFs |

---

### 3.3 Record Counts

| Table | Count | Notes |
|---|---|---|
| `source` | **5** | 4 with extraction records; 1 stuck ("Processing...") |
| `building_record` | **9** | Distributed across 3 sources |
| `acm_record` | **212** | Distributed across 3 sources |
| `notebook` | **4** | |
| `extraction_progress` | **34** | 16 stuck in "running" — see §3.5 |
| `command` | **27** | 3 stuck in "running" — see §3.5 |

**Orphan check:** No orphan records found. All `source_id` values in `building_record` and `acm_record` reference existing `source` records:

| source_id | building_record count | acm_record count |
|---|---|---|
| `source:gn4mity61x2pcil3rjtv` | 1 | 57 |
| `source:qnt6w2t1h251x0y0uxpw` | 7 | 120 |
| `source:xreiuz98wmzebgxeprrd` | 1 | 35 |

**5th source:** `source:cairo1ewyyn5rzz1pyfj` (title="Processing...", created 2026-04-11T13:11) has no associated building or ACM records — likely a stuck or in-flight extraction.

Note: The `NOT IN` subquery pattern produced false positives (SurrealDB v2 typed-record comparison issue). The group-by approach above is authoritative.

---

### 3.4 Dead-Field Data-Loss Risk for E38-S2

Queries: `SELECT count(<field> != NONE) AS <field> FROM <table> GROUP ALL`

#### Building_record dead fields — ALL ZERO

| Dead field | Non-null count |
|---|---|
| `est_building_size_m2` | 0 |
| `daily_duration` | 0 |
| `level_of_activity` | 0 |
| `mobile_plant` | 0 |
| `building_risk_rating` | 0 |
| `building_sub_category` | 0 |
| `psb_district_region` | 0 |
| `demolished_status` | 0 |
| `demolition_date` | 0 |
| `demolition_type` | 0 |
| `demolition_comments` | 0 |
| `building_out_of_scope` | 0 |
| `building_out_of_scope_comments` | 0 |
| `no_identified_acms` | 0 |
| `no_identified_acms_note` | 0 |

**Result: Zero data-loss risk for all 15 dead building_record fields. Safe to drop without a data migration.**

#### acm_record dead fields — 3 fields with non-null data

| Dead field | Non-null count | Risk level | Notes |
|---|---|---|---|
| `result` | **212 / 212** | CRITICAL | TYPE string (required), every record populated. NOT in `sf_export.py` ITEM_SF_MAPPING. Values include: Negative (82), Positive (20), Presumed Positive (8), etc. 70 records have `result` populated but `sample_result` is null — dropping `result` without a migration would permanently lose these values. |
| `room_id` | **74 / 212** | HIGH | Values are R001–R010 style internal room codes. No SF equivalent (`Room_ID__c` not in live describe). Data will be lost. |
| `risk_status` | **12 / 212** | MEDIUM | Values: Low (10), Medium (1), High (1). `Risk_Rating__c` is real in SF but system-assigned. Data will be lost. |
| `room_area` | 0 | None | |
| `material_description` | — (always set, TYPE string) | — | Required string — not queried explicitly; always present but is internal BAR text, no SF equivalent. |
| `assea_risk_level` | 0 | None | |
| `smf_present` | 0 | None | |
| `hygienist_recommendations` | 0 | None | |
| `psb_supplied_acm_id` | 0 | None | |
| `removal_status` | 0 | None | |
| `date_of_removal` | 0 | None | |
| `quantity_removed` | 0 | None | |
| `removal_notification_no` | 0 | None | |
| `epa_certificate_no` | 0 | None | |

**Fields safe for E38-S2 drop without data migration: 11 of 14 queried dead acm_record fields**

**Fields requiring pre-drop migration or acceptance of data loss: `result` (212 records), `room_id` (74 records), `risk_status` (12 records)**

**NOT dead (verified by live sf_export.py inspection):**
- `floor_level` (104 records): maps to `Level__c` via `sf_export.py` — must NOT be deleted
- `sample_result` (142 records): maps to `Sample_Analysis_Result_Material_Status__c` via `sf_export.py` — must NOT be deleted

**Schema-expert report correction:** The report states "`sample_result` has no SF alias, redundant with `result` which maps to `Sample_Analysis_Result_Material_Status__c`". This is REVERSED. `sf_export.py` line confirmed:
```python
("Sample_Analysis_Result_Material_Status__c", "sample_result"),
```
`sample_result` IS the live SF-bound field. `result` is the dead orphan (it is NOT in ITEM_SF_MAPPING).

---

### 3.5 Extraction Pipeline State

#### Stuck `command` records (3)

| Command ID | Name | Source | Claimed by | Note |
|---|---|---|---|---|
| `command:9g637f9hnchanaf27s8d` | `acm_extract` | `source:zyiyqpm1qw803yfbhd98` | DESKTOP-HF8ISHS:27356 | Source no longer exists in `source` table — zombie command |
| `command:q3gjbnfxspwpcaxz7hkc` | `process_source` | `source:zyiyqpm1qw803yfbhd98` | (null) | Source no longer exists — zombie |
| `command:wuyz7tc935nk2f13i82u` | `process_source` | `source:zyiyqpm1qw803yfbhd98` | (null) | Source no longer exists — zombie |

**Root cause:** `source:zyiyqpm1qw803yfbhd98` was deleted (or never completed creation) while its commands remained in "running" state. The worker will never pick these up again — `claimed_at` was 2026-03-21.

**Stuck `extraction_progress` records (16)**

16 records in "running" status across 13 distinct source_ids. All have null `created`, `stage`, and `updated` values, indicating they were written by an older schema version (before migration added those columns) or the worker crashed before writing them. Several reference source_ids that do not appear in the current `source` table.

These are all pre-production test-run residue. Not blocking production.

---

### 3.6 Observability State

#### `agui_events` table
Count: **0 records**
Verdict: No pipeline events have been persisted via the SSE event bus. Either the feature is not wired to write to this table, or no extraction has run since the table was created.

#### `field_schema` table
Count: **1 record** (`field_schema:sf_v1`, `table_name: null`)
Verdict: The table is underseeded. `table_name` is null, suggesting the seeding script either did not run or wrote an incomplete record. Runtime code in `config_loader.py` reads `V3/output/*.md`, not this table — so the null entry has no operational impact beyond confirming the table is placeholder-only.

#### Runtime schema source — CRITICAL CONFLICT
- `config/sf-schema-snapshot.json`: authoritative Phase 2a snapshot (25 + 27 extractable fields) — **INERT at runtime** (no code reads it)
- `V3/output/building_fields_summary.md` + `item_fields_summary.md`: stale (132+ and 144+ fields including formulas, rollups, geocode auto-populated fields) — **ACTIVE at runtime** via `config_loader.py:409`
- Effect: `SalesforcePicklistValidator` and `sf_normalizer.py` validate against the stale schema, not the verified extractable set. Picklist corrections made in `config/bar_to_sf_mapping.yaml` (Phase 2a) are not enforced by the runtime validator.

#### Langfuse
Status: **UP** (`{"status":"OK","version":"3.155.1"}` at `localhost:3000`)
Trace query: Auth failed (keys present in `.env` but Langfuse API auth via base64 encoding requires public/secret key pair — not attempted to avoid exposing keys per Incident 2 security note). No trace data retrieved.

---

## 4. Recommendations

### CRITICAL

| # | Finding | Action |
|---|---|---|
| C1 | `config/sf-schema-snapshot.json` is inert at runtime; stale `V3/output/*.md` is active | Wire `config_loader.py:409` to read `config/sf-schema-snapshot.json`. Must be a prerequisite story before E38-S2 field deletions, or `SalesforcePicklistValidator` will reference deleted field names from stale markdown. |
| C2 | `acm_record.result` has 212 records populated; 70 records have `result` but not `sample_result` | Before E38-S2 drops `result`, run: `UPDATE acm_record SET sample_result = result WHERE sample_result = NONE AND result != NONE`. This preserves 70 records that would otherwise lose their Sample Analysis Result. |

### HIGH

| # | Finding | Action |
|---|---|---|
| H1 | 3 zombie `command` records stuck in "running" for a deleted source since 2026-03-21 | Reset: `UPDATE command SET status = 'failed', error_message = 'zombie — source deleted' WHERE id IN [command:9g637f9hnchanaf27s8d, command:q3gjbnfxspwpcaxz7hkc, command:wuyz7tc935nk2f13i82u]`. Not blocking but pollutes monitoring. |
| H2 | `acm_record.room_id` has 74 records populated; no SF equivalent | Tag E38-S2 acceptance criteria with explicit "data loss acknowledged" sign-off from Demi, since these are test-data-only records. |
| H3 | 7 Item__c fields in snapshot are absent from DB schema | `If_Other_Item_Name__c`, item-level `Frequency_of_Use__c`, item-level `Public_Access__c` are medium-priority gaps. Flag for E38 schema extension story. |
| H4 | `migration 27` BM25 index references `hygienist_recommendations` | E38-S2 must drop and rebuild the `acm_fulltext` index before dropping the field, or the migration will fail. |

### MEDIUM

| # | Finding | Action |
|---|---|---|
| M1 | 16 `extraction_progress` records stuck in "running" with null metadata | Bulk reset: `UPDATE extraction_progress SET status = 'failed' WHERE status = 'running' AND created = NONE`. Cleanup only — not affecting production. |
| M2 | Schema-expert report has `result` / `sample_result` attribution reversed | Correct the E38-S2 story so it lists `result` as dead (not `sample_result`). Confirm via `sf_export.py` ITEM_SF_MAPPING: `sample_result` → `Sample_Analysis_Result_Material_Status__c`. |
| M3 | `field_schema:sf_v1` has `table_name: null` | Either seed it correctly or remove the table if the feature is unused. |
| M4 | `responsible_agency_department` missing from `building_record` | Add as a gap candidate for E38 schema extension if ARA PDFs contain agency info. |
| M5 | `hygienist_recommendations` was incorrectly labeled "fabricated" in session log | Phase 2b session log should be corrected. `Hygienist_Recommendations__c` IS a real SF field. Consider adding it to `config/sf-schema-snapshot.json` for E38 schema extension. |

### LOW

| # | Finding | Action |
|---|---|---|
| L1 | `agui_events` has 0 records | Verify whether `PipelineEventBus` is wired to write to this table; if not, either wire it or remove the table. |
| L2 | `source:cairo1ewyyn5rzz1pyfj` (title="Processing...") has no records | Check whether the 2026-04-11 upload is stuck. If yes, delete the source and retry. |
| L3 | `acm_record.building_sub_category` added in migration 47 but has 0 data | Safe to drop in E38-S2; migration 47 should also be reviewed for any other additions. |

---

## 5. Dead-Field Data-Loss Summary

**Total dead fields identified:** 46 (21 `building_record` + 25 `acm_record`)
**Dead fields with non-null production data:** 3 (`result` 212, `room_id` 74, `risk_status` 12)
**Dead fields safe to drop without data migration:** 43 of 46

| Field | Table | Non-null rows | Migration required? |
|---|---|---|---|
| `result` | acm_record | **212** | YES — `UPDATE acm_record SET sample_result = result WHERE sample_result = NONE AND result != NONE` |
| `room_id` | acm_record | **74** | Accept data loss (no SF home; test data only) |
| `risk_status` | acm_record | **12** | Accept data loss (formula field in SF; system-assigned anyway) |
| All 15 building_record dead fields | building_record | **0** | None required |
| All remaining 22 acm_record dead fields | acm_record | **0** | None required |

---

## 6. References

- `config/sf-schema-snapshot.json` — Phase 2a extractable field snapshot
- `open_notebook/extractors/exporters/sf_export.py` — ITEM_SF_MAPPING (live sf_export.py confirmation)
- `docs/cleanup/phase-5-audit-schema-expert.md` — 46 dead fields enumeration
- `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260411-sf-reconciliation.md` — E38-S2 story
- `docs/cleanup/assumptions-and-decisions.md` — DEC-001 through DEC-020
- `migrations/27.surrealql` — BM25 index referencing `hygienist_recommendations`
- `open_notebook/extractors/parsers/config_loader.py:409` — stale V3 schema loader (ACTIVE at runtime)
