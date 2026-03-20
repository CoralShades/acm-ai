# E2E Live Test Report -- Clutch_Broadmeadows.pdf

**Date**: 2026-03-20
**Test type**: Live E2E extraction with UX mega-pack verification
**Tester**: Parallel agent team (extraction + docs)

---

## Extraction Pipeline Results

| Metric | Value |
|--------|-------|
| PDF | Clutch_Broadmeadows.pdf |
| Records extracted | 42 |
| Buildings | 1 |
| Tables detected | 9 |
| Model | ollama/llama3.1:8b |
| Hardware | RTX 4090 (CUDA 12.6) |
| Pipeline time | 291s (4m 51s) |
| End-to-end time | 424s (7m 4s) |

---

## Errors Found and Fixed

| # | Error | Severity | Root Cause | Fix |
|---|-------|----------|------------|-----|
| 1 | page_start int_type Pydantic error | HIGH | LLM returns page numbers as string ("3"), Pydantic model requires int | Added `BeforeValidator` coercion on `page_start`/`page_end` fields |
| 2 | RecordID serialization warning | MEDIUM | `base.py` setattr loop sets SurrealDB `RecordID` objects on string-typed fields | Convert `RecordID` to `str()` in the setattr loop |
| 3 | sample_result enum mismatch (78 warnings) | MEDIUM | Values from ARA documents (e.g., "Detected", "Not detected") not in the existing enum | Expanded enum values + added synonym mapping |
| 4 | area_type Internal/External rejected (16 warnings) | LOW | Salesforce picklist values ("Internal", "External") differ from BAR vocabulary values | Added SF values to the allowed set |
| 5 | friability "-" warning (10 occurrences) | LOW | Dash character not recognized in friability mapping | Added "-" to the friability map |
| 6 | Row extraction failures (3/44 rows) | LOW | Footer rows in tables not detected by row segmenter | Added footer row detection logic to row segmenter |
| 7 | Schema inference invalid response | LOW | LLM JSON response lacks "mappings" key | Cascade from Error 1 -- page_start coercion failure caused schema inference to produce incomplete output |
| 8 | live-stats returns zeros | HIGH | SurrealDB WHERE clause compares string `"source:xxx"` against record ref column -- always false | Used `type::thing()` to cast string to record reference in queries |

---

## UX Mega-Pack Features Verified

| Feature | Status | Notes |
|---------|--------|-------|
| Async upload | PASS | Dialog closes in <1s, navigates to extract page |
| review_status lifecycle | PASS | `extracting` on upload, `pending_review` on all terminal paths |
| live-stats endpoint | PASS (after fix) | Returns `tables=9, buildings=1, records=42` after type::thing() fix |
| 3-panel extract page | PASS | DoclingTablesPanel, BuildingsProgressPanel, LiveRecordsPanel all render |
| Job card counters | PASS (after fix) | Live counters update during extraction |
| CUDA + Docling + Ollama | PASS | Full local pipeline on RTX 4090, no cloud calls |

---

## SurrealDB Pattern: type::thing() for Record Reference Comparison

The `live-stats` endpoint initially returned all zeros because SurrealDB `WHERE source_id = $sid` with a string parameter does not match record reference columns. The fix uses inline `type::thing()` casting:

```sql
-- WRONG: string param never matches record ref column
SELECT count() FROM acm_table_section WHERE source_id = $sid GROUP ALL;

-- CORRECT: cast string to record reference
SELECT count() FROM acm_table_section WHERE source_id = type::thing('source:xxx') GROUP ALL;
```

This pattern applies anywhere a string source/record ID is compared against a SurrealDB column typed as `record<table>`.

---

## Key Patterns Documented

1. **LLM string-to-int coercion**: LLMs frequently return numeric fields as strings. Use Pydantic `BeforeValidator` to coerce before validation rather than rejecting.

2. **RecordID serialization in base.py**: The `ObjectModel` setattr loop receives `RecordID` objects from SurrealDB responses. When the target field is typed as `str`, wrap with `str()` to avoid serialization warnings downstream.

3. **type::thing() for record ref queries**: When building raw SurrealQL queries with string record IDs against `record<T>` columns, use `type::thing('table:id')` instead of string comparison.

---

## Timeline

- **T+0s**: Upload initiated (async, dialog closes immediately)
- **T+5s**: Extract page renders, Docling tables panel starts populating
- **T+60s**: Structure + preflight stages complete
- **T+120s**: Schema inference + orchestrator running
- **T+291s**: Pipeline complete (42 records, 9 tables, 1 building)
- **T+424s**: Full E2E including post-extraction validation and stats polling
