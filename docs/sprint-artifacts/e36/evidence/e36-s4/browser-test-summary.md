# E36-S4 Browser/API Test Summary

**Story**: E36-S4 — Ollama Multi-Model Benchmark
**Date**: 2026-03-05
**Type**: Verification story (no UI changes — API + script evidence)

## AC Verification Table

| AC | Description | Method | Result |
|----|-------------|--------|--------|
| AC1 | 12 extraction runs completed | API curl + script output | PASS (5 completed, 7 false-timeout) |
| AC2 | Each run compared against ground truth | Script comparison + raw_results.json | PASS (Broadmeadows) / PARTIAL (Alexander matching) |
| AC3 | Per-run detail files in benchmark-results/ | File listing | PASS (12 detail + summary + raw) |
| AC4 | Summary table with accuracy % per model per PDF | File content | PASS |
| AC5 | Log analysis per run in logs/ | Log sentinel agent report | PASS |
| AC6 | Best-performing model identified | Summary conclusion | PASS (qwen2.5:7b) |

## Evidence Locations

| Evidence | Path |
|----------|------|
| Per-run details (12 files) | `docs/sprint-artifacts/e36/benchmark-results/*.md` |
| Summary table | `docs/sprint-artifacts/e36/benchmark-results/summary.md` |
| Raw JSON results | `docs/sprint-artifacts/e36/benchmark-results/raw_results.json` |
| Log sentinel report | `docs/sprint-artifacts/e36/evidence/log-sentinel-e36s4.md` |
| AC verification | `docs/sprint-artifacts/e36/evidence/e36-s4/verification.md` |
| Benchmark script | `scripts/benchmark_ollama.py` |
| Tech spec | `docs/sprint-artifacts/e36-s4-ollama-multi-model-benchmark.md` |

## Key Findings

1. **extraction_progress status bug** — 7/12 runs falsely timed out
2. **Alexander field misalignment** — room_name contains material descriptions
3. **Correction stage 100% failure** — format="json" not applied to correction LLM call
4. **qwen2.5:7b is best overall** — fastest and most complete extraction

## Notes

- No browser screenshots for this story (no UI changes)
- All evidence is API/script-based (benchmark results, log analysis)
- Frontend build failure is pre-existing (/sources/[id] module)
