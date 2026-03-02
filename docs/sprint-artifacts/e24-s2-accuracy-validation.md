---
epic: Epic 24
story_id: E24-S2
title: Broadmeadows & Alexander Accuracy Validation
status: archived  # Superseded by E26 Docling Direct API (31/31). See ADR-001 D7.
priority: P0
effort: S (1 SP)
depends_on: E24-S1
---

As a product owner,
I want validated evidence that TableFormer meets accuracy targets on both benchmark PDFs,
So that I can confidently promote the feature flag to default-on.

## Acceptance Criteria

- [x] Run extraction with `DOCLING_TABLE_STRUCTURE=true` on Broadmeadows benchmark PDF
- [ ] ~~Broadmeadows accuracy >= 30/31 records (96.8%)~~ **NOT MET: 17/31 (54.8%) with TableFormer**
- [ ] ~~Run extraction on Alexander District Hospital PDF to confirm no regression~~ **SKIPPED: Broadmeadows regression too severe**
- [x] Alexander accuracy maintains 54/54 records (100%) **(existing records maintained, not re-extracted)**
- [x] Document results in validation report: record count, field accuracy, processing time, memory usage
- [x] Identify any regressions (records correct before but wrong after TableFormer)
- [x] Decision gate documented: If Broadmeadows >= 30/31, proceed to promote flag. If < 28/31, investigate and do NOT promote.
- [ ] ~~Processing time benchmarked and asserted < 60s for Broadmeadows PDF~~ **N/A: not comparable (different pipelines)**

## Technical Notes

### Validation Process

1. **Baseline**: Capture current extraction results with `DOCLING_TABLE_STRUCTURE=false`
2. **TableFormer**: Run same extraction with `DOCLING_TABLE_STRUCTURE=true`
3. **Compare**: Record-by-record diff against ground truth CSV
4. **Report**: Write results to `docs/reviews/e24-validation-results.md`

### Files to Create/Modify

| File | Change |
|------|--------|
| `docs/reviews/e24-validation-results.md` | New validation report |
| `tests/test_e2e_extraction.py` | Add/update TableFormer-enabled test case |

### Ground Truth References

- Broadmeadows: 31 records (28 currently captured, 3 missing are Not Sampled/No Access edge cases)
- Alexander: 54 records (all currently captured)
- CSV ground truth files in `docs/samplePDF/`

### Key Metrics Captured

| Metric | Baseline (no TF) | With TableFormer | Target | Status |
|--------|-------------------|------------------|--------|--------|
| Broadmeadows records | 28/31 (E23) | **17/31** | >= 30/31 | REGRESSION |
| Alexander records | 54/54 | 54/54 (maintained) | 54/54 | OK |
| Broadmeadows time | ~222s (E2E test) | ~90.3s (worker) | < 300s | N/A |
| "As Per" rows | 9/9 | **0/9** | 9/9 | REGRESSION |
| "Not Sampled" rows | 3/6 | **0/6** | >= 5/6 | REGRESSION |

### Decision Gate

| Result | Action |
|--------|--------|
| Broadmeadows >= 30/31, Alexander 54/54 | Promote flag to `true` default |
| Broadmeadows 28-29/31 | Investigate; consider prompt tuning |
| Broadmeadows < 28/31 | Rollback; do NOT promote |
| Alexander < 54/54 | Investigate regression; do NOT promote |

## Dependencies

- E24-S1 must be complete (TableFormer activation)

## References

- Technical Design Section 9: `docs/architecture/tableformer-technical-design.md`
- Prior validation: `docs/reviews/e23-validation-results.md`
- E20-S6 investigation: `docs/reviews/e20-s6-validation-results.md`

## Dev Notes

### Validation Outcome: DO NOT PROMOTE

TableFormer (Docling v2.75.0) **degraded** Broadmeadows extraction from 28/31 to 17/31.
The `DOCLING_TABLE_STRUCTURE` flag remains at default `false`.

**Root cause**: Docling fragments table rows into individual cell values on separate
lines, losing row-level coherence. "Same as" references and "Not Sampled" rows become
isolated lines without context, making LLM extraction impossible for those record types.

**Additional discovery**: Installing `content-core[docling]` causes the "auto" engine
to prefer Docling even when `DOCLING_TABLE_STRUCTURE=false`. The auto engine selection
changed behavior just by having Docling installed. This means the docling dependency
should be carefully managed.

**Post-validation state**: Broadmeadows source text restored to PyMuPDF output (34,387 chars).
29 records re-extracted with PyMuPDF text (baseline-equivalent). Alexander 54/54 untouched.

See full report: `docs/reviews/e24-validation-results.md`
