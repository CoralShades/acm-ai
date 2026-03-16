# Mass Rejection (50-86%) on C_Broadmead / CF_Broadmead Document Variants

> **Discovered**: 2026-03-12 (extraction log audit + LangSmith trace analysis)
> **Source**: C_Broadmead.pdf / CF_Broadmead.pdf (Broadmeadows Police Station) — catastrophic validation rejection rates
> **Priority**: P0
> **Status**: Open

## Problem

Documents named `C_Broadmead.pdf` and `CF_Broadmead.pdf` (Broadmeadows Police Station) have catastrophic rejection rates during validation. Only 8/57 (14%) and 28/56 (50%) records survive validation. The rejected records are a mix of Negative-result ACM items that are intentionally filtered AND records with missing/malformed fields.

LangSmith trace analysis (trace `eed83b6e`) reveals:

- L1: The `records_failed=28` metric is misleading — the 28 "failed" records are Negative-result items (`result=Negative` or `result=Assumed Positive` floor/wall coverings) that the validator intentionally filters. They are not extraction failures.
- The validate node filters by result type: only ACM-positive records are persisted. This is by design but the metric name is confusing.
- For the 03:40 run (8/57), the higher rejection rate suggests additional field-level validation failures beyond the Negative-result filter.

## Evidence

- `acm-extraction.log` 03:40:11: `8 accepted, 49 rejected | with_issues=0` — 86% rejection
- `acm-extraction.log` 09:07:31: `28 accepted, 28 rejected | with_issues=0` — 50% rejection
- LangSmith trace `eed83b6e`: `validate` node processed 56 records → 28 accepted (all `result=Assumed Positive`), 28 rejected (all `result=Negative` or similar)
- LangSmith: `normalize_to_sf` generated 81 `data_issues` annotations but 0 `validation_errors`

## Impact

- Negative-result items are lost even though they may be valuable for completeness
- `records_failed` metric conflates intentional filtering with actual failures — misleading dashboards
- No CORRECT stage triggered (see bug-correction-stage-bypassed-on-rejection.md) compounds the issue

## Fix Approach

1. Rename `records_failed` → `records_filtered` in output metadata and Langfuse tags
2. Separate "intentionally filtered" (Negative results) from "validation failed" (malformed fields) in reporting
3. Consider storing Negative-result items with a `filtered=true` flag rather than discarding
4. Investigate why the 03:40 run had 49 rejections vs 28 for a similar document

## Files to Modify

| File | Change |
|------|--------|
| `open_notebook/graphs/acm_extraction.py` | Rename `records_failed` → `records_filtered`, separate counts |
| `open_notebook/extractors/pipeline_logger.py` | Add `records_filtered` to stage completion metrics |
