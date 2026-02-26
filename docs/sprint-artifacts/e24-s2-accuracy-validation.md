---
epic: Epic 24
story_id: E24-S2
title: Broadmeadows & Alexander Accuracy Validation
status: drafted
priority: P0
effort: S (1 SP)
depends_on: E24-S1
---

As a product owner,
I want validated evidence that TableFormer meets accuracy targets on both benchmark PDFs,
So that I can confidently promote the feature flag to default-on.

## Acceptance Criteria

- [ ] Run extraction with `DOCLING_TABLE_STRUCTURE=true` on Broadmeadows benchmark PDF
- [ ] Broadmeadows accuracy >= 30/31 records (96.8%)
- [ ] Run extraction on Alexander District Hospital PDF to confirm no regression
- [ ] Alexander accuracy maintains 54/54 records (100%)
- [ ] Document results in validation report: record count, field accuracy, processing time, memory usage
- [ ] Identify any regressions (records correct before but wrong after TableFormer)
- [ ] Decision gate documented: If Broadmeadows >= 30/31, proceed to promote flag. If < 28/31, investigate and do NOT promote.
- [ ] Processing time benchmarked and asserted < 60s for Broadmeadows PDF

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

### Key Metrics to Capture

| Metric | Baseline (no TF) | With TableFormer | Target |
|--------|-------------------|------------------|--------|
| Broadmeadows records | 28/31 | ? | >= 30/31 |
| Alexander records | 54/54 | ? | 54/54 |
| Broadmeadows time | ~5-10s | ~20-35s | < 60s |
| Peak memory (worker) | ~X GB | ~X+2-4 GB | < 8 GB |

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

<!-- Implementation notes will be added by the dev agent -->
