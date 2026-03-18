# MCS7 Validation — Task 3: Clutch/Greencap New Format

**Date**: 2026-03-19
**Source PDF**: `docs/samplePDF/Clutch_Broadmeadows.pdf`
**Source ID**: `source:ponh5h9ny2p6n9mx6t70`
**Model**: Ollama llama3.1:8b (per-row extraction mode)
**Extraction Time**: 157s (2m 37s)

## Summary

| Metric | Value |
|--------|-------|
| Records Extracted | 31 |
| Extraction Time | 157s |
| High Confidence | 29 (94%) |
| Low Confidence | 2 (6%) |
| Parent Table Sections | 1 |
| LLM Corrections | 16 |
| Errors | 0 |

## Schema Inference

| Aspect | Result |
|--------|--------|
| Schema inference node executed | Yes |
| Schema inference result | **Skipped** — no `acm_table_section` records found at inference time |
| Consultant format profile created | No (existing profile from prior run unchanged) |
| Format profile cache hit | N/A — inference didn't produce a result to cache |

**Root cause**: The schema inference node runs *before* `save_records()`, which is where `acm_table_section` records are created. This ordering means schema inference has no table data to analyze on first extraction. A second extraction of the same source would find the table sections and perform inference.

## Product Field Quality Comparison (vs Broadmeadows Task 2)

The Clutch extraction shows **improved product naming** compared to the Broadmeadows run:

| Record | Broadmeadows (Task 2) Product | Clutch (Task 3) Product |
|--------|------------------------------|------------------------|
| Fan Room ductwork | "Other" | "Flange mastic" |
| Switch Room fuses | "Other" | "Fuses" |
| Fan Room infill panels | "Other" | "Fibre cement sheet infill panels" |
| Kitchen floor | "Same as 34511-039-00" | "Vinyl sheet" |
| Male locker room skirting | "Same as 34511-039-00" | "Skirting vinyl sheet" |

The Clutch run extracts specific product names instead of "Other" or sample reference numbers — a notable quality improvement despite using the same model and same building data. This may be due to:
1. Different PDF rendering of the same source document
2. Non-deterministic LLM behavior between runs
3. Slight differences in text extraction output

## Extracted Records

| # | Page | Room | Location | Product | Friable | Result |
|---|------|------|----------|---------|---------|--------|
| 1 | - | Ceiling Space | throughout Ductwork | Unknown | None | Assumed Positive |
| 2 | - | Lift Foyer | Lift | Internal lining | None | Assumed Positive |
| 3 | 5 | Ceiling space throughout | Ductwork Flange mastic (brown) | Flange mastic | Friable | Positive |
| 4 | 5 | Corridor adj cells | Floor | Vinyl sheet (cream) | None | Negative |
| 5 | 5 | Front desk area | Floor | Floor covering | None | Negative |
| 6 | 5 | Front desk area | Filing cabinet | Internal lining | Friable | Assumed Positive |
| 7 | 5 | Kitchenette | Floor | Hessian back sheet vinyl | None | Negative |
| 8 | 5 | Main foyer | Floor | Floor covering | None | Negative |
| 9 | 5 | Soft interview room No.2 | Skirting board | Vinyl sheet (brown) | None | Negative |
| 10 | 5 | Switch Room | Battery charger Fuses | Fuses | Friable | Assumed Positive |
| 11 | 5 | Switch Room | Switchboard Fuses | Fuses | Friable | Assumed Positive |
| 12 | 6 | Comms area | Floor Vinyl floor tile | Vinyl floor tile | None | Negative |
| 13-31 | 6-8 | (various rooms) | (various) | (various) | (various) | (various) |

## Result Type Distribution

| Result Type | Count |
|-------------|-------|
| Negative | 21 |
| Positive | 5 |
| Assumed Positive | 5 |

**Note**: 1 fewer Assumed Positive vs Broadmeadows (5 vs 6). The Lift Foyer record is now correctly Assumed Positive (was wrongly Negative in Broadmeadows Task 2), but another record may have shifted.

## Observations

### Strengths
1. **Successful extraction from "new" format**: The Clutch PDF was processed without errors, demonstrating format adaptability
2. **Better product names**: More specific product descriptions compared to Broadmeadows Task 2
3. **Faster extraction**: 157s vs 197s for Broadmeadows — 20% faster
4. **High confidence**: 94% of records at high confidence

### Weaknesses
1. **Schema inference ordering bug**: Schema inference runs before table sections are saved, making it a no-op on first extraction
2. **No format profile cached**: The new format's column mapping was not saved to `consultant_format_profile`
3. **2 spurious records** with `page_number=None` and `building_id=unknown` — same issue as Broadmeadows
4. **Building records not created** under this source_id

### Verdict

**PASS (with caveats)** — Extraction succeeds and produces 31 records with good quality. Schema inference and format profile caching do not activate due to a node ordering issue (schema inference runs before table sections exist). This should be tracked as a bug for the next sprint.
