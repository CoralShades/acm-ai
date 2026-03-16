# CORRECT Stage Bypassed When rejected > 0 but with_issues = 0

> **Discovered**: 2026-03-12 (extraction log audit + LangSmith trace analysis)
> **Source**: C_Broadmead.pdf / CF_Broadmead.pdf — CORRECT stage never triggered despite high rejection count
> **Priority**: P0
> **Status**: Open

## Problem

The CORRECT stage gate checks `with_issues > 0` to decide whether correction is needed. But records can be rejected by the validator without having any `data_issues` flags — for example, missing required fields cause outright rejection rather than a flaggable warning. When `rejected=49, with_issues=0`, the CORRECT stage is never triggered, and 49 records are silently discarded with no correction attempt.

## Evidence

- `acm-extraction.log` 03:40:11: `[VALIDATE] COMPLETED in 0.0s | 8 accepted, 49 rejected | accepted=8 | rejected=49 | with_issues=0`
- Next line: `[STORE] STARTED | Deduplicating and saving 8 records...` — CORRECT was skipped entirely
- Same pattern at 09:07:31: `28 accepted, 28 rejected | with_issues=0` — no CORRECT stage
- Contrast with test run at 01:42: `67 accepted, 18 rejected | with_issues=52` — CORRECT DID trigger (58 LLM corrections)
- LangSmith trace `eed83b6e`: `should_correct` node routed to `deduplicate` (bypassed correction) in 0.003s

## Impact

- 86% of records (49/57) discarded from one run with zero correction attempt
- 50% of records (28/56) discarded from another run
- CORRECT stage is the safety net — bypassing it means no recovery from extraction errors
- Systematic data loss on documents where the LLM produces records missing required fields

## Fix Approach

1. In `should_correct` routing logic, change gate from `with_issues > 0` to `rejected > 0 OR with_issues > 0`
2. Alternatively, ensure rejected records have their rejection reason added to `data_issues` so `with_issues` is populated
3. Add explicit logging: `CORRECT skipped: {rejected} rejected, {with_issues} with_issues`

## Files to Modify

| File | Change |
|------|--------|
| `open_notebook/graphs/acm_extraction.py` | Fix `should_correct` routing condition |
| `open_notebook/extractors/` | Ensure rejected records populate `data_issues` with rejection reason |
