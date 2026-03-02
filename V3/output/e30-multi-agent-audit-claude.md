# E30 Salesforce Schema Alignment — Multi-Agent Audit Findings

**Date:** 2026-03-02
**Sprint Change Proposal:** SCP-20260301-SF
**Audit Scope:** Full system audit for E30 implementation impact
**Agents:** Winston (Architect), Mary (BA), John (PM), Bob (SM), Quinn (QA), Amelia (Dev)

---

## Winston (Architect) Audit Findings

### Data Model Impact — CRITICAL

1. **W1: Flat ACMRecord must split into two entities.** Current `open_notebook/domain/acm.py` has a single `ACMRecord(ObjectModel)` with `table_name = "acm_record"` containing ~50 fields that mix building-level data (building_name, building_address, suburb, postcode, building_type, building_year, building_construction) with ACM item-level data (product, material_description, friable, etc.). E30 requires splitting into `BuildingRecord` + `ACMRecord` with master-detail FK.

2. **W2: No `building_record` table exists in SurrealDB.** Current migrations (37 total) define `acm_record` and `acm_table_section` tables but no `building_record`. E30-S2 requires new migration creating `building_record` with 29+ extractable SF Building__c fields.

3. **W3: Field names use BAR vocabulary, not Salesforce API names.** ACMRecord uses `product` (not `Item_Name__c`), `friable` (not `Friability_of_Material__c`), `material_condition` (not `Condition__c`), `acm_product_group` (not `ACM_Classification__c`). E30-S3 requires Pydantic aliases for SF API names.

4. **W4: `building_id` is a freeform string, not a FK.** Current ACMRecord.building_id is a string like "B009" or a building name. E30-S2 requires it to be a record reference (`record<building_record>`) for master-detail.

5. **W5: No `field_schema` table for SF picklist config.** System loads enums from `register_enums.json` via `config_loader.py`. E30-S1 requires a `field_schema` SurrealDB table for SF picklist values, dependency chains, and versioning.

6. **W6: No dependent picklist validation.** `acm_validator.py` validates individual enum fields but has NO dependency chain validation. E30-S4 requires: Friability→ACM_Classification→ACM_Sub_Classification and BuildingType→Category→SubCategory.

7. **W7: `site_config` concept does not exist.** V3 architecture shows a `site_config` table for officer-configured fields (Department, Organisation, Building_Type). No equivalent in current codebase.

### AI Provider Impact — MEDIUM

8. **W8: System uses Esperanto multi-provider abstraction.** `api/model_provisioning.py` uses provider/model_name format with fallback chains. E30-S7 replaces with direct `ChatAnthropic`. Affects `graphs/utils.py`, `graphs/acm_extraction.py`, `extractors/orchestrator.py`.

9. **W9: `_unwrap_completion_state()` exists in pipeline stages.** E30-S7 requires removing this from all graph nodes.

### Pipeline Impact — MEDIUM

10. **W10: Extraction is NOT per-building two-phase.** Current pipeline extracts ACM records in a single pass per building section. V3 requires TWO AI calls per building (Building__c fields then Item__c fields).

### Target ER Diagram

```
source ||--o{ building_record : "extracted_from"
source ||--o{ acm_table_section : "has_tables"
source ||--o| site_config : "configured_with"
building_record ||--o{ acm_record : "has_acms"
field_schema ||--o{ building_record : "validates"
field_schema ||--o{ acm_record : "validates"

source { id PK, title, file_path, full_text, created_at }
building_record { id PK, source_id FK, building_name, building_address, suburb, postcode, state, construction_type, estimated_year_built, number_of_levels, estimated_size, date_of_inspection, roof_type, page_number, extraction_confidence }
acm_record { id PK, source_id FK, building_id FK→building_record, item_name, friability, acm_classification, acm_sub_classification, condition, disturbance_potential, room_name, floor_level, item_location, internal_external, sample_result, sample_number, quantity, assessor, date_identified, recommendations, additional_comments, labelled, page_number, extraction_confidence }
site_config { id PK, source_id FK, department, organisation, building_type, building_category, owned_or_leased, frequency_of_use }
field_schema { id PK, field_definitions JSON, picklist_values JSON, dependency_rules JSON, version }
```

---

## Mary (Business Analyst) Audit Findings

### PRD Gap Analysis — FR-1401 through FR-1412

1. **M1: FR-1401 (Building in building_record) — 100% GAP.** No building_record table, model, or API exists. Building data denormalized into ACMRecord.

2. **M2: FR-1402 (ACM mapped to Item__c) — 40% GAP.** ACMRecord exists but with BAR field names. Missing: `Internal_External__c`, `Labelled__c` (bool→picklist), `ASSEA_Survey_Guide_Risk_Level__c`, `Date_Identified__c`.

3. **M3: FR-1403 (Friability→Classification→SubClassification chain) — 100% GAP.** Fields exist but use BAR names ("T3 Vinyl products" vs SF "Vinyl products"). No dependency enforcement. 18 ACM_Classification × 2 Friability = 36 valid combinations.

4. **M4: FR-1404 (BuildingType→Category→SubCategory chain) — 100% GAP.** BuildingType field doesn't exist. 114 Building_Type → 13 Category values.

5. **M5: FR-1405 (Validate against exact SF values) — CONFLICT.** SF Condition: `Poor|Fair|Stable|Unknown|N/A (negative)|N/A (assumed negative)`. BAR uses `Good` which has NO SF equivalent. "Good"→"Stable" mapping needed everywhere.

6. **M6: FR-1406/FR-1407 (Export CSVs) — 100% GAP.** No SF Data Loader export exists.

7. **M7: FR-1408 (SF schema from JSON config) — PARTIAL.** config_loader.py loads BAR schema. `building_list.txt` and `item_list.txt` exist in V3/ but aren't parsed yet.

8. **M8: FR-1409 (Anthropic Claude Sonnet only) — 100% GAP.** System uses Esperanto multi-provider.

9. **M9: FR-1410 (Two-phase extraction) — 100% GAP.** Single-pass extraction currently.

10. **M10: FR-1411 (Item_Name subsets by Product Group) — 100% GAP.** 294 values too many for single prompt. No subsetting mechanism.

11. **M11: FR-1412 (Negative→Condition=N/A) — PARTIAL.** BAR-001 rule exists but uses BAR vocabulary.

12. **M12: CRITICAL CONFLICT — BAR "Good" → SF "Stable".** Affects 8+ templates, validator, domain model, all test fixtures.

---

## John (Product Manager) Audit Findings

### E30 Story Gap Analysis

1. **J1: E30-S1 underestimated.** Parse 143+154 field objects, build TWO dependency chain mappings, SurrealDB migration, startup loading. 3→5 SP.

2. **J2: E30-S2 underestimated.** Migration + domain model + API + FK update + data migration. 3→5 SP.

3. **J3: E30-S3 underestimated.** Backward-compat additive migration + 294-value picklist + Pydantic aliases for 35+ fields. 2→4 SP.

4. **J4: MISSING STORY — Data Migration Script.** No story covers migrating existing records from flat→split schema. Need E30-S2.5 (3 SP).

5. **J5: MISSING STORY — BAR→SF Value Migration.** Existing "Good"→"Stable", BAR group names→SF names. Need E30-S3.5 (2 SP).

6. **J6: E30-S4 — Unclear validation mode.** Warn vs reject? How do warnings surface to officers? AC needed.

7. **J7: E30-S5/S6 — Prompt regression risk.** Need AC: "Broadmeadows + Alexander benchmarks pass."

8. **J8: E30-S7 — SEQUENCING RISK.** If S7 lands before S5/S6, extraction tests break. Should be last or feature-flagged.

9. **J9: E30-S9 underestimated.** Two-view layout is a full frontend feature. 2→4 SP.

10. **J10: MISSING STORY — Frontend Building Detail Page.** Broader than S9. List/detail pattern needed.

11. **J11: Revised estimate — 12 stories, ~40 SP, 14-16 days** (vs SCP's 10 stories, 28 SP, 10-12 days).

---

## Bob (Scrum Master) Audit Findings

### Sprint Impact

1. **B1: sprint-status.yaml needs E30 block.** Must not conflict with existing epic numbering.

2. **B2: E29 must be DONE first.** SCP explicitly states dependency. Need E29 status verification.

3. **B3: Earlier stories affected.** E1-S11 (Generic Parser) built config_loader.py. E30-S1 evolves it.

4. **B4: BMAD story files needed.** Each S1-S10+ needs docs/sprint-artifacts/ story file with ACs.

5. **B5: Dependency graph incomplete.** S5 needs S1+S2 (not just S2). S6 needs S1+S3+S4.

6. **B6: Parallel S2||S3 merge conflict risk.** Both modify domain models and migrations.

---

## Quinn (QA) Audit Findings

### Test Coverage Gaps

1. **Q1: E30-S10 E2E is happy-path only.** Missing: error cases, invalid picklists, dependency violations, multi-building PDFs, negative-only buildings.

2. **Q2: No unit tests for SalesforceSchemaConfig (S1).** Complex parsing with dependency chains needs dedicated tests.

3. **Q3: No BAR→SF value migration test (S3.5).** "Good"→"Stable" conversion untested.

4. **Q4: Dependent picklist needs exhaustive combos.** 36 valid Friability×Classification combos + invalid combos.

5. **Q5: Prompt regression not covered.** S5/S6 change prompts; benchmarks may break.

6. **Q6: Export validation needs SF schema check.** Correct headers, valid picklist values, external ID present.

7. **Q7: AG Grid E2E not in S10 scope.** Playwright tests needed for two-view, dropdowns, drill-down.

8. **Q8: Missing cascading delete test.** Building delete should cascade ACM records.

9. **Q9: 33+ existing test files reference BAR fields.** ALL need fixture updates for SF vocabulary.

---

## Amelia (Dev) Audit Findings

### File-by-File Change Impact Matrix

| File | Impact | Changes Required |
|------|--------|-----------------|
| `open_notebook/domain/acm.py` | CRITICAL | Split ACMRecord: extract building fields→BuildingRecord. SF aliases. FK update. ~250 LOC. |
| `open_notebook/extractors/validators/acm_validator.py` | HIGH | Replace BAR enums with SF enums. Add dependent picklist validation. |
| `open_notebook/extractors/parsers/config_loader.py` | HIGH | Replace BAR schema with SF schema. New JSON parsers. Remap DISPLAY_NAME_TO_INTERNAL. |
| `prompts/acm/extraction.jinja` | HIGH | SF Item__c field names. SF picklist values. Item_Name subsetting. ~420 LOC rework. |
| `prompts/acm/building_extraction.jinja` | HIGH | Rewrite for Building__c fields only (currently extracts ACMs). ~600 LOC rework. |
| `open_notebook/graphs/acm_extraction.py` | HIGH | Add building extraction node. Two-phase routing. Esperanto→ChatAnthropic. |
| `open_notebook/extractors/orchestrator.py` | HIGH | Two-phase: building→ACM per building. BuildingRecord creation. |
| `api/routers/acm.py` | MEDIUM | BuildingRecord CRUD. Building-filtered ACM queries. |
| `api/model_provisioning.py` | MEDIUM | Esperanto→Anthropic only. Remove fallback chain. |
| `commands/source_commands.py` | MEDIUM | BuildingRecord creation in extraction flow. |
| `migrations/38.surrealql` (NEW) | MEDIUM | building_record + field_schema + site_config tables. FK constraints. |
| `prompts/acm/classification.jinja` | LOW | SF product group/type vocabulary. |
| `prompts/acm/correction.jinja` | LOW | SF field names + piclist values. |
| Tests (33+ files) | HIGH | All BAR fixtures→SF vocabulary. BuildingRecord fixtures. |
| Frontend (multiple) | HIGH | Two-view grid, dependent picklist dropdowns, building detail. |

### Key Technical Risks

- `acm_labelled` is `bool`, SF wants `picklist("Yes"/"No")` — type change
- `school_name`/`school_code` are required in ACMRecord but not in SF model — make optional
- `result` field maps to SF `Sample_Analysis_Result_Material_Status__c` which adds "Negative - Treated as Positive"
- Embedding fields must be preserved (no SF mapping but critical for search)
- `_unwrap_completion_state()` must be found+removed from all graph nodes

---

## Cross-Agent Consensus

| Area | Gap | Risk |
|------|-----|------|
| Data Model (flat→split) | 100% | HIGH |
| Dependent Picklists | 100% | HIGH |
| AI Provider (Esperanto→Anthropic) | 100% | MEDIUM |
| Extraction Prompts (BAR→SF) | 90% | HIGH |
| Validation (enum→dependency chain) | 80% | HIGH |
| Export (BAR Excel→SF CSV) | 100% | HIGH |
| Frontend (single→two-view grid) | 100% | HIGH |
| Tests (33+ files) | 100% | HIGH |
| **SP Estimate** | **SCP: 28 SP → Revised: ~40 SP** | **UNDERESTIMATED** |
| **Timeline** | **SCP: 10-12 days → Revised: 14-16 days** | **UNDERESTIMATED** |
