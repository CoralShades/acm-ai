# E26-S4 Validation Results — Accuracy Decision Gate

**Date**: 2026-02-27
**Model**: anthropic/claude-sonnet-4 (via OpenRouter)
**Flag**: `DOCLING_DIRECT_TABLE_EXTRACTION=true`
**Pipeline**: PyMuPDF (full_text) + Docling Direct API (DataFrames in context)
**Script**: `scripts/research/e26_s4_accuracy_validation.py`

## Summary

Two validation runs were performed:

| Run | Docling Injected? | Result | Notes |
|-----|-------------------|--------|-------|
| Run 1 (pre-fix) | NO | 28/31 (90.3%) | S3 gap: orchestrator skipped, injection never fired |
| Run 2 (post-fix) | YES (8 tables) | 28/31 (90.3%) | Tables injected but LLM still missed same 3 records |

**Finding**: Docling table injection is confirmed working (8 tables into LLM context)
but does not improve extraction accuracy for this document. Same 3 records missing
as E23 baseline.

## Broadmeadows Results

| Category | E23 Baseline | E25 DataFrames Only | E26 Full Pipeline | Target |
|----------|-------------|--------------------|--------------------|--------|
| Total | 28/31 (90.3%) | 29/31 (93.5%) | **28/31 (90.3%)** | >= 30/31 |
| NATA-sampled | 16/16 | 16/16 | **16/16** | 16/16 |
| "As Per" (Same as) | 9/9 | 9/9 | **9/9** | 9/9 |
| "Not Sampled" | 3/6 | 4/6 | **3/6** | >= 5/6 |
| Record #9 (Battery Charger) | Missing | Found (DataFrame) | **Missing (LLM)** | Found |
| Record #30 (Lift Foyer) | Missing | Missing (page 8) | **Missing** | Stretch |
| Record #31 (Disabled Toilet) | Missing | Missing (page 8) | **Missing** | Stretch |

## Alexander Results

| Metric | E23 Baseline | E26 | Target |
|--------|-------------|-----|--------|
| Total | 54/54 | N/A (no test) | 54/54 |

**Note**: Alexander regression check could not be performed — no ground truth CSV
or Python E2E test exists. Only a Playwright placeholder (`test.skip`) in
`tests/e2e/acm-extraction.spec.ts`. The BAR xlsm exists but needs ground truth
extraction. This is non-blocking since the decision is INVESTIGATE (not PROMOTE).

## Extraction Details

- Duration: 216.6s (vs E23 baseline 222.9s — comparable)
- Docling tables injected: 8 (all 3 register tables + 5 metadata tables)
- Raw records extracted: 31 (before dedup)
- After dedup: 28 (3 duplicates merged)
- LLM fallback used: Yes (structured output failed → fallback JSON parser)

## S3 Architecture Gap — Fixed During Validation

**Bug found**: The Docling table injection code (`_inject_docling_tables`) was only
in the orchestrator path (`orchestrator.py:_extract_single_building`). Single-building
documents like Broadmeadows where `building_inventory.buildings == 0` skip the
orchestrator entirely, bypassing Docling injection.

**Fix applied**: Added Docling table injection to `prepare_context()` in
`acm_extraction.py:1086-1103` — the non-orchestrator path. This ensures Docling
tables are injected regardless of whether the orchestrator is used.

**Verification**: Run 2 confirmed injection fired ("injected 8 Docling tables"
in pipeline log).

## Missing Records Analysis

### Record #9 — Switch Room / Battery Charger / Fuse cartridge

**Status**: Present in Docling DataFrame (Table 2, Row 9, page 5) but LLM still missed it.

**Root cause**: The LLM extracts one record for "Switch Room / Fuse cartridge" (the
Switchboard record, GT #8) but does not distinguish the Battery Charger (GT #9) as a
separate record. Both have:
- Room: Switch Room
- Product: Fuse cartridge
- Sample: Not Sampled
- Result: Assumed Positive

The only differentiator is `location` (Switchboard vs Automatic Battery Charger). The
Docling table data provides this distinction, but the LLM prompt does not emphasize
that multiple items in the same room with the same product should each be extracted
as separate records.

**Fix candidates**:
1. Prompt engineering: Add explicit instruction to extract each TABLE ROW as a
   separate record, even if room/product match
2. Post-processing: Direct DataFrame-to-record mapping (bypass LLM for structured data)
3. Dedup key refinement: Include `location` in dedup key (currently uses
   `room_id`, `product`, `sample_no`, `material_description_hash`)

### Records #30, #31 — Page 8 (Lift Foyer, Disabled Toilet)

**Status**: Not in any Docling table. Page 8 has only 2-3 continuation rows from the
register, below Docling's TableFormer detection threshold.

**Root cause**: These records appear ONLY in PyMuPDF page 8 text as free-text entries
with "No access" notes. The LLM receives this text but doesn't extract them — they
lack the standard tabular structure the extraction prompt expects.

**Fix candidates**:
1. Prompt engineering: Add "No Access" / "Not Sampled" extraction instructions
   targeting page 8 content
2. Regex fallback: Post-LLM regex scan for "no access" entries in PyMuPDF text
3. Docling configuration: Lower TableFormer threshold for small table fragments

## Decision

### Decision Gate Result: INVESTIGATE

| Condition | Threshold | Actual | Action |
|-----------|----------|--------|--------|
| Broadmeadows >= 30/31 | 96.8% | 90.3% | ~~PROMOTE~~ |
| **Broadmeadows 28-29/31** | **90-93%** | **90.3%** | **INVESTIGATE, keep false** |
| Broadmeadows < 28/31 | < 90% | | ~~ROLLBACK~~ |
| Alexander = 54/54 | 100% | N/A | Not tested |

### Recommendation

**Keep flag at `false` (default) and investigate further.** The Docling tables are
correctly stored and injected, but the LLM extraction doesn't benefit from them
for this document. The gap is in the LLM's ability to:

1. Extract multiple records from the same room with the same product (Record #9)
2. Extract "No Access" records from unstructured page 8 text (Records #30, #31)

### Next Steps

1. **Prompt engineering** (highest impact, lowest effort):
   - Add explicit "each table row = one record" instruction
   - Add "No Access" / page 8 targeting in extraction prompt
   - Re-run validation to measure improvement

2. **Direct DataFrame mapping** (medium effort, high impact for Record #9):
   - For records with NATA sample numbers or clear row structure, extract directly
     from Docling DataFrames without LLM
   - Use LLM only for ambiguous/free-text records

3. **Alexander ground truth** (prerequisite for promotion):
   - Extract 54 records from `Clutch_Alexandra_District_BAR.xlsm`
   - Create `docs/samplePDF/Clutch_Alexandra.csv`
   - Create Python E2E test `tests/test_alexander_e2e.py`

4. **Dedup refinement**:
   - Include `location` field in dedup key to prevent Battery Charger / Switchboard
     merge

## Artifacts

| File | Description |
|------|-------------|
| `scripts/research/e26_s4_accuracy_validation.py` | Validation script |
| `research-output/e26-s4/validation_results.json` | Run 2 JSON results |
| `docs/reviews/e26-s4-validation-results.md` | This report |
| `open_notebook/graphs/acm_extraction.py` | S3 gap fix (prepare_context injection) |
