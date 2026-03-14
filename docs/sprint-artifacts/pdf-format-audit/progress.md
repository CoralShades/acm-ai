# Progress: PDF Processing Layer & Format Detection Audit
Date: 2026-03-14

## Steps
- [x] Step 1: PyMuPDF full_text output audit — CRITICAL: no page markers in production
- [x] Step 2: Docling JSON output audit — ALL keys match row_segmenter
- [x] Step 3: Docling HTML output audit — correct, unused in LLM path
- [x] Step 4: Docling Markdown output audit — DataFrame-derived, correct
- [x] Step 5: Docling output cross-check — consistent across all 3 types
- [x] Step 6: mode="json" vs mode="python" usage — CLEAN, no mode="python" remaining
- [x] Step 7: SAMP format detection audit — regex documented, 3 test cases
- [x] Step 8: ARA format detection audit — one-line header gap identified (HIGH)
- [x] Step 9: Generic fallback audit — single-building handling verified
- [x] Step 10: BAR format impact analysis — CONFIRMED secondary, no pipeline branching
- [x] Step 11: Salesforce model alignment — internal_external mapping gap CRITICAL
- [x] Step 12: Broadmeadows ground truth comparison — 1 building correct, 31 records need per-row
- [x] Step 13: Document findings and recommendations — 3 CRITICAL, 4 HIGH, 4 MEDIUM, 5 LOW

## Summary
- 3 parallel subagents completed audit in ~8 minutes
- 16 findings documented with file:line references
- BAR confirmed secondary (no pipeline impact)
- Docling JSON fully aligned with row_segmenter
- mode="json" confirmed everywhere
