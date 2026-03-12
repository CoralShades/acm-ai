# Row Segmenter Missing `INTERNAL` Sub-header + Partial-Width Span Check

> **Discovered**: 2026-03-11 (Gap analysis vs Broadmeadows ground truth)
> **Source**: Clutch_Broadmeadows.pdf (Internal/External sub-headers mishandled)
> **Priority**: P1
> **Status**: Open

## Problem

### BUG-A: `_LEVEL_REGEX` missing `INTERNAL` keyword

In `open_notebook/extractors/row_segmenter.py:65-68`:

```python
_LEVEL_REGEX = re.compile(
    r"^(LEVEL|GROUND|FIRST|SECOND|THIRD|ROOF|BASEMENT|EXTERNAL|MEZZANINE)\b",
    re.IGNORECASE,
)
```

The Broadmeadows PDF has section sub-headers: `Internal` and `External` separating the register into areas. `EXTERNAL` is in the regex, but `INTERNAL` is not. When `"Internal"` appears as a spanning row:
- It's treated as a note row (Type E2) instead of a level/area marker (Type E3)
- The `internal_external` context is lost for all rows under that header
- Ground truth expects `internal_external: "Internal"` or `"External"` on each record

### BUG-B: Partial-width span check misses sub-headers

In `row_segmenter.py:335`:

```python
if col_span >= num_cols:
```

If a sub-header cell spans 7 of 8 columns (not all columns), it's not recognized as a sub-header. It becomes a regular data row with one cell, producing a spurious ACM record (e.g., a "Ground" record with no meaningful fields).

## Evidence

Ground truth shows 4 sections in Broadmeadows:
1. Internal / Ground (records 1-7, 29-31)
2. Internal / Level 1 (records 8-19)
3. External / Ground (records 20-28)

The segmenter tracks only one `current_level`, losing the Internal/External distinction.

## Impact

- `internal_external` field wrong on extracted records
- `floor_level` may be incorrect when Internal/External + Ground/Level are nested
- Potential dedup key collisions if `area_type` is used in `_generate_dedup_key`
- Not a record-dropping bug, but reduces field accuracy in benchmarks

## Fix Approach

1. Add `INTERNAL` to `_LEVEL_REGEX` pattern
2. Add a separate `_AREA_REGEX` for Internal/External tracking (or expand level tracking to support two dimensions)
3. Change span check to `col_span >= num_cols - 1` (allow off-by-one for merged cells)
4. Propagate `internal_external` context through segmentation

## Files to Modify

| File | Change |
|------|--------|
| `open_notebook/extractors/row_segmenter.py` | Add `INTERNAL` to regex, relax span check, add area tracking |
| `open_notebook/domain/acm_row_schemas.py` | Add `internal_external` field to `ACMItemRow` if not present |
| `open_notebook/domain/acm_row_mappers.py` | Map `internal_external` from row to extraction record |

---

## Status: RESOLVED (2026-03-11)

Fixed in Bug Fix 11 Phase 1 (commit `7eb73f27`):
- `_LEVEL_REGEX` updated to include `INTERNAL` keyword
- Partial-width span check for sub-header detection
