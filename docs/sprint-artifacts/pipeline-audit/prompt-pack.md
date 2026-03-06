# ACM Extraction Pipeline Redesign — Prompt Pack (S4–S9)

**Created**: 2026-03-07
**Prerequisite sessions completed**: S1 (audit report), S2 (message structure fix), S3 (Phase 1 cache)
**Dependencies**: S4, S5, S6, S7 can run in parallel after S2/S3. S8 depends on S4+S7. S9 depends on all.

---

## Session 4: Merge Pre-Extraction into 2 LLM Calls

### Goal
Replace 4 sequential pre-extraction calls (metadata, structure, inventory, page_tagging) with 2: (1) metadata+structure, (2) inventory. Drop page_tagging from the pipeline.

### Context
After S2 fixed the message structure, pre-extraction calls work correctly. But 4 sequential calls are wasteful — metadata and structure extraction analyze the same cover pages / full document and can be combined. Page tagging is redundant when building inventory provides page ranges.

### Skills to Load
- `/langgraph-fundamentals`
- `/pydantic-models-py`

### Changes

1. **Create `prompts/acm/metadata_and_structure.jinja`**
   - Merge instructions from `metadata_extraction.jinja` and `structure_extraction.jinja`
   - Combined output schema: `MetadataAndStructureResult` containing both `DocumentMeta` fields and `DocumentStructure` fields
   - HumanMessage will contain the full document content (from S2 pattern)

2. **Create `open_notebook/extractors/metadata_and_structure.py`**
   - Single function `extract_metadata_and_structure(content, model_id)` that returns `(DocumentMeta, DocumentStructure)`
   - Uses combined prompt, parses response into both models
   - Falls back to separate heuristic extractors on failure

3. **Modify `open_notebook/graphs/acm_extraction.py`**
   - Add `metadata_and_structure_node` that calls the combined extractor
   - Remove `tag_pages_node` from graph edges
   - Update graph: `START → metadata_and_structure → inventory → save_intelligence → extract_building → ...`
   - Keep `page_tags` in ExtractionState for backward compat (populate from inventory page ranges)

4. **Keep `prompts/acm/building_inventory.jinja`** as separate call 2
   - Inventory needs structure output (register_start_page) as input to `_trim_to_register()`

### Verification
- Langfuse trace shows 2 GENERATION observations for pre-extraction (was 4)
- Building inventory quality matches or exceeds sequential approach
- Test with both SAMP and ARA format documents
- `uv run pytest tests/` passes

### Estimated Changes
- 1 new file: `prompts/acm/metadata_and_structure.jinja`
- 1 new file: `open_notebook/extractors/metadata_and_structure.py`
- 1 modified: `open_notebook/graphs/acm_extraction.py` (graph topology)

---

## Session 5: Per-Building Parallelization

### Goal
Extract buildings concurrently using `asyncio.gather()` with a configurable semaphore.

### Context
After S3 cached Phase 1 results, `extract_building_node` and `extract_items_node` both iterate sequentially over buildings. For Ollama (single-GPU), a semaphore of 1-2 is appropriate. For cloud providers, 3-5 is better.

### Skills to Load
- `/langgraph-fundamentals`

### Changes

1. **Modify `open_notebook/graphs/acm_extraction.py`**
   - `extract_building_node`: Replace sequential for-loop with:
     ```python
     MAX_CONCURRENT_BUILDINGS = int(os.getenv("ACM_MAX_CONCURRENT_BUILDINGS", "3"))
     sem = asyncio.Semaphore(MAX_CONCURRENT_BUILDINGS)

     async def _extract_one(building_meta):
         async with sem:
             # existing per-building logic
             ...

     results = await asyncio.gather(
         *[_extract_one(b) for b in inventory.buildings],
         return_exceptions=True,
     )
     ```
   - Same pattern for `extract_items_node`
   - Ensure `meta_cache` dict is thread-safe (use regular dict — asyncio is single-threaded)
   - Ensure `PipelineEventBus.publish()` calls are safe within gather

2. **Add env var**: `ACM_MAX_CONCURRENT_BUILDINGS` (default 3, set to 1 for Ollama)

### Verification
- Extraction time decreases proportionally to building count
- Langfuse trace shows overlapping GENERATION timestamps
- All buildings still extracted correctly (same record count as sequential)
- No race conditions in event publishing

### Estimated Changes
- 1 modified: `open_notebook/graphs/acm_extraction.py` (2 functions)

---

## Session 6: Docling Tables as Primary Data in HumanMessage

### Goal
Inject Docling table HTML prominently in HumanMessage, separate from raw text, with clear priority instructions.

### Context
The `_get_docling_tables()` and `_inject_docling_tables()` helpers already exist in `orchestrator.py`. Currently tables are appended to the content string before it goes into SystemMessage. After S2, content is in HumanMessage — now we can structure it with clear sections.

### Skills to Load
- `/langchain-fundamentals`

### Changes

1. **Modify `open_notebook/graphs/acm_extraction.py` — `extract_items_node`**
   - After slicing building content, call `_get_docling_tables(source_id, page_start, page_end)`
   - Structure HumanMessage with clear sections:
     ```
     ## Structured Tables (from PDF extraction — PRIMARY SOURCE)
     {docling_table_html}

     ## Raw Text (for context only)
     {building_content}

     Extract all ACM items from the tables above.
     ```

2. **Update `prompts/acm/v3_item_extraction.jinja`**
   - Add instruction: "When structured table data is provided, use it as the primary source. The raw text is for context only — use it to resolve ambiguities in table data."

3. **Reuse existing functions** — no new extraction logic needed:
   - `_get_docling_tables(source_id, page_start, page_end)` in `orchestrator.py`
   - `_inject_docling_tables(content, tables)` in `orchestrator.py` (may be simplified)

### Verification
- Records from table-heavy documents have higher accuracy
- Langfuse HumanMessage shows tables clearly separated from raw text
- No regression on documents without Docling tables

### Estimated Changes
- 1 modified: `open_notebook/graphs/acm_extraction.py` (`extract_items_node`)
- 1 modified: `prompts/acm/v3_item_extraction.jinja` (add prioritization instruction)

---

## Session 7: Deterministic SF Normalization Node

### Goal
Add a dedicated `normalize_to_sf` graph node that applies Salesforce picklist normalization deterministically, eliminating the need for LLM correction calls.

### Context
The correction loop (observations 16-20 in the trace audit) spent 5 LLM calls to map `"Good Condition"→"Stable"`. The existing `normalize_enum_value()` function already handles this. A dedicated normalization node before validation removes the need for LLM-based correction entirely.

### Skills to Load
- `/pydantic-models-py`
- `/langgraph-fundamentals`

### Changes

1. **Create `open_notebook/extractors/normalizers/sf_normalizer.py`**
   - `normalize_record_to_sf(record: ACMExtractionRecord) -> ACMExtractionRecord`
   - Apply chain: normalize friability → look up valid classifications → auto-fix close matches
   - Validate building_type → derive building_category
   - Apply business rules: negative result → set condition/disturbance to "N/A"
   - Use existing helpers:
     - `normalize_enum_value()` from `open_notebook/extractors/normalizers/enums.py`
     - `SalesforcePicklistValidator` from `open_notebook/extractors/validators/sf_picklist_validator.py`
     - `load_sf_field_schema()` from `open_notebook/extractors/parsers/config_loader.py`

2. **Add `normalize_to_sf_node` to graph** (`acm_extraction.py`)
   - Insert between `extract_items` and `validate`
   - Node iterates over `state["records"]` and applies `normalize_record_to_sf()` to each
   - Returns updated records list

3. **Optionally simplify the correction loop**
   - After normalization, most corrections are already applied
   - Reduce max_correction_attempts from 3 to 1 (or remove entirely in S8)

### Verification
- Records have valid SF picklist values after normalization
- Correction loop has 0 records to correct for common mappings
- `uv run pytest` passes
- Run benchmark comparison: correction LLM calls should drop to 0-1

### Estimated Changes
- 1 new file: `open_notebook/extractors/normalizers/sf_normalizer.py`
- 1 modified: `open_notebook/graphs/acm_extraction.py` (add node + edge)

---

## Session 8: Clean Up Legacy Code

### Goal
Remove unreachable graph nodes, legacy prompts, and dead code paths.

### Context
After S4 (merged pre-extraction) and S7 (deterministic normalization), several code paths are unreachable. Clean up to reduce confusion and maintenance burden.

### Changes

1. **Move legacy prompts to `prompts/acm/legacy/`**:
   - `extraction.jinja` (replaced by v3_item_extraction.jinja)
   - `classification.jinja` (replaced by SF taxonomy in v3 prompts)
   - `building_extraction.jinja` (legacy non-V3 path — keep as fallback but mark deprecated)

2. **Remove unreachable graph nodes** from `acm_extraction.py`:
   - `prepare` node (if dead)
   - `extract` node (if dead)
   - Evaluate `orchestrate` node — keep as clearly-marked fallback with deprecation warning

3. **Clean up unused imports** in `acm_extraction.py`

4. **Remove `ACM_V3_PROMPTS` feature flag** — V3 is now the only path

### Verification
- `uv run pytest` passes
- `cd frontend && npm run build` passes
- `uv run ruff check .` passes
- Extraction on test documents produces identical results

### Estimated Changes
- 3 files moved to `prompts/acm/legacy/`
- 1 modified: `open_notebook/graphs/acm_extraction.py`
- 1 modified: `open_notebook/extractors/orchestrator.py` (remove feature flag)

---

## Session 9: End-to-End Benchmark & Fix Logfire Traces

### Goal
Verify the redesigned pipeline end-to-end, fix Logfire trace explosion, and benchmark against baseline.

### Skills to Load
- `/acm-observability`
- `/systematic-debugging`

### Changes

1. **Fix `instrument_pydantic()` in `open_notebook/observability/logfire_config.py`**
   - Use `include={}` with a safe set of ACM models only (not Docling models)
   - Alternatively, keep `instrument_pydantic()` disabled and rely on Langfuse for tracing

2. **Run baseline extraction** (before all changes — use git stash or worktree):
   - Capture: total records, field accuracy, LLM call count, total time, total cost
   - Save to `docs/sprint-artifacts/pipeline-audit/baseline-metrics.md`

3. **Run redesigned pipeline extraction**:
   - Same document, same model
   - Capture same metrics

4. **Document comparison** in `docs/sprint-artifacts/pipeline-audit/benchmark-results.md`:
   - | Metric | Baseline | Redesigned | Change |
   - Total LLM calls, total time, total cost, records extracted, accuracy

### Verification
- Langfuse traces are clean (no Docling Pydantic validation spam)
- Extraction results equal or better than baseline
- Total LLM calls reduced from 20 to ~5-7

### Estimated Changes
- 1 modified: `open_notebook/observability/logfire_config.py`
- 1 new: `docs/sprint-artifacts/pipeline-audit/benchmark-results.md`

---

## Session Dependency Graph

```
S1 (Audit) ← done
S2 (Message Fix) ← done
S3 (Phase 1 Cache) ← done
S4 (Merge Pre-Extraction) ← requires S2
S5 (Parallelization) ← requires S3
S6 (Docling Tables) ← requires S2
S7 (SF Normalization) ← requires S2
S8 (Dead Code Cleanup) ← requires S4 + S7
S9 (Benchmark) ← requires all previous
```

Sessions S4, S5, S6, S7 can run in parallel.

## Example Session Start Prompt

Copy-paste this to start any session:

```
I'm implementing Session [N] of the ACM pipeline redesign.

Context: [paste the relevant session section from this prompt pack]

Plan file: docs/sprint-artifacts/pipeline-audit/prompt-pack.md

After changes:
1. `uv run pytest tests/` must pass
2. Run extraction on test PDF
3. Verify via Langfuse that [session-specific verification criteria]
```
