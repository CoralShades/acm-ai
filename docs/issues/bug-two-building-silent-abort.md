# Two-Building Extractions Silently Abort After Building 1

> **Discovered**: 2026-03-12 (extraction log audit + LangSmith trace analysis)
> **Source**: Clutch_Broadmead.pdf / Broadmead.pdf — pipeline stops after 1/2 buildings saved
> **Priority**: P1
> **Status**: Open

## Problem

When extraction detects 2 buildings, only building 1 is saved. The pipeline then stops — no EXTRACT, VALIDATE, STORE, or COMPLETE/FAILED banner is logged. The second building is never attempted. This is distinct from the building-ID race condition fixed in Bug Fix 11 (that pre-assigned IDs to avoid unique-index violations). Here, one building saves but the pipeline silently abandons the session.

## Evidence

- `acm-extraction.log` 01:16:57: `[PIPELINE] [ORCHESTRATOR] Building extraction: 2 buildings`
- `acm-extraction.log` 01:17:09: `[PIPELINE] [ORCHESTRATOR] Building extraction: 1/2 saved | buildings_saved=1`
- No subsequent `2/2 saved`, no `[EXTRACT]`, no `[VALIDATE]`, no `[STORE]`, no `EXTRACTION COMPLETE` or `EXTRACTION FAILED` banner
- Same pattern repeated for source `0zt30ynmsactoaf2kx9h` at 01:28:15
- Both sources: `b73el5y25bpcmckk4xa3` (Clutch_Broadmead.pdf) and `0zt30ynmsactoaf2kx9h` (Broadmead.pdf)

## Impact

- Second building lost entirely — no records extracted
- No error logged — silent data loss
- Affects multi-building SAMP documents (majority of real-world documents)

## Fix Approach

1. Investigate `asyncio.gather` error handling in `extract_items_node` for swallowed exceptions
2. Check if building 2's save raises an exception caught by a bare `except` with no re-raise
3. Add explicit logging after each building save attempt with success/failure status
4. Add a final count check: if `buildings_saved < buildings_expected`, log error

## Files to Modify

| File | Change |
|------|--------|
| `open_notebook/graphs/acm_extraction.py` | Investigate building save loop error handling in `extract_items_node` |
