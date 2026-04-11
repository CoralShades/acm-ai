# Phase 5 Audit — Extraction Core Domain

**Auditor:** EXTRACTION-CORE specialist agent (Phase 5 post-code audit)  
**Date:** 2026-04-11  
**Branch:** `feat/sf-reconciliation-20260411`  
**Scope:** Read-only review. No code changes made.  
**Context docs read:** assumptions-and-decisions.md, session-log-2026-04-11.md,
PHASE-1-FINDINGS.md, sprint-change-proposal-20260411-sf-reconciliation.md,
git log of 8 commits ahead of main.

---

## 1. Scope

Files inspected:

| File | Focus |
|---|---|
| `open_notebook/graphs/acm_extraction.py:1806-1813, 1853+` | Surgical RAG fix + dead function |
| `open_notebook/extractors/row_segmenter.py` | Column alias catalog, RawTableRow |
| `open_notebook/extractors/row_extractor.py` | ACMItemRow extraction + fallback |
| `open_notebook/extractors/schema_inference.py` | SF_FIELD_CATALOG, SF_TO_CANONICAL, SF_TO_ITEM_ROW_FIELD |
| `open_notebook/domain/acm_row_schemas.py` | ACMItemRow (16 fields) |
| `open_notebook/domain/acm_row_mappers.py` | map_item_row_to_extraction_record() |
| `open_notebook/domain/acm.py` | ACMRecord, BuildingRecord |
| `open_notebook/extractors/exporters/sf_export.py` | ITEM_SF_MAPPING, BUILDING_SF_MAPPING |
| `open_notebook/extractors/acm_schemas.py:451-586` | ACMExtractionRecord + correction fields |
| `config/sf-schema-snapshot.json` | Ground truth for all field name checks |
| `tests/test_sf_export_contract.py` | Ran full test suite |

---

## 2. Findings

### F1 — Dead code + merge risk: `_llm_correct_records()` [HIGH]

The surgical fix in commit `5dc3ef30` replaced the 15-line `await _llm_correct_records(...)` call at
line 1811 with a 6-line no-op counter block. Correct on the main branch.

**Caller verification on main branch:** Grep across all `.py` files in the main worktree finds
exactly one definition (`acm_extraction.py:1853`) and zero callers. Dead code confirmed.

**MERGE RISK — worktree `fix-a-no-access-markers` still calls `_llm_correct_records()`:**
The worktree at `.claude/worktrees/fix-a-no-access-markers/` is based on commit `c560e2b0`
(predates `5dc3ef30`). Its `open_notebook/graphs/acm_extraction.py:1717` still has:
```python
await _llm_correct_records(records, records_needing_llm, correction_stats, model_id, ...)
```
If this worktree is merged or rebased onto the current branch without resolving the conflict,
the LLM correction call will be reintroduced, violating DEC-005 (literal-only extraction) and
DEC-006 (corrective RAG Layer 2 deleted). The worktree's latest commit is `c560e2b0 wip:
safety checkpoint — Extraction Quality — Fuse Cartridge & No-Access Records`. It is apparently
unfinished work.

**No import pollution on main:** All imports inside `_llm_correct_records()` are local imports
inside the function body. No dangling unused imports at module scope.

**Stale docstring references (two):**
- `acm_schemas.py:455`: `correction_attempts` field docstring says "Incremented by
  `_llm_correct_records()` on each attempt." — stale. The counter is no longer incremented.
- `acm_schemas.py:586`: `correction_stats` description mentions `llm_corrected` key — this
  will always be 0 after the fix but the description still implies it can be positive.

**Recommendation:** (1) Before merging the `fix-a-no-access-markers` worktree, resolve the
conflict so the Layer 2 call does NOT come back. (2) Delete `_llm_correct_records()` definition
in E38-S2 to eliminate the risk permanently. (3) Update the two field descriptions in
`acm_schemas.py` to remove stale references.

---

### F2 — schema_inference.py contains 5 fabricated SF field names [HIGH]

`open_notebook/extractors/schema_inference.py` was not updated as part of the Phase 2b
`sf_export.py` rewrite. Its `SF_FIELD_CATALOG` dict (lines 80-203) still contains SF field
names that either do not exist in the `vaea-demidev` describe dump or are wrong:

| Fabricated/wrong key | Line | Problem |
|---|---|---|
| `Hygienist_Recommendations__c` | 157, 214 | Not in SF describe. Removed from sf_export.py. |
| `Accessibility__c` | 167, 215 | Not in SF Item__c describe. No equivalent. |
| `Asbestos_Type__c` | 172, 216, 233 | Not in SF Item__c describe. |
| `Disturbance_Potential__c` | 177, 217, 231 | Wrong name. Real SF field is `Disturbance_Potential_of_Material__c`. |
| `Specific_Location__c` | 188, 218, 232 | Not in SF Item__c describe. No equivalent. |

These keys propagate into three derived lookup dicts in the same file:

- `SF_TO_CANONICAL` (lines 206-220): maps wrong SF names → canonical segmenter names
- `SF_TO_ITEM_ROW_FIELD` (lines 222-234): maps wrong SF names → ACMItemRow field names

**Impact:** `schema_inference.py` drives the LLM-based column mapping node
(`schema_inference_node`, line 357). When the node sees a PDF with a `Disturbance` column, it
maps it to `Disturbance_Potential__c` (wrong). The resulting `InferredSchema.column_mapping`
dict carries the wrong SF field name. Any downstream code that joins on `column_mapping` keys
to real SF names will silently fail to match `Disturbance_Potential__c` against the correct
field `Disturbance_Potential_of_Material__c`. This means the disturbance_potential field may
not be included in extraction_fields passed to the LLM, depending on which code path is used.

`row_segmenter.py` itself is safe: its `COLUMN_ALIASES` uses only internal canonical names
(`disturbance_potential`, `recommendation`, etc.), never SF API names. No contamination there.

**Fix required in E38-S2:** Update `SF_FIELD_CATALOG`, `SF_TO_CANONICAL`, and
`SF_TO_ITEM_ROW_FIELD` in `schema_inference.py` to use the real SF API names from
`config/sf-schema-snapshot.json`. Key replacements:

```python
# Replace:
"Disturbance_Potential__c"  →  "Disturbance_Potential_of_Material__c"
# Remove: Hygienist_Recommendations__c, Accessibility__c, Asbestos_Type__c, Specific_Location__c
```

---

### F3 — `acm_labelled` bool is extracted but `labelled_sf` string is never set [HIGH]

**Extraction path:** `acm_row_mappers.py:227-264` converts `row.acm_labelled` (string "Yes"/"No"
from LLM) → `acm_labelled_bool` (Python bool) → stored in `ACMExtractionRecord.acm_labelled`.

**Export path:** `sf_export.py:78` maps `("Labelled__c", "labelled_sf")` — it reads
`ACMRecord.labelled_sf`, which is the string picklist field ("Yes"/"No").

**Gap:** `map_item_row_to_extraction_record()` never sets `labelled_sf`. It sets `acm_labelled`
(bool) but the exporter reads `labelled_sf` (str). Since `labelled_sf` defaults to `None`,
`_format_value(None)` returns `""`. Every exported row will have `Labelled__c = ""` even when
the LLM correctly extracted "Yes" or "No".

**Fix:** Either (a) have the mapper set `labelled_sf = "Yes" if acm_labelled_bool else "No"`
in addition to `acm_labelled`, or (b) change the export to derive the string from
`acm_labelled` (bool) at export time:
```python
# In item_to_sf_row():
if sf_name == "Labelled__c":
    bool_val = getattr(record, "acm_labelled", None)
    row[sf_name] = "Yes" if bool_val else ("No" if bool_val is False else "")
```

---

### F4 — `result` vs `sample_result` dual-field split causes potential export data loss [HIGH]

`ACMRecord` has two semantically overlapping fields:
- `result: str` (required, non-nullable) — always set; aliases `Sample_Analysis_Result_Material_Status__c`
- `sample_result: Optional[str]` — nullable; set by mapper to the same normalized value

**Mapper** (`acm_row_mappers.py:255-258`):
```python
result=normalize_sample_result(row.sample_result) or "Unknown",  # required field — always has value
sample_result=normalize_sample_result(row.sample_result),         # optional — can be None
```

**Export** (`sf_export.py:69`): `("Sample_Analysis_Result_Material_Status__c", "sample_result")`

When `row.sample_result` is None (not extracted), `result = "Unknown"` (correct) but
`sample_result = None` → export value `""` (empty). `Sample_Analysis_Result_Material_Status__c`
will be empty in the Data Loader CSV even though the domain model holds "Unknown".

**Fallback record** (`row_extractor.py:497`): `_build_fallback_record()` sets
`result="Unknown"` but never sets `sample_result` (defaults to None). Same empty-export
outcome.

**Fix:** Export should prefer `result` when `sample_result` is None:
```python
# In item_to_sf_row() for Sample_Analysis_Result_Material_Status__c:
val = getattr(record, "sample_result", None) or getattr(record, "result", None)
```
Or consolidate the two fields into one canonical field on `ACMRecord` (longer-term cleanup
candidate for E38-S2).

---

### F5 — `_merge_site_config` injects two unverified SF field names [MEDIUM]

`sf_export.py:228-234` writes `Department__c` and `Agency__c` directly into the building
export row dict via `_merge_site_config()`. Neither field appears in:
- `config/sf-schema-snapshot.json` (Building__c extractable fields)
- The `BUILDING_SF_MAPPING` table

`Responsible_Agency_Department__c` IS in the snapshot, but `Department__c` and `Agency__c` are
not verified as real SF fields. If these are fabricated, Data Loader will reject any Building__c
row that includes them (unknown column error).

**Recommendation:** Verify `Department__c` and `Agency__c` against the raw describe dump at
`docs/sprint-artifacts/full-audit-2026-04-11/sf-describe/Building__c.json` before shipping.
If they don't exist, either remove them or map to `Responsible_Agency_Department__c`.

---

### F6 — BuildingRecord carries 8 non-SF alias fields not cleaned in this sprint [LOW]

`BuildingRecord` (`acm.py:763-916`) still has 8+ fields with non-SF or unverified SF aliases
that are correctly excluded from `BUILDING_SF_MAPPING` but will be deferred to E38-S2:

| Field | Alias | Issue |
|---|---|---|
| `est_building_size_m2` | `Est_Building_Size_m2__c` | Not in SF; E38-S2 target |
| `daily_duration` | `Daily_Duration__c` | Not in SF; E38-S2 target |
| `level_of_activity` | `Level_of_Activity__c` | Not in SF; E38-S2 target |
| `mobile_plant` | `Mobile_Plant__c` | Not in SF; E38-S2 target |
| `building_sub_category` | `Building_Sub_Category__c` | Not verified in snapshot |
| `building_risk_rating` | `Building_Risk_Rating__c` | Not verified in snapshot |
| `psb_district_region` | `PSB_District_Region__c` | Not in snapshot |
| `building_code` on BuildingRecord | `Building_Code__c` | This is an Item__c lookup field, not a Building__c field — wrong object |

These are documented in the SCP as E38-S2 work. The export correctly excludes them. Included
here for completeness.

---

### F7 — `risk_status` extracted, stored, never exported [LOW]

`ACMItemRow.risk_status` (schema `acm_row_schemas.py:81`) is extracted by the LLM. The mapper
(`acm_row_mappers.py:236`) normalizes it via `normalize_enum_value(row.risk_status, "risk_status")`
and stores it on `ACMExtractionRecord.risk_status`, which aliases `Risk_Rating__c`.

`Risk_Rating__c` is NOT in `config/sf-schema-snapshot.json` and NOT in `ITEM_SF_MAPPING`. The
field is silently discarded at export time. This is consistent with Phase 2b (the field was
removed from sf_export.py as a fabricated name), but the schema and mapper still extract it.

If this field has no SF equivalent, the extraction overhead is wasted. If it maps to a real SF
field under a different name, it should be added to ITEM_SF_MAPPING. Recommend verifying
against the raw describe dump.

---

## 3. Recommendations

### Critical (blocking correct Data Loader output)

| # | Finding | Action | File:Line |
|---|---|---|---|
| C1 | `acm_labelled` never flows to `labelled_sf` → Labelled__c always empty in export | Mapper sets `labelled_sf` string from bool, OR exporter derives it from `acm_labelled` | `acm_row_mappers.py:260-264`, `sf_export.py:78` |
| C2 | `sample_result` None when LLM saw nothing → `Sample_Analysis_Result_Material_Status__c` exports empty despite `result="Unknown"` | Export uses `result` as fallback when `sample_result` is None | `sf_export.py:69`, `acm_row_mappers.py:255-258` |

### High (merge risk + SF schema integrity)

| # | Finding | Action | File:Line |
|---|---|---|---|
| H1 | `fix-a-no-access-markers` worktree still calls `_llm_correct_records()` | Resolve merge conflict before merging worktree — do NOT let Layer 2 call return | `.claude/worktrees/fix-a-no-access-markers/acm_extraction.py:1717` |
| H2 | 5 fabricated SF field names in `schema_inference.py` SF_FIELD_CATALOG | Fix in E38-S2 — update to real SF names from snapshot | `schema_inference.py:157-233` |
| H3 | `_merge_site_config` writes `Department__c` / `Agency__c` unverified | Verify against raw describe; map to `Responsible_Agency_Department__c` if needed | `sf_export.py:228-234` |

### Medium (cleanup)

| # | Finding | Action | File:Line |
|---|---|---|---|
| M1 | `_llm_correct_records()` is dead code with no callers | Delete in E38-S2 | `acm_extraction.py:1853-2000+` |
| M2 | Two stale docstring refs to `_llm_correct_records()` | Update in E38-S2 | `acm_schemas.py:455, 586` |

### Low (future cleanup, E38-S2 scope)

| # | Finding | Action | File:Line |
|---|---|---|---|
| L1 | `risk_status` extracted but never exported; `Risk_Rating__c` alias is fabricated | Verify SF equivalent or remove extraction entirely | `acm_row_schemas.py:81`, `acm.py:184-188` |
| L2 | `BuildingRecord.building_code` aliases `Building_Code__c` (wrong object) | Fix alias to remove confusion | `acm.py:700-704` |
| L3 | 8 BuildingRecord fields with non-SF aliases still on model | E38-S2 scorched earth | `acm.py:763-916` |

---

## 4. Test Results

```
uv run pytest tests/test_sf_export_contract.py -v
10/10 PASSED  (8.52s)

uv run pytest tests/ -v
55/55 PASSED  (136.98s)
```

Note: the test suite validates that every SF field name in ITEM_SF_MAPPING and
BUILDING_SF_MAPPING exists in the real SF describe dump, and every Python field name exists on
the domain model. These tests did NOT catch F3 (`labelled_sf` gap) or F4 (`result` vs
`sample_result`) because they test mapping table structure but not data flow through the mapper.
Recommend adding data-flow tests to E38-S3.

---

## 5. References

| Finding | Files | Lines |
|---|---|---|
| F1 dead code | `acm_extraction.py`, `acm_schemas.py` | 1853, 455, 586 |
| F2 fabricated SF names | `schema_inference.py` | 157, 167, 172, 177, 188, 206-234 |
| F3 labelled gap | `acm_row_mappers.py`, `sf_export.py` | 227-264, 78 |
| F4 result/sample_result | `acm_row_mappers.py`, `sf_export.py`, `row_extractor.py` | 255-258, 69, 497-511 |
| F5 site_config fields | `sf_export.py` | 228-234 |
| F6 BuildingRecord aliases | `acm.py` | 763-916 |
| F7 risk_status gap | `acm_row_schemas.py`, `acm_row_mappers.py`, `acm.py` | 81, 236, 184-188 |
