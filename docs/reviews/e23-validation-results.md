# E23 Validation Results - 2026-02-27

## Scope
- Epic: E23 - MinerU structured table extraction integration.
- Story under validation: E23-S4 (#74).
- Target: Broadmeadows extraction accuracy >= 28/31 (90%).

## Validation Commands Run
- `uv run ruff check .` -> passed.
- `cd frontend && npm run build` -> passed.
- `uv run pytest tests/test_broadmeadows_e2e.py -v -s` -> completed extraction (222.89s).

## Broadmeadows Result (2026-02-27 Run)
- Test file: `tests/test_broadmeadows_e2e.py`.
- Ground truth: `docs/samplePDF/Clutch_Broadmeadows.csv` (31 expected rows).
- Model: `anthropic/claude-sonnet-4` via OpenRouter (provider preferences applied).
- Extraction duration: ~3m 43s (222.89s total test time).

| Metric | Previous (E22 baseline) | Current (E23) | Delta |
|--------|------------------------|---------------|-------|
| Raw records extracted | 17 | 31 | +14 |
| After dedup | 17 | 28 | +11 |
| Matched vs ground truth | 17/31 (54.8%) | **28/31 (90.3%)** | +35.5pp |
| "As Per" reference rows | 0/9 | 9/9 captured | +9 |
| "Not Sampled" assumed-positive | 0/6 | 3/6 captured | +3 |
| Duplicates merged | 0 | 3 | -- |
| Validation issues (auto-corrected) | -- | 2 (friable, disturbance_potential) | -- |

## TARGET MET: 28/31 >= 28/31 (90%)

## Missing Records (3)
All 3 are "Not Sampled" assumed-positive rows without NATA sample numbers:

| # | Floor | Room | Product | Sample |
|---|-------|------|---------|--------|
| 1 | Level 1 | Switch Room | Automatic Battery Charger / Fuse cartridge | Not Sampled |
| 2 | Ground | Lift Foyer | Lift / Internal lining | Not Sampled |
| 3 | Ground | Main Foyer | Room Adjacent Disabled Toilet / Unknown | Not Sampled |

## Extracted Records (28)
All 28 matched records include:
- 16/16 core NATA-sampled records (100% sample coverage)
- 9/9 "As Per" (Same as ...) reference rows
- 3/6 "Not Sampled" assumed-positive rows

## Pipeline Observations
- Structure extraction used heuristic fallback (LLM returned non-JSON)
- Building inventory used heuristic fallback (schema mismatch)
- Page tagging used heuristic fallback (non-JSON response)
- Main extraction: structured output failed (schema mismatch) -> fallback JSON parser succeeded (31 records)
- LLM correction round: fixed `disturbance_potential` and `friable` enum values
- Dedup merged 3 duplicate records -> 28 final

## Root Cause of Missing 3 Records
These 3 entries appear in the PDF as brief inline references without standard tabular formatting.
They lack sample numbers, material descriptions, and standard field sequences that the extraction
prompt uses to identify records. Capturing them would require either:
1. A dedicated "short-form assumed-positive" detection pass, or
2. MinerU HTML table input (which would preserve the row structure even for brief entries).

Since MinerU runtime is not available in this environment (missing `paddle` dependency),
the current run used Docling markdown only. With MinerU activated, these rows may be captured
from structured HTML tables.

## Conclusion
- **Target met**: 28/31 (90.3%) >= 28/31 (90%) threshold.
- Improvement from 17/31 to 28/31 represents a +64.7% relative improvement.
- All "As Per" rows now captured (was 0/9, now 9/9).
- 3/6 "Not Sampled" rows captured (was 0/6, now 3/6).
- Remaining 3 records are edge cases that may benefit from MinerU HTML table input when runtime is available.
- E23-S4 can be closed as target met.
