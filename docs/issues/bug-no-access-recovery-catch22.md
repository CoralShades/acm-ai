# Bug: No-Access Record Recovery Catch-22

**Severity**: High
**Impact**: 2 records consistently missed per Broadmeadows extraction (6.5% recall loss)
**Discovered**: 2026-03-13 via trace audit of LangSmith traces `eed83b6e` / `91d56ebd`
**Ground truth**: `benchmarks/ground_truth/broadmeadows.json` (31 records)

## Summary

When `ACM_ITEM_EXTRACTION_MODE=per_row` (default) but `docling_document_json` is NULL
in `acm_table_section` rows, "No Access" records hit a dead zone where **neither** the
per-row segmenter **nor** the bulk recovery node processes them.

## Missing Records

| # | Room | Location | Product | Sample | Result | Comments |
|---|------|----------|---------|--------|--------|----------|
| 30 | Lift Foyer | Lift | Internal lining | Not Sampled | Assumed Positive | No access. |
| 31 | Main Foyer | Room Adjacent Disabled Toilet | Unknown | Not Sampled | Assumed Positive | No access. |

Additionally, **Property Storage / Floor / Floor covering / 34511-039-017** is consistently
missed by bulk LLM extraction (19-column table too wide for 7b models).

## Root Cause Chain

### Step 1: `docling_json` key never stored (old extraction path)

`source_commands.py:141-151` — `_extract_tables_with_docling()` builds table dicts
**without** a `docling_json` key:

```python
tables.append({
    "table_index": idx,
    "page": page_no,
    "rows": len(df),
    "columns": list(df.columns),
    "csv": df.to_csv(index=False),
    "markdown": df.to_markdown(index=False),
    "html": table.export_to_html(doc=doc),
    # !! Missing: "docling_json": table.data.model_dump(mode="json")
})
```

`_store_docling_tables()` at line 189 calls `table.get("docling_json")` -> `None` -> stored as NULL.

**Note**: The `DoclingAdapter` (line 151) DOES populate `docling_json` correctly, but
`source_commands.py` uses the old direct path, not the adapter.

### Step 2: Per-row segmenter never runs

`acm_extraction.py:1024-1031`:
```python
docling_json_tables = []
for t in (docling_tables or []):
    dj = t.get("docling_document_json")
    if dj:  # Always None -> list stays empty
        docling_json_tables.append(dj)
```

Since `docling_json_tables` is empty, per-row extraction is disabled and falls back to
bulk LLM at line 1131.

### Step 3: `recover_no_access_node` checks env var, not actual execution

`acm_extraction.py:2376`:
```python
if os.getenv("ACM_ITEM_EXTRACTION_MODE", "per_row") == "per_row":
    logger.info("Skipping no-access recovery in per-row mode (handled by segmenter)")
    return state  # SKIPS RECOVERY
```

The node assumes per-row mode ran successfully and the segmenter already handled
synthetic rows. But when `docling_document_json` is NULL, per-row fell back to bulk,
and `scan_text_for_synthetics()` never executed.

### Result: Dead Zone

```
per_row mode (env var) ─┐
                        ├─> Per-row segmenter: SKIPPED (no docling JSON)
                        │   └─ scan_text_for_synthetics(): NEVER CALLED
                        │
                        └─> recover_no_access_node: SKIPPED (env var = per_row)
                            └─ _recover_no_access_records(): NEVER CALLED

No Access records: UNRECOVERABLE by either path
```

## Fix Plan

### Fix 1: Store `docling_json` in old extraction path

`source_commands.py:141-151` — Add the missing key:

```python
tables.append({
    ...
    "docling_json": table.data.model_dump(mode="json"),
})
```

This is the same call `DoclingAdapter` makes at line 151.

### Fix 2: Track actual per-row execution in state

`acm_extraction.py` — Set a state flag `per_row_actually_ran` when per-row extraction
runs successfully. Then `recover_no_access_node` checks the flag instead of the env var:

```python
# In recover_no_access_node:
if state.get("per_row_actually_ran"):
    logger.info("Skipping no-access recovery (per-row segmenter handled it)")
    return state
```

### Fix 3 (stretch): Migrate source_commands.py to use DoclingAdapter

Replace the old `_extract_tables_with_docling()` direct calls with `DoclingAdapter().extract()`,
which already produces `docling_json` correctly. This eliminates the key mismatch permanently.

## Verification

- Run extraction on `Clutch_Broadmeadows.pdf`
- Confirm 31/31 records matched (vs current 27/31)
- Specifically verify Lift Foyer and Main Foyer "No access" records appear

## Related Issues

- `bug-page-range-table-loss.md` — page range overlap filter (fixed)
- `ollama-extraction-hardening.md` — small model extraction quality
- Gate2 benchmark: `benchmarks/results/gate2_rerun_broadmeadows_results.json`
  - Best result: 30/31 matched (Property Storage still missed)
  - 2 hallucinated records: "Ceiling space throughout/Flange joints", "Ceiling Space/Unknown"

## Trace References

- LangSmith `eed83b6e`: ACM extraction — 343.9s, 76,628 tokens, 27 records
- LangSmith `91d56ebd`: Document ingestion — 125.5s, Docling processing
- Per-run log: `logs/runs/2026-03-12T13-57-07_hs6w3s4m8lbv/extraction.log`
