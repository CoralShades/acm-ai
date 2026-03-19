# Prompt Evaluation Framework — Progress

## Session 1: 2026-03-18 — COMPLETE

### Summary
Built a prompt evaluation framework and used it to systematically improve extraction quality from 64.4% to 74.8% overall accuracy (+10.4pp).

### What Was Done
1. **Ground truth CSVs** — Normalized Broadmeadows (31) and Alexander (43) into `scripts/eval/ground_truth/`
2. **Eval harness** — `scripts/eval/prompt_eval_harness.py` with 3-stage record matching, per-field scoring, synonym resolution, and domain-specific normalizers
3. **Test suite** — 28 tests in `tests/test_prompt_eval.py`, all passing
4. **Pipeline bug fixes**:
   - Product "Other" mapping in orchestrator (if_other_item_name preference)
   - Quantity int→str coercion for GPT-4o-mini compatibility
   - Ollama connectivity check (skip unreachable Ollama, fall through to cloud)
   - OpenAI as 4th priority extraction provider with max_tokens cap
5. **Re-extraction** — Ran live extraction with GPT-4o-mini, evaluated against ground truth
6. **Results documented** in findings.md with per-field comparisons

### Key Metrics
| Metric | v1 (Ollama bulk) | Final (GPT-4o-mini) | Delta |
|--------|------------------|---------------------|-------|
| Overall Accuracy | 64.4% | **74.8%** | **+10.4pp** |
| Friable | 29.6% | **92.6%** | **+63.0pp** |
| Room Name | 44.4% | **74.1%** | **+29.7pp** |
| Product | 22.2% | **59.3%** | **+37.1pp** |
| Location | 44.4% | **63.0%** | **+18.6pp** |

### Files Created
| File | Purpose |
|------|---------|
| `scripts/eval/convert_ground_truth.py` | BAR CSV → normalized format |
| `scripts/eval/prompt_eval_harness.py` | Main evaluation harness |
| `scripts/eval/baseline_results.json` | v1 baseline scores |
| `scripts/eval/baseline_results_v2.json` | v2 (GPT-4o-mini) scores |
| `scripts/eval/baseline_results_final.json` | Final scores |
| `scripts/eval/ground_truth/broadmeadows.csv` | 31 GT records |
| `scripts/eval/ground_truth/alexander.csv` | 43 GT records |
| `scripts/eval/ground_truth/broadmeadows_extracted.json` | Cached extraction output |
| `scripts/eval/ground_truth/alexander_extracted.json` | Cached extraction output |
| `tests/test_prompt_eval.py` | 28 evaluation tests |

### Files Modified
| File | Change |
|------|--------|
| `open_notebook/extractors/orchestrator.py` | Product "Other" mapping fix + quantity coercion |
| `open_notebook/extractors/acm_schemas_v3.py` | Quantity validator |
| `open_notebook/graphs/utils.py` | Ollama connectivity check + OpenAI fallback |

### Reboot Check
1. Last completed milestone: All tasks complete, verification passed
2. Current active task: None — session complete
3. Blockers: None
4. Last modified: prompt_eval_harness.py (synonym expansion)
5. Next planned action: Future session — Alexander re-extraction, taxonomy improvements
