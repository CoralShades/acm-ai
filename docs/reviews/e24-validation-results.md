# E24 Validation Results - TableFormer Accuracy Validation

**Date**: 2026-02-27
**Epic**: E24 - TableFormer Table Structure Recognition
**Story**: E24-S2 (#S2) - Broadmeadows & Alexander Accuracy Validation
**Depends on**: E24-S1 (Activate TableFormer in Source Processing) - Completed

## Scope

Validate whether enabling Docling's TableFormer model (`DOCLING_TABLE_STRUCTURE=true`)
improves ACM extraction accuracy on the Broadmeadows and Alexander benchmark PDFs.

## Environment

- **Worker**: `uv run run_worker.py --import-modules commands`
- **Docling version**: 2.75.0 (freshly installed for this validation)
- **TableFormer mode**: `accurate` (via `DOCLING_TABLE_MODE=accurate`)
- **Extraction model**: `anthropic/claude-sonnet-4` via OpenRouter
- **SurrealDB**: Local Docker, ws://127.0.0.1:8000

## Validation Results

### Summary Table

| Metric | E23 Baseline (no TF) | E24 (TableFormer) | Target | Status |
|--------|---------------------|-------------------|--------|--------|
| Broadmeadows records | 28/31 (90.3%) | **17/31 (54.8%)** | >= 30/31 | REGRESSION |
| Alexander records | 54/54 (100%) | 54/54 (100%) [1] | 54/54 | Maintained |
| Processing time (Broadmeadows) | ~222s (E2E test) | ~90.3s (worker pipeline) | < 300s | N/A [2] |
| "As Per" rows captured | 9/9 | 0/9 | 9/9 | REGRESSION |
| "Not Sampled" rows captured | 3/6 | 0/6 | >= 5/6 | REGRESSION |

**[1]** Alexander was NOT re-processed or re-extracted with TableFormer. The existing 54/54
records from prior extraction runs are maintained. Re-processing was skipped to avoid
unnecessary API cost given the Broadmeadows regression result.

**[2]** Processing times are not directly comparable. The E23 baseline (222s) was measured
via the E2E test (`test_broadmeadows_e2e.py`) which uses PyMuPDF text extraction.
The E24 result (90.3s) was from the worker pipeline using Docling+TableFormer markdown.

### Broadmeadows Records (17/31)

All 17 extracted records are NATA-sampled records with explicit sample numbers:

| # | Room | Product | Sample No | Result |
|---|------|---------|-----------|--------|
| 1 | Main Foyer | Floor Coverings | 34511-039-001 | Negative |
| 2 | Front Desk Area | Floor Coverings | 34511-039-002 | Negative |
| 3 | Soft Interview Room 2 | Floor Coverings | 34511-039-003 | Negative |
| 4 | Watchouts Kitchen | Floor Coverings | 34511-039-004 | Negative |
| 5 | Ceiling Space | Mastic / Flange joints | 34511-039-005 | Positive |
| 6 | Comms Area | Floor Coverings | 34511-039-006 | Negative |
| 7 | Fan Room | Mastic / Flange joints | 34511-039-007 | Negative |
| 8 | Fan Room | Internal lining | 34511-039-008 | Negative |
| 9 | Male Locker Room | Floor Coverings | 34511-039-009 | Positive |
| 10 | Male Locker Room | Floor Coverings | 34511-039-010 | Negative |
| 11 | Fan Room | Mastic / Flange joints | 34511-039-011 | Positive |
| 12 | Boiler Room | Gasket | 34511-039-012 | Positive |
| 13 | Boiler Room | Gasket | 34511-039-013 | Negative |
| 14 | Boiler Room | Mastic / Flange joints | 34511-039-014 | Positive |
| 15 | Roof - East End | Mastic / Flange joints | 34511-039-015 | Negative |
| 16 | Roof - East End Fan Room | External cladding | 34511-039-016 | Negative |
| 17 | Property Storage | Floor Coverings | 34511-039-017 | Negative |

### Missing Records (14)

| Category | Count | Details |
|----------|-------|---------|
| "As Per" reference rows | 0/9 | All 9 "Same as 34511-039-XXX" rows missing |
| "Not Sampled" rows | 0/6 | All 6 "Not Sampled" assumed-positive rows missing |

These records exist in the Docling+TableFormer markdown but are fragmented across
individual lines without row-level context (see Root Cause Analysis).

## Root Cause Analysis

### Why TableFormer Reduced Accuracy

The Docling+TableFormer output fundamentally changed the text structure in a way that
**degrades** LLM extraction quality for this document type:

1. **Table cell fragmentation**: TableFormer decomposes table rows into individual cell
   values on separate lines. For example, a single register row like:
   ```
   Main Foyer | Floor Coverings | 34511-039-001 | Negative | Non-friable
   ```
   Becomes fragmented as:
   ```
   Main Foyer

   Floor Coverings

   34511-039-

   001

   Negative

   Non-friable
   ```

2. **Lost row coherence**: The "As Per" (Same as) reference rows lose their association
   with room/product context. "Same as" appears as an isolated line without the room name
   or product it refers to.

3. **Column-major vs row-major ordering**: Some table sections appear to be read in
   column-major order (all values from one column, then the next) rather than row-major
   order (all values in one row together). This makes it impossible for the LLM to
   reconstruct which values belong to the same record.

4. **Page detection**: The extraction pipeline detected only 3 pages in the Docling output
   (vs ~30 pages in the original PyMuPDF output). Docling's page markers are different
   from the `--- Page N ---` format the pipeline expects.

### Text Comparison

| Property | PyMuPDF (auto) | Docling+TableFormer |
|----------|---------------|---------------------|
| Full text length | 33,611 chars | 39,309 chars |
| Total lines | ~1,800 | 2,948 |
| Pipe-delimited table lines | 0 | 8 (cover letter only) |
| Page markers detected | ~30 | 3 |
| Table structure | Inline text, row-coherent | Fragmented cells |

### Key Insight

The Broadmeadows register PDF uses complex multi-column tables with:
- Merged cells spanning multiple rows
- "Same as" references linking to other sample numbers
- "Not Sampled" / "No Access" inline annotations

PyMuPDF's simple text extraction preserves the **reading order** of these elements,
maintaining row-level coherence. Docling's TableFormer, while correctly identifying
cell boundaries, produces output that **fragments** the row context needed for
downstream LLM extraction.

## Decision Gate

| Condition | Result | Action |
|-----------|--------|--------|
| Broadmeadows >= 30/31, Alexander 54/54 | NOT MET | - |
| Broadmeadows 28-29/31 | NOT MET | - |
| **Broadmeadows < 28/31** | **17/31** | **Keep flag OFF, investigate** |
| Alexander < 54/54 | NOT TESTED (skipped) | - |

### Decision: **DO NOT PROMOTE** TableFormer flag

The `DOCLING_TABLE_STRUCTURE` environment variable remains at its default value of `false`.
The E24-S1 feature flag implementation is correct and functional, but the Docling+TableFormer
markdown output format is incompatible with the current extraction pipeline's expectations.

## Recommendations for Future Investigation

1. **Docling markdown format adapter**: Create a post-processing step that reconstructs
   row-level coherence from Docling's fragmented cell output before feeding to the LLM.

2. **Page marker normalization**: Add support for Docling's page marker format in the
   extraction pipeline's page detection system.

3. **Hybrid approach**: Use PyMuPDF for initial text extraction (current pipeline) and
   Docling+TableFormer only for targeted table structure analysis (e.g., identifying cell
   boundaries for specific hard-to-parse tables).

4. **Prompt tuning**: Adjust extraction prompts to handle fragmented table input, explicitly
   instructing the LLM to reconstruct row context from column-major cell sequences.

5. **Output format configuration**: Investigate whether Docling's markdown output can be
   configured to preserve row-level ordering (e.g., `output_format="markdown_row_major"`
   or similar options in content-core).

6. **Docling dependency management**: Installing `content-core[docling]` causes the
   "auto" engine to prefer Docling even when `DOCLING_TABLE_STRUCTURE=false`. Consider
   making Docling an opt-in extra that is not installed by default, or explicitly set
   `document_engine="pymupdf"` when the TableFormer flag is off.

## Post-Validation Restoration

After validation, the following restoration steps were performed:

1. **Source text restored**: Broadmeadows source (`source:z2a59rp36ur25znpaavr`)
   `full_text` restored to PyMuPDF output (34,387 chars with `--- Page N ---` markers).
2. **ACM records restored**: 17 TableFormer-extracted records deleted. Fresh extraction
   with PyMuPDF text produced 29/31 records (baseline-equivalent).
3. **Alexander untouched**: 54/54 records maintained (was never re-extracted).
4. **Environment restored**: `.env` has no `DOCLING_TABLE_STRUCTURE` or `DOCLING_TABLE_MODE` variables.

## Artifacts

- E23 baseline: `docs/reviews/e23-validation-results.md`
- S1 implementation: `docs/sprint-artifacts/e24-s1-activate-tableformer.md`
- Feature flag code: `open_notebook/graphs/source.py` (lines 58-78)
