# Phase 5 Audit — Pre-Extraction Domain
**Auditor:** acm-extraction-pre specialist  
**Branch:** `feat/sf-reconciliation-20260411`  
**Date:** 2026-04-11  
**Scope:** E1-S16 (Document Structure/TOC), E1-S17 (Building Inventory), E1-S18 (Page-Level Section Tagging), E1-S19 (Document Metadata Extraction)

---

## Scope

Pre-extraction covers the pipeline stages that run before per-building AI extraction. Active files:

| Story | File | Role |
|-------|------|------|
| E1-S16 | `open_notebook/extractors/document_structure.py` | TOC + section hierarchy |
| E1-S17 | `open_notebook/extractors/building_inventory.py` | Building page-range map |
| E1-S18 | `open_notebook/extractors/page_tagger.py` | Per-page section classification (LLM path) |
| E1-S18 (opt) | `open_notebook/extractors/metadata_and_structure.py` | Combined metadata+structure + synthesized page tags |
| E1-S19 | `open_notebook/extractors/metadata_extractor.py` | Document metadata extraction |
| Graph nodes | `open_notebook/graphs/acm_extraction.py` | `metadata_and_structure_node`, `compile_inventory`, `save_intelligence` |
| Prompts | `prompts/acm/metadata_and_structure.jinja`, `building_inventory.jinja`, `page_tagging.jinja`, `structure_extraction.jinja`, `metadata_extraction.jinja` |

---

## Findings

### Finding 1 — Pre-extraction DOES populate SF-bound fields (end-to-end trace confirmed)

Five `BuildingRecord` fields that appear in `BUILDING_SF_MAPPING` are populated exclusively via pre-extraction, not via per-building LLM extraction.

**Trace:**

```
extract_metadata_and_structure()           # metadata_and_structure.py
  → DocumentMeta stored in state["document_metadata"]

extract_building_node()                    # acm_extraction.py:647
  → _backfill_building_from_doc_meta(record, doc_meta)  # acm_extraction.py:619-644

_backfill_building_from_doc_meta() writes:
  BuildingRecord.building_address  ← DocumentMeta.site_address
  BuildingRecord.suburb            ← DocumentMeta.suburb
  BuildingRecord.postcode          ← DocumentMeta.postcode
  BuildingRecord.date_of_audit_report ← DocumentMeta.report_date
  BuildingRecord.site_name         ← DocumentMeta.site_name

BUILDING_SF_MAPPING in sf_export.py:
  Building_Address__c   → "building_address"   (sf_export.py:34)
  Suburb__c             → "suburb"             (sf_export.py:35)
  Postcode__c           → "postcode"           (sf_export.py:36)
  Date_of_Audit_Report__c → "date_of_audit_report" (sf_export.py:46)
  Site_Name__c          → "site_name"          (sf_export.py:47)
```

**References:**
- `acm_extraction.py:619-644` — `_backfill_building_from_doc_meta()`
- `acm_extraction.py:816-819` — backfill call in `extract_building_node`
- `sf_export.py:34-36, 46-47` — `BUILDING_SF_MAPPING`

---

### Finding 2 — Prompts use Python domain names, not SF API names (correct but opaque)

All five pre-extraction prompts ask the LLM for **Python domain field names** (`site_name`, `suburb`, `report_date`, etc.), not SF API names. This is intentional: the LLM writes to `DocumentMeta`, which `_backfill_building_from_doc_meta()` then maps to `BuildingRecord`, which `BUILDING_SF_MAPPING` maps to SF.

For the five SF-bound fields the alignment is correct:

| Prompt field | DocumentMeta field | BuildingRecord field | SF API name |
|---|---|---|---|
| `site_name` | `site_name` | `site_name` | `Site_Name__c` |
| `site_address` | `site_address` | `building_address` | `Building_Address__c` |
| `suburb` | `suburb` | `suburb` | `Suburb__c` |
| `postcode` | `postcode` | `postcode` | `Postcode__c` |
| `report_date` | `report_date` | `date_of_audit_report` | `Date_of_Audit_Report__c` |

The prompts also ask for nine additional fields (`organization`, `building_size`, `building_age`, `inspection_dates`, `inspector_names`, `document_scope`, `methodology`, `revision_date`, `regional_classification`) that have **no SF mapping and no `_backfill` handler**. These fields are extracted by the LLM on every document and silently discarded.

**References:**
- `prompts/acm/metadata_and_structure.jinja:6-22` — full field list requested from LLM
- `acm_extraction.py:619-644` — only 5 fields have backfill handlers
- `sf-schema-snapshot.json` — no matching SF fields for `building_size`, `building_age`, etc.

---

### Finding 3 — BuildingInventory (E1-S17) does NOT write directly to BuildingRecord

`BuildingInventory` produces `BuildingMeta` objects with `building_id`, `name`, `year`, `construction`, `levels`, `page_start`, `page_end`, `complexity`, `rooms`. None of these fields appear in `BUILDING_SF_MAPPING` or are written to `BuildingRecord` by the inventory compiler.

The inventory's role is **navigation only**: it tells the orchestrator which page ranges to pass to the per-building Phase 1 LLM. The Phase 1 LLM (not the inventory) populates `BuildingRecord` from the building's page content.

Indirect SF influence: `BuildingInventory` → `synthesize_page_tags()` → `PageTaggingResult` stored in state → determines which pages the orchestrator classifies as ASBESTOS_REGISTER, which affects which tables are extracted.

**References:**
- `acm_extraction.py:435-538` — `compile_inventory` node
- `acm_extraction.py:515-530` — `synthesize_page_tags()` call
- `building_inventory.py:772-887` — `compile_building_inventory()` — no BuildingRecord writes

---

### Finding 4 — E1-S19 metadata backfill works end-to-end; date format is a Data Loader risk

The E1-S19 connection is confirmed end-to-end. `DocumentMeta.report_date` reaches `Date_of_Audit_Report__c` in the SF export.

**Risk:** `Date_of_Audit_Report__c` is typed as `date` in SF (`sf-schema-snapshot.json:50`). `DocumentMeta.report_date` is `Optional[str]` preserving the original document format ("15/03/2023", "15 March 2023", "March 2023"). `sf_export.py:_format_value()` passes the raw string to the CSV unchanged. Data Loader requires ISO 8601 (`YYYY-MM-DD`) for date fields and will reject non-conforming values.

No date normalization step exists anywhere in the pipeline between extraction and export.

**References:**
- `metadata_extractor.py:50-64` — date regex patterns (Australian format, month-name format)
- `parsers/base.py:67` — `report_date: Optional[str]` (no date type constraint)
- `acm_extraction.py:641` — `record.date_of_audit_report = doc_meta.report_date` (raw str)
- `sf_export.py:241-255` — `_format_value()` — no date normalization
- `sf-schema-snapshot.json:50` — `Date_of_Audit_Report__c: type=date`

---

### Finding 5 — Three dead imports in acm_extraction.py

The pre-extraction refactor (S4 merge) left three functions imported but never called in the active graph:

| Import | File | Line | Status |
|--------|------|------|--------|
| `tag_pages` | `page_tagger.py` | `acm_extraction.py:84` | Dead — `synthesize_page_tags()` replaced it |
| `extract_document_metadata` | `metadata_extractor.py` | `acm_extraction.py:67` | Dead — combined `extract_metadata_and_structure()` is active |
| `extract_document_structure` | `document_structure.py` | `acm_extraction.py:59` | Dead — same reason |

These imports are harmless at runtime but create confusion: a reader or IDE jump-to-definition will find code that looks load-bearing but is bypassed.

**References:**
- `acm_extraction.py:59, 67, 84` — dead imports
- `acm_extraction.py:515-518` — `synthesize_page_tags()` is the live path
- `acm_extraction.py:364` — `extract_metadata_and_structure()` is the live call

---

### Finding 6 (Critical) — `_merge_site_config()` writes fabricated SF field names

`sf_export.py:218-238` writes to `Department__c` and `Agency__c`:

```python
department = getattr(site_config, "department", None)
if department:
    row["Department__c"] = str(department)      # sf_export.py:228-229

agency = getattr(site_config, "agency", None)
if agency:
    row["Agency__c"] = str(agency)              # sf_export.py:231-233
```

Neither `Department__c` nor `Agency__c` appears in `Building__c` in the SF schema. The real SF field is `Responsible_Agency_Department__c` (`sf-schema-snapshot.json:57`). `Agency__c` has no counterpart in SF at all.

This function is called from `building_to_sf_row()` at `sf_export.py:184` whenever a `SiteConfig` is present. If an officer has configured a department/agency, the export CSV will contain fabricated column names that Data Loader will reject.

The Phase 2b rewrite fixed `BUILDING_SF_MAPPING` and `ITEM_SF_MAPPING` but missed `_merge_site_config()`.

**References:**
- `sf_export.py:218-238` — `_merge_site_config()`
- `sf-schema-snapshot.json:57` — real SF field: `Responsible_Agency_Department__c`
- `site_config.py:92-103` — `SiteConfig.department`, `SiteConfig.agency`

---

### Finding 7 — Nine LLM-extracted fields are discarded with no consumer

The `metadata_and_structure.jinja` prompt (and the standalone `metadata_extraction.jinja`) asks the LLM to extract these fields on every document run:

| DocumentMeta field | SF equivalent | Status |
|---|---|---|
| `organization` | None direct — goes to `SiteConfig.agency` (itself broken per Finding 6) | Indirect dead end |
| `building_size` | `Est_Building_Size_m2__c` (doesn't exist in SF) | Fully dead |
| `building_age` | No SF counterpart | Fully dead |
| `inspection_dates` | No SF counterpart | Fully dead |
| `inspector_names` | `Identifying_Hygiene_Consulting_Company__c` (partial overlap) | Not wired |
| `document_scope` | No SF counterpart | Fully dead |
| `methodology` | No SF counterpart | Fully dead |
| `revision_date` | No SF counterpart | Fully dead |
| `regional_classification` | No SF counterpart | Fully dead |

These consume LLM tokens on every document extraction but produce no output that reaches SF or any other persisted downstream consumer (no DB column, no API endpoint, no export row).

**References:**
- `prompts/acm/metadata_and_structure.jinja:6-22` — full field list
- `parsers/base.py:50-107` — `DocumentMeta` model (all fields defined)
- `acm_extraction.py:619-644` — only 5 fields have backfill handlers
- `sf-schema-snapshot.json` — field universe

---

## Recommendations

| Priority | Action | Target |
|---|---|---|
| HIGH | Fix `_merge_site_config()`: replace `Department__c` → `Responsible_Agency_Department__c`, drop `Agency__c` | `sf_export.py:227-233` |
| HIGH | Add date normalization (ISO 8601) before `date_of_audit_report` reaches the CSV | `sf_export.py:_format_value()` or `_backfill_building_from_doc_meta()` |
| MED | Remove 3 dead imports from `acm_extraction.py` | Lines 59, 67, 84 |
| MED | Trim `metadata_and_structure.jinja` to the 5 fields that have backfill handlers, OR add backfill for the remaining fields if they have SF targets | `prompts/acm/metadata_and_structure.jinja` |
| LOW | Add `Responsible_Agency_Department__c` to `BUILDING_SF_MAPPING` and wire `SiteConfig.department` through it properly | `sf_export.py:BUILDING_SF_MAPPING` |

The first two are SF export correctness issues. The rest are dead-code/efficiency issues suitable for E38-S2.

---

## References

| File | Line(s) | Note |
|------|---------|------|
| `open_notebook/extractors/metadata_extractor.py` | 386-438 | `extract_document_metadata()` — standalone, now dead in graph |
| `open_notebook/extractors/document_structure.py` | 238-293 | `extract_document_structure()` — standalone, now dead in graph |
| `open_notebook/extractors/metadata_and_structure.py` | 47-102 | Active combined extraction path |
| `open_notebook/extractors/metadata_and_structure.py` | 165-219 | `synthesize_page_tags()` — active page-tag path |
| `open_notebook/extractors/building_inventory.py` | 772-887 | `compile_building_inventory()` |
| `open_notebook/extractors/page_tagger.py` | 402-477 | `tag_pages()` — exists but bypassed |
| `open_notebook/extractors/parsers/base.py` | 50-107 | `DocumentMeta` model |
| `open_notebook/graphs/acm_extraction.py` | 59, 67, 84 | Dead imports |
| `open_notebook/graphs/acm_extraction.py` | 619-644 | `_backfill_building_from_doc_meta()` |
| `open_notebook/graphs/acm_extraction.py` | 816-819 | Backfill call in `extract_building_node` |
| `open_notebook/extractors/exporters/sf_export.py` | 24-53 | `BUILDING_SF_MAPPING` |
| `open_notebook/extractors/exporters/sf_export.py` | 218-238 | `_merge_site_config()` — fabricated field names |
| `prompts/acm/metadata_and_structure.jinja` | 6-22 | Field list requested from LLM |
| `config/sf-schema-snapshot.json` | 38-59 | Real SF extractable field set |
