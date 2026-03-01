# Findings — E29-S3 Unified Orchestrator Path

## Date: 2026-03-01 | Agent: Amelia (Dev)

---

## Current Routing (Pre-S3)

**Graph edges** (`acm_extraction.py:2912-2917`):
```python
agent_state.add_conditional_edges(
    "tag_pages",
    lambda s: "orchestrate" if should_use_orchestrator(s) else "prepare",
    {"orchestrate": "orchestrate", "prepare": "prepare"},
)
```

**Decision function** (`orchestrator.py:322-329`):
```python
def should_use_orchestrator(state: dict) -> bool:
    inventory = state.get("building_inventory")
    if not inventory:
        return False
    if not inventory.buildings or inventory.total_buildings == 0:
        return False
    return True
```

**Problem**: Documents without building inventory fall to `prepare_context → extract_records` legacy path. Two code paths must be maintained.

---

## Key Code Points

| Location | What | Impact for S3 |
|----------|------|---------------|
| `acm_extraction.py:63` | `should_use_orchestrator` import | Remove from routing import |
| `acm_extraction.py:2912-2917` | Conditional edge | Replace with `add_edge` |
| `acm_extraction.py:2919-2922` | `prepare` conditional edge | Remove (make unreachable) |
| `acm_extraction.py:2924-2928` | `extract` conditional edge | Remove (make unreachable) |
| `acm_extraction.py:2899-2900` | `add_node("prepare"/"extract")` | KEEP (AC-5: present but unreachable) |
| `orchestrator.py:924` | `inventory: BuildingInventory = state["building_inventory"]` | Crashes if None — must guard |
| `orchestrator.py:936` | `plan_extraction(inventory, ...)` | Requires `BuildingInventory` — must handle synthetic case |

---

## Synthetic Plan Design

Architecture delta Section 2 prescribes:
```python
if not inventory or not inventory.buildings:
    plan = SyntheticExtractionPlan(
        building_name="Whole Document",
        page_start=1,
        page_end=state.get("total_pages", 999),
        source="synthetic_no_inventory"
    )
    buildings_to_process = [plan]
```

**Implementation approach**: Create `SyntheticExtractionPlan` in `acm_schemas.py` as a lightweight Pydantic model. In `orchestrate_extraction()`, detect None/empty inventory, create synthetic plan, convert to `BuildingExtractionPlan`, then run through existing `extract_building()` pipeline unchanged.

**`total_pages` source**: `state.get("page_tags")` → `.total_pages` with fallback to 999.

---

## Docling Injection Compatibility

`extract_building()` already calls `_get_docling_tables(source_id, page_start, page_end)` and `_inject_docling_tables()` for every building. For synthetic whole-doc plans, the page range covers all pages → Docling tables matching any page will be injected. **No changes needed in `extract_building()`**.

---

## LangGraph Node Pruning Risk

LangGraph may or may not include disconnected nodes (no incoming edges) in compiled `graph.nodes`. After removing edges to `prepare` and `extract`, they may disappear from `graph.nodes`.

**Mitigation**: AC-5 says "Functions still exist in codebase; no graph edge routes to them." The AC is about source code presence, not compiled graph. Update tests to check function existence rather than `graph.nodes` membership.

---

## Gate 1 Baseline (for benchmark comparison)

| Document | GT | Extracted | Recall | Precision | Field Acc | Latency |
|----------|----|-----------|--------|-----------|-----------|---------|
| Broadmeadows | 31 | 32 | 77.4% | 75.0% | 70.2% | 141.3s |
| Alexander | 43 | 71 | 69.8% | 42.3% | 55.2% | 211.3s |
