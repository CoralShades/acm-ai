# Building-Aware Table Routing Design (F5/F11)

> **Status**: Design only — implementation deferred to future sprint.

## Problem

When buildings share the same page range (e.g., NSW DoE SAMP grid format where all buildings are listed on pages 3-15), `_get_docling_tables()` returns the identical table set for every building. Each building's per-row extraction processes ALL tables from ALL buildings, producing N buildings x M total items = N*M output records.

## Chosen Approach

Process the shared table ONCE, then distribute records to buildings by matching row content (room_id, building_id) to the building inventory.

## Design

### 1. Detect Shared Page Ranges

In `extract_items_node`, before the per-building loop, detect if buildings share page ranges:

```python
page_sets = [(b.page_start, b.page_end) for b in inventory.buildings]
all_same = len(set(page_sets)) == 1 and len(page_sets) > 1
```

### 2. Grid Extraction Mode

If `all_same`, switch to "grid extraction mode":
- Fetch ALL tables once (not per-building)
- Run per-row extraction on ALL rows
- For each extracted record, match to a building using:
  - `room_id` prefix (e.g., "B009-R0001" -> building B009)
  - Building name in record content
  - Building ID in `data_issues` or metadata
- Assign `building_record_id` based on match

### 3. Fallback

If not `all_same`, use existing per-building extraction (unchanged).

## Key Implementation Areas

- `open_notebook/graphs/acm_extraction.py` — `extract_items_node()` — add grid detection + grid extraction path
- `open_notebook/extractors/orchestrator.py` — add `match_record_to_building()` function
- Tests with Aldavilla ground truth (4 records, 10 buildings, 9 with no ACM)

## Estimated Effort

1-2 weeks including testing across all format types.
