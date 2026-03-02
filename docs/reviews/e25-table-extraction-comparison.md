# E25 Table Extraction Research Spike Results

**Date**: 2026-02-27
**PDF**: Broadmeadows Police Station — `Clutch_Broadmeadows.pdf` (19 pages)
**Ground Truth**: 31 records (from `Clutch_Broadmeadows.csv`)
**GPU**: NVIDIA RTX 4090 (24GB VRAM), CUDA 12.6, torch 2.10.0+cu126
**MinerU**: Skipped (2-way comparison: PyMuPDF vs Docling Direct API)
**Script**: `scripts/research/e25_table_comparison.py`

## Method Comparison

| Metric | PyMuPDF (Baseline) | Docling Direct API | Docling Markdown (Approach C) |
|--------|-------------------|-------------------|------------------------------|
| Extraction time | 0.09s | 22.41s | (same run as Direct API) |
| Output type | Plain text + page markers | DataFrames + HTML | Markdown text |
| Output size | 34,369 chars / 1,658 lines | 74,056 chars / 410 lines | (same as Docling) |
| Tables detected | 0 (text only) | 8 (3 register, 5 other) | N/A (inline tables) |
| Register table rows | N/A | 30 (10 per page on pp.5-7) | 85 table lines |
| Row coherence | Yes (reading order) | **Yes** (row-major DataFrames) | Yes (pipe-delimited) |
| "Same as" rows present | Yes (in text) | **Yes (9/9)** | Yes (9 occurrences) |
| "Not Sampled" rows present | Yes (3/6 in E23) | **Yes (4/6)** | No (0 occurrences) |
| "No Access" rows present | Yes (on page 8) | **No (page 8 not detected)** | No (0 occurrences) |
| Page provenance | Yes (`--- Page N ---`) | Yes (`table.prov[].page_no`) | No (0 page markers) |
| Column headers → BAR fields | N/A (no structure) | Partial (needs normalization) | N/A |
| Merged cell handling | N/A | Yes (with artifacts) | N/A |
| NATA sample numbers clean | Yes | After regex normalization | After regex normalization |

## Ground Truth Cross-Reference

| Category | Ground Truth | PyMuPDF+LLM (E23) | Docling+TF/content-core (E24) | **Docling DataFrames (E25)** |
|----------|-------------|-------------------|-------------------------------|------------------------------|
| Total records | 31 | 28/31 (90.3%) | 17/31 (54.8%) | **29/31 (93.5%)** |
| NATA-sampled | 16 | 16/16 (100%) | 16/16 (100%) | **16/16 (100%)** |
| "As Per" (Same as) | 9 | 9/9 (100%) | 0/9 (0%) | **9/9 (100%)** |
| "Not Sampled" | 6 | 3/6 (50%) | 0/6 (0%) | **4/6 (67%)** |
| No Access / Unknown | (subset) | 0/2 (0%) | 0/2 (0%) | **0/2 (0%)** |

## The 3 Missing E23 Records

| Record | In PyMuPDF Text? | In Docling DataFrame? | Details |
|--------|-----------------|----------------------|---------|
| Switch Room / Automatic Battery Charger / Fuse cartridge (GT#9) | Yes (page 5) | **YES** (T2/R8) | Row: "Switch Room / Automatic battery charger / Fuses / Asbestos Assumed positive". Previously missed by LLM — now directly extractable from DataFrame. |
| Lift Foyer / Lift / Internal lining (GT#30) | Yes (page 8) | **NO** | Present in PyMuPDF text on page 8, but Docling detected NO table on page 8. Register overflows from page 7 to 8 with only 2-3 continuation rows — below TableFormer detection threshold. |
| Main Foyer / Room Adjacent Disabled Toilet / Unknown (GT#31) | Yes (page 8) | **NO** | "disabled toilet" and "no access" appear ONLY in PyMuPDF page 8 text. Completely absent from all Docling output (DataFrames AND markdown). |

## Extra Row Discovery

Docling found **Ceiling Space / 34511-039-005** (Table 2, Row 9, page 5) — a valid ACM register entry in the PDF that is **NOT present in the ground truth CSV**. This record contains:
- Room: Ceiling space throughout
- Feature: Ductwork
- Item: Flange mastic (brown)
- Hazard: Asbestos Positive
- Sample: 34511-039-005
- Friability: Non-friable

The ground truth CSV has 31 records but the PDF register has at least 32. This discrepancy should be verified with the original surveyor data.

## Docling DataFrame Quality — Register Tables

### Column Headers (per table)

Column headers vary across tables due to multi-level merged headers being parsed differently per page:

| Semantic Field | Table 2 (p.5) | Table 3 (p.6) | Table 4 (p.7) | BAR Field |
|---|---|---|---|---|
| Level/Area | `Area / Level Room& Location` | `Area / Level Room& Location Feature` | `Area / Level Room&` | Internal/External + Level |
| Room | `Area / Level Room& Location_1` | `Area / Level Room& Location Feature_1` | `Location` | Room or Area |
| Feature | `Feature` | `Area / Level Room& Location Feature_2` | `Feature` | Location in Room |
| Item | `Item Description` | `Item Description` | `Item Description` | Specific Item/ACM Name |
| Hazard+Result | `Hazard Type Hazard Status` | `Hazard Type Hazard Status` | `Hazard Type` + `Hazard Status` | Sample Result |
| Sample | `Sample Number` | `Sample Number` | `Sample Number Friability` | NATA Sample number |
| Friability | `Friability` | `Friability` | (merged with Sample) | Friability of material |
| Labelled | `Labelled Y/N` | `Labelled Y/N` | `Labelled Y/N` | Labelled |
| Potential | `Potential` | `Potential` | `Potential` | Disturbance Potential |
| Condition | `Condition` | `Condition` | `Condition` | Condition |
| Risk | `Risk Status` | `Risk Status` | `Risk Status` | (internal) |
| Quantity | `Quantity` | `Quantity` | `Quantity Control Priority` | Quantity |
| Recommendations | `Control Priority Comments &Recommendations` | `Comments &Recommendations` | `Comments &Recommendations` | Hygienist Recommendations |
| Date | `Date of Identification` | `Date of Identification Reinspect Date` | `Date of Identification` | Date of Inspection |

### Sample Rows — Table 2 (Page 5, Ground Floor)

| Area/Level | Room | Feature | Item Description | Hazard Status | Sample Number | Friability | Labelled |
|---|---|---|---|---|---|---|---|
| Ground floor | Main foyer | Floor | Vinyl sheet (cream) | Asbestos Negative | 34511-039- 001 | - | - |
| Ground floor | Front desk area | Floor | Vinyl sheet (grey) | Asbestos Negative | 34511-039- 002 | - | - |
| Ground floor | (merged cell) | (merged) | (merged) | (merged) | Assumed positive - | Non-friable | Yes |
| Ground floor | Soft interview room No.2 | Skirting board | Vinyl sheet (brown) | Asbestos Negative | 34511-039- 003 | - | - |
| First floor | Switch Room | Automatic battery charger | Fuses | Asbestos Assumed positive | - | Non-friable | Yes |

### Data Quality Issues

1. **Split sample numbers**: ALL sample numbers have embedded space (`34511-039- 001`). Fix: `re.sub(r'(\d+)-\s+(\d+)', r'\1-\2', value)` — 100% fixable.
2. **Compound column headers**: Names vary per table. Fix: Semantic column mapping by position (columns 0-3 always contain Level/Room/Feature/Item regardless of header text).
3. **Merged cell artifacts**: Row 3 of Table 2 (Filing Cabinet) has cell values concatenated into a single string. Fix: Detect rows where column values repeat the same text and apply special parsing.
4. **"Same as" vs "As Per"**: Docling uses "Same as" where ground truth uses "As Per". Semantic equivalence — simple normalization.
5. **Hazard Status combined**: "Asbestos Negative" / "Asbestos Positive" — strip "Asbestos " prefix.
6. **Page 8 gap**: Register continues onto page 8 but Docling detects no table there (only 2-3 rows, below detection threshold). This is the hard problem.

## Key Findings

1. **Row coherence: PRESERVED** — Docling Direct API returns row-major DataFrames where each row contains a complete ACM register entry. This is the critical difference from E24's content-core fragmentation.

2. **"Same as" recovery: 9/9 (100%)** — All "As Per" reference rows are present as complete DataFrame rows with room, feature, and sample reference intact. E24 lost all 9 of these.

3. **"Not Sampled" recovery: 4/6 (67%)** — Improvement over E23's 3/6 (50%). The newly found record #9 (Switch Room / Battery Charger) was always in the PDF text but the LLM missed it. Docling's structured DataFrame makes it directly extractable.

4. **Missing record recovery: 1/3** — Record #9 found. Records #30 and #31 remain on page 8, which Docling's table detection misses entirely. These are "No access" records at the end of the register that overflow to a 4th page.

5. **Column-to-BAR mapping: FEASIBLE** — Despite messy compound header names, column semantics are consistent by position. A column mapper using positional logic (cols 0-3 = location data, col 4 = hazard, col 5 = sample, etc.) can produce BAR-compatible output.

6. **Processing time: 22.41s** — Acceptable for production. Adds ~22s to the existing ~222s LLM extraction pipeline (10% overhead).

7. **Extra record discovery**: Ceiling Space/005 found in DataFrames but absent from ground truth — demonstrates Docling's ability to capture data the ground truth CSV may have missed.

## Recommendation

Based on these results, the recommended approach for E26 is:

- [x] **Approach A: Hybrid PyMuPDF + Docling Direct API** — Best of both worlds
- [ ] Approach C: Pure Docling Direct API — Missing page markers and page 8 content

### Why Approach A Over C

| Criterion | PyMuPDF Alone | Docling Alone | Hybrid (A) |
|---|---|---|---|
| Page markers | Yes | No | Yes (from PyMuPDF) |
| Page 8 content | Yes | No | Yes (from PyMuPDF) |
| Structured tables | No | Yes | Yes (from Docling) |
| Row coherence | Reading-order | DataFrame rows | Both |
| Register score | 28/31 (with LLM) | 29/31 (DataFrames only) | **Projected 30-31/31** |

PyMuPDF gives proven page markers + reading-order text (including page 8 content). Docling Direct API gives structured DataFrames with row-coherent table data. Together they cover all edge cases:

1. **PyMuPDF**: Provides `source.full_text` with page markers (unchanged production path)
2. **Docling DataFrames**: Provide structured table data that supplements the LLM context
3. **Page 8 gap**: PyMuPDF captures the 2 "No access" records that Docling misses

### Integration Design (High-Level)

```
PDF
├── PyMuPDF → source.full_text (unchanged — proven 28/31 path)
└── Docling Direct API → DataFrames per table
    ├── df.to_markdown() → inject into LLM context as supplementary table data
    ├── Store in acm_table_section (structured_json field)
    ├── Column mapping → potential direct BAR field extraction (no LLM needed)
    └── Page provenance → table.prov[].page_no
```

### Post-Processing Pipeline for DataFrames

```python
# Required normalizations for production use:
1. re.sub(r'(\d+)-\s+(\d+)', r'\1-\2', value)  # Fix split sample numbers
2. Column position mapping (0-3 = location, 4 = hazard, 5 = sample)
3. "Same as" → "As Per" normalization
4. "Asbestos " prefix stripping from hazard status
5. Detect merged-cell rows (all columns identical) → special parsing
```

### Estimated Impact

| Metric | Current (E23) | Projected (E26 with Approach A) |
|--------|--------------|-------------------------------|
| Broadmeadows | 28/31 (90.3%) | 30-31/31 (96.8-100%) |
| "As Per" rows | 9/9 | 9/9 |
| "Not Sampled" rows | 3/6 | 5-6/6 |
| Processing time | 222s (LLM) | 222s + 22s (Docling) = ~244s |
| No Access records | 0/2 | 1-2/2 (via PyMuPDF page 8 + improved LLM prompt) |

### Path to 31/31

1. **Records 1-29**: Directly extractable from Docling DataFrames (no LLM needed for structured fields)
2. **Record #9**: Now found in DataFrames (was missed by LLM in E23)
3. **Records #30, #31**: Present in PyMuPDF page 8 text. Options:
   a. Improved LLM prompt targeting "No access" / "Not Sampled" entries specifically
   b. Docling with lower table detection threshold (if configurable)
   c. PyMuPDF page 8 text parsing with targeted regex for continuation rows

## Artifacts

| File | Description |
|---|---|
| `scripts/research/e25_table_comparison.py` | Comparison script |
| `research-output/e25/pymupdf/full_text.txt` | PyMuPDF full text extraction |
| `research-output/e25/pymupdf/summary.json` | PyMuPDF extraction metadata |
| `research-output/e25/docling_direct_api/table_N.csv` | Per-table CSV exports (N=0-7) |
| `research-output/e25/docling_direct_api/table_N.md` | Per-table markdown exports |
| `research-output/e25/docling_direct_api/table_N.html` | Per-table HTML exports |
| `research-output/e25/docling_direct_api/table_N_analysis.json` | Per-table analysis metadata |
| `research-output/e25/docling_direct_api/markdown_full.md` | Full Docling markdown export |
| `research-output/e25/cross_reference.json` | Ground truth cross-reference |
| `research-output/e25/comparison_summary.json` | Overall comparison summary |
| `docs/reviews/e25-table-extraction-comparison.md` | This report |
