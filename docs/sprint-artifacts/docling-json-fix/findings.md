# Docling Document JSON Fix — Findings

## Issue

GitHub #104: `docling_document_json` stored as empty dict `{}` in `acm_table_section` table, blocking per-row extraction (#105).

## Data Flow Under Investigation

```
DoclingAdapter.extract()
  └─ table.data.model_dump(mode="json")        → docling_json (Dict)        [docling_adapter.py:151]
       └─ NormalizedTable(docling_json=...)     → NormalizedTable dataclass   [docling_adapter.py:158-169]
            └─ _merge_provider_tables()         → merged dict list           [source_commands.py:447]
                 └─ _store_docling_tables()     → repo_create() call         [source_commands.py:197]
                      └─ connection.insert()    → SurrealDB storage          [repository.py:93]

Retrieval:
_get_docling_tables()                           → SELECT * FROM acm_table_section  [orchestrator.py:54-61]
  └─ extract_items_node                         → dj = t.get("docling_document_json")  [acm_extraction.py:1034]
       └─ if dj:                                → {} is FALSY → per-row skipped!
```

## Root Cause: SurrealDB `TYPE option<object>` Missing `FLEXIBLE` Keyword

**Confirmed 2026-03-14.**

### The Problem

Migration 48 defined `docling_document_json` as `TYPE option<object>` **without the `FLEXIBLE` keyword**:

```sql
-- migrations/48.surrealql (BROKEN)
DEFINE FIELD IF NOT EXISTS docling_document_json ON TABLE acm_table_section TYPE option<object>;
```

SurrealDB's `SCHEMAFULL` mode (set in migration 18) enforces strict type constraints. A non-FLEXIBLE `object` type **silently strips nested arrays** from the stored value. The `docling_document_json` payload contains `table_cells: [...]` (an array of cell objects), which was being discarded on every INSERT.

### Evidence

1. **Direct SurrealQL test**: Created a record with `{num_rows: 2, table_cells: [{text: "Room 1", ...}]}` → retrieved `{}` (empty dict)
2. **Added `FLEXIBLE`**: Same insert → retrieved full data with all nested arrays intact
3. **Pattern in existing codebase**: Fields that successfully store nested data (`source.asset`, `episode.transcript`, `episode.outline`) all use `FLEXIBLE TYPE option<object>` (migrations 1 and 7)
4. **Existing DB data**: All 10 `acm_table_section` rows had `docling_document_json: {}` despite Docling producing valid data

### Why Only This Field?

- The `source_intelligence` table also has `option<object>` fields without `FLEXIBLE` (building_inventory, document_structure, page_tags)
- Those fields store nested arrays successfully because they use `UPSERT ... SET` query path, not `connection.insert()` RPC
- The INSERT RPC path (used by `repo_create()`) enforces schema more strictly than the UPSERT query path

### Layer-by-Layer Diagnosis

| Layer | File:Line | Value Type | Size | Data Present? |
|-------|-----------|------------|------|---------------|
| Adapter output | docling_adapter.py:151 | dict | ~50KB+ | YES — model_dump produces full data |
| Merge step | source_commands.py:317-465 | dict (7 paths) | ~50KB+ | YES — all paths propagate docling_json correctly |
| Pre-insert | source_commands.py:197 | dict | ~50KB+ | YES — table.get("docling_json") resolves correctly |
| Post-insert return | repository.py:93 | dict | minimal | NO — SurrealDB returns `{}` |
| DB query | SurrealDB direct | object | minimal | NO — `{}` stored |
| Graph retrieval | orchestrator.py:71 | dict | minimal | NO — `{}` passed to extract_items_node |

### Other Eliminated Causes

- **`parse_record_ids()`** — Safe recursive converter, only touches RecordID types. No data corruption.
- **CBOR client** — Python SurrealDB client uses CBOR encoding which natively supports nested maps/arrays. No size limits.
- **`model_dump(mode="json")`** — Produces valid data. The `mode="python"` bug was fixed in a prior commit.
- **Data flow in Python** — All merge paths correctly propagate `docling_json` from adapter to `_store_docling_tables()`.

## Fix Applied

### Migration 51 — Add `FLEXIBLE` keyword

```sql
-- migrations/51.surrealql
REMOVE FIELD IF EXISTS docling_document_json ON TABLE acm_table_section;
DEFINE FIELD docling_document_json ON TABLE acm_table_section FLEXIBLE TYPE option<object>;
```

### Test File Fix

Updated `tests/test_docling_json_storage.py`:
- Class renamed: `TestDoclingAdapterExportToDict` → `TestDoclingAdapterModelDump`
- Mocks now use `table.data.model_dump(mode="json")` instead of `table.export_to_dict()`
- Asserts `mock_data.model_dump.assert_called_once_with(mode="json")`

### Pre-Existing Test Fixes (discovered during full suite run)

1. `test_item_extraction.py` — Added `per_row_actually_ran: False` to expected return dicts
2. `test_ollama_chunking.py` — Updated num_ctx tests to match current `_apply_ollama_extraction_settings()` behavior (only sets num_ctx when caller passes 0)
3. `test_pipeline_integration.py` — Changed recovery test to check `per_row_actually_ran` state key instead of env var

## Verification Results

### Round-trip Test (SurrealQL)

```
CREATE → {num_rows: 3, table_cells: [{text: "Room 101", ...}, {text: "Ceiling tiles", ...}, {text: "Chrysotile", ...}]}
SELECT → {num_rows: 3, table_cells: [{text: "Room 101", ...}, {text: "Ceiling tiles", ...}, {text: "Chrysotile", ...}]}
✓ All nested data preserved
```

### Full Extraction Run (Broadmeadows)

- Source: `source:mc5llofksqsglrjsfssj` (Clutch_Broadmeadows.pdf)
- Command: `force=True` re-extraction
- **8 docling tables** with populated `docling_document_json` (cell counts: 18, 9, 187, 188, 191, 75, 38, 23)
- **33 acm_records** extracted (vs 29 before, vs 31 ground truth)
- **1 building** detected (correct)
- Per-row extraction confirmed via `row_index:` markers in `data_issues`
- Records contain: location, product, material_description, sample_no, sample_result, room_name, friable, area_type

### Test Suite

- `uv run ruff check .` — All checks passed
- `uv run pytest tests/ -x` — **2167 passed, 0 failed**, 15 skipped, 2 xfailed
