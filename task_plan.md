# E29-R2: Match-Gap Remediation — Task Plan

## Story Context

> As a pipeline developer, I want the LLM inventory compilation to return proper
> `RoomMeta` objects and extraction output to use normalized room/material names,
> so that Gate 2 thresholds are met.

R2 scope only. S3/S4 architecture unchanged. No scope creep into S5/S6.

---

## Tasks

### T1: Fix RoomMeta Typing in LLM Inventory Compilation
- [ ] Add `_coerce_rooms_in_inventory(parsed: dict)` to `building_inventory.py`
  - Convert string rooms → `{"room_id": name, "name": name}`
  - Handle dict rooms (pass through)
  - Handle None/missing rooms (default to empty list)
- [ ] Call `_coerce_rooms_in_inventory(parsed)` before `BuildingInventory.model_validate(parsed)` at line 503
- [ ] Write `test_inventory_coerces_string_rooms` — strings → RoomMeta objects
- [ ] Write `test_inventory_preserves_dict_rooms` — dicts pass through
- [ ] Write `test_inventory_handles_mixed_rooms` — mix of strings and dicts

**AC**: R2-AC1
**Files**: `building_inventory.py`, `tests/test_orchestrator.py`

### T2: Add Building Name Normalization to Benchmark Matching
- [ ] Add `BUILDING_SYNONYMS` map to `e29_benchmark_harness.py`
  - `"old alexandra hospital"` → `["main hospital building", "alexandra hospital"]`
- [ ] Add `_normalize_building(building: str) -> str` function (like `_normalize_product`)
- [ ] Apply `_normalize_building()` in tier 2 composite key construction (both GT and extracted)
- [ ] Write `test_building_name_synonym_matching` — GT "Old Alexandra Hospital" matches extracted "Main Hospital Building"

**AC**: R2-AC3, R2-AC5
**Files**: `e29_benchmark_harness.py`

### T3: Expand Product Synonyms
- [ ] Add missing product synonyms to `PRODUCT_SYNONYMS`:
  - `"heater flue"` → `["heater"]`
  - `"ceiling"` → `["porch ceiling"]`
  - `"floor covering"` → `["floor covering (beneath carpet)"]`
  - `"electrical board"` → `["electrical distribution board"]`
- [ ] Add parenthetical stripping to `_normalize_product()`: `"Floor covering (beneath carpet)"` → `"floor covering"`
- [ ] Write `test_product_synonym_new_entries` for each new synonym

**AC**: R2-AC3
**Files**: `e29_benchmark_harness.py`

### T4: Normalize Room Names in Matching
- [ ] Add `ROOM_SYNONYMS` map:
  - `"exterior"` → `["external"]`
- [ ] Add `_normalize_room(room: str) -> str` function
  - Resolve room synonyms
  - Collapse multiple whitespace to single space
  - Strip trailing/leading dashes with surrounding spaces
- [ ] Apply `_normalize_room()` in tier 2 and tier 3 key construction
- [ ] Write `test_room_name_external_exterior_match`
- [ ] Write `test_room_name_whitespace_normalization`

**AC**: R2-AC2
**Files**: `e29_benchmark_harness.py`

### T5: Run Verification Suite (Pre-Benchmark)
- [ ] `uv run ruff check .` — zero errors
- [ ] `uv run pytest tests/test_orchestrator.py -x` — all pass (incl. new tests)
- [ ] `uv run pytest tests/test_strategy_registry.py -x` — all pass (no changes, regression check)

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
