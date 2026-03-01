# E29-S4 Progress — Capability Registry + Fallback Contract

## Session: 2026-03-01 — Planning Phase

### Status: PLANNING COMPLETE — READY TO IMPLEMENT

### 5-Question Reboot Check
1. **Last completed milestone**: All context files read, findings documented, task plan created
2. **Current active task**: Ready to begin T1 (strategy_registry.py)
3. **Blockers**: None — S3 complete, Gate 1 PASS, S4 dependencies met
4. **Files last modified**: `task_plan.md`, `findings.md`, `progress.md` (planning files only)
5. **Next planned action**: Begin T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8 in order

### Key Decisions
- `strategy_registry.py` is a lookup table with `FallbackId` enum, `FallbackContract` frozen dataclass, and `FALLBACK_MATRIX` dict
- `emit_fallback_telemetry()` uses `loguru.logger.info()` with structured dict — no custom telemetry framework
- Retry cap change: `max_correction_attempts` from 2 → 3 in `should_correct()` (AC-5)
- Minimal `acm_schemas.py` change: add `fallback_tags` to `BuildingExtractionStats`, `fallback_activated` to `OrchestratorStats`
- No routing behavior changes — S4 is purely additive (structured logging + registry)
- Benchmark results should be identical to post-S3 baseline (no extraction logic changes)

### Context Files Read
- `docs/sprint-artifacts/e29-s4-capability-registry-fallback-contract.md` — story spec (8 ACs, 8 tasks)
- `V3/epic-29-execution-contract.md` — gate contract, story scope
- `docs/architecture/e29-architecture-delta.md` — fallback matrix §3.1, routing contract §2
- `open_notebook/extractors/orchestrator.py` — full file (1051 lines)
- `open_notebook/extractors/acm_schemas.py` — full file (513 lines)
- `open_notebook/graphs/acm_extraction.py` — graph topology (2880-2926), should_correct (2073-2112)
- `tests/test_orchestrator.py` — full file (1168 lines)
- `scripts/research/e29_benchmark_harness.py` — harness structure
- `docs/sprint-artifacts/e29-worklog.md` — S1 entry
- `docs/sprint-artifacts/e29-gate-decisions.md` — Gate 1 PASS, Gate 2 PENDING

### Implementation Plan Summary
1. **T1**: Create `strategy_registry.py` — FallbackId enum (F1-F8), FallbackContract, FALLBACK_MATRIX, RetryContract, emit_fallback_telemetry(), check_retry_budget()
2. **T2**: Add `fallback_tags` to BuildingExtractionStats, `fallback_activated` to OrchestratorStats in orchestrator.py
3. **T3**: Wire telemetry emissions into orchestrator at 6 decision points (F1-F4, F7 in orchestrator; F5-F6 in acm_extraction.py should_correct)
4. **T4**: Write `tests/test_strategy_registry.py` — 12 tests covering F1-F8, retry cap, telemetry, routing, matrix completeness
5. **T5**: Update `tests/test_orchestrator.py` — verify telemetry emission at F1, F2, F4 points
6. **T6**: Lint + full test suite
7. **T7-T8**: Benchmark validation (Broadmeadows 31/31, Alexander >=36/43)
