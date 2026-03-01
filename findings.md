# E29 Gate 2 FAIL Triage — PM Findings

## Gate 2 Evidence Summary (from QA evaluation)

### What PASSED
- **G2.4**: Fallback contract codified and tested — 33/33 registry tests, 61/61 orchestrator tests
- **G2.5**: No-inventory documents use synthetic plan — 4 tests pass, E2E confirmed

### What FAILED
- **G2.1**: Broadmeadows 28/31 (need 31/31) — 90.3% recall, +4 from baseline
- **G2.2**: Alexander 31/43 (need 36/43) — 72.1% recall, +1 from baseline
- **G2.3**: Docling injection NOT TESTABLE — no Docling tables seeded in benchmark DB

### Regression Analysis — NO REGRESSION OBSERVED
| Metric | Gate 1 (baseline) | Gate 2 (unified) | Delta |
|--------|-------------------|------------------|-------|
| Broadmeadows matched | 24/31 (77.4%) | 28/31 (90.3%) | **+4 (+12.9%)** |
| Alexander matched | 30/43 (69.8%) | 31/43 (72.1%) | **+1 (+2.3%)** |

### Root Cause Analysis

1. **Test environment gap (G2.3)**: Docling tables aren't seeded in benchmark DB → F2 fallback fires for all buildings → extraction runs without table data → undercounts.
2. **Code defect (inventory typing)**: LLM inventory compilation returns strings instead of `RoomMeta` objects → falls back to heuristic → loses room-level precision.
3. **Harness fidelity (matching)**: Matching algorithm uses strict field comparison → semantically correct records rejected due to casing, description variants, normalization differences.

### Contract Interpretation

The execution contract G2.1 fail action says: *"STOP — file regression bug, rollback S3 changes"*. This contemplated a regression scenario. Since the unified path **improved** both documents, the rollback action is **inapplicable**. The correct reading: maintain FAIL status (thresholds unmet) but do NOT roll back (no regression to revert).

### Threshold Waiver Assessment

**Recommendation: NO WAIVER until R1/R2 rerun.**
- The gap is addressable with targeted fixes (R1 + R2)
- Granting a waiver would let S5-S8 proceed on unverified quality
- Better to invest in 2 remediation stories than carry quality debt into agent decomposition
- Re-run Gate 2 after R1+R2 — clear pass/fail, no ambiguity
