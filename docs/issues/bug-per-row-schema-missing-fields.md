# Per-Row Schema Missing `sample_no`, `sample_result`, and Other Critical Fields

> **Discovered**: 2026-03-11 (Gap analysis vs Broadmeadows ground truth)
> **Source**: ACMItemRow schema only has 9 fields, ground truth expects 9+ fields
> **Priority**: P0
> **Status**: Open
> **Blocks**: Benchmark accuracy, field completeness

## Problem

The v3.5 per-row extraction schema (`ACMItemRow` in `open_notebook/domain/acm_row_schemas.py`) captures only 9 fields:

```python
# Current ACMItemRow fields:
room_name, floor_level, item_location, item_name, friability,
acm_classification, acm_sub_classification, condition, disturbance_potential
```

**Missing critical fields** that the ground truth expects:

| Field | Ground Truth | ACMItemRow | Mapper Default |
|-------|-------------|------------|----------------|
| `sample_no` | "34511-039-001" | NOT extracted | `None` |
| `sample_result` | "Positive" / "Negative" / "Assumed Positive" | NOT extracted | `result="Unknown"` |
| `product` / `acm_product` | "Floor covering", "Skirting" | Partially via `item_name` | Mapping unclear |
| `internal_external` | "Internal" / "External" | NOT extracted | `None` |
| `level` | "Ground" / "Level 1" | Via `floor_level` | Mapping exists |

### Hardcoded `result="Unknown"` in mapper

In `open_notebook/domain/acm_row_mappers.py:184`:

```python
result="Unknown",  # Always hardcoded
```

Every extracted record gets `result="Unknown"` regardless of what the PDF says. This directly causes:
- Benchmark field accuracy drops to 0% for `sample_result`
- Primary match key (`sample_no`) always `None` → falls to secondary matching
- Records that could match by sample_no are missed

### `acm_product` field mapping gap

The ground truth `product` field ("Floor covering", "Fuse cartridge", "Flange joints") maps to `acm_product` in `ACMExtractionRecord`. The per-row pipeline extracts `item_name` but doesn't clearly map it to `acm_product`.

## Evidence

From the Bug Fix 11 live extraction (16 records):
- `acm_product`: null on all records
- `room_area`: null on all records
- `result`: "Unknown" on all records (should be Negative/Positive/Assumed Positive)

## Impact

- **Benchmark matching fails**: Primary key `sample_no` is always None
- **Field accuracy**: `sample_result` = 0%, `product` = 0%
- **Data quality**: Records missing essential compliance fields
- **Export unusable**: BAR/SF exports require sample_no and sample_result

## Fix Approach

### Phase 1: Add fields to ACMItemRow schema
```python
class ACMItemRow(BaseModel):
    # Existing 9 fields...
    sample_number: Optional[str] = None       # NEW
    sample_result: Optional[str] = None       # NEW
    acm_product: Optional[str] = None         # NEW (or rename item_name)
    internal_external: Optional[str] = None   # NEW
```

### Phase 2: Update row extraction prompt
Update `prompts/acm/row_extraction.jinja` to instruct LLM to extract sample_number, sample_result, and product.

### Phase 3: Update mapper
Update `map_item_row_to_extraction_record` in `acm_row_mappers.py` to map new fields:
```python
result=row.sample_result or "Unknown",
sample_number=row.sample_number,
acm_product=row.acm_product or row.item_name,
```

### Phase 4: Update Ollama context budget
More fields = more tokens per row. May need to increase `ACM_ROW_EXTRACTION_NUM_CTX` from 2048.

## Files to Modify

| File | Change |
|------|--------|
| `open_notebook/domain/acm_row_schemas.py` | Add `sample_number`, `sample_result`, `acm_product`, `internal_external` |
| `open_notebook/domain/acm_row_mappers.py` | Map new fields, remove `result="Unknown"` hardcode |
| `prompts/acm/row_extraction.jinja` | Add extraction instructions for new fields |
| `open_notebook/extractors/row_extractor.py` | Verify token budget accommodates new fields |
| `tests/test_row_extraction.py` | Update tests for new schema |

---

## Status: RESOLVED (2026-03-11)

Fixed in Bug Fix 11 Phase 1 (commit `7eb73f27`):
- Added `sample_number`, `sample_result`, `acm_product`, `internal_external` to `ACMItemRow`
- Updated row extraction prompt (`prompts/acm/row_extraction.jinja`)
- Updated mapper (`open_notebook/domain/acm_row_mappers.py`) to use new fields
