# E23 Validation Results - 2026-02-26

## Scope
- Epic: E23 - MinerU structured table extraction integration.
- Story under validation: E23-S4 (#74).
- Target: Broadmeadows extraction accuracy >= 28/31 (90%).

## Validation Commands Run
- `uv run ruff check .` -> passed.
- `cd frontend && npm run build` -> passed.
- `uv run pytest tests/ -x` -> stopped at `tests/test_broadmeadows_e2e.py::test_broadmeadows_all_records_extracted`.

## Broadmeadows Result (Current Run)
- Test file: `tests/test_broadmeadows_e2e.py`.
- Ground truth: `docs/samplePDF/Clutch_Broadmeadows.csv` (31 expected rows).
- Runtime result: extraction failed before record comparison.
- Failure mode: OpenRouter HTTP 402 (insufficient credits / max token budget mismatch).
- Effective extracted record count in this run: 0 (pipeline failed in extraction stage).

## Comparison vs E23 Goal
- Required: >= 28/31 matched rows.
- Achieved in this environment: not measurable due provider credit failure.
- Status: target not met in this validation pass.

## Gap Notes
- This is an environment/runtime blocker (provider credits), not a deterministic parser assertion failure.
- Because extraction aborted, we cannot yet measure:
  - improvement of "As Per" row capture,
  - improvement of "Not Sampled" row capture,
  - net delta from the prior 17/31 baseline.

## Recommended Next Steps
1. Re-run `uv run pytest tests/test_broadmeadows_e2e.py -m integration -v -s` with sufficient provider credits (or alternate funded provider key).
2. Capture matched/missing record breakdown and explicitly count "As Per" and "Not Sampled" rows.
3. Update this file with final measured accuracy and close #74 only after >= 28/31 is verified, or document concrete residual misses if still below target.
