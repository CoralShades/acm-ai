# Findings: E25-S3 Architecture Decision

## E25-S2 Comparison Results (Primary Evidence)

Source: `docs/reviews/e25-table-extraction-comparison.md`

### Raw Metrics
| Metric | PyMuPDF (Baseline) | Docling Direct API |
|--------|-------------------|-------------------|
| Extraction time | 0.09s | 22.41s |
| Tables detected | 0 (text only) | 8 (3 register, 5 other) |
| Register table rows | N/A | 30 (10 per page on pp.5-7) |
| Row coherence | Yes (reading order) | **Yes** (row-major DataFrames) |
| "Same as" rows | Yes (in text) | **Yes (9/9)** |
| "Not Sampled" rows | Yes (3/6 in E23) | **Yes (4/6)** |
| "No Access" rows | Yes (page 8) | **No (page 8 not detected)** |

### Ground Truth Cross-Reference
| Category | Ground Truth | PyMuPDF+LLM (E23) | Docling DataFrames (E25) |
|----------|-------------|-------------------|--------------------------|
| Total records | 31 | 28/31 (90.3%) | **29/31 (93.5%)** |
| NATA-sampled | 16 | 16/16 (100%) | **16/16 (100%)** |
| "As Per" (Same as) | 9 | 9/9 (100%) | **9/9 (100%)** |
| "Not Sampled" | 6 | 3/6 (50%) | **4/6 (67%)** |
| No Access / Unknown | 2 | 0/2 (0%) | **0/2 (0%)** |

### Data Quality Issues Identified
1. Split sample numbers: `34511-039- 001` → fixable with regex
2. Compound column headers: vary per table, fixable via positional mapping
3. Merged cell artifacts: row 3 Table 2 (Filing Cabinet) concatenated
4. "Same as" vs "As Per" semantic equivalence
5. "Asbestos " prefix on hazard status
6. **Page 8 gap**: 2-3 rows below TableFormer detection threshold (HARD problem)

### Extra Discovery
Ceiling Space / 34511-039-005 found in DataFrames but absent from ground truth CSV.
Ground truth has 31 records, PDF has at least 32.

## E24 Failure Analysis

Source: `docs/reviews/e24-validation-results.md`

**Root cause**: content-core's markdown serializer destroyed row coherence.
- TableFormer correctly identified cell boundaries
- content-core serialized cells as individual lines (column-major)
- "Same as" rows lost association with room/product context
- Result: 17/31 (54.8%) — regression from 28/31

**Key insight**: The problem was NOT TableFormer, it was content-core's serialization layer.
E25 bypasses content-core entirely by using `table.export_to_dataframe(doc=doc)`.

## E23 Baseline

Source: `docs/reviews/e23-validation-results.md`

- 28/31 (90.3%) via PyMuPDF text + LLM extraction
- 3 missing: Switch Room Battery Charger (#9), Lift Foyer Internal Lining (#30), Disabled Toilet (#31)
- All 3 are "Not Sampled" assumed-positive without NATA sample numbers
- #9 is now found in Docling DataFrames → recoverable
- #30, #31 are on page 8 → only in PyMuPDF text

## Existing Codebase Analysis

### source_commands.py
- Clean: MinerU code already removed
- process_source_command() invokes source_graph → content_process → save_source
- Integration point: add Docling extraction AFTER source_graph completes (parallel path)

### source.py
- Already has DOCLING_TABLE_STRUCTURE flag (E24, controls content-core's serialization)
- content_process() → extract_content() → save_source()
- source.full_text set from content_state.content
- **E25 approach does NOT modify this path** — PyMuPDF/content-core continues unchanged

### orchestrator.py
- extract_building() takes building content + plan + state
- _llm_extract_building() renders prompt with building_content and input_format
- No MinerU references — clean
- **Integration point**: inject Docling table data into building_content or state

### acm_extraction.py
- prepare_context() is legacy (non-orchestrator) path
- Reads source.full_text, applies normalize_docling_text, preprocesses, chunks
- No MinerU/acm_table_section references — clean after E24-S3

## Schema Assessment

### Migration 18 (acm_table_section) — Already Exists
| Field | Type | Status |
|-------|------|--------|
| source_id | record<source> | EXISTS — link to source |
| page_start | int | EXISTS — from table.prov |
| page_end | int | EXISTS — from table.prov |
| raw_html | option<string> | EXISTS — from table.export_to_html() |
| raw_text | option<string> | EXISTS — from df.to_markdown() |
| building_name | option<string> | EXISTS — optional building inference |
| table_type | option<string> | EXISTS — use "docling_direct_api" |
| created | datetime | EXISTS — auto timestamp |
| updated | option<datetime> | EXISTS |

### New Fields Needed
| Field | Type | Purpose |
|-------|------|---------|
| structured_json | option<string> | DataFrame as JSON for programmatic access |
| extraction_method | option<string> | "docling_direct_api" vs future methods |
| column_mapping | option<string> | JSON column → BAR field mapping |

### Indexes — Sufficient
- section_source: index on source_id (query by source)
- section_pages: index on page_start, page_end (query by page range)

## Feature Flag Design

**CRITICAL**: Must be SEPARATE from E24's DOCLING_TABLE_STRUCTURE flag.

| Flag | Controls | Status |
|------|----------|--------|
| DOCLING_TABLE_STRUCTURE | content-core's markdown serialization (E24) | Exists, default false |
| DOCLING_DIRECT_TABLE_EXTRACTION | Docling Direct API parallel path (E25/E26) | **NEW**, default false |

## Projected Impact (Hybrid Approach A)

| Metric | Current (E23) | Projected (E26) |
|--------|--------------|-----------------|
| Broadmeadows | 28/31 (90.3%) | 30-31/31 (96.8-100%) |
| "As Per" rows | 9/9 | 9/9 |
| "Not Sampled" rows | 3/6 | 5-6/6 |
| Processing time | ~222s (LLM) | ~244s (LLM + 22s Docling) |
| No Access records | 0/2 | 1-2/2 (via PyMuPDF page 8 + improved prompt) |
