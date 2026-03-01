# E29-S3: Unified Orchestrator Path — Task Plan

## Pre-Implementation
- [x] T0: Read + understand current routing in `acm_extraction.py:2912-2917` and `orchestrator.py:915-1020`

## Implementation Tasks (execute in order)

### T1: Create SyntheticExtractionPlan dataclass
- **File**: `open_notebook/extractors/acm_schemas.py`
- **What**: Add `SyntheticExtractionPlan` dataclass with `building_name`, `page_start`, `page_end`, `source` fields
- **Note**: Architecture delta (section 2) specifies exact shape: `SyntheticExtractionPlan(building_name="Whole Document", page_start=1, page_end=total_pages, source="synthetic_no_inventory")`
- **AC**: AC-3
- [ ] Implement
- [ ] Verify import

### T2: Implement synthetic plan logic in `orchestrate_extraction()`
- **File**: `open_notebook/extractors/orchestrator.py`
- **What**:
  - T2.1: When `building_inventory` is None/empty → create synthetic whole-doc `BuildingExtractionPlan`
  - T2.2: Synthetic plan uses `page_start=1, page_end=total_pages` (from state or fallback 999)
  - T2.3: Ensure `_inject_docling_tables()` works for synthetic plans (already called in `extract_building`)
  - T2.4: `orchestrate_extraction` must not crash when `state["building_inventory"]` is None — currently line 924 does `inventory: BuildingInventory = state["building_inventory"]` with no guard
- **AC**: AC-3, AC-4
- [ ] Implement
- [ ] Verify no crash on None inventory

### T3: Replace conditional edge with unconditional edge
- **File**: `open_notebook/graphs/acm_extraction.py`
- **What**:
  - T3.1: Replace lines 2912-2917 `add_conditional_edges("tag_pages", ...)` with `add_edge("tag_pages", "orchestrate")`
  - T3.2: Remove edges from `prepare` and `extract` nodes (lines 2919-2928). Leave `add_node` calls in place (AC-5).
  - T3.3: Remove `should_use_orchestrator` from import at line 63 (no longer needed in routing)
  - T3.4: Keep the `should_use_orchestrator` function in `orchestrator.py` (still importable, just unused in graph routing)
- **AC**: AC-1, AC-2, AC-5
- [ ] Implement
- [ ] Verify graph compiles

### T4: Update orchestrator tests
- **File**: `tests/test_orchestrator.py`
- **What**:
  - Add `TestSyntheticPlan`: test that `orchestrate_extraction` creates synthetic plan when `building_inventory` is None
  - Add test: synthetic plan when inventory has empty buildings list
  - Add test: synthetic plan page range = (1, total_pages)
  - Add test: Docling table injection fires for synthetic plan
  - Keep existing `TestShouldUseOrchestrator` tests (function still exists)
- **AC**: AC-3, AC-4
- [ ] Implement
- [ ] All pass

### T5: Update extraction graph tests
- **File**: `tests/test_acm_ai_extraction.py`
- **What**:
  - Update `TestGraphWiring` to reflect unconditional edge (not conditional)
  - Update `TestBackwardCompatibility` — legacy functions present in source, nodes may/may not be in compiled graph
  - Add test: no-inventory doc routes through orchestrator
- **AC**: AC-1, AC-2, AC-5
- [ ] Implement
- [ ] All pass

### T6: Run benchmark — Broadmeadows 31/31
- **Command**: `uv run python scripts/research/e29_benchmark_harness.py --doc broadmeadows`
- **AC**: AC-6
- [ ] Run + capture results

### T7: Run benchmark — Alexander >=36/43
- **Command**: `uv run python scripts/research/e29_benchmark_harness.py --doc alexander`
- **AC**: AC-7
- [ ] Run + capture results

### T8: Lint + full test suite
- **Commands**:
  - `uv run ruff check .`
  - `uv run pytest tests/test_orchestrator.py -x`
  - `uv run pytest tests/test_acm_ai_extraction.py -x`
  - `uv run pytest tests/ -x` (full suite)
- [ ] All pass

## Post-Implementation
- [ ] Update story status: `drafted` → `in-progress` → `review`
- [ ] Fill Post-Dev Notes in `e29-s3-unified-orchestrator-path.md`
- [ ] Append session to `e29-worklog.md`
- [ ] Produce routing diff summary + AC-by-AC evidence
