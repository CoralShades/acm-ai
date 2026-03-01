# E29-S4: Capability Registry + Fallback Contract — Task Plan

## Pre-Implementation
- [x] T0: Read all context (story spec, arch delta, execution contract, orchestrator.py, acm_schemas.py, acm_extraction.py, test_orchestrator.py)

## Implementation Tasks (execute in order)

### T1: Create `strategy_registry.py` with FallbackId enum and routing rules
- **File**: `open_notebook/extractors/strategy_registry.py` (NEW)
- **What**:
  - T1.1: `FallbackId(str, Enum)` — F1 through F8 with detection, behavior, telemetry_tag
  - T1.2: `FallbackContract` dataclass — `id`, `detection`, `behavior`, `severity`, `telemetry_tag`, `retry_eligible`
  - T1.3: `FALLBACK_MATRIX: dict[FallbackId, FallbackContract]` — static lookup table for all 8 fallbacks
  - T1.4: `RetryContract` dataclass — `max_retries=3`, `backoff_seconds=5`, `retry_eligible` flag
  - T1.5: `select_strategy(state) -> ExtractionStrategy` — centralized routing (replaces scattered conditionals)
  - T1.6: `detect_fallback(state, fallback_id) -> bool` — check if a fallback condition applies
  - T1.7: `emit_fallback_telemetry(fallback_id, building_name, reason)` — structured log with `fallback.*` tag
  - T1.8: `check_retry_budget(attempt, contract) -> bool` — returns False when attempt >= max_retries
- **AC**: AC-1 (single file), AC-5 (retry contract), AC-6 (telemetry tags)
- [ ] Implement
- [ ] Verify import

### T2: Add strategy metadata fields to `acm_schemas.py`
- **File**: `open_notebook/extractors/acm_schemas.py`
- **What**:
  - T2.1: Add `fallback_activated: list[str]` field to `OrchestratorStats` (in orchestrator.py, or via a new field on ACMExtractionOutput — check which fits)
  - T2.2: Add `strategy_metadata: Optional[dict]` to `BuildingExtractionStats` for per-building fallback tracking
- **AC**: AC-6
- [ ] Implement

### T3: Integrate registry into orchestrator
- **File**: `open_notebook/extractors/orchestrator.py`
- **What**:
  - T3.1: Import `strategy_registry` functions
  - T3.2: In `orchestrate_extraction()`: call `emit_fallback_telemetry(FallbackId.F1, ...)` when synthetic plan created
  - T3.3: In `extract_building()`: call `emit_fallback_telemetry(FallbackId.F2, ...)` when no Docling tables found
  - T3.4: In `_llm_extract_building()`: emit F3 on JSON parse failure, F4 on zero records, F7 on LLM error
  - T3.5: Wire retry contract check into existing `should_correct()` max_attempts logic (currently `max_correction_attempts=2`, needs to be 3 per AC-5)
  - T3.6: Collect `fallback_activated` tags into orchestrator stats output
- **AC**: AC-2, AC-3, AC-4, AC-5, AC-6
- [ ] Implement

### T4: Write registry tests — `tests/test_strategy_registry.py`
- **File**: `tests/test_strategy_registry.py` (NEW)
- **What**:
  - T4.1: `test_no_inventory_fallback` — F1: state with no/empty inventory → synthetic plan, telemetry tag emitted (AC-2)
  - T4.2: `test_no_tables_fallback` — F2: empty Docling tables → text-only, telemetry tag (AC-3)
  - T4.3: `test_json_parse_fallback` — F3: JSONDecodeError → resilient parser activation, telemetry tag
  - T4.4: `test_empty_extraction_fallback` — F4: zero records → log warning, continue
  - T4.5: `test_validation_failure_fallback` — F5: ValidationError → correction retry, telemetry tag
  - T4.6: `test_correction_exhausted_fallback` — F6: attempt >= 3 → accept partials, telemetry tag
  - T4.7: `test_llm_failure_fallback` — F7: 5xx/timeout → retry once, then skip (AC-4)
  - T4.8: `test_docling_failure_fallback` — F8: Docling exception → text-only fallback
  - T4.9: `test_retry_cap_enforcement` — 4th retry rejected (AC-5)
  - T4.10: `test_telemetry_tags_emitted` — structured log contains `fallback.*` tags (AC-6)
  - T4.11: `test_select_strategy` — routing rules return correct ExtractionStrategy
  - T4.12: `test_fallback_matrix_completeness` — all 8 FallbackIds have contracts
- **AC**: AC-2, AC-3, AC-4, AC-5, AC-6
- [ ] Implement
- [ ] All pass

### T5: Update existing orchestrator tests
- **File**: `tests/test_orchestrator.py`
- **What**:
  - T5.1: Verify `orchestrate_extraction()` emits F1 telemetry when no inventory
  - T5.2: Verify `extract_building()` emits F2 telemetry when no Docling tables
  - T5.3: Verify retry contract uses max_retries=3 (not 2)
- **AC**: AC-2, AC-3, AC-5
- [ ] Implement
- [ ] All pass

### T6: Lint + full test suite
- **Commands**:
  - `uv run ruff check .`
  - `uv run pytest tests/test_strategy_registry.py -x -v`
  - `uv run pytest tests/test_orchestrator.py -x`
  - `uv run pytest tests/ -x`
- [ ] All pass

### T7: Run benchmark — Broadmeadows 31/31
- **Command**: `uv run python scripts/research/e29_benchmark_harness.py --doc broadmeadows`
- **AC**: AC-7
- [ ] Run + capture results

### T8: Run benchmark — Alexander >=36/43
- **Command**: `uv run python scripts/research/e29_benchmark_harness.py --doc alexander`
- **AC**: AC-8
- [ ] Run + capture results

## Post-Implementation
- [ ] Update story status: `drafted` → `in-progress` → `review`
- [ ] Fill Post-Dev Notes in `e29-s4-capability-registry-fallback-contract.md`
- [ ] Append session to `e29-worklog.md`
- [ ] Produce fallback matrix implementation mapping + AC-by-AC evidence + Gate 2 readiness
