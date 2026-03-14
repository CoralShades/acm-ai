# Task Plan: Audit PDF Processing Layer — PyMuPDF, Docling Outputs, Format Detection
Date: 2026-03-14
Status: COMPLETE

## Goal
Audit the ACM extraction pipeline's PDF processing layer and format detection system. Verify PyMuPDF output, all three Docling output types (JSON, HTML, Markdown), and format detection templates (SAMP, ARA, generic) are correct and aligned with v3.5 pipeline and Salesforce models. Confirm BAR format is secondary and never impacts pipeline flow.

## Steps
- [x] Step 1: Audit PyMuPDF full_text output — page marker format, reliability for page range slicing
  - FINDING: CRITICAL — no page markers in source.full_text (content_core concatenates without separators)
- [x] Step 2: Audit Docling JSON output — cell structure vs row_segmenter expectations
  - FINDING: ALL keys match — table_cells, num_rows, num_cols, text, row_span, col_span, offsets, column_header
- [x] Step 3: Audit Docling HTML output — quality for LLM consumption in bulk extraction
  - FINDING: Correct merged cell handling, but NOT used in LLM path (display/provenance only)
- [x] Step 4: Audit Docling Markdown output — accuracy for table display and LLM context
  - FINDING: DataFrame-derived (not Docling-native), merged cells expanded — correct for LLM
- [x] Step 5: Cross-check all three Docling output types agree on row/column counts
  - FINDING: Consistent — all derive from same TableData object
- [x] Step 6: Verify `mode="json"` vs `mode="python"` usage across all Docling call sites
  - FINDING: CLEAN — mode="json" at both call sites, zero mode="python" anywhere
- [x] Step 7: Audit SAMP format detection (`_BUILDING_HEADER` regex) against real PDF headers
  - FINDING: Regex correct for B###/D### format, correctly excludes room headers
- [x] Step 8: Audit ARA format detection (`_detect_ara_buildings`) against Greencap/Prensa variants
  - FINDING: HIGH gap — two-line regex misses one-line `Building Name: <name>` format
- [x] Step 9: Audit generic fallback — page range accuracy, single-building handling
  - FINDING: Robust — single-building fix extends page_end to total_pages
- [x] Step 10: Verify BAR format is secondary — trace all DocumentType references
  - FINDING: CONFIRMED — BAR never gates extraction logic. 18+ references traced, all display/vocabulary/audit only
- [x] Step 11: Cross-check format detection against Salesforce models
  - FINDING: CRITICAL — ACMItemRow.internal_external never mapped to ACMExtractionRecord
  - FINDING: CRITICAL — material_description can be None when required (Pydantic error)
  - FINDING: HIGH — building_year type mismatch (int vs str)
- [x] Step 12: Run Broadmeadows ground truth comparison
  - FINDING: 1 building correct. 31 records need per-row extraction (blocked by RC8)
- [x] Step 13: Document all findings with specific file:line references and recommendations
  - FINDING: 3 CRITICAL, 4 HIGH, 4 MEDIUM, 5 LOW documented in findings.md

## Risks (assessed)
- Docling cell structure: VERIFIED — keys match installed version
- SAMP regex: VERIFIED — correct for coded building IDs
- ARA format detection: GAP FOUND — one-line header variant not covered
- BAR in prompt templates: VERIFIED — context-setting only, no conditional logic
