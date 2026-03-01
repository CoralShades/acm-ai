# Gate 2 Validation — Findings

## Date: 2026-03-01 | Evaluator: Quinn (BMAD QA)

---

## Gate 2 Verdict: FAIL (2/5 criteria pass)

### Results Summary

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| G2.1 | Broadmeadows >= 31/31 | **FAIL** (28/31) | 90.3% recall. Improved +4 from Gate 1 (24/31). |
| G2.2 | Alexander >= 36/43 | **FAIL** (31/43) | 72.1% recall. Improved +1 from Gate 1 (30/43). 6/6 buildings producing. |
| G2.3 | Docling injection confirmed | **NOT TESTED** | F2 fallback fired for ALL buildings — no Docling tables in benchmark DB. Unit test passes. |
| G2.4 | Fallback contract tested | **PASS** | 33/33 registry tests + 61/61 orchestrator tests. |
| G2.5 | Synthetic plan tested | **PASS** | 4 synthetic plan tests pass. E2E confirmed for Broadmeadows. |

### Critical Finding: No Regression

The execution contract's fail action for G2.1 is "STOP — file regression bug, rollback S3 changes". However, **there is no regression** — both documents improved from the Gate 1 baseline. The unified path is strictly better than the dual-path baseline.

### Root Causes for Match Shortfall

1. **No Docling tables in benchmark DB** — The benchmark harness does not pre-populate Docling tables. F2 (no_docling_tables) fired for ALL buildings. Extraction ran without table injection.
2. **LLM inventory compilation failing** — Both documents had validation errors (rooms as strings not RoomMeta). Fell back to heuristic inventory.
3. **Matching algorithm strictness** — Some extracted records are semantically correct but don't match due to exact-field comparison (e.g., casing, product description variants).

### OpenRouter Provider Verification

**PASS** — Anthropic hard-locked:
- `OPENROUTER_ALLOWED_PROVIDERS = ["Anthropic"]` at `utils.py:28`
- `allow_fallbacks=False` at `utils.py:70`
- All benchmark LLM calls routed through `openrouter/anthropic/claude-sonnet-4.6`
- `_verify_provider_routing()` called at all LLM sites (6 call sites verified)
- `test_openrouter_provider_routing.py`: 43/43 pass

### Test Suite Status

| Test File | Result |
|-----------|--------|
| `test_strategy_registry.py` | 33/33 pass |
| `test_orchestrator.py` | 61/61 pass |
| `test_openrouter_provider_routing.py` | 43/43 pass |
| `test_benchmark_harness.py` | 30/30 pass |
| Full suite | 1212 pass, 13 fail (pre-existing), 2 xfail |
| `ruff check .` | All checks passed |

### Recommendation

The gate FAILS against stated thresholds, but the no-regression finding means S3 changes should NOT be rolled back. Options for PM:

1. **Lower thresholds** — Accept current numbers as the unified-path baseline, PASS gate, proceed to S5
2. **Defer and investigate** — Keep FAIL, investigate Docling table population in benchmark DB and matching algorithm
3. **Conditional pass** — PASS G2 with a caveat that G3 must meet original thresholds after agent decomposition
