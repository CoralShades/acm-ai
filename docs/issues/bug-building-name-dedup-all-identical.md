# Building Name Dedup Failure — All Buildings Named Identically (N9)

> **Discovered**: 2026-03-12 (Bug Fix 11 live extraction verification)
> **Source**: worker-debug.log 20:04, LangSmith trace `eed83b6e`
> **Priority**: P2
> **Status**: Open
> **Blocks**: Building sidebar usability; building-level filtering and grouping

## Problem

When extracting from documents with multiple buildings, all buildings are assigned the same name (typically the site name). The dedup/naming logic does not differentiate buildings — they all get the generic site name instead of building-specific names.

LangSmith trace analysis (trace `eed83b6e`, L3 finding) also reveals:
- Building category is hallucinated: `building_category="Educational and training facilities"` for a Police Station
- The `extract_building` node returns correct address/consultant but wrong category

## Evidence

- `worker-debug.log` 20:04: All 3 buildings named identically (exact name not logged but dedup reports no differentiation)
- LangSmith trace `eed83b6e`: `extract_building` returned `building_category="Educational and training facilities"` for Broadmeadows Police Station

## Impact

- Building sidebar shows 3 identical entries — users can't distinguish them
- Building-level filtering/grouping broken
- Building category hallucination pollutes metadata

## Fix Approach

1. Use building address, floor, or wing to differentiate building names when site name is the same
2. Add building category enum constraint to extraction prompt (valid categories only)
3. Cross-validate building category against building type from inventory

## Files to Modify

| File | Change |
|------|--------|
| `open_notebook/graphs/acm_extraction.py` | Add building name differentiation logic |
| `prompts/acm/` | Add constrained enum for building category |
