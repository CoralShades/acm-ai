# ACM Extraction Pipeline Redesign — Claude Code Session Prompts (S4-S9)

**Created**: 2026-03-07
**Revised**: 2026-03-07 (v2 — self-contained Claude Code session prompts)
**Prerequisite sessions completed**: S1 (audit report), S2 (message structure fix), S3 (Phase 1 cache)

---

## How to Use This Document

Each session below is a **self-contained Claude Code prompt**. Copy the entire session section (from `### Prompt` to the end of the session) and paste it into a new Claude Code conversation.

**Key conventions:**
- Skills are loaded via `/skill-name` (e.g., `/langgraph-fundamentals`). Claude Code loads the skill content into context automatically.
- `CLAUDE.md` is auto-loaded at session start — it provides project overview, commands, architecture, and code style. The glossary below supplements it with pipeline-specific terms.
- `uv run` is the project's Python runner (uses `pyproject.toml` dependencies).
- All paths are relative to the repo root (`D:\ailocal\acm-ai` or `$CLAUDE_PROJECT_DIR`).
- Langfuse is the self-hosted trace viewer at `localhost:3000`.
- "SF" = Salesforce — the target CRM whose picklist values constrain extraction output.
- For LangGraph/LangChain/Pydantic API questions, use Context7 MCP (`resolve-library-id` → `query-docs`) to get current docs instead of relying on training data.

---

## Pipeline Glossary (included in each session prompt)

The following glossary is embedded in each session prompt so Claude Code doesn't waste tokens searching for definitions.

| Term | Definition |
|------|-----------|
| **Building__c extraction (Phase 1)** | LLM call that extracts building-level metadata (name, type, address, year built) from a building's section of the document. Implemented by `_v3_extract_building_meta()` in `open_notebook/extractors/orchestrator.py:726`. Returns a `BuildingExtractionResult`. |
| **Item__c extraction (Phase 2)** | LLM call that extracts individual ACM item records (location, product, condition, sample number) from a building's section. Implemented by `_v3_extract_items()` in `open_notebook/extractors/orchestrator.py:800`. Returns a list of `ACMExtractionRecord`. |
| **ExtractionState** | TypedDict at `open_notebook/graphs/acm_extraction.py:431`. The shared state for all graph nodes. Key fields: `source`, `content`, `document_structure`, `building_inventory`, `page_tags`, `document_metadata`, `records`, `building_records`, `building_meta_cache`. |
| **building_meta_cache** | Dict field in ExtractionState (`acm_extraction.py:474`) that maps `building_code → BuildingExtractionResult`. Populated by `extract_building_node`, consumed by `extract_items_node` to avoid duplicate Phase 1 LLM calls. Added in S3. |
| **Pre-extraction stages** | Four sequential LLM calls that analyze the document before per-building extraction: (1) `extract_metadata_node` → `DocumentMeta`, (2) `extract_structure` → `DocumentStructure`, (3) `compile_inventory` → `BuildingInventory`, (4) `tag_page_sections` → `PageTaggingResult`. |
| **Docling tables** | HTML tables extracted from PDF by the Docling library. Fetched via `_get_docling_tables(source_id, page_start, page_end)` at `orchestrator.py:69`. More accurate than raw text for tabular data. |
| **SF picklist normalization** | Mapping raw LLM output values to valid Salesforce picklist values. E.g., `"Good Condition"→"Stable"`, `"Cement products (f)"→"Cement products"`. Handled by `normalize_enum_value()` in `open_notebook/extractors/normalizers/enums.py:84`. |
| **SalesforcePicklistValidator** | Validates dependent picklist chains (e.g., friability → valid classifications for that friability). Located at `open_notebook/extractors/validators/sf_picklist_validator.py`. |
| **PipelineEventBus** | SSE event publisher at `open_notebook/extractors/pipeline_event_bus.py`. Publishes extraction progress events consumed by the frontend. |
| **S2 message fix** | Commit `c5aa555b` that moved document content from Jinja2 templates/SystemMessage to HumanMessage across all 7 LLM call sites. Pattern: SystemMessage = instructions + picklists only (<5K chars), HumanMessage = document content. |
| **SAMP** | School Asbestos Management Plan — one of two document formats the pipeline handles. - Outdated Not Using Anymore|
| **ARA** | Asbestos Risk Assessment — the other document format. - Outdated Not Using Anymore|
| **ACM_V3_PROMPTS** | Environment variable feature flag that switches between legacy and V3 extraction paths. V3 is the current path. |
| **Correction loop** | `correct_records` node at `acm_extraction.py:2358` that uses LLM calls to fix invalid picklist values. Currently wastes 3-5 LLM calls for trivial mappings that `normalize_enum_value()` handles deterministically. |

---

## Current Graph Topology

```
START → extract_metadata → structure → inventory → tag_pages
  → save_intelligence → extract_building → extract_items
  → [conditional: should_run_orchestrate] → {orchestrate | validate}
  → [conditional: should_correct] → {correct → validate (loop) | deduplicate}
  → recover_no_access → save → END
```

**Graph definition**: `acm_extraction.py:3523-3573`
**Legacy nodes** (registered but unreachable): `prepare` (line 3539), `extract` (line 3540)

---

## Session Dependency Graph

```
S1 (Audit Report)         ← DONE
S2 (Message Structure Fix) ← DONE
S3 (Phase 1 Cache)        ← DONE
S4 (Merge Pre-Extraction) ← requires S2 ← can run now
S5 (Parallelization)      ← requires S3 ← can run now
S6 (Docling Tables)       ← requires S2 ← can run now
S7 (SF Normalization)     ← requires S2 ← can run now
S8 (Dead Code Cleanup)    ← requires S4 + S7
S9 (Benchmark)            ← requires all previous
```

Sessions S4, S5, S6, S7 can run in parallel.

---

## Session 4: Merge Pre-Extraction into 2 LLM Calls

### Goal

Replace 4 sequential pre-extraction LLM calls with 2:
- **Call 1**: Combined metadata + structure extraction (currently two separate calls)
- **Call 2**: Building inventory (currently a third call)
- **Drop**: Page tagging (currently a fourth call — redundant because building inventory already provides page ranges)

### Prompt

```
I'm implementing Session 4 of the ACM pipeline redesign: merging 4 pre-extraction LLM calls into 2.

Load skills: /langgraph-fundamentals, /pydantic-models-py

## Context

The ACM extraction pipeline currently makes 4 sequential LLM calls before per-building extraction:

1. `extract_metadata_node` (graph node at acm_extraction.py:3523) → calls `_llm_extract_metadata()` in `metadata_extractor.py` → returns `DocumentMeta`
2. `extract_structure` (graph node at acm_extraction.py:3524) → calls `_llm_extract_structure()` in `document_structure.py` → returns `DocumentStructure`
3. `compile_inventory` (graph node at acm_extraction.py:3525) → calls `_llm_compile_inventory()` in `building_inventory.py` → returns `BuildingInventory`
4. `tag_page_sections` (graph node at acm_extraction.py:3526) → calls `tag_pages()` in `page_tagger.py` → returns `PageTaggingResult`

Calls 1 and 2 analyze the same document content and can be combined. Call 4 (page tagging) is redundant — building inventory already provides page ranges per building, which is all downstream nodes need.

After S2 (commit c5aa555b), all calls use the correct message structure:
- SystemMessage = instructions only (<5K chars)
- HumanMessage = document content

The ExtractionState (TypedDict at acm_extraction.py:431) has fields for all four results:
- `document_metadata: Optional[DocumentMeta]`
- `document_structure: Optional[DocumentStructure]`
- `building_inventory: Optional[BuildingInventory]`
- `page_tags: Optional[PageTaggingResult]`

The graph edges (acm_extraction.py:3547-3553) are:
```python
agent_state.add_edge(START, "extract_metadata")
agent_state.add_edge("extract_metadata", "structure")
agent_state.add_edge("structure", "inventory")
agent_state.add_edge("inventory", "tag_pages")
agent_state.add_edge("tag_pages", "save_intelligence")
```

## What to Change

### 1. Create combined prompt template
**File**: `prompts/acm/metadata_and_structure.jinja`
- Merge instructions from `prompts/acm/metadata_extraction.jinja` and `prompts/acm/structure_extraction.jinja`
- Read both existing templates first to understand their instructions
- Combined output schema: a single JSON containing both DocumentMeta fields and DocumentStructure fields
- Do NOT include document content in the template — content goes in HumanMessage (S2 pattern)

### 2. Create combined extractor
**File**: `open_notebook/extractors/metadata_and_structure.py`
- Function: `async def extract_metadata_and_structure(content: str, model_id: Optional[str] = None) -> Tuple[DocumentMeta, DocumentStructure]`
- Uses the combined prompt template
- Renders SystemMessage from template, puts content in HumanMessage
- Parses the JSON response into both `DocumentMeta` and `DocumentStructure` models
- On failure, falls back to the existing heuristic extractors:
  - `_heuristic_extract_metadata()` from `metadata_extractor.py`
  - `_heuristic_extract_structure()` from `document_structure.py`

### 3. Modify graph topology
**File**: `open_notebook/graphs/acm_extraction.py`
- Add a new `metadata_and_structure_node` that calls `extract_metadata_and_structure()`
- This node returns both `document_metadata` and `document_structure` to state
- Remove `tag_pages_node` from graph edges (page tagging is redundant)
- Keep `page_tags` field in ExtractionState for backward compat — populate from inventory page ranges
- New edges:
  ```python
  agent_state.add_edge(START, "metadata_and_structure")
  agent_state.add_edge("metadata_and_structure", "inventory")
  agent_state.add_edge("inventory", "save_intelligence")
  ```
- Keep the old `extract_metadata` and `structure` nodes registered (but unreachable) for rollback safety

### 4. Keep building_inventory.jinja as separate Call 2
- Inventory needs `register_start_page` from DocumentStructure as input to `_trim_to_register()` (a function that slices document content to just the register section)
- So it must run after the combined metadata+structure call

## Verification Checklist
1. `uv run pytest tests/` passes
2. Run extraction on a test PDF document
3. Check Langfuse trace: should show 2 GENERATION observations for pre-extraction (was 4)
4. Building inventory quality matches or exceeds the sequential approach
5. Test with both SAMP and ARA format documents if available

## Files Summary
- 1 NEW: `prompts/acm/metadata_and_structure.jinja`
- 1 NEW: `open_notebook/extractors/metadata_and_structure.py`
- 1 MODIFY: `open_notebook/graphs/acm_extraction.py` (new node + updated edges)
```

---

## Session 5: Per-Building Parallelization

### Goal

Extract buildings concurrently using `asyncio.gather()` with a configurable semaphore, reducing total extraction time proportionally to building count.

### Prompt

```
I'm implementing Session 5 of the ACM pipeline redesign: per-building parallelization.

Load skills: /langgraph-fundamentals

## Context

The ACM extraction pipeline processes buildings sequentially in two graph nodes:

1. `extract_building_node` (acm_extraction.py:1086) — iterates over `inventory.buildings` and calls `_v3_extract_building_meta()` (orchestrator.py:726) for each building. This is "Phase 1" — extracts Building__c metadata (name, type, address, year built). Results are cached in `state["building_meta_cache"]` (a Dict[str, Any] keyed by building_code).

2. `extract_items_node` (acm_extraction.py:1300) — iterates over `inventory.buildings` and calls `_v3_extract_items()` (orchestrator.py:800) for each building. This is "Phase 2" — extracts Item__c records (location, product, condition, sample number). It reads cached Phase 1 results from `building_meta_cache` to avoid duplicate LLM calls.

Both nodes currently use sequential `for` loops. For a document with 8 buildings, this means 8 sequential LLM calls per node = 16 total sequential calls.

The `PipelineEventBus` (at `open_notebook/extractors/pipeline_event_bus.py`) publishes SSE events during extraction. Its `publish()` method must remain safe to call from within `asyncio.gather()` — since asyncio is single-threaded, a regular dict and non-async publish are safe.

For Ollama (single-GPU local inference), a semaphore of 1-2 is appropriate. For cloud providers (Anthropic, OpenRouter), 3-5 is better.

## What to Change

### 1. Modify `extract_building_node` (acm_extraction.py:1086)
Replace the sequential for-loop with concurrent extraction:
```python
import asyncio
import os

MAX_CONCURRENT_BUILDINGS = int(os.getenv("ACM_MAX_CONCURRENT_BUILDINGS", "3"))

async def extract_building_node(state: dict, config: RunnableConfig) -> dict:
    # ... existing setup code ...

    sem = asyncio.Semaphore(MAX_CONCURRENT_BUILDINGS)
    meta_cache: Dict[str, Any] = {}

    async def _extract_one(building_meta):
        async with sem:
            # existing per-building extraction logic
            # ... call _v3_extract_building_meta() ...
            # ... store result in meta_cache[building_meta.building_id] ...
            return result

    results = await asyncio.gather(
        *[_extract_one(b) for b in inventory.buildings],
        return_exceptions=True,
    )

    # Process results, handle exceptions
    # ...

    return {"building_records": saved_ids, "building_meta_cache": meta_cache}
```

### 2. Apply same pattern to `extract_items_node` (acm_extraction.py:1300)
Same `asyncio.gather()` + semaphore pattern for Phase 2 extraction.

### 3. Add environment variable
`ACM_MAX_CONCURRENT_BUILDINGS` — default 3, set to 1 for Ollama in `.env`.

## Verification Checklist
1. `uv run pytest tests/` passes
2. Run extraction on a multi-building test PDF
3. Extraction time decreases proportionally to building count
4. Langfuse trace shows overlapping GENERATION timestamps for building extractions
5. All buildings still extracted correctly (same record count as sequential)
6. No race conditions in PipelineEventBus event publishing

## Files Summary
- 1 MODIFY: `open_notebook/graphs/acm_extraction.py` (2 functions: `extract_building_node`, `extract_items_node`)
```

---

## Session 6: Docling Tables as Primary Data in HumanMessage

### Goal

When Docling HTML tables are available for a building's page range, inject them prominently in the HumanMessage as the PRIMARY data source, with raw text as secondary context.

### Prompt

```
I'm implementing Session 6 of the ACM pipeline redesign: Docling tables as primary data.

Load skills: /langchain-fundamentals

## Context

The pipeline has two existing helper functions in `open_notebook/extractors/orchestrator.py`:

1. `_get_docling_tables(source_id, page_start, page_end)` (line 69) — fetches Docling HTML tables from the database for a given page range. Returns a list of table HTML strings.

2. `_inject_docling_tables(content, tables)` (line 105) — appends Docling tables to the end of a content string. Currently used in the legacy extraction path.

After S2 (commit c5aa555b), document content is passed in HumanMessage (not SystemMessage). This means we can now structure the HumanMessage with clear sections that tell the LLM which data to prioritize.

Currently in `extract_items_node` (acm_extraction.py:1300), the HumanMessage for Phase 2 (Item__c extraction) looks like:
```
## Document Content

{building_content}

Extract all ACM item records from the building content above.
```

ACM documents are heavily tabular — the asbestos register is a table with columns for location, product, condition, sample number, etc. Docling's HTML table extraction is more accurate than raw text OCR for these structured tables.

## What to Change

### 1. Modify `extract_items_node` (acm_extraction.py:1300)
After slicing `building_content` for each building, fetch Docling tables:
```python
# Fetch Docling tables for this building's page range
docling_tables = await _get_docling_tables(
    source_id=str(state["source"].id),
    page_start=building_meta.page_start,
    page_end=building_meta.page_end,
)
```

Then structure the HumanMessage with clear priority sections:
```python
if docling_tables:
    tables_html = "\n\n".join(docling_tables)
    human_content = (
        f"## Structured Tables (from PDF extraction — PRIMARY SOURCE)\n\n"
        f"{tables_html}\n\n"
        f"## Raw Text (for context only)\n\n"
        f"{building_content}\n\n"
        f"Extract all ACM items from the tables above. Use raw text only to resolve ambiguities."
    )
else:
    human_content = (
        f"## Document Content\n\n"
        f"{building_content}\n\n"
        f"Extract all ACM item records from the building content above."
    )
```

### 2. Update item extraction prompt template
**File**: `prompts/acm/v3_item_extraction.jinja`
Add this instruction near the top of the template:
```
When structured table data is provided in the user message, use it as the primary source for extraction. The raw text section is for context only — use it to resolve ambiguities in the table data, such as building names or section headers not present in the table.
```

### 3. Reuse existing functions
- `_get_docling_tables()` already exists — just call it from `extract_items_node`
- `_inject_docling_tables()` may become unused after this change — leave it for now (S8 cleanup)

## Verification Checklist
1. `uv run pytest tests/` passes
2. Run extraction on a table-heavy PDF document
3. Records from table-heavy documents have higher accuracy (compare field completeness)
4. Langfuse trace shows HumanMessage with tables clearly separated from raw text
5. No regression on documents without Docling tables (fallback to raw text only)

## Files Summary
- 1 MODIFY: `open_notebook/graphs/acm_extraction.py` (`extract_items_node`)
- 1 MODIFY: `prompts/acm/v3_item_extraction.jinja` (add table prioritization instruction)
```

---

## Session 7: Deterministic SF Normalization Node

### Goal

Add a dedicated `normalize_to_sf` graph node that applies Salesforce picklist normalization deterministically, eliminating most or all LLM correction calls.

### Prompt

```
I'm implementing Session 7 of the ACM pipeline redesign: deterministic SF normalization.

Load skills: /pydantic-models-py, /langgraph-fundamentals

## Context

### The Problem
The current `correct_records` node (acm_extraction.py:2358) uses LLM calls to fix invalid Salesforce picklist values in extraction output. In the trace audit (see docs/sprint-artifacts/pipeline-audit/trace-audit-report.md), this node made 5 LLM calls just to map `"Good Condition"→"Stable"` — a trivial string mapping.

### Existing Deterministic Tools
The codebase already has functions that handle these mappings without LLM calls:

1. **`normalize_enum_value(raw_value, field_name)`** at `open_notebook/extractors/normalizers/enums.py:84`
   - Maps raw LLM output to canonical Salesforce picklist values
   - Example: `"Good Condition"→"Stable"`, `"Cement products (f)"→"Cement products"`
   - Uses fuzzy matching for close matches

2. **`SalesforcePicklistValidator`** at `open_notebook/extractors/validators/sf_picklist_validator.py`
   - Validates dependent picklist chains (e.g., friability determines which classifications are valid)
   - Has `validate_chain()` method that checks full dependency chains

3. **`load_sf_field_schema()`** at `open_notebook/extractors/parsers/config_loader.py`
   - Loads Salesforce field definitions from `V3/output/building_fields_summary.md` and `V3/output/item_fields_summary.md`
   - Provides valid picklist values and dependency rules

### ACMExtractionRecord Model
Defined in `open_notebook/domain/acm.py`. Key SF-aligned fields that need normalization:
- `friability` — "Friable" or "Non-friable"
- `product_classification` — depends on friability
- `material_condition` — "Stable", "Fair", "Poor", "Severely Damaged"
- `surface_treatment` — "Painted", "Unpainted", "Coated", etc.
- `accessibility` — "Accessible", "Inaccessible", "Restricted"
- `asbestos_determination` — "Confirmed", "Assumed Positive", "Negative"
- `building_type`, `building_category` — building_category is derived from building_type

### Current Graph Flow (relevant section)
```
extract_items → [should_run_orchestrate] → {orchestrate | validate}
validate → [should_correct] → {correct → validate (loop) | deduplicate}
```

The new normalize node should go between `extract_items` and `validate`.

## What to Change

### 1. Create normalizer module
**File**: `open_notebook/extractors/normalizers/sf_normalizer.py`

```python
def normalize_record_to_sf(record: ACMExtractionRecord) -> ACMExtractionRecord:
    """Apply deterministic SF picklist normalization to one record."""
    # 1. Normalize friability first (other fields depend on it)
    record.friability = normalize_enum_value(record.friability, "friability")

    # 2. Normalize product_classification (constrained by friability)
    record.product_classification = normalize_enum_value(
        record.product_classification, "product_classification"
    )

    # 3. Normalize other picklist fields
    for field in ["material_condition", "surface_treatment", "accessibility",
                   "asbestos_determination", "building_type"]:
        value = getattr(record, field, None)
        if value:
            setattr(record, field, normalize_enum_value(value, field))

    # 4. Derive building_category from building_type
    # (use existing logic or SalesforcePicklistValidator)

    # 5. Business rules: negative determination → condition/disturbance = "N/A"
    if record.asbestos_determination == "Negative":
        record.material_condition = "N/A"
        # ... other N/A fields

    return record
```

### 2. Add `normalize_to_sf_node` to graph
**File**: `open_notebook/graphs/acm_extraction.py`

```python
async def normalize_to_sf_node(state: dict, config: RunnableConfig) -> dict:
    """Deterministic SF picklist normalization — no LLM calls."""
    records = state.get("records", [])
    normalized = [normalize_record_to_sf(r) for r in records]
    return {"records": normalized}
```

Insert into graph topology (around line 3558):
```python
# After extract_items, normalize before validate
agent_state.add_node("normalize_to_sf", normalize_to_sf_node)

# Update edges: extract_items → normalize_to_sf → validate (or orchestrate)
agent_state.add_edge("extract_items", "normalize_to_sf")  # NEW
agent_state.add_conditional_edges(
    "normalize_to_sf",  # Changed from "extract_items"
    should_run_orchestrate,
    {"orchestrate": "orchestrate", "validate": "validate"},
)
```

### 3. Optionally reduce correction loop
After normalization handles most mappings, reduce `max_correction_attempts` from 3 to 1 (or remove the correction loop entirely in S8).

## Verification Checklist
1. `uv run pytest tests/` passes
2. After normalization, records have valid SF picklist values
3. Correction loop has 0 records to correct for common mappings like "Good Condition"→"Stable"
4. `uv run ruff check .` passes
5. Run benchmark comparison: correction LLM calls should drop to 0-1

## Files Summary
- 1 NEW: `open_notebook/extractors/normalizers/sf_normalizer.py`
- 1 MODIFY: `open_notebook/graphs/acm_extraction.py` (add node + update edges)
```

---

## Session 8: Clean Up Legacy Code

### Goal

Remove unreachable graph nodes, legacy prompt templates, and dead code paths that are no longer needed after S4 (merged pre-extraction) and S7 (deterministic normalization).

### Prompt

```
I'm implementing Session 8 of the ACM pipeline redesign: legacy code cleanup.

## Prerequisites
Sessions S4 (merge pre-extraction) and S7 (SF normalization) must be completed first.

## Context

After S4 and S7, several code paths are unreachable:

### Legacy Prompt Templates
These templates in `prompts/acm/` are no longer used by the V3 extraction path:
- `extraction.jinja` — replaced by `v3_item_extraction.jinja`
- `classification.jinja` — replaced by SF taxonomy in V3 prompts
- `building_extraction.jinja` — legacy non-V3 building extraction (replaced by `v3_building_extraction.jinja`)

### Unreachable Graph Nodes
In `open_notebook/graphs/acm_extraction.py`:
- `prepare` node (line 3539) — `prepare_context` function, originally wired before `extract` but edges were removed
- `extract` node (line 3540) — `extract_records` function, legacy extraction path

These nodes are registered via `add_node()` but have no incoming edges — they are unreachable.

### Feature Flag
`ACM_V3_PROMPTS` — an environment variable in `open_notebook/extractors/orchestrator.py` that switches between legacy and V3 extraction. V3 is now the only path and this flag should be removed.

### The `orchestrate` Node
The `orchestrate` node (line 3537-3538) wraps `orchestrate_with_logging` — the legacy agentic orchestrator. It's currently reachable via `should_run_orchestrate` conditional edge from `extract_items`. Evaluate whether this fallback is still needed. If keeping it, mark it with a clear deprecation warning.

## What to Change

### 1. Move legacy prompts to `prompts/acm/legacy/`
```bash
mkdir -p prompts/acm/legacy
mv prompts/acm/extraction.jinja prompts/acm/legacy/
mv prompts/acm/classification.jinja prompts/acm/legacy/
mv prompts/acm/building_extraction.jinja prompts/acm/legacy/
```

### 2. Remove unreachable graph nodes from `acm_extraction.py`
- Remove `prepare` and `extract` node registrations (lines 3539-3540)
- Remove their function definitions (`prepare_context`, `extract_records`) if not imported elsewhere
- Check with grep: `grep -r "prepare_context\|extract_records" open_notebook/`

### 3. Clean up unused imports in `acm_extraction.py`
After removing nodes, some imports will be unused. Run `uv run ruff check . --fix` to auto-remove.

### 4. Remove `ACM_V3_PROMPTS` feature flag
- Search: `grep -r "ACM_V3_PROMPTS" open_notebook/`
- Remove the flag checks and collapse to V3-only code path
- In `orchestrator.py`, remove the `if os.getenv("ACM_V3_PROMPTS")` branches

### 5. Evaluate `orchestrate` node
- Read `should_run_orchestrate()` conditional function to understand when it triggers
- If it's a dead-letter fallback, add a deprecation warning log and keep it
- If it's actively used, leave it as-is

## Verification Checklist
1. `uv run pytest tests/` passes
2. `cd frontend && npm run build` passes (no broken imports)
3. `uv run ruff check .` passes (no unused imports)
4. Run extraction on a test PDF — results identical to pre-cleanup
5. Verify moved templates exist in `prompts/acm/legacy/`

## Files Summary
- 3 MOVE: prompt templates to `prompts/acm/legacy/`
- 1 MODIFY: `open_notebook/graphs/acm_extraction.py` (remove dead nodes, clean imports)
- 1 MODIFY: `open_notebook/extractors/orchestrator.py` (remove feature flag)
```

---

## Session 9: End-to-End Benchmark & Fix Logfire Traces

### Goal

Verify the redesigned pipeline end-to-end, fix the Logfire/Pydantic trace explosion, and create a benchmark comparison report.

### Prompt

```
I'm implementing Session 9 of the ACM pipeline redesign: end-to-end benchmark.

Load skills: /acm-observability, /systematic-debugging

## Prerequisites
All previous sessions (S4-S8) must be completed.

## Context

### Logfire Trace Explosion (already partially fixed)
Commit `27bd2060` removed `instrument_pydantic()` from `open_notebook/observability/logfire_config.py` because it was instrumenting ALL Pydantic models — including Docling's internal models (BoundingBox, TableCell, etc.), which generated 48K trace spans per extraction. The fix removed instrumentation entirely.

This session should add it back selectively — only for ACM domain models, not Docling models.

### Langfuse Setup
- Self-hosted at `localhost:3000`
- Auth: `$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY` (HTTP Basic)
- Session ID convention: `extraction-{source_id}`
- Query traces: `curl -u "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" "$LANGFUSE_BASE_URL/api/public/traces?sessionId=extraction-{source_id}"`
- List GENERATION observations: `curl -u "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" "$LANGFUSE_BASE_URL/api/public/observations?traceId={trace_id}&type=GENERATION"`

### What to Benchmark
Compare the redesigned pipeline (after S4-S8) against the baseline (before all changes). Metrics:
- Total LLM calls (count GENERATION observations in Langfuse)
- Total extraction time
- Total cost (sum token costs from Langfuse)
- Records extracted (count)
- Field-level accuracy (compare against known-good extraction)

### Baseline Reference
The trace audit report at `docs/sprint-artifacts/pipeline-audit/trace-audit-report.md` documents the baseline:
- 20 GENERATION observations
- ~72 minutes total
- 5 correction LLM calls for trivial mappings

## What to Change

### 1. Fix `instrument_pydantic()` selectively
**File**: `open_notebook/observability/logfire_config.py`

Add selective Pydantic instrumentation for ACM models only:
```python
# Only instrument ACM domain models, NOT Docling models
from open_notebook.domain.acm import ACMExtractionRecord, ACMExtractionResult
from open_notebook.extractors.building_inventory import BuildingInventory
from open_notebook.extractors.document_structure import DocumentStructure
from open_notebook.extractors.metadata_extractor import DocumentMeta

logfire.instrument_pydantic(
    include={ACMExtractionRecord, ACMExtractionResult, BuildingInventory, DocumentStructure, DocumentMeta}
)
```

Alternatively, if `include={}` with specific models is not supported by the Logfire API, keep `instrument_pydantic()` disabled and rely on Langfuse alone. Check the Logfire docs first.

### 2. Run baseline extraction
Use `git stash` or a worktree to run the pre-S4 code on the same test document:
```bash
# Option A: git worktree
git worktree add ../acm-ai-baseline c5aa555b  # commit before S4
cd ../acm-ai-baseline && uv sync && uv run python -c "..."

# Option B: just use the trace audit data as baseline (already documented)
```

Capture metrics and save to `docs/sprint-artifacts/pipeline-audit/baseline-metrics.md`.

### 3. Run redesigned pipeline extraction
Same document, same model (qwen2.5:7b or whichever is configured).
Capture same metrics from Langfuse trace.

### 4. Create benchmark comparison report
**File**: `docs/sprint-artifacts/pipeline-audit/benchmark-results.md`

```markdown
| Metric | Baseline (pre-S4) | Redesigned (post-S8) | Change |
|--------|-------------------|---------------------|--------|
| Total LLM calls | 20 | ? | ? |
| Total time | ~72 min | ? | ? |
| Total cost | ? | ? | ? |
| Records extracted | ? | ? | ? |
| Field accuracy | ? | ? | ? |
| Correction calls | 5 | ? | ? |
```

## Verification Checklist
1. Langfuse traces are clean (no Docling Pydantic validation spam)
2. Extraction results equal or better than baseline
3. Total LLM calls reduced from 20 to ~5-7
4. Benchmark report saved to `docs/sprint-artifacts/pipeline-audit/benchmark-results.md`
5. `uv run pytest tests/` passes

## Files Summary
- 1 MODIFY: `open_notebook/observability/logfire_config.py` (selective instrumentation)
- 1 NEW: `docs/sprint-artifacts/pipeline-audit/baseline-metrics.md`
- 1 NEW: `docs/sprint-artifacts/pipeline-audit/benchmark-results.md`
```

---

## Claude Code Tips for All Sessions

### Skill Loading
Skills are loaded by typing `/skill-name` (e.g., `/langgraph-fundamentals`). This loads domain-specific patterns and constraints into context. Always load skills BEFORE starting implementation.

### Subagent Usage
For sessions with independent subtasks, use the `/dispatching-parallel-agents` skill to parallelize. Example:
- S4: Template creation and extractor creation can be parallelized
- S7: Normalizer module and graph topology change can be parallelized

### Verification Pattern
After every session, run this verification sequence:
```bash
uv run ruff check .              # Lint
uv run pytest tests/             # Tests
cd frontend && npm run build     # Frontend build (if applicable)
```

### Langfuse Trace Inspection
After running an extraction, inspect the trace:
```bash
# Load the /acm-observability skill, then:
# Find the latest trace for a source
curl -s -u "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" \
  "$LANGFUSE_BASE_URL/api/public/traces?sessionId=extraction-{source_id}&limit=1" | jq '.data[0].id'

# List all GENERATION observations
curl -s -u "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" \
  "$LANGFUSE_BASE_URL/api/public/observations?traceId={trace_id}&type=GENERATION" | jq '.data[] | {name, startTime, endTime}'
```

### Context7 for Library Docs
If you need current documentation for LangGraph, LangChain, Pydantic, or other libraries:
1. Use Context7 MCP: resolve the library ID first, then query docs
2. This fetches live documentation instead of relying on training data

### Commit Convention
Use conventional commits: `feat(extraction):`, `fix(extraction):`, `refactor(extraction):`, etc.
