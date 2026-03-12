# Compound sample_result Values + Empty Correction JSON (N4+N6)

> **Discovered**: 2026-03-12
> **Priority**: P1
> **Status**: Open

## Problem

The LLM (llama3.1:8b) concatenates two adjacent columns into `sample_result`, producing values like `"Positive Assumed Positive"`, `"Negative No Access"`, `"Positive Stable"`. These are compound enum values that should be separate fields (`sample_result` + another field like `condition` or `access_status`).

When the correction loop attempts to fix these values, llama3.1:8b returns empty JSON (`{}`), causing `json.JSONDecodeError: Expecting value: line 1 column 1 (char 0)` for all 39 correction attempts. The correction loop runs but produces zero fixes.

## Evidence

- `worker.log` 07:05: 10 unique bad values seen across 13/18 records:
  - `Positive Assumed Positive`, `Negative No Access`, `Positive Stable`, `Negative Stable`, `Positive Good`, etc.
- `worker.log` 07:05: 39 correction attempts, all return `json.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`
- All corrections produce `auto=0, llm=0` — zero successful fixes
- Model: `llama3.1:8b` with `format="json"`

## Impact

- 13/18 records have invalid `sample_result` values
- Correction loop wastes ~280 seconds of LLM calls with no result
- Records stored with compound values fail downstream validation
- Affects any document where ACM register columns are not cleanly separated

## Fix Approach

1. Add `sample_result` to `_normalize_extraction_json()` — split compound values by known enum boundaries
2. Known valid `sample_result` values: `Positive`, `Negative`, `Assumed Positive`, `No Access`, `Not Sampled`
3. If compound detected, extract the first valid enum and move remainder to `material_condition` or `data_issues`
4. Improve correction prompt to be more explicit about expected enum values
5. Add a fallback: if correction returns empty JSON, skip that record's correction (don't retry)

## Files to Modify

| File | Change |
|------|--------|
| `open_notebook/extractors/orchestrator.py` | Add compound `sample_result` splitting to `_normalize_extraction_json()` |
| `prompts/acm/` | Improve correction prompt with explicit enum constraints |
| `open_notebook/graphs/acm_extraction.py` | Handle empty correction JSON gracefully (skip, don't crash) |
