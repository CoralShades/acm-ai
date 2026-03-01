# Progress — E29-S1: JSON Parser Resilience

## Session: 2026-03-01

### Entry 1 — Research & Planning (DONE)
- Read story spec, execution contract, architecture delta, current `utils.py`
- Identified 5 callers of `parse_json_response` (backward-compat surface)
- Found existing tests in `test_qwen_extraction.py:63-113` (7 tests)
- Bug found: fenced regex uses non-greedy `\{.*?\}` which fails on nested JSON in fences
- Plan: strip fences first → brace-depth scan → multi-block selection → truncation detection
- `TruncationError(ValueError)` subclass for backward-compat

### Entry 2 — Implementation (DONE)
- T1: sprint-status.yaml → in-progress, story status → in-progress
- T2: Added `TruncationError(ValueError)` exception class at utils.py:497
- T3: Rewrote `parse_json_response()` — strip fences → brace-depth scan → multi-block → truncation
- T3: Added `_extract_json_objects()` helper — handles strings with escaped quotes and braces
- T4: Created `tests/test_json_parser.py` — 34 tests across 6 test classes

### Entry 3 — Verification (DONE)
- `ruff check .` — All checks passed
- `pytest tests/test_json_parser.py -x -v` — 34/34 passed (25.34s)
- `pytest tests/test_qwen_extraction.py::TestParseJsonResponse -x -v` — 7/7 passed (5.64s)

### Entry 4 — Documentation & Status (DONE)
- Updated story Post-Dev Notes with implementation summary, test evidence, risks
- Set sprint-status → review
- Created `e29-worklog.md`

### STATUS: COMPLETE — Ready for QA

---

# Progress — E29-S2: Benchmark Harness + Baseline Capture

## Session: 2026-03-01

### Entry 1 — Research & Planning
- Read all context: execution contract, S2 story spec, architecture delta, sprint-status
- Explored extraction pipeline: `extract_acm_from_source()`, `ACMExtractionOutput`, `ACMExtractionRecord`
- Studied existing E2E test pattern in `test_broadmeadows_e2e.py` (mocked DB, real LLM)
- Analyzed ground truth CSVs: Broadmeadows (31 rows, 43-col BAR), Alexander (43 rows, 7-col minimal)
- Identified third doc candidates: 1124 (604KB), 3980 (645KB), 4601 (567KB) — no existing ground truth
- Token tracking: only ad-hoc via `_verify_provider_routing()` — must intercept for harness
- Created task plan with 11 tasks (T1-T11)
- **Next**: T1 (set status), T2 (dir structure), T3-T5 (ground truth), T6 (harness), T7 (tests)

### Reboot Check
1. Last completed milestone: Planning phase
2. Current active task: T1 (set sprint-status to in-progress)
3. Blockers: None for S2 dev. S1 must merge before Gate 1 pass.
4. Files last modified: task_plan.md, findings.md, progress.md
5. Next planned action: T1 → set sprint-status → T2 → create benchmarks/ dir
