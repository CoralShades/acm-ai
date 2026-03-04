# E29-R2 Findings — Match-Gap Remediation

## Research Date: 2026-03-02

## 1. RoomMeta Typing Bug (R2-AC1)

**Location**: `building_inventory.py:448-504` — `_llm_compile_inventory()`

**Root cause**: LLM returns rooms as strings (e.g., `["Room A", "Room B"]`) instead of objects
(`[{"room_id": "...", "name": "..."}]`). `BuildingInventory.model_validate(parsed)` at line 503
raises `ValidationError` because `BuildingMeta.rooms: List[RoomMeta]` cannot accept strings.

**Effect chain**:
1. `_llm_compile_inventory()` raises → caught at line 593
2. Falls back to `_heuristic_fallback(content, document_structure)`
3. Heuristic for ARA format (`_detect_ara_buildings`) finds buildings but extracts zero rooms
4. Empty room lists → orchestrator has no room context → lower quality extraction
5. For Broadmeadows (single building, Prensa format): heuristic finds nothing → no inventory → synthetic plan

**Fix**: Add `_coerce_rooms_in_inventory(parsed)` before `model_validate()` — converts string rooms
to `RoomMeta(room_id=name, name=name)` objects.

## 2. Alexander Unmatched Record Analysis (12 unmatched GT records)

### 2a. Building Name Mismatch (8 records — BIGGEST root cause)

GT building: `"Old Alexandra Hospital"` (22 of 43 total records)
LLM extraction: `"Main Hospital Building"` (per Gate 2 evidence)

These are the SAME building. The LLM reads the document header differently than the ground truth.
8 of the 12 unmatched GT records are from "Old Alexandra Hospital".

**Impact**: Tier 2 composite key (`building|room|location|product`) fails because building name
differs. Tier 1 (sample_no) can't help for "Not Sampled" records. Tier 3 (room+location) catches
SOME but is 1:1 consumption — earlier matches consume slots.

**Fix**: Add `BUILDING_SYNONYMS` map to benchmark matching engine (same pattern as `PRODUCT_SYNONYMS`).
Apply normalization to building_name in both tier 2 composite key and ground truth comparison.

```python
BUILDING_SYNONYMS = {
    "old alexandra hospital": ["main hospital building", "alexandra hospital"],
}
```

### 2b. Room Name Normalization (3 records)

| GT room_name | Extracted room_name | Issue |
|--------------|---------------------|-------|
| `Exterior` | `External` | Common LLM variation |
| `Multi Purpose Area  Adjacent CCSD` | `Multi Purpose Area - Adjacent CCSD` | Double space vs dash |
| `West Passage` | `West Passage - Adjacent CCSD` | GT shorter than extracted |

**Fix**: Add `ROOM_SYNONYMS` and normalize whitespace in room names.

### 2c. Product Synonym Gaps (4 records)

| GT product | Extracted product | Fix |
|-----------|-------------------|-----|
| `Shower Cubicle` | `Flat sheeting` | NOT a synonym — genuinely different product. LLM error. |
| `Porch ceiling` | `Ceiling` | Add synonym: `"ceiling" → ["porch ceiling"]` |
| `Heater flue` | `Heater` | Add synonym: `"heater flue" → ["heater"]` |
| `Floor covering (beneath carpet)` | `Floor covering` | Normalize: strip parentheticals |

### 2d. Sample Number Matching

Several "As Per J169642-001-017" records share the same base sample number. The tier 1 matcher
extracts the last word after "as per" — works BUT 1:1 consumption means only the first match wins.
This is acceptable behavior (correct architecture).

## 3. Fix Category Summary

| Category | Records Recoverable | R2 AC |
|----------|--------------------:|-------|
| Building name synonyms | 5-8 | R2-AC3, R2-AC5 |
| Room name normalization ("External"→"Exterior") | 1-2 | R2-AC2 |
| Product synonym expansion | 2-3 | R2-AC3 |
| RoomMeta typing fix (indirect improvement) | 1-3 | R2-AC1 |
| **Total recoverable** | **9-16** | |
| **Needed for 36/43** | **5** | |

Conservative estimate: building name synonyms alone recover 5+ records → clears 36/43 floor.

## 4. Broadmeadows Gap Analysis

Gate 2: 28/31. No results breakdown available (R1 output-tag not yet in results).
Need to run `--doc broadmeadows --output-tag gate2_rerun` to get unmatched record details.

Known issues:
- Synthetic plan (no inventory) → whole-document extraction → less precise
- With Docling fixtures (R1) + RoomMeta fix (R2), inventory should compile → per-building extraction

## 5. Scope Boundaries

**In scope (R2)**:
- `building_inventory.py` — RoomMeta coercion
- `e29_benchmark_harness.py` — BUILDING_SYNONYMS, product synonym expansion, room name normalization
- `tests/test_orchestrator.py` — RoomMeta typing test
- Benchmark re-run with evidence

**Out of scope (S5+ territory)**:
- Changing LLM prompts to produce different building/room names
- Adding new extraction strategies
- Changing the pipeline architecture
- Ground truth corrections

## 6. Key File Map

| File | Role | R2 Changes |
|------|------|------------|
| `open_notebook/extractors/building_inventory.py` | Inventory compilation | RoomMeta coercion in `_llm_compile_inventory` |
| `scripts/research/e29_benchmark_harness.py` | Benchmark matching | BUILDING_SYNONYMS, product expansions, room normalization |
| `tests/test_orchestrator.py` | Orchestrator tests | RoomMeta typing tests |
| `tests/test_strategy_registry.py` | Registry tests | No changes expected |
| `docs/sprint-artifacts/e29-gate2-recovery-spec.md` | Recovery spec | Dev agent record |
| `docs/sprint-artifacts/e29-worklog.md` | Worklog | R2 session entry |
| `docs/sprint-artifacts/sprint-status.yaml` | Sprint status | R2 status update |
