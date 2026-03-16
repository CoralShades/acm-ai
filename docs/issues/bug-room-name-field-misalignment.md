# ACM extraction puts material descriptions in room_name field instead of room names

> **GitHub Issue**: #100
> **Discovered**: 2026-03-05 (E36-S4 benchmark)
> **Finding**: F013
> **Priority**: CONCERN
> **Status**: Open

## Problem

ACM extraction consistently places material/product descriptions in the `room_name` field instead of actual room names. This causes ground truth matching to fail and produces semantically incorrect records.

## Evidence

All 6 Ollama models produced the same field misalignment on Alexander District Hospital PDF (43 ground truth records, 33-42 extracted):

| Field | Extracted Value | Ground Truth | Match? |
|-------|----------------|-------------|--------|
| building_name | "Mortuary Buildings" | "Mortuary Buildings" | ✓ |
| room_name | "Infill Panels - Flat Cement Sheeting" | "Shower Room" | ✗ |
| product | "Infill panels below windows" | "Infill panels" | ~ |
| room_name | "Window Frames" | "Exterior" | ✗ |
| room_name | "Ceiling - Flat Cement Sheeting" | "Mortuary Room" | ✗ |
| room_name | "Fire Door - Fire Door Core" | "Boiler Room" | ✗ |
| room_name | "Shower Cubicle - Flat Cement Sheet" | "Shower Room" | ✗ |

**Pattern**: The extraction prompt interprets material-specific location descriptions as room names. The actual room name (from the PDF's "Location" column) is lost.

**Result**: 0% record recall on Alexander PDF across all 6 models despite extracting the right number of records.

## Root Cause

The Alexander PDF has a table structure with these columns:
```
Building | Room/Area | Location | Product/Material | Sample No | Result | Friable
```

The "Room/Area" column contains actual room names (e.g., "Shower Room", "Boiler Room"), while the "Location" column contains specific locations within that room (e.g., "Above Door", "Cubicle - Behind Ceramic Tile"). The "Product/Material" column has the ACM type.

The extraction prompt maps:
- "Location" → `room_name` (WRONG — this should be `location_detail`)
- "Room/Area" → gets lost or merged into room_name
- "Product/Material" → `product` (partially correct)

## Impact

- **Ground truth matching**: 0% recall on Alexander PDF (0/43 records matched)
- **Data quality**: Records have semantically wrong room_name values
- **Downstream**: Room-based grouping/filtering/reporting produces meaningless results
- **Scope**: Likely affects ALL PDFs with similar table structure, not just Alexander

## Fix

### 1. Update extraction prompt

Clearly define the field semantics in the ACM extraction prompt:

```
room_name: The name of the physical room, area, or location zone
  (e.g., "Shower Room", "Boiler Room", "Corridor", "Exterior", "Kitchen")
  Do NOT put material or product descriptions here.

product: The ACM material or product type
  (e.g., "Floor Covering", "Infill Panels", "Ceiling", "Window Frame")

location_detail: The specific location within the room where the material is found
  (e.g., "Above Door", "Under Sink", "Behind Ceramic Tile", "Beneath Shower Tray")
  This is the sub-location within the room, NOT the room name itself.
```

### 2. Add field validation

If `room_name` contains known material keywords (from the SF picklist `Item_Name__c` with 294 values), flag it for review:

```python
MATERIAL_KEYWORDS = {"cement", "sheeting", "covering", "panel", "tile", "door", "frame", "gasket"}

def validate_room_name(room_name: str) -> bool:
    words = set(room_name.lower().split())
    if words & MATERIAL_KEYWORDS:
        return False  # Likely a material, not a room
    return True
```

### 3. Consider location_detail field

The Alexander PDF has 3-level location data:
1. Building (e.g., "Mortuary Buildings")
2. Room (e.g., "Shower Room")
3. Specific location (e.g., "Cubicle - Behind Ceramic Tile")

The current schema only has `building_name` and `room_name`. Consider adding `location_detail` to capture the third level.

## Key Files

- [`open_notebook/graphs/acm_extraction.py`](../../open_notebook/graphs/acm_extraction.py) — extraction prompt and record parsing
- [`prompts/`](../../prompts/) — Jinja2 prompt templates for ACM extraction
- [`docs/samplePDF/Alexander_GroundTruth.csv`](../../docs/samplePDF/Alexander_GroundTruth.csv) — Alexander ground truth
- [`tests/e2e/fixtures/samps/broadmeadows-expected-results.json`](../../tests/e2e/fixtures/samps/broadmeadows-expected-results.json) — Broadmeadows ground truth
- [`open_notebook/domain/acm.py`](../../open_notebook/domain/acm.py) — ACMRecord domain model

## Related

- GitHub Issue: [#100](https://github.com/CoralShades/acm-ai/issues/100)
- Finding: F013 in [`docs/sprint-artifacts/e36/findings.md`](../sprint-artifacts/e36/findings.md)
- Evidence: [`docs/sprint-artifacts/e36/benchmark-results/summary.md`](../sprint-artifacts/e36/benchmark-results/summary.md) — Alexander Matching Limitation section
- Benchmark raw data: [`docs/sprint-artifacts/e36/benchmark-results/raw_results.json`](../sprint-artifacts/e36/benchmark-results/raw_results.json)
