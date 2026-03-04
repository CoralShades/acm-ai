# Tech Spec: E32-S2 — Item__c AI Extraction Node

**Story ID**: E32-S2
**Story Points**: 3
**Risk**: MEDIUM
**Type**: backend
**Dependency**: E32-S1 (done — `extract_building_node` added, `building_records` in state)

---

## 1. Overview

E32-S2 adds `extract_items_node` to the LangGraph extraction pipeline. This node runs immediately after `extract_building_node` (E32-S1) and before `orchestrate`. For each building in `state["building_inventory"].buildings`, it calls `_v3_extract_items()` from the orchestrator to get `ACMItemRecord` objects, normalises them to `ACMExtractionRecord` via `_normalize_v3_records()`, and appends all results to `state["records"]`. Downstream nodes (`validate`, `correct`, `deduplicate`, `recover_no_access`, `save`) consume `state["records"]` without modification.

The existing `orchestrate` node is preserved as a fallback for two cases:
1. `building_inventory` is `None` or empty (legacy docs without structure detection).
2. `extract_items_node` produced zero records (signals extraction failure or all-no-access docs).

A new boolean state key `items_extracted` conveys the result of this node to the conditional edge router that decides whether to invoke `orchestrate`.

---

## 2. Existing Infrastructure (read before implementing)

| Symbol | File | Purpose |
|--------|------|---------|
| `_v3_extract_items()` | `open_notebook/extractors/orchestrator.py:792` | Phase 2 LLM call — returns `ACMItemExtractionResult` |
| `_normalize_v3_records()` | `open_notebook/extractors/orchestrator.py:879` | Maps `ACMItemRecord` list → `List[ACMExtractionRecord]` |
| `_extract_building_content()` | `open_notebook/extractors/orchestrator.py` | Slices document text to a page range |
| `BuildingExtractionPlan` | `open_notebook/extractors/orchestrator.py` | Dataclass passed to `_v3_extract_items` |
| `ExtractionStrategy` | `open_notebook/extractors/orchestrator.py` | Enum; use `FULL_LLM` for all item extraction |
| `ACMItemExtractionResult` | `open_notebook/extractors/acm_schemas_v3.py:87` | Pydantic wrapper: `records: List[ACMItemRecord]`, `status: str` |
| `BuildingExtractionResult` | `open_notebook/extractors/acm_schemas_v3.py:18` | Phase 1 output; needed to pass `building_meta` to Phase 2 |
| `ExtractionState` | `open_notebook/graphs/acm_extraction.py:417` | LangGraph TypedDict — add `items_extracted: bool` |
| `extract_building_node` | `open_notebook/graphs/acm_extraction.py:1044` | E32-S1 node — produces `building_records: List[str]` (positional IDs) |
| `ACMRecord.building_record_id` | `open_notebook/domain/acm.py:117` | Optional FK field; already exists — populate when `building_records` list has a matching entry |
| `ACMRecord.raw_row_id` | `open_notebook/domain/acm.py` | **Does NOT exist** — skip AC7 gracefully (no migration in this story) |

### Key observation: `building_records` positional mapping

`extract_building_node` appends one `record_id` string to `saved_ids` per successfully saved building, in the same iteration order as `inventory.buildings`. A building that fails or has empty content is skipped, so the lists may be shorter than `inventory.buildings`. The safe approach is to iterate buildings and maintain a parallel index into `building_records`:

```python
building_records: List[str] = state.get("building_records", [])
# building_records[i] is the DB id for inventory.buildings[i]
# but only if every building was saved. Use a dict keyed by building_code instead.
```

Because `extract_building_node` may skip buildings on error, the safest mapping is **by building_code**, not by positional index. The node should use `BuildingRecord.get_by_source()` or an in-memory lookup constructed during E32-S1. Since E32-S1 does not store a code→id map in state, E32-S2 must reconstruct the mapping at runtime.

**Approach**: Call `BuildingRecord.get_by_source(source_id)` at the start of `extract_items_node` to get all saved `BuildingRecord` objects, build a `{building_code: record_id}` dict, and use it when setting `ACMExtractionRecord.building_record_id`.

---

## 3. State Changes

Add one field to `ExtractionState` in `open_notebook/graphs/acm_extraction.py`:

```python
class ExtractionState(TypedDict):
    # ... existing fields ...
    # E32-S1
    building_records: List[str]
    # E32-S2
    items_extracted: bool  # True when extract_items_node produced >= 1 record
```

`items_extracted` defaults to `False` via `state.get("items_extracted", False)`.

---

## 4. New Node: `extract_items_node`

### Location

`open_notebook/graphs/acm_extraction.py` — insert after `extract_building_node` definition (approx line 1181).

### Signature

```python
async def extract_items_node(state: dict, config: RunnableConfig) -> dict:
    """Phase 2 Item__c extraction: one AI call per building section.

    For each building in building_inventory, calls _v3_extract_items()
    and normalises results to ACMExtractionRecord via _normalize_v3_records().
    Appends all records to state["records"] for consumption by validate/save nodes.

    Returns items_extracted=True when at least one record was produced.

    Story: E32-S2 Item__c AI Extraction Node
    """
```

### Algorithm

```
1. Read state["source"], state["building_inventory"], state["building_records"]
2. If inventory is None or inventory.buildings is empty:
   - Log info, return {"items_extracted": False, "records": []}
3. Emit AG-UI step_started("extract_items")
4. Build building_code -> record_id lookup:
   - Call BuildingRecord.get_by_source(source_id_str) → List[BuildingRecord]
   - Dict comprehension: {br.building_code: str(br.id) for br in saved_buildings if br.building_code}
5. For each building_meta in inventory.buildings:
   a. page_start = building_meta.page_start
      page_end   = building_meta.page_end or page_start
   b. building_content = _extract_building_content(content, page_start, page_end)
   c. If building_content.strip() is empty → log warning, continue
   d. plan = BuildingExtractionPlan(
          building_id=building_meta.building_id,
          building_name=building_meta.name,
          page_range=(page_start, page_end),
          strategy=ExtractionStrategy.FULL_LLM,
      )
   e. building_meta_result = await _v3_extract_building_meta(building_content, plan, state, schema_bundle)
      # Re-run Phase 1 for this building to get building_meta for picklist subsetting.
      # Phase 1 is cheap (small prompt). This avoids state complexity of caching Phase 1 results.
      # If None, _normalize_v3_records handles gracefully (bldg_name falls back to plan.building_name).
   f. item_result = await _v3_extract_items(building_content, plan, building_meta_result, state, schema_bundle)
   g. records = _normalize_v3_records(building_meta_result, item_result, plan)
   h. building_record_id = code_to_id_map.get(building_meta.building_id)
      If building_record_id is set, set record.building_record_id = building_record_id on each record
   i. Append records to all_records
   j. Log: f"[E32-S2] Building {building_meta.building_id}: {len(records)} items"
6. Log total: f"[E32-S2] Item extraction complete: {len(all_records)} records from {n} buildings"
7. Emit AG-UI step_finished("extract_items", records=len(all_records), buildings=n)
8. Update pipeline logger stage progress (ORCHESTRATOR stage, reuse existing stage)
9. Return {"records": all_records, "items_extracted": len(all_records) > 0}
```

### Batching (AC6)

`_v3_extract_items()` already handles a full building's content as one LLM call. The target of ~15 items/call is a guideline for when building content is very large. The existing `provision_langchain_model()` enforces `max_tokens=32768`. For V3 documents encountered so far, a single building fits within one call.

For AC6 implementation in this story: if `building_content` exceeds **12,000 tokens** (estimated via `len(building_content) / 4`), split into page-range sub-chunks of equal size, call `_v3_extract_items()` for each sub-chunk, and merge `item_result.records` before normalising. Use a constant `_ITEM_EXTRACTION_CHUNK_CHARS = 48_000` (approx 12k tokens).

```python
_ITEM_EXTRACTION_CHUNK_CHARS = 48_000

async def _chunk_and_extract_items(
    building_content: str,
    plan: BuildingExtractionPlan,
    building_meta: Optional[BuildingExtractionResult],
    state: dict,
    schema_bundle: Optional[Any],
) -> ACMItemExtractionResult:
    """Split oversized building content and merge item results."""
    from open_notebook.extractors.acm_schemas_v3 import ACMItemExtractionResult

    if len(building_content) <= _ITEM_EXTRACTION_CHUNK_CHARS:
        return await _v3_extract_items(building_content, plan, building_meta, state, schema_bundle)

    # Split into N equal-sized char chunks
    chunks = [
        building_content[i : i + _ITEM_EXTRACTION_CHUNK_CHARS]
        for i in range(0, len(building_content), _ITEM_EXTRACTION_CHUNK_CHARS)
    ]
    merged_records = []
    final_status = "valid"
    for chunk in chunks:
        result = await _v3_extract_items(chunk, plan, building_meta, state, schema_bundle)
        merged_records.extend(result.records)
        if result.status == "invalid":
            final_status = "invalid"

    return ACMItemExtractionResult(records=merged_records, status=final_status)
```

Call `_chunk_and_extract_items()` instead of `_v3_extract_items()` directly in the node loop.

---

## 5. Graph Wiring Changes

### New conditional router: `should_run_orchestrate`

```python
def should_run_orchestrate(state: dict) -> str:
    """Route to orchestrate (fallback) or validate directly.

    Orchestrate runs when:
    - building_inventory is None/empty (legacy document, no structure detection)
    - items_extracted is False (E32-S2 produced zero records — possible extraction failure)

    Otherwise skip directly to validate.
    """
    inventory: Optional[BuildingInventory] = state.get("building_inventory")
    items_extracted: bool = state.get("items_extracted", False)

    if not inventory or not inventory.buildings:
        return "orchestrate"
    if not items_extracted:
        return "orchestrate"
    return "validate"
```

### Updated graph topology

**Before (E32-S1)**:
```
save_intelligence → extract_building → orchestrate → validate
```

**After (E32-S2)**:
```
save_intelligence → extract_building → extract_items → [conditional] → validate
                                                                     ↘ orchestrate → validate
```

**Code changes** in the graph wiring section (approx line 3148):

```python
# Remove direct edge: extract_building → orchestrate
# Add node
agent_state.add_node(
    "extract_items", extract_items_node
)  # E32-S2: Item__c Phase 2 extraction

# Re-wire
agent_state.add_edge("extract_building", "extract_items")  # was: "orchestrate"
agent_state.add_conditional_edges(
    "extract_items",
    should_run_orchestrate,
    {"orchestrate": "orchestrate", "validate": "validate"},
)
# orchestrate → validate edge already exists; no change needed
```

---

## 6. `ACMExtractionRecord.building_record_id` Population

`ACMExtractionRecord` (in `open_notebook/extractors/acm_schemas.py`) must accept an optional `building_record_id` field so the node can pass it through to the save node.

**Check first**: open `open_notebook/extractors/acm_schemas.py` and verify whether `building_record_id` already exists on `ACMExtractionRecord`. If it does, populate it from the lookup map. If it does not, add it as `building_record_id: Optional[str] = None`.

The existing `save_records` node maps `ACMExtractionRecord` fields to `ACMRecord`. Verify that the mapping at approx line 2980 already copies `building_record_id`. If not, add one line:

```python
acm_record = ACMRecord(
    ...
    building_record_id=record.building_record_id,  # E32-S2
    ...
)
```

`ACMRecord.building_record_id` already exists as `Optional[str]` (domain/acm.py:117).

---

## 7. AC7: `raw_row_id` FK

`raw_row_id` does **not** exist on `ACMRecord` (confirmed by search). No migration is introduced in this story. The AC7 requirement is satisfied by skipping gracefully: the node does not attempt to set this field.

If the field is added in a later story, the FK linkage can be backfilled via a data migration.

---

## 8. Imports to Add

In `open_notebook/graphs/acm_extraction.py`, add to the existing import block from `open_notebook.extractors.orchestrator`:

```python
from open_notebook.extractors.orchestrator import (
    BuildingExtractionPlan,
    ExtractionStrategy,
    OrchestratorStats,
    _extract_building_content,
    _get_docling_tables,
    _inject_docling_tables,
    _normalize_v3_records,        # ADD
    _v3_extract_building_meta,
    _v3_extract_items,             # ADD
    orchestrate_extraction,
)
```

Also import `BuildingRecord` from domain (already imported at line 25):
```python
from open_notebook.domain.acm import ACMRecord, ACMTableSection, BuildingRecord
```

And `ACMItemExtractionResult` from schemas:
```python
from open_notebook.extractors.acm_schemas_v3 import BuildingExtractionResult, ACMItemExtractionResult  # ADD
```

---

## 9. File Changes

| File | Change |
|------|--------|
| `open_notebook/graphs/acm_extraction.py` | Add `items_extracted: bool` to `ExtractionState`; add `_ITEM_EXTRACTION_CHUNK_CHARS` constant; add `_chunk_and_extract_items()` helper; add `extract_items_node()`; add `should_run_orchestrate()` router; rewire graph edges; update imports |
| `open_notebook/extractors/acm_schemas.py` | Add `building_record_id: Optional[str] = None` to `ACMExtractionRecord` if absent |
| `open_notebook/graphs/acm_extraction.py` | Update `save_records` node to map `record.building_record_id → acm_record.building_record_id` if not already present |
| `tests/test_item_extraction.py` | New test file (see Section 10) |

---

## 10. Unit Tests: `tests/test_item_extraction.py`

Create a new file. Tests must be runnable with `uv run pytest tests/test_item_extraction.py` without a live SurrealDB.

### Test list

| Test | Description |
|------|-------------|
| `test_extract_items_node_happy_path` | Mock `_v3_extract_items` returning 3 records, `_normalize_v3_records` returning 3 `ACMExtractionRecord`s, `_v3_extract_building_meta` returning a `BuildingExtractionResult`. Assert `state["records"]` has 3 entries and `state["items_extracted"]` is `True`. |
| `test_extract_items_node_no_inventory` | State has `building_inventory=None`. Assert node returns `{"records": [], "items_extracted": False}` without calling LLM. |
| `test_extract_items_node_empty_buildings` | State has `building_inventory` with `buildings=[]`. Same assertion as above. |
| `test_extract_items_node_multiple_buildings` | Two buildings, 2 records each. Assert 4 total records, `items_extracted=True`. |
| `test_extract_items_node_building_failure` | First building raises exception in `_v3_extract_items`. Assert second building still processed (partial results preserved), warning logged. |
| `test_extract_items_node_zero_records` | `_v3_extract_items` returns empty `ACMItemExtractionResult(records=[])`. Assert `items_extracted=False`. |
| `test_chunk_and_extract_items_small` | Content length < `_ITEM_EXTRACTION_CHUNK_CHARS` → calls `_v3_extract_items` exactly once. |
| `test_chunk_and_extract_items_large` | Content length = 3 * `_ITEM_EXTRACTION_CHUNK_CHARS`. Assert `_v3_extract_items` called 3 times, records merged. |
| `test_should_run_orchestrate_no_inventory` | Returns `"orchestrate"` when `building_inventory` is None. |
| `test_should_run_orchestrate_not_extracted` | Returns `"orchestrate"` when `items_extracted=False` with valid inventory. |
| `test_should_run_orchestrate_extracted` | Returns `"validate"` when `items_extracted=True` with valid inventory. |
| `test_building_record_id_populated` | `BuildingRecord.get_by_source()` returns one record with `building_code="B01"`. Assert the resulting `ACMExtractionRecord.building_record_id` matches the saved record's id. |

### Mock setup pattern

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from open_notebook.extractors.acm_schemas_v3 import (
    ACMItemExtractionResult,
    ACMItemRecord,
    BuildingExtractionResult,
)
from open_notebook.extractors.acm_schemas import ACMExtractionRecord
from open_notebook.extractors.building_inventory import (
    BuildingEntry,
    BuildingInventory,
)


def _make_inventory(building_ids=("B01",)):
    buildings = [
        BuildingEntry(
            building_id=bid,
            name=f"Building {bid}",
            page_start=1,
            page_end=5,
        )
        for bid in building_ids
    ]
    return BuildingInventory(buildings=buildings, total_buildings=len(buildings))


def _make_state(inventory=None, building_records=None):
    source = MagicMock()
    source.id = "source:001"
    source.full_text = "--- Page 1 ---\nContent\n--- Page 5 ---\nMore content"
    return {
        "source": source,
        "building_inventory": inventory,
        "building_records": building_records or [],
        "schema_bundle": None,
        "model_id": None,
        "_langchain_config": None,
        "pipeline_logger": None,
        "agui_emitter": None,
        "document_metadata": None,
    }
```

---

## 11. Acceptance Criteria Checklist

| AC | Criterion | Implementation location |
|----|-----------|------------------------|
| AC1 | `extract_items_node` added to orchestrator graph | `acm_extraction.py` — node + `add_node()` |
| AC2 | Uses `v3_item_extraction.jinja` via `_v3_extract_items()` with picklist injection | Delegated to existing `_v3_extract_items()` in orchestrator.py |
| AC3 | Item_Name__c subsetting by product group via `acm_classification` from Phase 1 | `_v3_extract_items()` calls `build_picklist_context(schema_bundle, acm_classification=...)` — already in orchestrator.py:820 |
| AC4 | `ACMItemExtractionResult[]` → `ACMExtractionRecord[]` appended to `state["records"]` | `_normalize_v3_records()` + node return value |
| AC5 | One AI call per building | Per-building loop in `extract_items_node` |
| AC6 | ~15 items/call — chunked if building content > 48k chars | `_chunk_and_extract_items()` helper |
| AC7 | Link to `raw_row_id` FK if field exists — gracefully skipped otherwise | Field confirmed absent; skip noted in code comment |
| AC8 | Unit tests with mock Claude responses | `tests/test_item_extraction.py` |

---

## 12. Verification Protocol

Before marking story complete, run:

```bash
cd "$CLAUDE_PROJECT_DIR"
uv run ruff check open_notebook/graphs/acm_extraction.py --fix
uv run pytest tests/test_item_extraction.py -v
uv run pytest tests/test_orchestrator.py -v        # regression check
uv run pytest tests/test_orchestrator_docling.py -v  # regression check
```

All tests must pass. The three known pre-existing failures (`test_e2e_extraction`, `test_field_config_api`, `test_source_commands_docling`) are unrelated and do not block this story.

---

## 13. Edge Cases and Risk Mitigations

| Risk | Mitigation |
|------|-----------|
| `building_records` list shorter than `buildings` list (E32-S1 skipped a building) | Use `BuildingRecord.get_by_source()` keyed by `building_code` instead of positional index |
| `_v3_extract_building_meta` re-run cost (two Phase 1 calls per building — one in E32-S1, one here) | Acceptable for V3 sprint scope; a future story can cache Phase 1 results in state as `building_meta_cache: Dict[str, BuildingExtractionResult]` |
| `orchestrate` fallback running after items already extracted | Conditional router `should_run_orchestrate` prevents this; `items_extracted=True` skips orchestrate |
| Empty building content after slicing | Guard `if not building_content.strip(): continue` in node loop |
| Phase 2 LLM returns status="invalid" | `_v3_extract_items` already returns `ACMItemExtractionResult(records=[], status="invalid")` on failure; normalisation returns empty list; building contributes 0 records |
| Large multi-building document | Chunking via `_chunk_and_extract_items()` keeps individual calls within token budget |
