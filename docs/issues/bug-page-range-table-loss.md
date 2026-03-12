# Page Range Underestimation + Table Merge Overwrite → Records Lost

> **Discovered**: 2026-03-11 (Bug Fix 11 live extraction verification)
> **Source**: Clutch_Broadmeadows.pdf (31 ground truth records, 16 extracted)
> **Priority**: P0
> **Status**: Open
> **Blocks**: Achieving >80% recall on any PDF

## Problem

Two compounding bugs cause tables (and their rows) to be silently excluded from extraction:

### BUG-A: Building `page_end` underestimation excludes tables on later pages

In `open_notebook/extractors/building_inventory.py`, the generic heuristic fallback (added in Bug Fix 11) computes `page_end` from `document_structure.total_pages`. When the LLM underestimates the register span, or when `total_pages` from pre-extraction intelligence is inaccurate, the building's page range is too narrow.

The SQL query in `open_notebook/extractors/orchestrator.py:51-57` then filters tables strictly:

```python
"AND page_start >= $page_start "
"AND page_end <= $page_end "
```

Tables on pages beyond `page_end` are silently excluded. With a single-building document like Broadmeadows, there's no `_apply_boundary_overlap` correction (only fires between consecutive buildings).

### BUG-B: `_merge_provider_tables` overwrites multiple tables per page

In `commands/source_commands.py:276-317`, tables are keyed by page number:

```python
for t in docling_result.tables:
    if t.page > 0:
        docling_by_page[t.page] = t  # Overwrites earlier tables on same page
```

If a PDF page contains 2+ tables (e.g., Internal and External sections), only the last table survives. The Broadmeadows PDF has multi-table pages.

### BUG-C: Silent fallback in page filter masks page_number=0

In `open_notebook/extractors/row_segmenter.py:486-494`:

```python
tables = filtered if filtered else tables  # Silent fallback
```

When page filtering produces 0 matches (because `page_number=0` for unknown-page tables), the code silently uses ALL tables — potentially processing tables from unrelated buildings.

## Evidence

- Bug Fix 11 stored 8 Docling tables, extracted only 16 of 31 ground truth records
- Building B001 page range may not span full document
- No warning or error logged when tables are excluded by page range

## Impact

- **Record loss**: ~10-15 records silently dropped (Broadmeadows: 31→16)
- **Scales with document size**: Larger documents lose more records
- **Affects all document types**: ARA, Division_5, and SAMP formats

## Fix Approach

### BUG-A Fix
1. For single-building documents, set `page_end = total_pages` (no risk of cross-building contamination)
2. Add safety margin: `page_end = min(page_end + 2, total_pages)` for multi-building docs
3. Log a warning when the page range filter excludes tables

### BUG-B Fix
1. Change `docling_by_page` from `dict` to `defaultdict(list)` — store ALL tables per page
2. Update downstream consumers to handle multiple tables per page

### BUG-C Fix
1. Log a warning instead of silent fallback
2. If `page_number=0`, treat as "unknown page" and include in ALL buildings (better to over-include than drop)

## Files to Modify

| File | Change |
|------|--------|
| `open_notebook/extractors/building_inventory.py` | Single-building page_end = total_pages |
| `open_notebook/extractors/orchestrator.py` | Add page range exclusion warning |
| `commands/source_commands.py` | `docling_by_page` → list-based, support multi-table pages |
| `open_notebook/extractors/row_segmenter.py` | Log warning on silent fallback, include page_number=0 tables |

---

## Status: RESOLVED (2026-03-11)

Fixed in Bug Fix 11 Phase 1 (commit `7eb73f27`):
- `_merge_provider_tables` multi-table-per-page overwrite → uses `defaultdict(list)` instead of dict assignment
- Building `page_end` expansion for single-building documents
- Page filter silent fallback + `page_number=0` handling
