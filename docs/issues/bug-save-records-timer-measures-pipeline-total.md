# save_records Timer Reports Pipeline Total Instead of DB Write Time (N7)

> **Discovered**: 2026-03-12 (Bug Fix 11 live extraction verification)
> **Source**: worker-debug.log 20:37, LangSmith trace `eed83b6e`
> **Priority**: P2
> **Status**: Open
> **Blocks**: Accurate DB write performance measurement

## Problem

The `save_records` log entry reports the total pipeline elapsed time (e.g., 2001s) rather than the actual database write duration (e.g., 0.7s). The timer captures the wrong start point — likely using the pipeline start time rather than the save operation start time.

## Evidence

- `worker-debug.log` 20:37: save_records reports ~2001s duration
- LangSmith trace `eed83b6e`: `save` node actual duration = 0.684s
- The 2001s matches the full pipeline runtime, not the save operation

## Impact

- Misleading performance metrics for DB write operations
- Cannot identify actual save bottlenecks from logs
- Dashboard/monitoring would show inflated save times

## Fix Approach

1. In the save stage, capture `time.monotonic()` at save start, not pipeline start
2. Report delta from save-start to save-end

## Files to Modify

| File | Change |
|------|--------|
| `open_notebook/graphs/acm_extraction.py` | Fix timer scope in `store_results_node` or save stage |
