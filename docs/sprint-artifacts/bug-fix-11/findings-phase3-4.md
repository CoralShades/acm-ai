# Bug Fix 11 Phase 3+4 — Research Findings

**Date**: 2026-03-11
**Scope**: Building Persistence + Correction/Progress Fixes

## Finding F1: Building persistence code EXISTS but LLM failure causes skip

**Location**: `open_notebook/graphs/acm_extraction.py:606-611`

The `extract_building_node` already has full BuildingRecord persistence logic (lines 613-644).
However, when `_v3_extract_building_meta()` returns `None` (LLM failure), the entire building
is skipped — no BuildingRecord is created at all.

**Evidence from test run**:
```
WARNING | _v3_extract_building_meta:348 - V3 Phase 1 [BUILDING_1] failed — continuing without building meta: Error code: 402
WARNING | extract_building_node:607 - [E32-S1] Phase 1 returned None for building BUILDING_1 — skipping
INFO    | extract_building_node:698 - [E32-S1] Building extraction complete: 0/1 buildings saved
```

**Fix**: When `result is None`, create a minimal `BuildingRecord` from `BuildingMeta` fields
(name, building_id, source_id) instead of returning `None`. The LLM enrichment (address,
type, category, etc.) is nice-to-have, but the basic record is essential for FK linkage.

## Finding F2: `_heuristic_fallback` does NOT receive `document_metadata`

**Location**: `open_notebook/extractors/building_inventory.py:326-329`

`_heuristic_fallback(content, document_structure)` — no `document_metadata` parameter.
The generic fallback at line 463-471 hardcodes `name="Main Building"` because it has
no access to `site_name`.

**Fix chain**:
1. Add `document_metadata: Optional[dict] = None` param to `_heuristic_fallback`
2. In the catch-all at line 463-471: use `document_metadata.get("site_name", "Main Building")`
3. Caller `compile_building_inventory` already has `document_metadata` — pass it through

## Finding F3: Correction model lacks `format="json"` for Ollama

**Location**: `open_notebook/graphs/acm_extraction.py:1594-1601`

The correction model is provisioned via `provision_langchain_model()` at line 1595 but
`_apply_ollama_extraction_settings()` is never called on it. The extraction model
gets this treatment via `ensure_extraction_settings()` in utils.py (lines 900, 991),
but the correction path doesn't use that wrapper.

**Fix**: After line 1601, add:
```python
from open_notebook.graphs.utils import _apply_ollama_extraction_settings
model = _apply_ollama_extraction_settings(model)
```

**Import note**: `_apply_ollama_extraction_settings` is already importable — it's used
at lines 900 and 991 in the same `utils.py` module. In `acm_extraction.py`, it's imported
indirectly via `ensure_extraction_settings`. Need to check if direct import is needed.

## Finding F4: PipelineLogger has no `finalize()` method

**Location**: `open_notebook/extractors/pipeline_logger.py`

There is no `finalize()` or `mark_completed()` method. The `_persist_state()` method
writes whatever `self._state.status` is, but nothing explicitly sets it to `COMPLETED`
after the graph finishes. The final state depends on the last `stage_exit()` call.

**Fix**: Add a `finalize()` method to PipelineLogger that:
1. Sets `self._state.status = PipelineRunStatus.COMPLETED`
2. Calls `await self._persist_state()` (direct, not fire-and-forget)
3. Call it from `acm_commands.py` after `extract_acm_from_source()` returns

## Finding F5: `acm_commands.py` has no pipeline_logger reference

**Location**: `commands/acm_commands.py:215-220`

The command handler calls `extract_acm_from_source(source, model_id, force, command_id)`
but doesn't hold a reference to the PipelineLogger. The logger is created inside
the graph's initial state setup.

**Fix options**:
- **Option A**: Have `extract_acm_from_source` return the pipeline_logger (or its run_id)
  so the command can call `finalize()` — requires changing the return type
- **Option B**: Write terminal status directly in `acm_commands.py` using raw SurrealDB
  query (simpler, no return type change)
- **Option C**: Add finalize logic inside the graph's terminal node (save_records or
  a new finalize_node)

**Recommended**: Option B — minimal blast radius, direct DB write after extraction completes.
