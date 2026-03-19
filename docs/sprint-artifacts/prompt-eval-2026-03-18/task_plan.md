# Prompt Evaluation Framework — Task Plan

## Phase 1: Ground Truth & Harness Setup
- [x] 1.1 Verify ground truth CSVs exist
- [x] 1.2 Create normalized ground truth CSVs in `scripts/eval/ground_truth/`
- [x] 1.3 Build `scripts/eval/prompt_eval_harness.py`
- [x] 1.4 Build `tests/test_prompt_eval.py` — 28 tests

## Phase 2: Baseline Current Prompts
- [x] 2.1 Export real extraction data from SurrealDB
- [x] 2.2 Run eval harness — v1: 64.4%, v2: 73.1%, final: 74.8%
- [x] 2.3 Record per-field accuracy matrix in findings.md
- [x] 2.4 Identify lowest-scoring fields

## Phase 3: Pipeline Improvements
- [x] 3.1 Fixed eval normalization: area_type, floor_level, condition
- [x] 3.2 Fixed orchestrator product mapping: if_other_item_name
- [x] 3.3 Fixed quantity coercion for GPT-4o-mini
- [x] 3.4 Added Ollama connectivity check
- [x] 3.5 Added OpenAI as fallback provider
- [x] 3.6 Re-extracted with GPT-4o-mini: friable 29.6%→92.6%, overall 64.4%→74.8%
- [x] 3.7 Expanded product synonym map for better eval matching

## Phase 4: Verification
- [x] 4.1 `uv run ruff check .` — lint clean
- [x] 4.2 `uv run pytest tests/test_prompt_eval.py -v` — 28 tests pass
- [x] 4.3 Document results in findings.md
- [x] 4.4 Re-extracted with GPT-4o-mini and evaluated
- [x] 4.5 Final verification: all tests pass, lint clean
