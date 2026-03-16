# Findings — Pipeline Fix Integrity Audit (2026-03-17)

## Fix Inventory (3 prior sessions)

### Session 1: Pipeline Debug (8 fixes, commit 476c285e)

| Fix | File | Signature | Status | Evidence |
|-----|------|-----------|--------|----------|
| F1: `format="json"` on metadata LLM | metadata_and_structure.py | `_apply_ollama_extraction_settings(model)` | **PRESENT** | line 152 (import), line 170 (call) |
| F2: `format="json"` on inventory LLM | building_inventory.py | `_apply_ollama_extraction_settings(model)` | **PRESENT** | line 767 (import), line 786 (call) |
| F3: Prompt rewrites (3 templates) | prompts/acm/*.jinja | Shortened templates | **PRESENT** | metadata=71L, inventory=93L, row_split=18L (all <100) |
| F4: WebSocket retry in `_get_docling_tables` | orchestrator.py | `for attempt in range(2)` | **PRESENT** | line 69 |
| F5: Stale detection `IS NULL OR = {}` | acm_commands.py | `docling_document_json IS NULL OR docling_document_json = {}` | **PRESENT** | line 249 |
| F6: `ensure_record_id()` in stale check | acm_commands.py | `_eri(source_id)` / `ensure_record_id` | **PRESENT** | lines 185, 244, 246 |
| F7: Page overlap logic in `_get_docling_tables` | orchestrator.py | `page_start <= $page_end AND page_end >= $page_start` | **PRESENT** | lines 58-59 |
| F8: Diagnostic query fix | acm_extraction.py | `IS NONE OR docling_document_json = {}` | **PRESENT** | line 996 |

### Session 2: PDF Format Audit (5 fixes, commit f26f7376)

| Fix | File | Signature | Status | Evidence |
|-----|------|-----------|--------|----------|
| C1: `internal_external` → `area_type` mapping | orchestrator.py + acm_extraction.py | `area_type` field mapping | **PRESENT** | orchestrator lines 513-544; acm_extraction lines 190-191, 199, 2147, 2215, 2564 |
| C2: `material_description` null safety | orchestrator.py | 4-level fallback chain | **PRESENT** | line 547: `material_description=item.acm_sub_classification` |
| C3: PyMuPDF page marker injection | source_commands.py | `--- Page N ---` markers | **PRESENT** | lines 97, 738, 773, 780 |
| H1: ARA one-line building header detection | building_inventory.py | Single-building fix | **PRESENT** | lines 454-455, 675-682, 978 |
| M2: `sample_result` field populated | acm_extraction.py | `sample_result` mapping | **PRESENT** | acm_extraction.py lines 1407, 1561, 1571, 1672+ (field lives in graph, not row_extractor — architecturally correct) |

### Session 3: Docling JSON Fix (commit f6441995)

| Fix | File | Signature | Status | Evidence |
|-----|------|-----------|--------|----------|
| Migration 51: FLEXIBLE TYPE | migrations/51.surrealql | `FLEXIBLE TYPE option<object>` | **PRESENT (file)** | File exists, correct SQL content |
| Test file fix: model_dump | test_docling_json_storage.py | `TestDoclingAdapterModelDump` | **PRESENT** | line 113 |
| model_dump(mode="json") | docling_adapter.py | `table.data.model_dump(mode="json")` | **PRESENT** | line 165 |
| num_ctx guard | utils.py | Only sets num_ctx when current == 0 | **PRESENT** | lines 284-286 |

## Code Audit Summary

**16/16 fix signatures PRESENT in current HEAD.** No code regressions found.

## Critical Regression: Migration Manager Not Updated

**Root cause:** `AsyncMigrationManager.__init__()` in `async_migrate.py` only listed migrations 1-49. Migrations 50, 51, and 52 existed as files but were **never registered** in the manager, so they never ran on API startup.

- **DB version before fix:** 49 (last applied: 2026-03-16T12:38:12Z)
- **Missing migrations:** 50 (remove orphan KG tables), 51 (FLEXIBLE TYPE), 52 (nullable config_json)
- **Impact:** docling_document_json always stored as `{}` because non-FLEXIBLE `option<object>` silently strips nested arrays/objects on SCHEMAFULL tables

**Fix applied:**
1. Added migrations 50-52 (up + down) to `AsyncMigrationManager` in `async_migrate.py`
2. Applied all 3 migrations directly to running SurrealDB
3. Verified `FLEXIBLE` keyword now present in schema via `INFO FOR TABLE acm_table_section`

## Data Flow Verification

| Check | Result |
|-------|--------|
| docling_document_json populated? | **NO** — 28 rows, all `{}`. Schema is now fixed but existing data was written pre-fix. Re-extraction needed. |
| Building names clean? | **MIXED** — 1/11 clean (Broadmeadows B001), 10/11 corrupted (Alexander Hospital — raw markdown table rows as names) |
| ACM record count | 142 total (Alexander=107, Broadmeadows copies=32+3) |
| Migration 51 applied? | **YES** (after manual application in this session) |
| DB version | 52 (up from 49) |

## Data Anomalies

1. **Corrupted building records** — 10/11 building_record rows have `building_name` containing pipe-delimited markdown table rows instead of clean names. All from `source:1zygd7x7lwcgswifbdzk` (Alexander Hospital). Likely extracted before building inventory fixes were applied.

2. **Ghost source** — `source:wog2zpyjh6lxvsrbq3h2` (Broadmeadows_2, created 20:23) has 0 buildings, 0 records, 0 table sections — incomplete/aborted extraction.

3. **Existing docling_document_json all empty** — Even though schema is now fixed, the 28 existing `acm_table_section` rows were written when the schema was non-FLEXIBLE. They store `{}`. A re-extraction is needed to populate this data.

## Test Results

- **2018 passed, 1 failed, 10 skipped, 2 xfailed** in 76.65s
- **Failed test:** `test_source_commands_docling::test_creates_acm_table_section_records` — **pre-existing known failure** (ensure_record_id returns RecordID object with angle brackets vs expected string format)
- **Lint:** All checks passed (`ruff check`)

## Regressions Found

| # | Severity | Description | Fix Applied |
|---|----------|-------------|-------------|
| 1 | **CRITICAL** | Migrations 50-52 not registered in AsyncMigrationManager — migration 51 (FLEXIBLE TYPE) never ran, causing docling_document_json to silently store {} | YES — added to manager + applied to running DB |

## Recommendations

1. **Re-extract Broadmeadows** — existing data has `docling_document_json = {}` because it was stored pre-migration-51. After re-extraction, per-row path will be reachable.
2. **Clean up Alexander Hospital data** — 10 corrupted building records should be deleted and re-extracted with current code (which includes all building inventory fixes).
3. **Delete ghost source** — `source:wog2zpyjh6lxvsrbq3h2` has no data and can be removed.
4. **Consider auto-discovery for migrations** — the manual list in AsyncMigrationManager is fragile. A glob-based approach (`sorted(glob("migrations/*.surrealql"))`) would prevent this class of regression.
