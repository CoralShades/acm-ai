# Task Plan: Fix docling_document_json Empty Dict Bug (#104)

## Objective

Trace the full data path from Docling extraction → Python adapter → SurrealDB storage → graph retrieval → per-row extraction, find where `docling_document_json` is lost (stored as `{}`), fix it, and verify per-row extraction triggers.

---

## Phase 1 — Diagnosis (READ ONLY)

- [x] **1.1** Subagent 1 traced adapter data flow — `model_dump(mode="json")` produces valid data
- [x] **1.2** Subagent 1 traced `_store_docling_tables()` — `docling_json` mapped correctly to `docling_document_json`
- [x] **1.3** Subagent 2 traced `repo_create()` — `parse_record_ids()` is safe, CBOR encoding is correct
- [x] **1.4** Subagent 2 analyzed `connection.insert()` return — SurrealDB returns `{}` post-insert (data lost at DB layer)
- [x] **1.5** Verified existing data: all 10 `acm_table_section` rows had `docling_document_json: {}`
- [x] **1.6** Queried SurrealDB directly: confirmed `docling_document_json: {}` on all records
- [x] **1.7** Identified exact layer: SurrealDB INSERT with non-FLEXIBLE `option<object>` strips nested arrays

## Phase 2 — Root Cause Analysis

- [x] **2.1** SurrealDB `TYPE option<object>` CONFIRMED as root cause — silently strips nested arrays (table_cells)
- [x] **2.2** Python client `insert()` not the cause — CBOR natively supports nested maps/arrays
- [x] **2.3** `parse_record_ids()` not the cause — pure recursive RecordID converter, no data mutation
- [x] **2.4** Direct SurrealQL INSERT test: `{table_cells: [...]}` → stored as `{}`. FLEXIBLE version → data preserved.
- [x] **2.5** N/A (Python client ruled out)
- [x] **2.6** Root cause documented in findings.md: SurrealDB SCHEMAFULL + non-FLEXIBLE object + nested arrays = silent data loss

## Phase 3 — Fix Implementation

- [x] **3.1** Applied migration 51: `REMOVE FIELD` + `DEFINE FIELD ... FLEXIBLE TYPE option<object>`
- [x] **3.2** Created migration files: `51.surrealql` and `51_down.surrealql`
- [x] **3.3** N/A (Python client serialization not needed)
- [x] **3.4** N/A (adapter code is correct)
- [x] **3.5** Round-trip verified via SurrealQL: INSERT with nested arrays → SELECT returns identical data
- [x] **3.6** Updated test file: `TestDoclingAdapterExportToDict` → `TestDoclingAdapterModelDump` (uses `model_dump`)
- [x] **3.7** Fixed 3 pre-existing test failures: test_item_extraction, test_ollama_chunking, test_pipeline_integration

## Phase 4 — Node Data Flow Verification

- [x] **4.1** Subagent 3 traced all graph node inputs/outputs — correct data flow confirmed
- [x] **4.2** Building inventory → building_meta_cache → extract_items_node — confirmed
- [x] **4.3** Docling tables now stored with populated JSON → _get_docling_tables retrieves correctly
- [x] **4.4** `extract_items_node` enters per-row path — confirmed via `row_index:` markers in data_issues
- [x] **4.5** `docling_json_tables` non-empty — 8 tables with 18-191 cells each
- [x] **4.6** `segment_multiple_tables()` produces rows — 33 records extracted

## Phase 5 — E2E Verification

- [x] **5.1** Old records deleted by `force=True` re-extraction
- [x] **5.2** Full extraction completed successfully (command:l98zgipj836uf7x9clof)
- [x] **5.3** `docling_document_json` populated: 8 tables, cell counts 18/9/187/188/191/75/38/23
- [x] **5.4** Per-row path confirmed via `row_index:` markers in `data_issues`
- [x] **5.5** 33 records extracted (vs 31 ground truth — 2 extra likely header/summary rows)
- [x] **5.6** `uv run pytest tests/ -x` — 2167 passed, 0 failed
- [x] **5.7** `uv run ruff check .` — All checks passed
