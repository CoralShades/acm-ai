# Tech Spec: E32-S1 — Building__c AI Extraction Node

**Story ID**: E32-S1
**Epic**: E32 — Two-Phase SF Object Extraction
**Story Points**: 3
**Risk**: MEDIUM
**Type**: backend
**Dependencies**: E31-S5 (done), E30-S7 (done)
**Output Path**: `docs/sprint-artifacts/e32-s1-building-extraction-node.md`

---

## 1. Overview

Introduce a dedicated `extract_building_node` LangGraph node into the ACM extraction pipeline. The node runs immediately after `save_intelligence` and before `orchestrate`, iterating over each `BuildingMeta` in `state["building_inventory"]` to perform one AI call per building using the existing `_v3_extract_building_meta()` helper in `orchestrator.py`. Extraction results are mapped to `BuildingRecord` domain objects, persisted to the `building_record` SurrealDB table, and their IDs are written back into `ExtractionState` for downstream consumption.

This is a "plumbing" story — the heavy lifting (LLM call, prompt rendering, picklist injection, JSON parsing) is already implemented in `_v3_extract_building_meta()`. This story wires that function into the graph as a proper first-class node with state management, error recovery, and unit tests.

---

## 2. Background and Context

### Current Graph Flow (pre-E32-S1)

```
START
  → extract_metadata      (E1-S19) document metadata
  → structure             (E1-S16) document structure / TOC
  → inventory             (E1-S17) building inventory compilation
  → tag_pages             (E1-S18) page-level section tagging
  → save_intelligence     (E30-S9) persist pre-extraction intelligence
  → orchestrate           (E1-S20) per-building ACM item extraction
  → validate              (E1-S21) strict validation + corrective loop
  → correct               RAG correction pass
  → deduplicate           dedup
  → recover_no_access     no-access recovery
  → save                  persist ACMRecord objects
  → END
```

### Target Graph Flow (post-E32-S1)

```
START
  → extract_metadata
  → structure
  → inventory
  → tag_pages
  → save_intelligence
  → extract_building      [NEW] Building__c AI extraction — one call per building
  → orchestrate           (unchanged) ACM Item__c extraction
  → validate
  → correct
  → deduplicate
  → recover_no_access
  → save
  → END
```

### Relevant Existing Infrastructure

| Symbol | Location | Role |
|---|---|---|
| `_v3_extract_building_meta(building_content, plan, state, schema_bundle)` | `open_notebook/extractors/orchestrator.py:717` | Phase 1 LLM call + JSON parsing — returns `BuildingExtractionResult` or `None` on failure |
| `_extract_building_content(content, page_start, page_end)` | `open_notebook/extractors/orchestrator.py:356` | Slices full-document content by page range using `_PAGE_PATTERN` markers |
| `BuildingExtractionResult` | `open_notebook/extractors/acm_schemas_v3.py:18` | Pydantic model for Phase 1 LLM output |
| `BuildingRecord` | `open_notebook/domain/acm.py:659` | Domain model mapping to `building_record` SurrealDB table; has `generate_internal_id()` classmethod and `save()` method |
| `BuildingInventory` / `BuildingMeta` | `open_notebook/extractors/building_inventory.py:84,57` | Container with `buildings: List[BuildingMeta]`; each `BuildingMeta` has `building_id`, `name`, `page_start`, `page_end` |
| `BuildingExtractionPlan` | `open_notebook/extractors/orchestrator.py:180` | Existing plan type consumed by `_v3_extract_building_meta()` — constructed from `BuildingMeta` inside the new node |
| `ExtractionState` | `open_notebook/graphs/acm_extraction.py:412` | Graph state TypedDict — needs new `building_records: List[str]` field |
| `provision_langchain_model()` | `open_notebook/graphs/utils.py` | Used by `_v3_extract_building_meta()` internally — no direct call needed in the node |
| `_get_pipeline_logger()` / `_get_agui_emitter()` | `open_notebook/graphs/acm_extraction.py:448,453` | Null-safe accessors for observability handles |
| `PipelineLogger` / `StageId` | `open_notebook/extractors/pipeline_logger.py` | Pipeline observability |
| `AGUIEventEmitter` | `open_notebook/extractors/agui_event_emitter.py` | AG-UI SSE events |

### Why `BuildingExtractionPlan` Instead of `BuildingMeta`

`_v3_extract_building_meta()` accepts a `BuildingExtractionPlan` (not a `BuildingMeta`) because the orchestrator uses plan objects. The new node must construct a minimal `BuildingExtractionPlan` from each `BuildingMeta`. The only fields required by `_v3_extract_building_meta()` are:
- `plan.building_id` — for logging
- `plan.page_range` — tuple `(page_start, page_end)` used by `_create_building_prompt_context()`

All other plan fields default to `None` / sensible defaults.

---

## 3. Acceptance Criteria

| AC | Requirement | Verification |
|---|---|---|
| AC1 | New `extract_building_node` async function exists in `open_notebook/graphs/acm_extraction.py`, registered as a node named `"extract_building"` in the `StateGraph` | `grep "extract_building" acm_extraction.py` |
| AC2 | Node calls `_v3_extract_building_meta()` which uses `v3_building_extraction.jinja` prompt with picklist injection via `build_picklist_context(schema_bundle)` | Covered by existing `_v3_extract_building_meta()` implementation |
| AC3 | Successful extractions produce `BuildingRecord` objects (mapped from `BuildingExtractionResult`) persisted to `building_record` table; saved record IDs returned in `state["building_records"]` | Unit test asserts `BuildingRecord.save()` called N times; state contains IDs |
| AC4 | Building `internal_id` generated by calling `await BuildingRecord.generate_internal_id(source_id)` before each `BuildingRecord.save()` call | Unit test asserts `generate_internal_id` called per building |
| AC5 | Model provisioned via `provision_langchain_model()` — done implicitly through `_v3_extract_building_meta()` | Covered by existing helper |
| AC6 | One AI call per building section: node iterates `state["building_inventory"].buildings` and invokes `_v3_extract_building_meta()` once per `BuildingMeta` | Unit test with 3-building inventory asserts 3 LLM calls |
| AC7 | Per-building try/except: provider failure logs a warning via `logger.warning()` and continues to next building; partial results are preserved in state | Unit test: second building raises exception; first and third still produce records |
| AC8 | Unit tests in `tests/test_building_extraction.py` covering: normal path, partial failure path, empty inventory path | Test file exists and all tests pass |

---

## 4. File Changes

| File | Action | Description |
|---|---|---|
| `open_notebook/graphs/acm_extraction.py` | MODIFY | Add `building_records: List[str]` to `ExtractionState`; add `extract_building_node()` async function; register node `"extract_building"`; rewire edges `save_intelligence → extract_building → orchestrate` |
| `tests/test_building_extraction.py` | CREATE | Unit tests for `extract_building_node` with mocked LLM responses and DB calls |

No new files outside these two. No prompt files to create (`v3_building_extraction.jinja` already exists at `prompts/acm/v3_building_extraction.jinja`).

---

## 5. Implementation Details

### 5.1 ExtractionState Extension

In `open_notebook/graphs/acm_extraction.py`, add one field to `ExtractionState`:

```python
class ExtractionState(TypedDict):
    # ... existing fields unchanged ...

    # E32-S1: Building__c extraction results (record IDs of persisted BuildingRecords)
    building_records: List[str]
```

Place this after the `agui_emitter` field (line ~446) to group it with E32-series additions.

### 5.2 New Node: `extract_building_node`

Add the following function to `open_notebook/graphs/acm_extraction.py`, after `save_intelligence_node` and before `orchestrate_with_logging`:

```python
async def extract_building_node(state: dict, config: RunnableConfig) -> dict:
    """Phase 1 Building__c extraction: one AI call per building section.

    Iterates over state["building_inventory"].buildings and calls
    _v3_extract_building_meta() for each building, mapping results to
    BuildingRecord domain objects and persisting them to the DB.

    Story: E32-S1 Building__c AI Extraction Node
    """
    from open_notebook.domain.acm import BuildingRecord
    from open_notebook.extractors.acm_schemas_v3 import BuildingExtractionResult
    from open_notebook.extractors.orchestrator import (
        BuildingExtractionPlan,
        ExtractionStrategy,
        _extract_building_content,
        _v3_extract_building_meta,
    )

    source: Source = state["source"]
    content: str = source.full_text or ""
    inventory: Optional[BuildingInventory] = state.get("building_inventory")
    schema_bundle = state.get("schema_bundle")  # may be None — _v3_extract_building_meta handles None
    pl = _get_pipeline_logger(state)
    agui = _get_agui_emitter(state)

    if agui:
        await agui.emit_step_started("extract_building")

    if not inventory or not inventory.buildings:
        logger.info(
            f"[E32-S1] No building inventory for source {source.id} — skipping building extraction"
        )
        if agui:
            await agui.emit_step_finished("extract_building", buildings=0)
        return {"building_records": []}

    if pl:
        pl.stage_enter(
            StageId.ORCHESTRATOR,
            f"Building extraction: {inventory.total_buildings} buildings",
        )

    saved_ids: List[str] = []
    source_id_str = str(source.id)

    for building_meta in inventory.buildings:
        try:
            # Slice document content to this building's page range
            page_start = building_meta.page_start
            page_end = building_meta.page_end or page_start
            building_content = _extract_building_content(content, page_start, page_end)

            if not building_content.strip():
                logger.warning(
                    f"[E32-S1] Empty content for building {building_meta.building_id} "
                    f"(pages {page_start}-{page_end}) — skipping"
                )
                continue

            # Construct a minimal BuildingExtractionPlan so _v3_extract_building_meta
            # can access building_id and page_range for logging/prompt context
            plan = BuildingExtractionPlan(
                building_id=building_meta.building_id,
                building_name=building_meta.name,
                page_range=(page_start, page_end),
                strategy=ExtractionStrategy.FULL_LLM,
            )

            # Phase 1 LLM call — returns BuildingExtractionResult or None on failure
            result: Optional[BuildingExtractionResult] = await _v3_extract_building_meta(
                building_content=building_content,
                plan=plan,
                state=state,
                schema_bundle=schema_bundle,
            )

            if result is None:
                logger.warning(
                    f"[E32-S1] Phase 1 returned None for building {building_meta.building_id} — skipping"
                )
                continue

            # Generate server-side internal ID: BLD#{source_short}_{seq:03d}
            internal_id = await BuildingRecord.generate_internal_id(source_id_str)

            # Map BuildingExtractionResult fields to BuildingRecord domain model
            record = BuildingRecord(
                internal_id=internal_id,
                source_id=source_id_str,
                building_code=building_meta.building_id,
                building_name=result.building_name,
                building_type=result.building_type,
                building_category=result.building_category,
                building_address=result.building_address,
                suburb=result.suburb,
                postcode=result.postcode,
                building_year=result.estimated_year_built,
                building_construction=result.construction_type,
                date_of_audit_report=result.date_of_audit,
                frequency_of_use=result.frequency_of_use,
            )

            saved_record = await record.save()
            record_id = str(saved_record.id) if saved_record and saved_record.id else internal_id
            saved_ids.append(record_id)

            logger.info(
                f"[E32-S1] Saved BuildingRecord {internal_id} for building "
                f"{building_meta.building_id} (confidence={result.extraction_confidence})"
            )

        except Exception as e:
            logger.warning(
                f"[E32-S1] Failed to extract/save building {building_meta.building_id}: {e} "
                "(skipping — partial results preserved)"
            )
            continue

    logger.info(
        f"[E32-S1] Building extraction complete for source {source_id_str}: "
        f"{len(saved_ids)}/{len(inventory.buildings)} buildings saved"
    )

    if pl:
        pl.stage_progress(
            StageId.ORCHESTRATOR,
            f"Building extraction: {len(saved_ids)}/{len(inventory.buildings)} saved",
            buildings_saved=len(saved_ids),
        )

    if agui:
        await agui.emit_step_finished(
            "extract_building",
            buildings=len(saved_ids),
            total=len(inventory.buildings),
        )

    return {"building_records": saved_ids}
```

### 5.3 Imports

The node uses `_extract_building_content`, `_v3_extract_building_meta`, `BuildingExtractionPlan`, and `ExtractionStrategy` from `orchestrator`. These are currently imported at the function level (local imports inside the node body) to mirror the pattern used by `_v3_extract_building_meta()` itself. This avoids circular import risk and keeps the diff minimal.

`BuildingRecord` is already imported at module level in `acm_extraction.py` (`from open_notebook.domain.acm import ACMRecord, ACMTableSection`) — add `BuildingRecord` to that import.

### 5.4 Graph Wiring

In the graph assembly block (around line 2978), add the new node and rewire the edges:

```python
# Add node (after save_intelligence, before orchestrate)
agent_state.add_node(
    "extract_building", extract_building_node
)  # E32-S1: Building__c Phase 1 extraction

# Rewire edges
# BEFORE:  save_intelligence → orchestrate
# AFTER:   save_intelligence → extract_building → orchestrate
agent_state.add_edge("save_intelligence", "extract_building")   # replaces old edge
agent_state.add_edge("extract_building", "orchestrate")
```

Remove the old direct edge:
```python
# REMOVE this line:
agent_state.add_edge("save_intelligence", "orchestrate")
```

### 5.5 Field Mapping: `BuildingExtractionResult` → `BuildingRecord`

| `BuildingExtractionResult` field | `BuildingRecord` field | Notes |
|---|---|---|
| `building_name` | `building_name` | Direct |
| `building_type` | `building_type` | Picklist — validated downstream |
| `building_category` | `building_category` | Picklist |
| `building_address` | `building_address` | Direct |
| `suburb` | `suburb` | Direct |
| `postcode` | `postcode` | Direct |
| `estimated_year_built` | `building_year` | String; SF picklist format |
| `construction_type` | `building_construction` | Direct |
| `date_of_audit` | `date_of_audit_report` | Direct |
| `frequency_of_use` | `frequency_of_use` | Picklist |
| _(from `BuildingMeta`)_ | `building_code` | `BuildingMeta.building_id` (e.g. `"B001"`) |
| `extraction_confidence` | _(not stored)_ | Logged only — no field on `BuildingRecord` |
| `extraction_notes` | _(not stored)_ | Logged only |

Fields on `BuildingRecord` not populated by this node (remain `None`): `building_address_lga`, `building_address_region`, `roof_type`, `number_of_levels`, `est_building_size_m2`, `daily_duration`, `level_of_activity`, `public_access`, `mobile_plant`, `owned_or_leased`, `asbestos_register_available`, `audit_report_available`, `no_identified_acms`, `site_name`, `school_uid`, etc. These can be populated by future enrichment stories.

### 5.6 `schema_bundle` Availability

`schema_bundle` is not currently a declared field in `ExtractionState`. The node retrieves it with `state.get("schema_bundle")` which returns `None` if absent — `_v3_extract_building_meta()` already handles `None` gracefully by calling `build_picklist_context(None, acm_classification=None)`. No change to `ExtractionState` is needed for this field.

### 5.7 Error Handling Pattern

```
for each building_meta in inventory.buildings:
    try:
        slice content → _extract_building_content()
        construct plan → BuildingExtractionPlan(...)
        call LLM    → _v3_extract_building_meta()  [returns None on internal failure]
        if None: log warning + continue
        generate ID  → BuildingRecord.generate_internal_id()
        map fields   → BuildingRecord(...)
        persist      → record.save()
        append ID    → saved_ids
    except Exception as e:
        logger.warning(f"[E32-S1] Failed ... skipping — partial results preserved")
        continue
```

The `_v3_extract_building_meta()` function already has its own internal try/except that returns `None` on any failure. The outer try/except in the node covers unexpected exceptions from `_extract_building_content()`, `generate_internal_id()`, model construction, or `save()`.

---

## 6. Test Plan

### File: `tests/test_building_extraction.py`

```python
"""
Unit tests for extract_building_node (E32-S1).

All DB calls and LLM calls are mocked. Tests validate:
- Normal path: N buildings → N BuildingRecord saves + N IDs in state
- Partial failure: middle building raises exception → first/last still save
- Empty inventory: node returns empty list without error
- None LLM result: _v3_extract_building_meta returns None → building skipped
"""
```

#### Test Cases

| Test | Setup | Assertion |
|---|---|---|
| `test_normal_path_saves_all_buildings` | 3-building inventory; mock `_v3_extract_building_meta` returns valid `BuildingExtractionResult`; mock `generate_internal_id` returns sequential IDs; mock `record.save()` returns record with id | `building_records` list has 3 entries; `save()` called 3 times |
| `test_partial_failure_preserves_results` | 3-building inventory; second building raises `RuntimeError` inside `_v3_extract_building_meta` | `building_records` has 2 entries (first + third); `logger.warning` called once |
| `test_empty_inventory_returns_empty_list` | `state["building_inventory"] = None` | Returns `{"building_records": []}` without error |
| `test_none_inventory_buildings_returns_empty` | `BuildingInventory(buildings=[], ...)` | Returns `{"building_records": []}` |
| `test_llm_returns_none_skips_building` | 1 building; `_v3_extract_building_meta` returns `None` | `building_records` is `[]`; `generate_internal_id` not called |
| `test_empty_building_content_skips` | 1 building; `_extract_building_content` returns `""` | `building_records` is `[]`; `_v3_extract_building_meta` not called |
| `test_state_dict_has_correct_keys` | 2 buildings, normal path | Returned dict has key `"building_records"` with a list value |

#### Mock Strategy

```python
@pytest.fixture
def mock_state():
    """Minimal state dict for extract_building_node tests."""
    source = MagicMock()
    source.id = "source:test123"
    source.full_text = "<!-- Page 1 -->\nBuilding content..."
    return {
        "source": source,
        "model_id": "openai:gpt-4o-mini",
        "building_inventory": BuildingInventory(
            buildings=[
                BuildingMeta(building_id="B001", name="Main", page_start=1, page_end=5),
                BuildingMeta(building_id="B002", name="Gym", page_start=6, page_end=10),
            ],
            processing_groups=[],
            total_buildings=2,
        ),
        "pipeline_logger": None,
        "agui_emitter": None,
    }


@patch("open_notebook.graphs.acm_extraction._v3_extract_building_meta")
@patch("open_notebook.domain.acm.BuildingRecord.generate_internal_id")
@patch("open_notebook.domain.acm.BuildingRecord.save")
async def test_normal_path_saves_all_buildings(mock_save, mock_gen_id, mock_extract, mock_state):
    mock_extract.return_value = BuildingExtractionResult(
        building_name="Main Building",
        extraction_confidence="high",
    )
    mock_gen_id.return_value = "BLD#TEST1234_001"
    saved_mock = MagicMock()
    saved_mock.id = "building_record:abc"
    mock_save.return_value = saved_mock

    result = await extract_building_node(mock_state, config={})
    assert len(result["building_records"]) == 2
    assert mock_save.call_count == 2
```

Use `pytest-asyncio` with `@pytest.mark.asyncio` on all async tests. Import `extract_building_node` directly from `open_notebook.graphs.acm_extraction`.

---

## 7. Definition of Done

- [ ] `ExtractionState` contains `building_records: List[str]` field
- [ ] `extract_building_node` function exists in `open_notebook/graphs/acm_extraction.py`
- [ ] Node is registered in `StateGraph` as `"extract_building"`
- [ ] Graph edge `save_intelligence → extract_building → orchestrate` is wired correctly (old direct edge removed)
- [ ] `BuildingRecord` is imported at module level in `acm_extraction.py`
- [ ] All 7 unit tests in `tests/test_building_extraction.py` pass
- [ ] `uv run pytest tests/test_building_extraction.py -v` exits 0
- [ ] `uv run ruff check open_notebook/graphs/acm_extraction.py tests/test_building_extraction.py` exits 0
- [ ] No regressions in existing tests: `uv run pytest tests/ -x --ignore=tests/test_building_extraction.py` exits 0 (excluding known pre-existing failures)
- [ ] Node does not break the pipeline when `building_inventory` is `None` (backward compatibility with documents that fail structure/inventory stages)

---

## 8. Risk Notes

**MEDIUM risk** is driven by:

1. **`_v3_extract_building_meta()` signature dependency**: The function accepts `BuildingExtractionPlan`, not `BuildingMeta`. The node must correctly construct a `BuildingExtractionPlan` from a `BuildingMeta`. Verify that `_create_building_prompt_context()` (called inside `_v3_extract_building_meta`) only accesses `plan.building_id` and `plan.page_range` — confirmed by reading `orchestrator.py:387`.

2. **`generate_internal_id()` counts existing records**: Because it queries `get_by_source()` each call, the sequence numbers increment correctly even when multiple buildings are saved in the same node execution. This is correct behavior but means the DB is queried N times per pipeline run (once per building). For documents with many buildings this adds latency — acceptable for a 3-SP story; optimization deferred.

3. **`schema_bundle` not in `ExtractionState`**: Retrieved via `state.get("schema_bundle")` defensively. If a future story adds `schema_bundle` to `ExtractionState`, this code remains correct.

4. **Graph edge rewiring**: The existing edge `save_intelligence → orchestrate` must be removed. If both old and new edges exist simultaneously, LangGraph will raise a compilation error. The diff must be atomic: remove old edge, add two new edges.
