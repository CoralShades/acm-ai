# Story 1.20: Agentic Extraction Orchestrator

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **system**,
I want **an agentic orchestrator layer in the LangGraph extraction pipeline that dynamically routes document sections to appropriate extraction tools and strategies based on page tags, document structure, and building inventory**,
so that **extraction accuracy improves by applying section-specific prompts, skipping non-register pages entirely, parallelizing per-building extraction where possible, and using page tags to select optimal extraction strategies per section type**.

## Acceptance Criteria

1. **AC-1: Section-Aware Content Routing** - The orchestrator uses `PageTaggingResult` (E1-S18) to route pages by section type: register pages (section_id=4) go to full ACM extraction, metadata pages (section_id=0-3) are skipped, appendix pages (section_id=7) use specialized lab-result parsing
2. **AC-2: Per-Building Extraction Strategy** - Instead of processing the entire document as one chunk, the orchestrator uses `BuildingInventory` (E1-S17) processing groups to extract per-building, passing building-specific context (building name, code, page range) to each extraction call
3. **AC-3: Dynamic Tool Selection** - The orchestrator selects extraction strategies per section: full LLM extraction for register tables, regex-only extraction for simple "No Asbestos" buildings, and skip for non-register sections. Selection is based on `BuildingMeta.complexity` and page tag confidence scores
4. **AC-4: Parallel Building Extraction** - For documents with 3+ buildings, the orchestrator extracts buildings concurrently using `asyncio.gather()` with a configurable concurrency limit (default: 3) to balance throughput and API rate limits
5. **AC-5: Context Enrichment** - Each per-building extraction call receives enriched context: building metadata from inventory, document structure from E1-S16, page section tags from E1-S18, and document metadata from E1-S19 (if available)
6. **AC-6: Fallback to Legacy Pipeline** - If page tags, building inventory, or document structure are ALL None (e.g., older documents or pipeline failures), the orchestrator falls back to the current monolithic extraction path (prepare_context -> extract_records loop) - ensuring full backward compatibility
7. **AC-7: Extraction Statistics** - The orchestrator produces extraction statistics per building: records extracted, pages processed, strategy used (full_llm/regex_only/skipped), time taken. Statistics aggregated into `ACMExtractionOutput.orchestrator_stats`
8. **AC-8: Pipeline Integration** - Replace the current `prepare -> extract -> (loop)` section of the graph with `orchestrate -> (per-building subgraph) -> merge_results`. The pre-extraction stages (structure, inventory, tag_pages) and post-extraction stages (validate, correct, deduplicate, save) remain unchanged

## Tasks / Subtasks

- [ ] Task 1: Define orchestrator Pydantic models (AC: #3, #5, #7)
  - [ ] 1.1 Create `ExtractionStrategy` enum: `FULL_LLM`, `REGEX_ONLY`, `SKIP`
  - [ ] 1.2 Create `BuildingExtractionPlan` model: building_id, building_name, page_range (tuple), strategy (ExtractionStrategy), complexity, context_summary
  - [ ] 1.3 Create `ExtractionPlan` model: plans (list of BuildingExtractionPlan), total_buildings, buildings_to_extract, buildings_skipped, estimated_llm_calls
  - [ ] 1.4 Create `BuildingExtractionStats` model: building_id, records_extracted, pages_processed, strategy_used, time_ms, errors (optional)
  - [ ] 1.5 Create `OrchestratorStats` model: total_buildings, buildings_extracted, buildings_skipped, total_records, strategy_distribution (dict), total_time_ms, plan (ExtractionPlan)
  - [ ] 1.6 Add `orchestrator_stats: Optional[OrchestratorStats]` to `ACMExtractionOutput` in `acm_schemas.py`
- [ ] Task 2: Implement extraction planning logic (AC: #1, #2, #3)
  - [ ] 2.1 Create `open_notebook/extractors/orchestrator.py` with planning functions
  - [ ] 2.2 Implement `plan_extraction(state: ExtractionState) -> ExtractionPlan`:
    - Use page_tags to identify register pages (section_id=4)
    - Use building_inventory to map buildings to page ranges
    - Classify each building's strategy based on complexity:
      - `FULL_LLM`: buildings with `complexity == "complex"` or unknown
      - `REGEX_ONLY`: buildings with `complexity == "simple"` (e.g., "No Asbestos" buildings)
      - `SKIP`: buildings where all pages are non-register (section_id != 4)
    - Generate context summary per building from metadata
  - [ ] 2.3 Implement `should_use_orchestrator(state: ExtractionState) -> bool`:
    - Returns True if building_inventory is not None AND has 1+ buildings
    - Returns False otherwise (fallback to legacy pipeline)
  - [ ] 2.4 Handle edge cases: buildings with no page range, overlapping page ranges, single-page buildings
- [ ] Task 3: Implement per-building extraction (AC: #2, #4, #5)
  - [ ] 3.1 Implement `extract_building(plan: BuildingExtractionPlan, content: str, state: ExtractionState) -> Tuple[List[ACMExtractionRecord], BuildingExtractionStats]`:
    - Trim content to building's page range using page markers
    - Apply building-specific context to extraction prompt
    - For FULL_LLM: use existing extraction logic (chunk + LLM)
    - For REGEX_ONLY: use regex patterns to extract simple "No Asbestos" records
    - For SKIP: return empty list immediately
  - [ ] 3.2 Implement `_extract_building_content(content: str, page_start: int, page_end: int) -> str`:
    - Extract content between page markers for a building's page range
    - Reuse `_PAGE_PATTERN` from document_structure.py
  - [ ] 3.3 Implement `_create_building_prompt_context(plan: BuildingExtractionPlan, doc_meta: Optional[DocumentMeta]) -> dict`:
    - Merge building metadata, document metadata, and school context
  - [ ] 3.4 Implement `_regex_extract_simple_building(content: str, building_id: str, building_name: str) -> List[ACMExtractionRecord]`:
    - For simple buildings: create one ACMExtractionRecord per room with result="Not Detected"
    - Use room patterns from building_inventory to find room entries
- [ ] Task 4: Implement parallel orchestration (AC: #4, #8)
  - [ ] 4.1 Implement `orchestrate_extraction(state: dict, config: RunnableConfig) -> dict` as a LangGraph node:
    - Call `should_use_orchestrator()` to decide path
    - Call `plan_extraction()` to generate plan
    - For each non-SKIP building, call `extract_building()` with asyncio.gather (max concurrency)
    - Collect all records and stats
    - Return merged records, orchestrator_stats, updated state
  - [ ] 4.2 Implement `merge_building_results(results: List[Tuple[List[ACMExtractionRecord], BuildingExtractionStats]]) -> Tuple[List[ACMExtractionRecord], OrchestratorStats]`:
    - Combine all records from all buildings
    - Aggregate stats
  - [ ] 4.3 Add concurrency limiter using `asyncio.Semaphore(max_concurrent)` with default=3
  - [ ] 4.4 Graceful error handling: if one building's extraction fails, log error, continue with others, include error in stats
- [ ] Task 5: Update LangGraph pipeline wiring (AC: #6, #8)
  - [ ] 5.1 Add `orchestrate` node to the graph
  - [ ] 5.2 Add conditional edge after `tag_pages`: if `should_use_orchestrator()` returns True -> `orchestrate`, else -> `prepare` (legacy path)
  - [ ] 5.3 Wire `orchestrate` -> `validate` (skipping legacy prepare/extract loop entirely)
  - [ ] 5.4 Keep legacy `prepare` -> `extract` -> (loop) path intact for backward compatibility
  - [ ] 5.5 Add `orchestrator_stats: Optional[OrchestratorStats]` to `ExtractionState` TypedDict
  - [ ] 5.6 Update initial state in `extract_acm_from_source()`: add `orchestrator_stats=None`
  - [ ] 5.7 Pass orchestrator_stats to `ACMExtractionOutput` in the final return
  - [ ] 5.8 New graph topology:
    ```
    START -> structure -> inventory -> tag_pages -> CONDITIONAL:
      - orchestrator path: orchestrate -> validate -> correct <-> validate -> deduplicate -> save -> END
      - legacy path: prepare -> extract -> (loop) -> validate -> correct <-> validate -> deduplicate -> save -> END
    ```
- [ ] Task 6: Update extraction prompt with building context (AC: #5)
  - [ ] 6.1 Create or update `prompts/acm/building_extraction.jinja` template for per-building extraction
  - [ ] 6.2 Include building-specific context: building name, code, year, construction type, expected rooms
  - [ ] 6.3 Include page range hint: "You are extracting from pages X to Y of the document"
  - [ ] 6.4 Include document type hint from document_structure
  - [ ] 6.5 Reuse existing extraction output schema (ACMExtractionResult) - no schema changes needed
- [ ] Task 7: Write comprehensive tests (AC: #1-8)
  - [ ] 7.1 Create `tests/test_orchestrator.py` with class-based test organization
  - [ ] 7.2 Test ExtractionStrategy enum values
  - [ ] 7.3 Test BuildingExtractionPlan creation and validation
  - [ ] 7.4 Test ExtractionPlan generation from various building inventories
  - [ ] 7.5 Test OrchestratorStats aggregation
  - [ ] 7.6 Test `should_use_orchestrator()`:
    - True when building_inventory present with buildings
    - False when building_inventory is None
    - False when building_inventory has 0 buildings
  - [ ] 7.7 Test `plan_extraction()`:
    - Correct strategy assignment based on complexity
    - SKIP for non-register buildings (no section_id=4 pages)
    - REGEX_ONLY for simple "No Asbestos" buildings
    - FULL_LLM for complex buildings
    - Handle missing page_tags gracefully (default to FULL_LLM)
  - [ ] 7.8 Test `_extract_building_content()`:
    - Correct page range extraction using markers
    - Handle missing page markers
    - Handle single-page buildings
  - [ ] 7.9 Test `_regex_extract_simple_building()`:
    - Creates records with result="Not Detected"
    - Finds rooms using room patterns
    - Returns empty list for content without room patterns
  - [ ] 7.10 Test `extract_building()`:
    - FULL_LLM path with mocked LLM
    - REGEX_ONLY path
    - SKIP path returns empty
    - Error handling (LLM failure -> empty + error stats)
  - [ ] 7.11 Test `orchestrate_extraction()` LangGraph node:
    - Orchestrator path triggered when inventory present
    - Legacy fallback when inventory missing
    - Correct state updates (records, orchestrator_stats)
  - [ ] 7.12 Test parallel extraction:
    - Multiple buildings extracted concurrently
    - Semaphore limits concurrency
    - One building failure doesn't block others
  - [ ] 7.13 Test `merge_building_results()`:
    - Records from multiple buildings combined correctly
    - Stats aggregated (total_records, strategy_distribution, time)
  - [ ] 7.14 Test graph wiring:
    - Conditional edge routes correctly based on should_use_orchestrator
    - Both paths (orchestrate and legacy) compile and are reachable
  - [ ] 7.15 Test backward compatibility:
    - Document with no structure/inventory/tags uses legacy path
    - Results are identical to pre-orchestrator behavior
  - [ ] 7.16 Test ACMExtractionOutput includes orchestrator_stats when present
- [ ] Task 8: Verification
  - [ ] 8.1 Run `uv run ruff check .` - lint passes
  - [ ] 8.2 Run `uv run pytest tests/test_orchestrator.py -v` - all tests pass
  - [ ] 8.3 Run `uv run pytest tests/` - full suite passes (no regressions)
  - [ ] 8.4 Verify graph compilation: both orchestrator and legacy paths present in compiled graph nodes

## Dev Notes

### Architecture & Design

**Pipeline Position: Replaces Legacy Extract Loop**

This story transforms the extraction pipeline from a monolithic "process entire document" approach to an agentic "plan-and-execute per-building" approach. The orchestrator sits between the pre-extraction intelligence stages (E1-S16..S19) and the post-extraction validation stages (E1-S15).

```
CURRENT:  START -> structure -> inventory -> tag_pages -> prepare -> extract -> (loop) -> validate -> correct <-> validate -> deduplicate -> save -> END

WITH S20: START -> structure -> inventory -> tag_pages -> CONDITIONAL:
  (A) Orchestrator path (when building_inventory present):
      orchestrate -> validate -> correct <-> validate -> deduplicate -> save -> END
  (B) Legacy path (fallback):
      prepare -> extract -> (loop) -> validate -> correct <-> validate -> deduplicate -> save -> END
```

**Critical Design Decisions:**

1. **Conditional routing, not replacement**: The orchestrator is an ADDITIONAL path, not a replacement. The legacy `prepare -> extract -> loop` path is preserved intact for backward compatibility. A conditional edge after `tag_pages` decides which path to take.

2. **Per-building extraction is the key insight**: Currently, the pipeline processes the entire document as one blob (with page-based chunking). The orchestrator leverages E1-S17's `BuildingInventory` processing groups to extract per-building, giving each extraction call focused content and building-specific context. This dramatically reduces noise and improves accuracy.

3. **Three extraction strategies**: Not all buildings need full LLM extraction:
   - `FULL_LLM`: Complex buildings with ACM register data → full extraction pipeline
   - `REGEX_ONLY`: Simple "No Asbestos" buildings → regex creates minimal records
   - `SKIP`: Non-register sections (methodology, conclusions, appendices) → skip entirely
   This reduces LLM costs by 30-50% for typical SAMP documents.

4. **Parallel extraction with semaphore**: Multiple buildings are extracted concurrently using `asyncio.gather()` with a semaphore (default: 3). This improves throughput for large documents with many buildings while respecting API rate limits.

5. **Orchestrator stats for observability**: The orchestrator produces detailed statistics per building, enabling monitoring of extraction quality, cost optimization, and debugging of per-building issues.

6. **Post-extraction stages unchanged**: The validate -> correct -> deduplicate -> save pipeline remains exactly the same. The orchestrator only changes HOW records are extracted, not how they're validated or stored.

7. **No new database tables**: All new models are transient pipeline state. `OrchestratorStats` is embedded in `ACMExtractionOutput` for API consumers.

### Key Source Files to Study Before Implementation

| File | What to Learn | Key Patterns |
|------|---------------|--------------|
| `open_notebook/graphs/acm_extraction.py` | Full pipeline: ExtractionState, graph wiring, prepare_context, extract_records, chunk logic, initial state | **CRITICAL** - this is what you're refactoring |
| `open_notebook/extractors/building_inventory.py` | `BuildingInventory`, `BuildingMeta`, `ProcessingGroup`, complexity classification, page ranges | Per-building data to drive orchestration |
| `open_notebook/extractors/page_tagger.py` | `PageTaggingResult`, `PageTag`, `SectionTaxonomy`, register_page_range | Section routing input |
| `open_notebook/extractors/document_structure.py` | `DocumentStructure`, `_PAGE_PATTERN`, register_start_page | Content splitting patterns |
| `open_notebook/extractors/acm_schemas.py` | `ACMExtractionOutput`, `ACMExtractionResult`, `ACMExtractionRecord`, `BuildingRoomContext` | Output schemas to extend |
| `open_notebook/extractors/parsers/base.py` | `DocumentMeta`, `RawACMItem` | Metadata models |
| `prompts/acm/extraction.jinja` | Current extraction prompt template | Base prompt to adapt for building context |

### Current Pipeline Flow (What Changes)

```python
# CURRENT graph wiring (acm_extraction.py:1268-1309)
agent_state.add_edge(START, "structure")              # E1-S16
agent_state.add_edge("structure", "inventory")         # E1-S17
agent_state.add_edge("inventory", "tag_pages")         # E1-S18
agent_state.add_edge("tag_pages", "prepare")           # CHANGE: conditional edge
agent_state.add_conditional_edges("prepare", ...)       # KEEP (legacy path)
agent_state.add_conditional_edges("extract", ...)       # KEEP (legacy path)
agent_state.add_conditional_edges("validate", ...)      # KEEP (both paths)
agent_state.add_edge("correct", "validate")             # KEEP
agent_state.add_edge("deduplicate", "save")             # KEEP
agent_state.add_edge("save", END)                       # KEEP

# NEW graph wiring
agent_state.add_node("orchestrate", orchestrate_extraction)  # NEW
agent_state.add_conditional_edges(
    "tag_pages",
    lambda s: "orchestrate" if should_use_orchestrator(s) else "prepare",
    {"orchestrate": "orchestrate", "prepare": "prepare"},
)
agent_state.add_edge("orchestrate", "validate")  # Orchestrate feeds into same validate
```

### BuildingInventory Data Available for Orchestration

From E1-S17, `BuildingInventory` provides:

```python
class BuildingMeta(BaseModel):
    building_id: str           # e.g., "B00A"
    building_name: str         # e.g., "Admin Building"
    building_year: Optional[int]
    construction_type: Optional[str]
    page_start: int            # First page of this building's data
    page_end: int              # Last page of this building's data
    room_count: int            # Number of rooms detected
    complexity: str            # "simple" or "complex"
    acm_item_estimate: Optional[int]  # Estimated ACM items

class ProcessingGroup(BaseModel):
    buildings: List[str]       # Building IDs in this group
    page_start: int
    page_end: int
    total_rooms: int

class BuildingInventory(BaseModel):
    buildings: List[BuildingMeta]
    processing_groups: List[ProcessingGroup]
    total_buildings: int
    total_rooms: int
```

### PageTaggingResult Data Available for Routing

From E1-S18, `PageTaggingResult` provides:

```python
class SectionTaxonomy(IntEnum):
    EXECUTIVE_SUMMARY = 0
    INTRODUCTION = 1
    SITE_DESCRIPTION = 2
    METHODOLOGY = 3
    ASBESTOS_REGISTER = 4  # <-- This is what we extract
    RISK_ASSESSMENT = 5
    CONCLUSION = 6
    APPENDIX = 7

class PageTag(BaseModel):
    page_number: int
    section_id: int            # SectionTaxonomy value
    section_title: str
    confidence: float          # 0.0-1.0
    page_type: str             # title_page, toc_page, content, special

class PageTaggingResult(BaseModel):
    pages: List[PageTag]
    total_pages: int
    register_page_range: Optional[Tuple[int, int]]  # (start, end) of section_id=4
```

### Extraction Strategy Selection Logic

```python
def _select_strategy(
    building: BuildingMeta,
    page_tags: Optional[PageTaggingResult],
) -> ExtractionStrategy:
    """Select extraction strategy for a building based on complexity and page tags."""

    # If no page tags, default to FULL_LLM (safe choice)
    if not page_tags:
        return ExtractionStrategy.FULL_LLM

    # Check if ANY of this building's pages are register pages (section_id=4)
    building_pages = [
        tag for tag in page_tags.pages
        if building.page_start <= tag.page_number <= building.page_end
    ]
    register_pages = [p for p in building_pages if p.section_id == 4]

    if not register_pages:
        return ExtractionStrategy.SKIP  # No register content for this building

    # Simple buildings with low complexity can use regex
    if building.complexity == "simple":
        return ExtractionStrategy.REGEX_ONLY

    return ExtractionStrategy.FULL_LLM
```

### Parallel Extraction Pattern

```python
async def _extract_buildings_parallel(
    plans: List[BuildingExtractionPlan],
    content: str,
    state: ExtractionState,
    max_concurrent: int = 3,
) -> List[Tuple[List[ACMExtractionRecord], BuildingExtractionStats]]:
    """Extract multiple buildings in parallel with concurrency limit."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _extract_with_limit(plan: BuildingExtractionPlan):
        async with semaphore:
            return await extract_building(plan, content, state)

    tasks = [_extract_with_limit(plan) for plan in plans if plan.strategy != ExtractionStrategy.SKIP]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle exceptions gracefully
    valid_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            plan = plans[i]
            logger.error(f"Building {plan.building_id} extraction failed: {result}")
            valid_results.append(([], BuildingExtractionStats(
                building_id=plan.building_id,
                records_extracted=0,
                pages_processed=0,
                strategy_used=plan.strategy.value,
                time_ms=0,
                errors=[str(result)],
            )))
        else:
            valid_results.append(result)

    return valid_results
```

### Existing Code Patterns to Follow

1. **LangGraph Node Functions:** `async def node_name(state: dict, config: RunnableConfig) -> dict:` from `acm_extraction.py`
2. **Conditional Edges:** `agent_state.add_conditional_edges("node", routing_fn, {"path_a": "node_a", "path_b": "node_b"})` - pattern already used for extract loop and corrective loop
3. **Structured LLM Output:** Use `model.with_structured_output(PydanticModel)` for extraction (already proven in E1-S15..S18)
4. **Prompt Loading:** Use `Prompter(prompt_template="acm/building_extraction")` then `prompter.render(data={...})`
5. **Error Handling:** Catch exceptions, log warnings, continue with remaining buildings
6. **Page Splitting:** Import `_PAGE_PATTERN` from `document_structure.py` for content slicing
7. **Test Organization:** Class-based tests with mocked LLM responses (pattern from `test_page_tagger.py`, `test_building_inventory.py`)

### Regex-Only Extraction for Simple Buildings

For buildings classified as "simple" (typically "No Asbestos Found" buildings), regex extraction is sufficient and avoids an LLM call:

```python
# These buildings typically have room entries like:
# B00A-R0001 - External Movement
# No Asbestos Detected
#
# The regex creates one ACMExtractionRecord per room with:
# - building_id from plan
# - room_id from regex
# - result = "Not Detected"
# - extraction_confidence = "high" (regex is certain for this pattern)

ROOM_ENTRY_PATTERN = r"([A-Z]\d+[A-Z]?-R\d+)\s*[-\u2013]\s*(.+?)(?:\n|$)"
NO_ACM_PATTERN = r"(?:No\s+Asbestos|Not\s+Detected|NAD|No\s+ACM)"
```

### Integration with E1-S19 (Document Metadata)

If E1-S19 is implemented (document_metadata in state), the orchestrator enriches each building's extraction context with:
- `document_meta.consultant_name` - helps LLM understand format conventions
- `document_meta.site_name` - provides school/site context
- `document_meta.report_date` - contextual information

If `document_metadata` is None, the orchestrator proceeds without it (backward compatible).

### Project Structure Notes

- **New file locations align with existing structure:**
  - `open_notebook/extractors/orchestrator.py` - alongside `page_tagger.py`, `building_inventory.py`
  - `prompts/acm/building_extraction.jinja` - alongside existing `extraction.jinja`
  - `tests/test_orchestrator.py` - alongside `test_page_tagger.py`, `test_building_inventory.py`
- **Modified files:**
  - `open_notebook/graphs/acm_extraction.py` - ExtractionState + node + conditional wiring
  - `open_notebook/extractors/acm_schemas.py` - Add orchestrator_stats to ACMExtractionOutput
- **No new dependencies required** - uses existing asyncio, LangChain/LangGraph, Pydantic
- **No migration required** - all models are transient pipeline state; stats embedded in existing output

### Potential Breaking Changes to Watch

1. **Graph topology change**: The conditional edge after `tag_pages` changes routing. Tests that assert specific graph edge sequences need updating.
2. **ACMExtractionOutput extension**: Adding `orchestrator_stats` field is non-breaking (Optional with default None).
3. **ExtractionState extension**: Adding `orchestrator_stats` field is non-breaking (Optional with default None).
4. **Existing extraction tests**: Tests that mock the full graph flow may need updating for the conditional edge. The legacy path should still pass all existing tests.
5. **Import changes**: `orchestrate_extraction` and `should_use_orchestrator` imported into `acm_extraction.py`.

Run `grep -r "ExtractionState\|ACMExtractionOutput\|graph\.compile\|tag_pages.*prepare" --include="*.py"` to find all usages before making changes.

### References

- [Source: _bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md] Epic 1 story list (E1-S20 not explicitly defined in epics file - defined via sprint change proposals)
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-07.md#CP-2] FR-109 Agentic RAG Orchestrator requirement
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-02-07.md#CP-23] Pipeline agentic orchestrator layer specification
- [Source: _bmad-output/project-planning-artifacts/acm-ai/04-architecture.md#5.1] Two-Stage Pipeline Architecture
- [Source: _bmad-output/project-planning-artifacts/acm-ai/04-architecture.md#5.2] Generic Configurable Parser Architecture
- [Source: open_notebook/graphs/acm_extraction.py] Full LangGraph pipeline (ExtractionState, graph wiring, node functions)
- [Source: open_notebook/extractors/building_inventory.py] BuildingInventory, BuildingMeta, ProcessingGroup models
- [Source: open_notebook/extractors/page_tagger.py] PageTaggingResult, PageTag, SectionTaxonomy
- [Source: open_notebook/extractors/document_structure.py] DocumentStructure, _PAGE_PATTERN
- [Source: open_notebook/extractors/acm_schemas.py] ACMExtractionOutput, ACMExtractionResult, ACMExtractionRecord
- [Source: _bmad-output/implementation-artifacts/e1-s18-page-level-section-tagging.md] E1-S18 implementation details, graph wiring pattern
- [Source: _bmad-output/implementation-artifacts/e1-s19-document-metadata-extraction-enhancement.md] E1-S19 DocumentMeta enhancement, pipeline integration pattern

### Dependencies

| Direction | Story | Relationship |
|-----------|-------|-------------|
| Depends on | E1-S16 (Document Structure & TOC) | Uses DocumentStructure for document_type, register_start_page (DONE) |
| Depends on | E1-S17 (Building Inventory) | Uses BuildingInventory and ProcessingGroups for per-building extraction (DONE) |
| Depends on | E1-S18 (Page-Level Section Tagging) | Uses PageTaggingResult for section-aware routing (REVIEW) |
| Depends on | E1-S15 (Corrective RAG) | Corrective validation loop is preserved after orchestrator output (DONE) |
| Soft depends on | E1-S19 (Document Metadata) | Can use DocumentMeta for context enrichment if available (READY-FOR-DEV) |
| Depends on | E1-S3 (Two-Stage Pipeline) | Pipeline infrastructure exists (DONE) |
| Blocks | E12-S1 (Extraction Settings) | Settings page may reference orchestration mode toggles |

### Git Intelligence (Recent Commits)

Last 10 commits on main:
```
256b05b docs: update sprint status - E1-S11..S17 done, 56/85 stories (66%)
943a37c feat(e1-s18): add page-level section tagging with LLM + heuristic
f488691 feat(e1-s16..s17): add document structure extraction and building inventory
76c0bf0 feat(e1-s15): add corrective RAG validation loop with auto-correction
ba115ed feat(e1-s14): add contextual embedding enrichment with re-embed API
06a4f09 feat(e1-s12): enhance consultant wording normalization
8690d68 feat(e1-s11): rewrite parser to generic configurable with BAR field schema
92c06dc docs: apply course correction and update sprint planning artifacts
9ee7b6a chore: fix startup race condition and update project config
35a842a Merge pull request #9 from CoralShades/Epic8
```

Key observations:
- E1-S16, S17, S18 are all implemented and committed - orchestrator can rely on their APIs
- E1-S19 is ready-for-dev but NOT implemented yet - orchestrator should handle None document_metadata
- The pipeline in `acm_extraction.py` has been updated 4 times recently (S15, S16, S17, S18) - watch for merge conflicts
- Pattern: each story added one node and one edge - S20 adds one node but changes the edge topology (conditional)

### Previous Story Intelligence (E1-S18, E1-S17)

Key learnings from predecessor stories:
- **Graph wiring is straightforward**: Adding nodes and edges to the LangGraph StateGraph is well-tested and reliable.
- **ExtractionState extension is minimal**: Each story adds one Optional field, initializes to None. Follow the same pattern.
- **Heuristic fallback is critical**: Always provide a code path that works without LLM. The orchestrator's REGEX_ONLY strategy and legacy fallback path serve this purpose.
- **Test graph compilation**: Always verify the compiled graph has expected nodes and edges. Pattern from `test_document_structure.py`.
- **Batch processing worked well**: E1-S18 batch-processed pages 5 at a time. The orchestrator processes buildings in parallel with a similar concurrency concept.
- **Error isolation**: Each pipeline stage handles its own errors and returns None on failure. The orchestrator must similarly isolate per-building errors.

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
