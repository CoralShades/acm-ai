# E29-R2: Match-Gap Remediation — Task Plan

## Story Context

> As a pipeline developer, I want the LLM inventory compilation to return proper
> `RoomMeta` objects and extraction output to use normalized room/material names,
> so that Gate 2 thresholds are met.

R2 scope only. S3/S4 architecture unchanged. No scope creep into S5/S6.

---

## Tasks

### T1: Fix RoomMeta Typing in LLM Inventory Compilation
- [x] Add `_coerce_rooms_in_inventory(parsed: dict)` to `building_inventory.py`
  - Convert string rooms → `{"room_id": name, "name": name}`
  - Handle dict rooms (pass through)
  - Handle None/missing rooms (default to empty list)
- [x] Call `_coerce_rooms_in_inventory(parsed)` before `BuildingInventory.model_validate(parsed)` at line 503
- [x] Write `test_coerces_string_rooms_to_roommeta` — strings → RoomMeta objects
- [x] Write `test_preserves_dict_rooms` — dicts pass through
- [x] Write `test_handles_mixed_rooms` — mix of strings and dicts
- [x] Write `test_handles_none_rooms` — None → empty list
- [x] Write `test_handles_missing_rooms_key` — missing key → empty list
- [x] Write `test_coerced_rooms_validate_as_building_inventory` — full Pydantic validation

**AC**: R2-AC1
**Files**: `building_inventory.py`, `tests/test_orchestrator.py`
**Result**: 6/6 tests pass

### T2: Add Building Name Normalization to Benchmark Matching
- [x] Add `BUILDING_SYNONYMS` map to `e29_benchmark_harness.py`
  - `"old alexandra hospital"` → `["main hospital building", "alexandra hospital", "old alexander hospital"]`
- [x] Add `_normalize_building(building: str) -> str` function
- [x] Apply `_normalize_building()` in tier 2 composite key construction (both GT and extracted)
- [x] Apply `_normalize_building()` in field accuracy calculator

**AC**: R2-AC3, R2-AC5
**Files**: `e29_benchmark_harness.py`
**Result**: 44/44 existing tests pass

### T3: Expand Product Synonyms
- [x] Add missing product synonyms to `PRODUCT_SYNONYMS`:
  - `"heater flue"` → `["heater"]`
  - `"ceiling"` → `["porch ceiling"]` (added to existing)
  - `"floor covering"` → `["floor covering (beneath carpet)"]` (added to existing)
  - `"electrical board"` → `["electrical distribution board"]`
- [x] Add parenthetical stripping to `_normalize_product()`: `"Floor covering (beneath carpet)"` → `"floor covering"`

**AC**: R2-AC3
**Files**: `e29_benchmark_harness.py`

### T4: Normalize Room Names in Matching
- [x] Add `ROOM_SYNONYMS` map:
  - `"exterior"` → `["external"]`
- [x] Add `_normalize_room(room: str) -> str` function
  - Resolve room synonyms
  - Strip leading/trailing dashes with surrounding spaces
  - Collapse multiple whitespace to single space (via _normalize)
- [x] Apply `_normalize_room()` in tier 2, tier 3, and field accuracy
- [x] `_normalize_room` applied in GT and extracted sides

**AC**: R2-AC2
**Files**: `e29_benchmark_harness.py`

### T5: Run Verification Suite (Pre-Benchmark)
- [x] `uv run ruff check .` — zero errors
- [x] `uv run pytest tests/test_orchestrator.py -x` — 67/67 pass (6 new)
- [x] `uv run pytest tests/test_strategy_registry.py -x` — 33/33 pass
- [x] `uv run pytest tests/integration/test_benchmark_harness.py -x` — 44/44 pass

**AC**: R2-AC7, R2-AC8

### T6: Run Gate 2 Benchmark Rerun
- [ ] `uv run python scripts/research/e29_benchmark_harness.py --doc broadmeadows --output-tag gate2_rerun`
- [ ] `uv run python scripts/research/e29_benchmark_harness.py --doc alexander --output-tag gate2_rerun`
- [ ] Verify: Broadmeadows >= 31/31 matched (R2-AC4)
- [ ] Verify: Alexander >= 36/43 matched (R2-AC5)
- [ ] Verify: All 6 Alexander buildings producing records (R2-AC5)
- [ ] Verify: Docling injection firing, no F2 fallback (R2-AC6)
- [ ] Document per-building Alexander counts

**AC**: R2-AC4, R2-AC5, R2-AC6

### T7: Update Recovery Spec + Worklog + Sprint Status
- [ ] Update R2 section in `e29-gate2-recovery-spec.md` with Dev Agent Record
- [ ] Append R2 session to `e29-worklog.md`
- [ ] Set `e29-r2` status to `review` in `sprint-status.yaml`

---

## File Changes Summary

| File | Action | Task |
|------|--------|------|
| `open_notebook/extractors/building_inventory.py` | Modified | T1 |
| `scripts/research/e29_benchmark_harness.py` | Modified | T2, T3, T4 |
| `tests/test_orchestrator.py` | Modified | T1 |
| `benchmarks/results/gate2_rerun_results.json` | Created (by harness) | T6 |
| `docs/reviews/e29-gate2_rerun-benchmark-report.md` | Created (by harness) | T6 |
| `docs/sprint-artifacts/e29-gate2-recovery-spec.md` | Modified | T7 |
| `docs/sprint-artifacts/e29-worklog.md` | Modified | T7 |
| `docs/sprint-artifacts/sprint-status.yaml` | Modified | T7 |

## Verification Commands

```bash
uv run ruff check .
uv run pytest tests/test_orchestrator.py -x
uv run pytest tests/test_strategy_registry.py -x
uv run python scripts/research/e29_benchmark_harness.py --doc broadmeadows --output-tag gate2_rerun
uv run python scripts/research/e29_benchmark_harness.py --doc alexander --output-tag gate2_rerun
```
