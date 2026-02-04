# Two-stage AI Pipeline: Extract → Interpret (BAR Register)

This design uses the **Alexander BAR.xlsm** as a *register specification* (schema + rules), and treats each incoming PDF as *evidence*.

## Stage 0 — Preflight
1. **Classify PDF type**
   - digital PDF with embedded text vs scanned images
2. **Choose parser**
   - Prefer a document parser that preserves tables/layout (e.g., MinerU-style output into JSON/Markdown tables)
3. **Create page-level artifacts**
   - `pages[].text`
   - `pages[].tables[]` (each table as rows/columns)
   - `pages[].images[]` (optional)

## Stage 1 — EXTRACT (Evidence → Raw fields)
**Goal:** extract *verbatim* values from the PDF, with provenance.

### Output: `raw_extraction.json`
- `document_meta`: client/site/job/date, consultant, etc.
- `items[]`: array of extracted rows from the asbestos register tables
- each field includes:
  - `value`
  - `source.page`
  - `source.table_id`
  - `source.row/col` or bounding box
  - `confidence`

**Rule:** Do **not** normalize wording here (keep the original consultant phrasing).

## Stage 2 — INTERPRET (Raw → BAR-compliant record)
**Goal:** transform raw extraction into the **BAR Register Row Spec**.

### Steps
1. **Field mapping**
   - Map raw columns from the PDF register to BAR fields (Excel headers).
2. **Normalization**
   - Convert synonyms into controlled enums:
     - Sample Result → ['Positive', 'Assumed Positive', 'Negative', 'Assumed Negative']
     - Condition → ['Poor', 'Fair', 'Good', 'Unknown', 'N/A (negative)', 'N/A (assumed negative)']
     - Disturbance Potential → ['High', 'Moderate', 'Low', 'Unknown', 'N/A (negative)', 'N/A (assumed negative)']
     - Friability → ['Non-friable', 'Friable']
     - Yes/No fields → ['YES', 'NO']
3. **Derived rules**
   - If Sample Result is *Negative* or *Assumed Negative*, then columns relating to asbestos-specific control actions may be blank (matches the Instruction guidance).
4. **Consultant wording → Canonical actions**
   - Run regex mapping (see `consultant_wording_rules.json`) over recommendations/comments to produce `normalized_actions[]`.
5. **Validation**
   - Validate each output row against `register_row.schema.json`
   - Enforce required fields (A, B, E-L, N-AH)
6. **Excel writer**
   - Write clean rows into your target output workbook (e.g., Broadmeadows output format or your unified app output).

## Prompt skeletons (drop-in)

### Stage 1 prompt (Extractor)
- Task: “Extract asbestos register rows exactly as written.”
- Output: JSON with provenance and confidence.

### Stage 2 prompt (Interpreter)
- Task: “Convert raw extraction to BAR schema; normalize enums; compute normalized actions.”
- Output: JSON strictly conforming to the schema.

## Files produced by this package
- `register_row.schema.json` — authoritative machine-readable schema
- `register_taxonomy.nonfriable.json` — ACM product taxonomy (Appendix A)
- `register_taxonomy.friable.json` — ACM product taxonomy (Appendix B)
- `consultant_wording_rules.json` — universal vs consultant-specific normalization
- `alexander_instructions.txt` — human-readable rules pulled from Instructions sheet
