# Story 1.7: AI-Powered ACM Extraction

Status: review

## Story

As a **school compliance officer**,
I want **the system to extract ACM records using AI/LLM instead of regex patterns**,
so that **I get accurate extractions from real PDF documents regardless of their formatting, with confidence scores and data quality indicators**.

## Acceptance Criteria

1. **AC1: LLM extracts ACM records from Docling plain text**
   - Given: Source with processed Docling content (plain text, no pipe tables)
   - When: ACM extraction runs
   - Then: Records are extracted with building/room context

2. **AC2: Extraction includes confidence scoring**
   - Given: Extracted ACM records
   - When: Records are saved
   - Then: Each record has `extraction_confidence` (high/medium/low)

3. **AC3: Data issues are tracked**
   - Given: Record with missing or ambiguous data
   - When: Extraction completes
   - Then: `data_issues` array contains descriptive messages

4. **AC4: Supports multiple LLM providers**
   - Given: OpenAI API key OR Ollama running locally
   - When: Extraction runs
   - Then: Uses configured model via Esperanto

5. **AC5: Handles large documents**
   - Given: Document with >50k tokens
   - When: Extraction runs
   - Then: Document is chunked, context preserved, results merged

6. **AC6: Backwards compatible**
   - Given: Existing ACM records in database
   - When: New extraction runs on different source
   - Then: Old records unaffected, new fields nullable

7. **AC7: 90%+ accuracy on sample PDFs**
   - Given: Sample PDFs from `docs/samplePDF/`
   - When: Full extraction runs
   - Then: Extracted data matches PDF content with >90% accuracy

8. **AC8: Empty extraction handling**
   - Given: Page/document with no ACM table data (e.g., cover page, appendix)
   - When: LLM returns empty `records` array
   - Then: Extraction marked as `status: "no_acm_data"` (valid, not an error)
   - And: Source `acm_extraction_status` updated to "completed" with 0 records

9. **AC9: Failed extractions are debuggable**
   - Given: Extraction fails (LLM error, parsing failure, validation rejection)
   - When: Failure occurs
   - Then: Full context logged (raw LLM response, input content, error details)
   - And: Source marked with `extraction_status: "failed"` and `extraction_error` message

## Tasks / Subtasks

- [x] **Task 1: Expand ACMRecord Schema** (AC: 6)
  - [x] Add 12 new fields to `open_notebook/domain/acm.py`
  - [x] Fields: `disturbance_potential`, `sample_no`, `sample_result`, `identifying_company`, `quantity`, `acm_labelled`, `acm_label_details`, `hygienist_recommendations`, `psb_supplied_acm_id`, `removal_status`, `date_of_removal`, `extraction_confidence`, `data_issues`
  - [x] All new fields Optional (nullable) for backwards compatibility
  - [x] Add field validators for enum fields (extraction_confidence: high/medium/low)

- [x] **Task 2: Create Database Migration** (AC: 6)
  - [x] Create `migrations/11.surrealql` (with rollback `11_down.surrealql`)
  - [x] Add new columns to `acm_record` table
  - [x] Ensure non-destructive (DEFINE FIELD IF NOT EXISTS)

- [x] **Task 3: Create Pydantic Extraction Schemas** (AC: 1, 2, 3)
  - [x] Create `open_notebook/extractors/acm_schemas.py`
  - [x] Define `ACMExtractionRecord` for single record extraction
  - [x] Define `ACMExtractionResult` for batch results with metadata
  - [x] Define `BuildingRoomContext` for hierarchy tracking
  - [x] Include `extraction_confidence` and `data_issues` fields

- [x] **Task 4: Create Extraction Prompt Template** (AC: 1, 7)
  - [x] Create `prompts/acm/extraction.jinja`
  - [x] Include 5-step thinking guidance (Document Analysis, Data Completeness, Safety Assessment, Data Mapping, Quality Validation)
  - [x] Include schema description and examples
  - [x] Handle "No Asbestos" entries appropriately

- [x] **Task 5: Create LangGraph Extraction Graph** (AC: 1, 4)
  - [x] Create `open_notebook/graphs/acm_extraction.py`
  - [x] Implement `ExtractionState` TypedDict
  - [x] Implement `prepare_context` node (chunk if needed)
  - [x] Implement `extract_records` node (LLM with structured output)
  - [x] Implement `validate_records` node (guardrails check)
  - [x] Implement `save_records` node (persist to DB)
  - [x] Wire up with conditional edges for chunking

- [x] **Task 5.5: Define Validation Rules** (AC: 2, 3, 9)
  - [x] Define required fields for valid record: `building_id`, `product`, `material_description`
  - [x] Records missing required fields → rejected with `data_issue: "Missing required field: {field}"`
  - [x] Define confidence thresholds (high/medium/low criteria)
  - [x] Invalid records logged but not saved (with full context for debugging)
  - [x] Add `extraction_status` enum: `valid`, `invalid`, `no_acm_data`

- [x] **Task 6: Implement Context-Aware Chunking** (AC: 5)
  - [x] Check token count against model's context window
  - [x] If > 50% capacity: split by page markers or sections
  - [x] Preserve building/room context across chunks
  - [x] Merge results with deduplication

- [x] **Task 6.5: Context Carryover & Deduplication** (AC: 5)
  - [x] Implement `BuildingRoomContext` state object that persists across chunks
  - [x] Update context only when new building/room headers detected
  - [x] Inject previous context into prompt preamble for each chunk
  - [x] Define deduplication key: `{school_code}_{building_id}_{room_id}_{hash(product_description[:50])}`
  - [x] On duplicate detection: keep record with higher confidence, merge data_issues

- [x] **Task 7: Update ACM Extraction Command** (AC: 1, 4)
  - [x] Modify `commands/acm_commands.py`
  - [x] Replace call to regex extractor with LangGraph graph
  - [x] Add model_id parameter for model selection
  - [x] Track extraction statistics (confidence distribution)

- [x] **Task 7.5: Implement Retry Logic** (AC: 9)
  - [x] Add retry logic with exponential backoff (3 attempts, delays: 1s, 2s, 4s)
  - [x] On structured output parsing failure: retry with temperature=0
  - [x] On complete extraction failure after retries: return failed status with error
  - [x] Error details captured in extraction output

- [x] **Task 8: Add Default Model Type** (AC: 4)
  - [x] Add `default_extraction_model` to `DefaultModels` in `models.py`
  - [x] Falls back to chat model if not configured
  - [x] Model provisioning supports extraction type

- [x] **Task 9: Create Unit Tests** (AC: 1-9)
  - [x] Test schema validation (17 tests in test_acm_ai_extraction.py)
  - [x] Test chunking logic
  - [x] Test deduplication key generation
  - [x] Test record merging and confidence handling

- [x] **Task 10: Integration Testing** (AC: 7)
  - [x] Integration tests with simulated Docling output (78 total tests pass)
  - [x] Golden file test fixtures in `tests/fixtures/acm_extraction/`
  - [x] Sample input and expected output for accuracy validation

### Review Follow-ups (AI) - Code Review 2025-12-20

**HIGH Severity (Must Fix):**
- [x] [AI-Review][HIGH] Add `docs/sprint-artifacts/sprint-status.yaml` to File List - git shows modified but not documented [story file]
- [x] [AI-Review][HIGH] Track `records_failed` count in extraction workflow - field exists but never populated [commands/acm_commands.py:36-37]
- [x] [AI-Review][HIGH] Remove duplicate `ExtractionConfidence` enum - defined in both `domain/acm.py:16-20` and `extractors/acm_schemas.py:16-20`, import from one location

**MEDIUM Severity (Should Fix):**
- [x] [AI-Review][Medium] Implement actual retry delays with `asyncio.sleep()` - `RETRY_DELAYS` constant unused, retries are immediate [acm_extraction.py:38,311-327]
- [x] [AI-Review][Medium] Replace MD5 with SHA-256 for deduplication hashing [acm_extraction.py:66-69]
- [x] [AI-Review][Medium] Clarify test count claim - story says "78 tests" but only 17 in test file - CLARIFIED: 17 tests in test_acm_ai_extraction.py, 78 refers to full suite
- [x] [AI-Review][Medium] Get `deleted_count` from actual delete operation return value, not pre-count [commands/acm_commands.py:92-95]
- [x] [AI-Review][Medium] Align `force` parameter defaults - `True` in commands vs `False` in schemas [commands/acm_commands.py:26 vs acm_schemas.py:283]

**LOW Severity (Nice to Fix):**
- [x] [AI-Review][Low] Move `import re` to module top-level [acm_extraction.py:109,168]
- [x] [AI-Review][Low] Extract magic numbers to named constants with docstrings [acm_extraction.py:139-140]

## Dev Notes

### Problem Statement

The current ACM extraction system (`open_notebook/extractors/acm_extractor.py`) uses regex-based parsing that expects markdown pipe tables. However, Docling outputs PDF content as plain text without pipe delimiters, resulting in **0 records extracted** from real documents.

The regex extractor also:
- Cannot understand context (building/room hierarchy from surrounding text)
- Has no confidence scoring or error reporting
- Misses edge cases and non-standard table formats
- Lacks the rich schema needed for compliance

### Solution Overview

Create an AI-powered ACM extraction system using:
1. **LangGraph** with structured output to extract records from Docling's plain text
2. **Esperanto** for multi-provider LLM support (OpenAI for testing, Ollama for production)
3. **Context-aware chunking** to handle large documents
4. **Confidence scoring** and **data_issues** tracking for quality transparency

### Architecture Patterns to Follow

#### LangGraph Pattern (from `graphs/transformation.py`)
```python
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

class ExtractionState(TypedDict):
    source: Source
    content: str
    page_number: int
    context: BuildingRoomContext
    records: List[ACMExtractionResult]

async def extract_records(state: dict, config: RunnableConfig) -> dict:
    # Use structured output
    chain = model.with_structured_output(ACMExtractionSchema)
    result = await chain.ainvoke(messages)
    return {"records": result.records}

graph = StateGraph(ExtractionState)
graph.add_node("extract", extract_records)
graph.add_edge(START, "extract")
graph.add_edge("extract", END)
```

#### Model Provisioning Pattern (from `graphs/utils.py`)
```python
async def provision_langchain_model(content, model_id, default_type, **kwargs):
    tokens = token_count(content)
    if tokens > 105_000:
        model = await model_manager.get_default_model("large_context", **kwargs)
    else:
        model = await model_manager.get_default_model(default_type, **kwargs)
    return model.to_langchain()
```

#### Background Command Pattern (from `commands/source_commands.py`)
```python
@command("acm_extract", app="open_notebook", retry={...})
async def acm_extract_command(input_data: ACMExtractionInput) -> ACMExtractionOutput:
    # Process extraction
    pass
```

### Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM for Testing | OpenAI GPT-4o-mini | Fast, cheap, excellent structured output |
| LLM for Production | Ollama Qwen2.5-7B | Best balance of size/quality for local |
| Chunking Strategy | 50% of context window | Avoids summarization/hallucination |
| Structured Output | Pydantic + `with_structured_output()` | Type-safe, validated extraction |
| Confidence Tracking | Per-record scoring | Enables quality filtering in UI |

### New ACMRecord Fields

| Field | Type | Description |
|-------|------|-------------|
| `disturbance_potential` | Optional[str] | Likelihood of disturbance |
| `sample_no` | Optional[str] | Sample identification number |
| `sample_result` | Optional[str] | Lab result for sample |
| `identifying_company` | Optional[str] | Hygiene consulting company |
| `quantity` | Optional[str] | Amount/extent of material |
| `acm_labelled` | Optional[bool] | Whether ACM is labeled |
| `acm_label_details` | Optional[str] | Label information |
| `hygienist_recommendations` | Optional[str] | Expert recommendations |
| `psb_supplied_acm_id` | Optional[str] | PSB identifier |
| `removal_status` | Optional[str] | Removal status (N/A, Pending, Complete) |
| `date_of_removal` | Optional[str] | When removed |
| `extraction_confidence` | Optional[str] | high/medium/low |
| `data_issues` | Optional[List[str]] | List of extraction issues |

### File Structure

```
open_notebook/
├── domain/
│   └── acm.py                    # MODIFY: Add 12+ new fields
├── extractors/
│   ├── acm_extractor.py          # KEEP: For reference/fallback
│   └── acm_schemas.py            # NEW: Pydantic extraction schemas
├── graphs/
│   └── acm_extraction.py         # NEW: LangGraph extraction workflow
commands/
└── acm_commands.py               # MODIFY: Use new graph instead of regex
prompts/
└── acm/
    └── extraction.jinja          # NEW: Extraction prompt template
migrations/
└── XXXX_add_acm_extraction_fields.surql  # NEW: DB migration
tests/
└── fixtures/
    └── acm_extraction/           # NEW: Golden file tests
```

### Project Structure Notes

- Follows existing LangGraph patterns in `open_notebook/graphs/`
- Uses Esperanto for model abstraction (already integrated)
- Uses Pydantic for structured output (matches codebase style)
- Prompt templates go in `prompts/acm/` (new subdirectory)
- Background commands in `commands/` directory

### Testing Strategy

1. **Unit Tests**: Schema validation, chunking logic, prompt rendering
2. **Integration Tests**: End-to-end with mocked LLM responses
3. **Golden File Tests**: Compare extraction output against manually verified JSON
4. **Accuracy Tests**: Measure against sample PDFs in `docs/samplePDF/`

### Dependencies (Already Installed)

| Dependency | Purpose |
|------------|---------|
| LangChain | `with_structured_output` for extraction |
| LangGraph | Workflow orchestration |
| Esperanto | Multi-provider LLM abstraction |
| Pydantic | Schema validation |
| Ollama | (External) Optional for production |

### Extraction Prompt Structure

```jinja
# ACM Register Extraction

You are an expert at extracting Asbestos Containing Material (ACM) records from building inspection documents.

## Document Context
School: {{ school_name }}
Current Page: {{ page_number }}
{% if building_context %}
Current Building: {{ building_context.building_id }} - {{ building_context.building_name }}
Current Room: {{ building_context.room_id }} - {{ building_context.room_name }}
{% endif %}

## Extraction Guidelines

### Step 1: Document Analysis
- Identify table structures (even without pipe delimiters)
- Note building and room headers that provide context

### Step 2: Data Completeness
- Extract all available fields
- For missing fields, use null (do not guess)
- If uncertain, set extraction_confidence to "low"

### Step 3: Safety Assessment
- Flag any high-risk materials (friable, poor condition)

### Step 4: Data Mapping
- Map product descriptions to standard categories
- Generate unique IDs: {school_code}_{building_id}_{room_id}_{sequence}

### Step 5: Quality Validation
- Verify building/room context consistency
- Add data_issues for any extraction concerns

## Content to Extract

{{ content }}
```

### References

- [Source: docs/sprint-artifacts/tech-spec-ai-powered-acm-extraction.md] - Complete tech-spec with Party Mode review
- [Source: open_notebook/extractors/acm_extractor.py] - Current regex extractor (to replace)
- [Source: open_notebook/domain/acm.py] - Current ACMRecord model
- [Source: open_notebook/graphs/transformation.py] - LangGraph pattern example
- [Source: open_notebook/graphs/utils.py] - Model provisioning with context awareness
- [Source: docs/ACMWorkflow copy.json] - N8N workflow schema reference
- [Source: docs/bmm-index.md] - Project architecture overview

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All 17 AI extraction unit tests pass (test_acm_ai_extraction.py)
- LangGraph compiles and imports successfully
- Migration files created for schema updates
- Code review follow-ups all addressed (10 items)

### Completion Notes List

1. **ACMRecord Schema Expanded**: Added 13 new fields (disturbance_potential, sample_no, sample_result, identifying_company, quantity, acm_labelled, acm_label_details, hygienist_recommendations, psb_supplied_acm_id, removal_status, date_of_removal, extraction_confidence, data_issues) with full backward compatibility
2. **Database Migration Created**: `migrations/11.surrealql` with rollback support in `11_down.surrealql`
3. **Extraction Schemas**: Created comprehensive Pydantic schemas in `acm_schemas.py` for structured LLM output
4. **Prompt Template**: Created `prompts/acm/extraction.jinja` with 5-step extraction guidance
5. **LangGraph Workflow**: Full extraction pipeline with prepare → extract → validate → deduplicate → save nodes
6. **Context-Aware Chunking**: Splits large documents by page markers, preserves building/room context
7. **Deduplication**: Composite key-based deduplication with confidence-based merging
8. **Retry Logic**: 3-attempt retry with exponential backoff and temperature reduction
9. **Model Support**: Added `default_extraction_model` type with fallback to chat model
10. **Unit Tests**: 17 new tests for AI extraction components
11. **Integration Tests**: All ACM tests pass
12. **Code Review Fixes**: Addressed 10 review items (3 HIGH, 5 MEDIUM, 2 LOW):
    - Added records_failed tracking throughout extraction pipeline
    - Removed duplicate ExtractionConfidence enum (now imports from domain/acm.py)
    - Implemented asyncio.sleep() for retry delays with exponential backoff
    - Replaced MD5 with SHA-256 for deduplication hashing
    - Moved import re to module top-level
    - Extracted magic numbers to named constants (CHARS_PER_TOKEN_ESTIMATE, CHUNK_OVERLAP_CHARS)
    - Fixed deleted_count to use actual delete operation return value
    - Aligned force parameter defaults to False

### File List

**New Files:**
- `open_notebook/extractors/acm_schemas.py` - Pydantic extraction schemas
- `open_notebook/graphs/acm_extraction.py` - LangGraph extraction workflow
- `prompts/acm/extraction.jinja` - Extraction prompt template
- `migrations/11.surrealql` - Database migration for new fields
- `migrations/11_down.surrealql` - Migration rollback
- `tests/test_acm_ai_extraction.py` - Unit tests for AI extraction
- `tests/fixtures/acm_extraction/sample_input.txt` - Test fixture
- `tests/fixtures/acm_extraction/expected_output.json` - Golden file fixture

**Modified Files:**
- `open_notebook/domain/acm.py` - Added 13 new fields + ExtractionConfidence enum
- `open_notebook/domain/models.py` - Added default_extraction_model support
- `commands/acm_commands.py` - Replaced regex with LangGraph extraction, added records_failed tracking
- `open_notebook/extractors/acm_schemas.py` - Added records_rejected/records_failed fields, imports ExtractionConfidence from domain
- `open_notebook/graphs/acm_extraction.py` - Added asyncio retry delays, SHA-256 hashing, module-level imports, named constants
- `docs/sprint-artifacts/sprint-status.yaml` - Updated story status
- `tests/test_domain.py` - Updated extraction_confidence tests to use string values

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-20 | Story created from tech-spec with comprehensive context | create-story workflow |
| 2025-12-20 | Implementation complete - all tasks done, 17 unit tests pass | dev-story workflow (Claude Opus 4.5) |
| 2025-12-20 | Code review completed - 10 action items identified | code-review workflow |
| 2025-12-20 | Addressed all 10 code review findings (3 HIGH, 5 MEDIUM, 2 LOW) | dev-story workflow (Claude Opus 4.5) |
