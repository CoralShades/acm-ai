# Story 1.17: Building Inventory Compilation

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **system**,
I want **to compile a complete building inventory with page locations from the document structure**,
so that **extraction can target specific page ranges per building for higher accuracy and create processing groups for efficient batched extraction**.

## Acceptance Criteria

1. **AC-1: Building ID Detection** - Identify all building codes from document content: B000-series (standard buildings, e.g. B00A, B00B), D-series (demountables, e.g. D01, D02)
2. **AC-2: Building Metadata Extraction** - Extract building metadata: name, year built, construction type, purpose/use, area (m2), levels
3. **AC-3: Page Range Mapping** - Map each building to its document page range (start page, end page)
4. **AC-4: Building Complexity Classification** - Classify each building's complexity: `simple` ("No Asbestos" / few items) vs `complex` (full register with multiple rooms)
5. **AC-5: Processing Groups** - Create processing groups of 3-5 pages based on building complexity for efficient batched extraction
6. **AC-6: Pydantic Model Output** - Output a `BuildingInventory` Pydantic model with `BuildingMeta` entries containing all extracted metadata
7. **AC-7: Multi-Page Buildings** - Handle buildings spanning multiple pages correctly (page_end > page_start)
8. **AC-8: Room Code Detection** - Detect room codes (R000-series, e.g. B00A-R0001) within each building

## Tasks / Subtasks

- [x] Task 1: Create `BuildingInventory` Pydantic models (AC: #6, #4)
  - [x] 1.1 Define `BuildingComplexity` enum (simple, complex)
  - [x] 1.2 Define `RoomMeta` model with room_id, name, area_m2, page
  - [x] 1.3 Define `BuildingMeta` model with building_id, name, year, construction, purpose, area_m2, levels, page_start, page_end, complexity, rooms list, acm_item_count_estimate
  - [x] 1.4 Define `ProcessingGroup` model with group_id, building_ids, page_start, page_end, estimated_pages
  - [x] 1.5 Define `BuildingInventory` model aggregating buildings list, processing_groups, total_buildings, document_type (from E1-S16)
- [x] Task 2: Create `building_inventory.jinja` prompt template (AC: #1, #2, #3, #4)
  - [x] 2.1 Define structured output format matching BuildingInventory Pydantic model
  - [x] 2.2 Include building ID detection instructions (B000-series, D-series for demountables)
  - [x] 2.3 Include room code detection instructions (R000-series within buildings)
  - [x] 2.4 Include complexity classification heuristics (simple: "No Asbestos" keyword or <3 items; complex: multiple rooms/items)
  - [x] 2.5 Include page range extraction instructions using page markers
  - [x] 2.6 Include building metadata extraction guidance (year, construction, area from building header rows)
- [x] Task 3: Implement `compile_building_inventory()` function (AC: #1-5, #7, #8)
  - [x] 3.1 Create `open_notebook/extractors/building_inventory.py` with extraction logic
  - [x] 3.2 Accept `content: str` and `document_structure: Optional[DocumentStructure]` as inputs
  - [x] 3.3 Use LLM with `with_structured_output(BuildingInventory)` for building analysis
  - [x] 3.4 Integrate DocumentStructure data: use `building_ids` and `register_start_page` to focus analysis on register content only
  - [x] 3.5 Implement heuristic fallback using custom regex patterns (own _BUILDING_HEADER/_ROOM_HEADER instead of importing acm_extractor patterns due to overlap)
  - [x] 3.6 Create processing groups from building list: group buildings by page proximity, target 3-5 pages per group
- [x] Task 4: Integrate into LangGraph extraction pipeline (AC: all)
  - [x] 4.1 Add `building_inventory: Optional[BuildingInventory]` to `ExtractionState` TypedDict
  - [x] 4.2 Create `compile_inventory()` LangGraph node function
  - [x] 4.3 Wire new node after structure: `START -> structure -> inventory -> prepare_context -> ...`
  - [x] 4.4 Pass `document_structure` from state into `compile_building_inventory()`
  - [x] 4.5 Graceful fallback: if inventory compilation fails, continue pipeline with None (backward compatible)
- [x] Task 5: Write comprehensive tests (AC: #1-8)
  - [x] 5.1 Create `tests/test_building_inventory.py` with class-based test organization
  - [x] 5.2 Test Pydantic model creation: BuildingMeta, RoomMeta, ProcessingGroup, BuildingInventory
  - [x] 5.3 Test building ID detection from inline markdown with B000 and D-series codes
  - [x] 5.4 Test room code detection (R000-series within building context)
  - [x] 5.5 Test page range extraction from page markers
  - [x] 5.6 Test complexity classification (simple vs complex buildings)
  - [x] 5.7 Test processing group generation (groups of 3-5 pages)
  - [x] 5.8 Test heuristic fallback (regex-based when LLM unavailable)
  - [x] 5.9 Test LangGraph node integration (node runs after structure, before prepare_context)
  - [x] 5.10 Test with empty content and missing DocumentStructure (graceful handling)
- [x] Task 6: Verification
  - [x] 6.1 Run `uv run ruff check .` - lint passes (auto-fixed import sorting)
  - [x] 6.2 Run `uv run pytest tests/test_building_inventory.py -v` - all 42 tests pass
  - [x] 6.3 Run `uv run pytest tests/` - 608 pass, 5 pre-existing failures only, 1 E1-S16 test updated for new graph wiring

## Dev Notes

### Architecture & Design

**Pipeline Position: Stage -1.5 (Between Structure and Per-Building Extraction)**

This story adds a new LangGraph node that runs AFTER `extract_document_structure` (E1-S16) and BEFORE `prepare_context`. It uses the DocumentStructure output to compile a building-level inventory.

```
CURRENT:  START -> structure -> prepare_context -> extract_records -> validate -> correct -> deduplicate -> save
WITH S17: START -> structure -> compile_inventory -> prepare_context -> extract_records -> validate -> correct -> deduplicate -> save
                               ^ NEW Stage -1.5
```

**Critical Design Decisions:**
- `BuildingInventory` is a **transient Pydantic model** (in-memory pipeline state), NOT a database table
- **No migration needed** - data flows through `ExtractionState` TypedDict only
- **One LLM call per document** for building compilation (efficient - operates on register section only, ~10-30 pages)
- **Uses E1-S16 output** - `DocumentStructure.building_ids` provides initial building list, `register_start_page` trims content
- **Backward compatible** - if `building_inventory` is None (failed or skipped), pipeline continues without per-building targeting
- **Prepares for future** - processing groups enable targeted extraction per building range (not wired in this story, but available for E1-S18/E1-S20)

**Building Header Pattern (from existing codebase):**
```python
# From acm_extractor.py - ALREADY ESTABLISHED patterns
BUILDING_PATTERN = r"^([A-Z]\d+[A-Z]?)\s*[-\u2013]\s*(.+?)(?:\s*[-\u2013]\s*(\d{4}))?$"
# Matches: "B00A - Other-Dse Admin - 1924"
# Groups: (1) building_id, (2) name, (3) year

ROOM_PATTERN = r"^([A-Z]\d+[A-Z]?-R\d+)\s*[-\u2013]\s*(.+?)(?:\s*[-\u2013]\s*([\d.]+)\s*m\u00b2)?$"
# Matches: "B00A-R0001 - External Movement" or "B00A-R0001 - Office Area - 32.5 m2"
# Groups: (1) room_id, (2) name, (3) area_m2
```

These regex patterns are defined in `open_notebook/extractors/acm_extractor.py` lines 32-51. **Reuse them** - do NOT duplicate.

### Key Source Files to Study Before Implementation

| File | What to Learn | Key Patterns |
|------|---------------|--------------|
| `open_notebook/extractors/document_structure.py` | E1-S16 Pydantic models (`DocumentStructure`, `DocumentType`), `_heuristic_fallback()`, `extract_document_structure()` function signature | Full file - direct predecessor |
| `open_notebook/graphs/acm_extraction.py` | LangGraph pipeline, `ExtractionState` TypedDict, graph wiring, node function signatures | L184-220 (state), L1136-1168 (graph), L399-443 (prepare_context) |
| `open_notebook/extractors/acm_extractor.py` | BUILDING_PATTERN, ROOM_PATTERN regex patterns, `ParseContext` dataclass | L32-51 (patterns), L60-102 (register detection) |
| `prompts/acm/structure_extraction.jinja` | Jinja template patterns for structured output, section taxonomy | Full file - template pattern to follow |
| `open_notebook/extractors/validators/acm_validator.py` | Pydantic `with_structured_output()` pattern, validation model design | Full file - output model pattern |

### Existing Code Patterns to Follow

1. **LangGraph Node Functions:** `async def node_name(state: dict, config: RunnableConfig) -> dict:` pattern from `acm_extraction.py`
2. **Structured LLM Output:** Use `model.with_structured_output(PydanticModel)` established in E1-S7, E1-S15, E1-S16
3. **Prompt Loading:** Use `ai_prompter.render("acm/building_inventory", **context)` pattern from `acm_extraction.py`
4. **State Extension:** Add new Optional fields to `ExtractionState` TypedDict (pattern from E1-S15, E1-S16)
5. **Test Organization:** Class-based tests with inline markdown data (pattern from `test_document_structure.py`, `test_acm_validator.py`)
6. **Error Handling:** Catch exceptions, log warnings, return None in state, continue pipeline (pattern from `extract_structure` node in E1-S16)
7. **Heuristic Fallback:** Implement regex-based fallback alongside LLM extraction (pattern from `document_structure.py:_heuristic_fallback()`)
8. **Import Organization:** Group imports by stdlib, third-party, local project following PEP 8 (ruff will check this)

### Integration Points with Existing Code

**`document_structure.py` (E1-S16 output):**
- `DocumentStructure.building_ids: List[str]` - provides initial building ID list (may be incomplete for heuristic extractions)
- `DocumentStructure.register_start_page: Optional[int]` - trim content to register section only
- `DocumentStructure.total_pages: int` - use for page range validation
- `DocumentStructure.sections: List[Section]` - section 4 (Asbestos Register) contains target pages

**`acm_extractor.py` (established patterns):**
- Import and reuse `BUILDING_PATTERN`, `ROOM_PATTERN` regex constants
- Do NOT redefine these patterns - import from `acm_extractor.py`
- `ParseContext` dataclass shows how building/room context is tracked during extraction

**`prepare_context()` node (acm_extraction.py):**
- Currently uses `register_start_page` from DocumentStructure to trim content
- With BuildingInventory, future stories (E1-S20) can pass per-building page ranges for targeted extraction
- This story does NOT modify `prepare_context()` - only adds inventory data to state

**`ExtractionState` TypedDict (acm_extraction.py):**
- Current state fields include: `content`, `source_id`, `model_id`, `records`, `document_structure`, `correction_attempt`, `correction_stats`
- Add: `building_inventory: Optional[BuildingInventory]`
- Initialize as `None` in the graph invocation in `extract_acm_from_source()`

### Processing Group Algorithm

Groups should target 3-5 pages per group for optimal LLM context window usage:

```
Algorithm:
1. Sort buildings by page_start ascending
2. Initialize current_group with first building
3. For each subsequent building:
   a. If adding this building keeps group_pages <= 5: add to current group
   b. Else: finalize current group, start new group with this building
4. Finalize last group
5. Simple (no-asbestos) buildings can be grouped together regardless of page proximity
```

### Project Structure Notes

- **New file locations align with existing structure:**
  - `open_notebook/extractors/building_inventory.py` - alongside `document_structure.py`, `acm_extractor.py`
  - `prompts/acm/building_inventory.jinja` - alongside `structure_extraction.jinja`, `extraction.jinja`
  - `tests/test_building_inventory.py` - alongside `test_document_structure.py`, `test_acm_extractor.py`
- **No new dependencies required** - uses existing LangChain/LangGraph, Pydantic, Jinja2
- **No migration required** - BuildingInventory is transient pipeline state
- **Reuse regex imports** from `acm_extractor.py` - do not duplicate BUILDING_PATTERN/ROOM_PATTERN

### References

- [Source: _bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md#E1-S17] Story definition and acceptance criteria
- [Source: _bmad-output/project-planning-artifacts/acm-ai/04-architecture.md#5.1] Two-Stage Pipeline Architecture
- [Source: _bmad-output/sprint-change-proposal-20260207-workflow-extraction.md] Original proposal adding E1-S17
- [Source: open_notebook/extractors/document_structure.py] E1-S16 DocumentStructure models and extraction
- [Source: open_notebook/graphs/acm_extraction.py] Current LangGraph extraction pipeline
- [Source: open_notebook/extractors/acm_extractor.py] BUILDING_PATTERN, ROOM_PATTERN regex patterns
- [Source: _bmad-output/implementation-artifacts/e1-s16-document-structure-toc-extraction.md] Predecessor story implementation details

### Dependencies

| Direction | Story | Relationship |
|-----------|-------|-------------|
| Depends on | E1-S16 (Document Structure & TOC) | Uses DocumentStructure output (REVIEW - implementation complete) |
| Depends on | E1-S3 (Two-Stage Pipeline) | Pipeline infrastructure exists (DONE) |
| Blocks | E1-S18 (Page-Level Section Tagging) | Needs building page ranges for section-aware tagging |
| Blocks | E1-S20 (Agentic Extraction Orchestrator) | Uses processing groups for per-building extraction |

### Git Intelligence (Recent Commits)

Last 5 commits on main:
```
35a842a Merge pull request #9 from CoralShades/Epic8
28483ca chore: remove junk nul file and root package-lock.json
380c943 fix(e14): apply code review fixes across Epic 14 stories
e305371 fix(e14): add missing settings subroute pages and /models redirect
7b7dd00 docs: apply course correction - generic configurable parser + sprint planning
```

Key observations:
- E1-S16 (predecessor) is implemented and in review status (working directory changes)
- E1-S11, E1-S14, E1-S15 also in review with unstaged changes
- **Caution:** Working directory has many unstaged changes - ensure no conflicts when modifying `acm_extraction.py`
- Pattern to follow: E1-S16's implementation style for new LangGraph node + Pydantic models

### Previous Story Intelligence (E1-S16)

Key learnings from predecessor story that apply to E1-S17:
- **Single LLM call per document** is efficient and reliable for structure analysis
- **Heuristic fallback** with regex patterns provides reliability when LLM is unavailable
- **Transient Pydantic models** (not DB tables) work well for pipeline state
- **Graph wiring** follows pattern: add node to state, create async node function, wire into graph
- **37 tests** were written for E1-S16 - aim for similar coverage (30+ tests)
- **`_extract_total_pages()` helper** already exists in `document_structure.py` - reuse for page marker parsing
- **Content trimming** using `register_start_page` in `prepare_context()` is already implemented - E1-S17 should focus on building-level page ranges within the register section

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Custom `_BUILDING_HEADER` and `_ROOM_HEADER` regex patterns were needed instead of importing from `acm_extractor.py` because the existing `BUILDING_PATTERN` and `ROOM_PATTERN` are designed for line-by-line parsing and match room headers as buildings (and vice versa). The new patterns use `\s+[-–]\s+` (space-dash-space) for buildings vs `-R####` prefix requirement for rooms.
- `_find_page_end()` was refined to use room page data and check for actual content after page markers, avoiding counting trailing page markers that belong to the next building.
- `_classify_complexity()` uses building-level "No Asbestos" markers only (not individual row "Not Detected" entries) to correctly distinguish simple vs complex buildings.

### Completion Notes List

- Task 1: Created 5 Pydantic models (BuildingComplexity, RoomMeta, BuildingMeta, ProcessingGroup, BuildingInventory) as transient pipeline state (no DB migration needed)
- Task 2: Created `building_inventory.jinja` prompt template with B/D-series building detection, R-series room detection, complexity heuristics, page range extraction, and processing group instructions
- Task 3: Implemented `compile_building_inventory()` with LLM structured output + heuristic regex fallback, `_trim_to_register()` for DocumentStructure integration, and `_create_processing_groups()` targeting 3-5 pages per group
- Task 4: Wired `compile_inventory` LangGraph node between structure and prepare: `START -> structure -> inventory -> prepare -> ...`, added `building_inventory: Optional[BuildingInventory]` to ExtractionState, initialized as None
- Task 5: 42 comprehensive tests across 6 test classes covering all acceptance criteria
- Task 6: Lint passes, all 42 E1-S17 tests pass, 608/614 full suite pass (5 pre-existing failures unrelated to E1-S17), 1 E1-S16 test updated for new graph wiring

### Change Log

- 2026-02-09: E1-S17 Building Inventory Compilation implemented - 4 new files, 2 modified files, 42 tests

### File List

| File | Action | Purpose |
|------|--------|---------|
| `open_notebook/extractors/building_inventory.py` | CREATE | BuildingComplexity, RoomMeta, BuildingMeta, ProcessingGroup, BuildingInventory Pydantic models + compile_building_inventory() with LLM + heuristic fallback + processing groups |
| `prompts/acm/building_inventory.jinja` | CREATE | LLM prompt for building inventory compilation with page ranges, room detection, complexity classification |
| `open_notebook/graphs/acm_extraction.py` | MODIFY | Import BuildingInventory, add compile_inventory node, building_inventory to ExtractionState, graph wiring structure->inventory->prepare, initialize building_inventory=None |
| `tests/test_building_inventory.py` | CREATE | 42 tests: model creation, building/room detection, page ranges, complexity classification, processing groups, heuristic fallback, LLM mock, LangGraph integration |
| `tests/test_document_structure.py` | MODIFY | Updated test_graph_structure_before_prepare to expect structure->inventory->prepare wiring (E1-S17 inserts inventory node) |
| `docs/sprint-artifacts/sprint-status.yaml` | MODIFY | Update E1-S17 status: ready-for-dev -> in-progress -> review |

## Senior Developer Review (AI)

**Date:** 2026-02-09
**Reviewer:** Claude Opus 4.6 (adversarial code review)
**Verdict:** APPROVED

### Issues Found: 7 total (1 HIGH, 4 MEDIUM, 2 LOW)

#### HIGH (1) - Fixed
1. **Unused parameters in `_extract_rooms_from_section`** (`building_inventory.py:135`): `building_id` and `base_page` were accepted but never used. Removed both unused parameters and updated call site.

#### MEDIUM (4) - Fixed
2. **`acm_item_count_estimate` never populated by heuristic fallback** (`building_inventory.py:70,288`): Field existed on `BuildingMeta` but was always `None` from heuristic path. Fixed `_classify_complexity` to return `(complexity, acm_count)` tuple and populate the field. Added test `test_acm_item_count_estimate_populated`.
3. **Weak test assertion in `test_groups_target_3_to_5_pages`** (`test_building_inventory.py:401`): Only asserted `>= 1` which is trivially true. Strengthened to verify group count, page bounds, and B009 isolation.
4. **`test_graph_structure_to_inventory_edge` didn't verify edges** (`test_building_inventory.py:552`): Only checked node existence. Fixed to actually verify `("structure", "inventory")` edge via `agent_state.edges`.
5. **Misleading docstring in `_heuristic_fallback`** (`building_inventory.py:246`): Said "from acm_extractor.py" but uses custom patterns. Corrected to reference `_BUILDING_HEADER` / `_ROOM_HEADER`.

#### LOW (2) - Not fixed (acceptable)
6. **Code duplication with `prepare_context()` for register trimming**: `_trim_to_register` duplicates logic from `acm_extraction.py:527-538`. Acceptable since `_trim_to_register` is a clean extraction; `prepare_context` can be refactored in a future story.
7. **No test for 3+ page building span (AC-7 edge case)**: B00A test covers 2-page span. A 3+ page test would strengthen AC-7 coverage but is not strictly required since the algorithm is page-marker based.

### Acceptance Criteria Validation

| AC | Status | Evidence |
|----|--------|----------|
| AC-1: Building ID Detection | IMPLEMENTED | B000-series and D-series detected via `_BUILDING_HEADER` regex, tests confirm B00A/B00B/B009/D01 |
| AC-2: Building Metadata Extraction | IMPLEMENTED | name, year, construction extracted; purpose/area/levels supported via LLM path |
| AC-3: Page Range Mapping | IMPLEMENTED | `_find_page_at_position` + `_find_page_end` with room-aware accuracy |
| AC-4: Building Complexity Classification | IMPLEMENTED | `_classify_complexity` with no-asbestos markers, room count, ACM count |
| AC-5: Processing Groups | IMPLEMENTED | `_create_processing_groups` targets 3-5 pages, verified by strengthened tests |
| AC-6: Pydantic Model Output | IMPLEMENTED | BuildingInventory, BuildingMeta, RoomMeta, ProcessingGroup, BuildingComplexity |
| AC-7: Multi-Page Buildings | IMPLEMENTED | page_end > page_start tested for B00A (pages 10-11) |
| AC-8: Room Code Detection | IMPLEMENTED | `_ROOM_HEADER` regex detects R000-series, rooms extracted with page/area |

### Test Results
- **43 tests passed** (42 original + 1 new `test_acm_item_count_estimate_populated`)
- **0 failures**
- **Lint: clean** (ruff check passes)
- **Document structure tests: 37/37 pass** (no regressions)
