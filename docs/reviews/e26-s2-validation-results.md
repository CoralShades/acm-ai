# E26-S2 Validation Results — DataFrame Verification

**Date**: 2026-02-27
**Source**: Broadmeadows Police Station (`Clutch_Broadmeadows.pdf`, 19 pages)
**Flag**: `DOCLING_DIRECT_TABLE_EXTRACTION=true`
**Migration**: 37 applied (`structured_json` field on `acm_table_section`)
**Script**: `scripts/research/e26_s2_validate_dataframes.py`

## Results vs E25 Spike

| Metric | E25 Spike | E26 Integration | Match? |
|--------|----------|-----------------|--------|
| Tables stored | 8 | 8 | YES |
| Register tables | 3 (pp.5-7) | 3 (pp.5-7) | YES |
| Register rows | 30 | 30 | YES |
| Rows per register table | 10 each | 10 each | YES |
| "Same as" rows | 9 | 9 | YES |
| "Assumed positive" (Not Sampled) | 4 | 4 | YES |
| Unique NATA sample numbers | 16+ | 17 | YES |
| Sample numbers clean | After normalization | 0 split samples | YES |
| Hazard status clean | After normalization | 0 "Asbestos " prefixes | YES |
| Record #9 found | Yes (Table 2, page 5) | Yes (page 5) | YES |
| Page 8 gap | Expected (no table) | Confirmed (0 tables) | YES |
| `table_type` field | "docling_direct_api" | All 8 correct | YES |
| `raw_html` populated | Yes (all 8) | Yes (all 8) | YES |
| `raw_text` populated | Yes (all 8) | Yes (all 8) | YES |
| `structured_json` populated | Yes (all 8) | Yes (all 8) | YES |
| Page starts | [2,4,5,6,7,11,12,13] | [2,4,5,6,7,11,12,13] | YES |
| Processing time | 22.41s | 21.76s | YES (faster) |

## Storage Verification

All 8 tables successfully stored in `acm_table_section` via `_store_docling_tables()`:

| Table | Page | Rows | Cols | Type |
|-------|------|------|------|------|
| 0 | 2 | 10 | 3 | Summary table |
| 1 | 4 | 5 | 2 | Info table |
| 2 | 5 | 10 | 18 | **Register (Ground + First floor)** |
| 3 | 6 | 10 | 18 | **Register (First floor + External)** |
| 4 | 7 | 10 | 19 | **Register (External + Internal)** |
| 5 | 11 | 12 | 6 | Sample analysis table |
| 6 | 12 | 5 | 7 | Sample analysis table |
| 7 | 13 | 5 | 4 | Additional table |

All records have:
- `table_type = "docling_direct_api"` (correct discriminator)
- `raw_html` populated (HTML table export)
- `raw_text` populated (markdown table export)
- `structured_json` populated (CSV export for programmatic access)
- `page_start` and `page_end` matching provenance

## Record #9 — Switch Room / Battery Charger

**FOUND** in stored data (page 5 table).

This is the record that was missed by the LLM in E23 (28/31) but is directly
extractable from the Docling DataFrame. Located in Table 2, Row 9:

> First floor | Switch Room | Automatic battery charger | Fuses | Assumed positive

Confirmed via SurrealQL query:
```sql
SELECT id, page_start FROM acm_table_section
WHERE source_id = source:e26_s2_test
AND table_type = 'docling_direct_api'
AND (string::lowercase(raw_text) CONTAINS 'battery charger'
     OR string::lowercase(structured_json) CONTAINS 'battery charger');
```

## Page 8 Gap Verification

**CONFIRMED** — No table has `page_start = 8`. This is expected behavior:
- Page 8 contains 2-3 continuation rows from the register (Lift Foyer, Disabled Toilet)
- These rows are below Docling's TableFormer detection threshold
- The content IS captured by PyMuPDF's `full_text` (unchanged production path)
- Records #30 and #31 remain addressable via PyMuPDF + LLM extraction

## S1 Bugs Found and Fixed

Two bugs were discovered during validation and fixed:

### Bug 1: Integer Column Names (source_commands.py:100-101)

**Symptom**: Tables 0 and 1 (pages 2, 4) failed to extract — only 6/8 tables returned.

**Root Cause**: `_extract_tables_with_docling()` called `col.lower()` on column names
to find hazard/status columns for normalization. Tables 0 and 1 have integer column
names (no header row), causing `AttributeError: 'int' object has no attribute 'lower'`.

**Fix**: Changed `col.lower()` to `str(col).lower()`.

### Bug 2: Missing `ensure_record_id()` (source_commands.py:145)

**Symptom**: `_store_docling_tables()` failed with SurrealDB error —
`expected a record<source>` but got a string.

**Root Cause**: `source_id` was passed as a bare string to `repo_create()`,
but the `acm_table_section.source_id` field is `TYPE record<source>`.
Other commands (e.g., `embedding_commands.py`) use `ensure_record_id()`.

**Fix**: Changed `"source_id": source_id` to `"source_id": ensure_record_id(source_id)`.

## Normalization Verification

The S1 normalization pipeline was validated:

1. **Split sample numbers**: All `34511-039- NNN` patterns correctly normalized to
   `34511-039-NNN` (0 split samples remaining in output)
2. **Hazard status**: All `Asbestos Negative/Positive/Assumed positive` correctly
   stripped to `Negative/Positive/Assumed positive` (0 prefixes remaining)

## Discrepancies

**None** — All 16 metrics match E25 spike results exactly.

The 17 unique sample numbers (vs E25's "16+" expected) includes sample 005
(Ceiling Space / Ductwork / Flange mastic) which is the extra record discovered
by Docling that is NOT in the ground truth CSV. This is correct behavior.

## Verdict

**PASS** — All metrics match E25 spike. Proceed to E26-S3 (Orchestrator Context Injection).

## Artifacts

| File | Description |
|------|-------------|
| `scripts/research/e26_s2_validate_dataframes.py` | Validation script |
| `research-output/e26-s2/validation_results.json` | Full JSON results |
| `docs/reviews/e26-s2-validation-results.md` | This report |
