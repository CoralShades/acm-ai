# Tech-Spec: AI-Powered ACM Extraction

**Created:** 2025-12-20
**Status:** Ready for Development
**Epic:** E1 - ACM Data Extraction Pipeline
**Story:** Enhancement to E1-S3 - Replace regex-based extraction with LLM-powered approach

---

## Overview

### Problem Statement

The current ACM extraction system (`open_notebook/extractors/acm_extractor.py`) uses regex-based parsing that expects markdown pipe tables. However, Docling outputs PDF content as plain text without pipe delimiters, resulting in 0 records extracted from real documents.

Additionally, the current approach:
- Cannot understand context (building/room hierarchy from surrounding text)
- Has no confidence scoring or error reporting
- Misses edge cases and non-standard table formats
- Lacks the rich schema needed for compliance (removal status, hygienist recommendations, etc.)

### Solution

Create an AI-powered ACM extraction system that:
1. Uses LangGraph with structured output to extract records from Docling's plain text
2. Supports multiple LLM providers via Esperanto (OpenAI for testing, Ollama for production)
3. Understands document context to associate records with correct building/room hierarchy
4. Provides extraction confidence scoring and data issue tracking
5. Handles batch or page-by-page processing based on context size

### Scope

**In Scope:**
- New LangGraph-based extraction graph (`open_notebook/graphs/acm_extraction.py`)
- Expanded ACMRecord schema with 12 additional fields
- New extraction prompt template (`prompts/acm/extraction.jinja`)
- Context-aware chunking strategy (50% of model context window)
- Confidence scoring and data_issues tracking
- Database migration for new fields
- Update to `commands/acm_commands.py` to use new extractor

**Out of Scope:**
- Changes to Docling integration (content-core)
- Frontend changes (existing grid supports all fields)
- Real-time streaming extraction (batch only for now)

---

## Context for Development

### Codebase Patterns

#### 1. LangGraph Pattern (from `graphs/transformation.py`)
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

#### 2. Model Provisioning Pattern (from `graphs/utils.py`)
```python
async def provision_langchain_model(content, model_id, default_type, **kwargs):
    tokens = token_count(content)
    if tokens > 105_000:
        model = await model_manager.get_default_model("large_context", **kwargs)
    else:
        model = await model_manager.get_default_model(default_type, **kwargs)
    return model.to_langchain()
```

#### 3. Background Command Pattern (from `commands/source_commands.py`)
```python
@command("acm_extract", app="open_notebook", retry={...})
async def acm_extract_command(input_data: ACMExtractionInput) -> ACMExtractionOutput:
    # Process extraction
    pass
```

### Files to Reference

| File | Purpose |
|------|---------|
| `open_notebook/graphs/transformation.py` | LangGraph pattern example |
| `open_notebook/graphs/utils.py` | Model provisioning with context awareness |
| `open_notebook/domain/acm.py` | Current ACMRecord model |
| `commands/acm_commands.py` | Current extraction command |
| `open_notebook/extractors/acm_extractor.py` | Current regex-based extractor (to replace) |
| `prompts/ask/entry.jinja` | Example prompt template |
| `docs/ACMWorkflow copy.json` | N8N workflow schema reference |

### Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| LLM for Testing | OpenAI GPT-4o-mini | Fast, cheap, excellent structured output |
| LLM for Production | Ollama Qwen2.5-7B | Best balance of size/quality, good structured output support |
| Chunking Strategy | 50% of context window | Avoids summarization/hallucination, leaves room for output |
| Structured Output | Pydantic + `with_structured_output()` | Type-safe, validated extraction |
| Context Window Check | Per-page vs full-doc | Extract page-by-page if document exceeds threshold |
| Confidence Tracking | Per-record scoring | Enables quality filtering in UI |

---

## Implementation Plan

### Tasks

- [ ] **Task 1: Expand ACMRecord Schema**
  - Add 12 new fields to `open_notebook/domain/acm.py`
  - Fields: `disturbance_potential`, `sample_no`, `sample_result`, `identifying_company`, `quantity`, `acm_labelled`, `acm_label_details`, `hygienist_recommendations`, `psb_supplied_acm_id`, `removal_status`, `date_of_removal`, `extraction_confidence`, `data_issues`
  - All new fields Optional (nullable) for backwards compatibility
  - Add field validators for enum fields (extraction_confidence: high/medium/low)

- [ ] **Task 2: Create Database Migration**
  - Create `migrations/XXXX_add_acm_extraction_fields.surql`
  - Add new columns to `acm_record` table
  - Ensure non-destructive (ALTER TABLE ADD)

- [ ] **Task 3: Create Pydantic Extraction Schemas**
  - Create `open_notebook/extractors/acm_schemas.py`
  - Define `ACMExtractionRecord` for single record extraction
  - Define `ACMExtractionResult` for batch results with metadata
  - Define `BuildingRoomContext` for hierarchy tracking
  - Include `extraction_confidence` and `data_issues` fields

- [ ] **Task 4: Create Extraction Prompt Template**
  - Create `prompts/acm/extraction.jinja`
  - Include 5-step thinking guidance (from n8n workflow):
    1. Document Analysis Reflection
    2. Data Completeness Assessment
    3. Safety Assessment Thinking
    4. Data Mapping Strategy
    5. Quality Validation Planning
  - Include schema description and examples
  - Handle "No Asbestos" entries appropriately

- [ ] **Task 5: Create LangGraph Extraction Graph**
  - Create `open_notebook/graphs/acm_extraction.py`
  - Implement `ExtractionState` TypedDict
  - Implement `prepare_context` node (chunk if needed)
  - Implement `extract_records` node (LLM with structured output)
  - Implement `validate_records` node (guardrails check)
  - Implement `save_records` node (persist to DB)
  - Wire up with conditional edges for chunking

- [ ] **Task 5.5: Define Validation Rules** *(Added from review)*
  - Define required fields for valid record: `building_id`, `room_id`, `product_description`
  - Records missing required fields → rejected with `data_issue: "Missing required field: {field}"`
  - Define confidence thresholds:
    - `high`: All required fields present, clear source text
    - `medium`: Required fields present but some ambiguity
    - `low`: Required fields inferred from context, uncertain
  - Invalid records logged but not saved (with full context for debugging)
  - Add `extraction_status` enum: `valid`, `invalid`, `no_acm_data`

- [ ] **Task 6: Implement Context-Aware Chunking**
  - Check token count against model's context window
  - If > 50% capacity: split by page markers or sections
  - Preserve building/room context across chunks
  - Merge results with deduplication

- [ ] **Task 6.5: Context Carryover & Deduplication** *(Added from review)*
  - Implement `BuildingRoomContext` state object that persists across chunks:
    ```python
    class BuildingRoomContext(TypedDict):
        last_building_id: Optional[str]
        last_building_name: Optional[str]
        last_room_id: Optional[str]
        last_room_name: Optional[str]
        page_number: int
    ```
  - Update context only when new building/room headers detected in content
  - Inject previous context into prompt preamble for each chunk
  - Define deduplication key: `{school_code}_{building_id}_{room_id}_{hash(product_description[:50])}`
  - On duplicate detection: keep record with higher confidence, merge data_issues

- [ ] **Task 7: Update ACM Extraction Command**
  - Modify `commands/acm_commands.py`
  - Replace call to regex extractor with LangGraph graph
  - Add model_id parameter for model selection
  - Track extraction statistics (confidence distribution)

- [ ] **Task 7.5: Implement Retry Logic** *(Added from review)*
  - Add retry decorator with exponential backoff (3 attempts, 1s → 2s → 4s)
  - On structured output parsing failure:
    1. Log the raw LLM response for debugging
    2. Retry with same model (may be transient)
    3. If still failing, try with `temperature=0` for more deterministic output
  - On complete extraction failure after retries:
    - Mark source with `extraction_status: "failed"`
    - Store error details in `extraction_error` field
    - Do NOT save partial/invalid records
  - Future enhancement (E1-S3.1): Retry with fallback model

- [ ] **Task 8: Add Default Model Type**
  - Add `default_extraction_model` to `DefaultModels` in `models.py`
  - Configure OpenAI as default for testing
  - Document Ollama setup for production

- [ ] **Task 9: Create Unit Tests**
  - Test schema validation
  - Test chunking logic
  - Test prompt rendering
  - Mock LLM responses for deterministic testing

- [ ] **Task 10: Integration Testing**
  - Test with sample PDFs from `docs/samplePDF/`
  - Verify >90% accuracy on known documents
  - Test with both OpenAI and Ollama

### Acceptance Criteria

- [ ] **AC1**: LLM extracts ACM records from Docling plain text
  - Given: Source with processed Docling content (plain text, no pipe tables)
  - When: ACM extraction runs
  - Then: Records are extracted with building/room context

- [ ] **AC2**: Extraction includes confidence scoring
  - Given: Extracted ACM records
  - When: Records are saved
  - Then: Each record has `extraction_confidence` (high/medium/low)

- [ ] **AC3**: Data issues are tracked
  - Given: Record with missing or ambiguous data
  - When: Extraction completes
  - Then: `data_issues` array contains descriptive messages

- [ ] **AC4**: Supports multiple LLM providers
  - Given: OpenAI API key OR Ollama running locally
  - When: Extraction runs
  - Then: Uses configured model via Esperanto

- [ ] **AC5**: Handles large documents
  - Given: Document with >50k tokens
  - When: Extraction runs
  - Then: Document is chunked, context preserved, results merged

- [ ] **AC6**: Backwards compatible
  - Given: Existing ACM records in database
  - When: New extraction runs on different source
  - Then: Old records unaffected, new fields nullable

- [ ] **AC7**: 90%+ accuracy on sample PDFs
  - Given: Sample PDFs from `docs/samplePDF/`
  - When: Full extraction runs
  - Then: Extracted data matches PDF content with >90% accuracy

- [ ] **AC8**: Empty extraction handling *(Added from review)*
  - Given: Page/document with no ACM table data (e.g., cover page, appendix)
  - When: LLM returns empty `records` array
  - Then: Extraction marked as `status: "no_acm_data"` (valid, not an error)
  - And: Source `acm_extraction_status` updated to "completed" with 0 records
  - Note: Distinguished from extraction failure (which sets `status: "failed"`)

- [ ] **AC9**: Failed extractions are debuggable *(Added from review)*
  - Given: Extraction fails (LLM error, parsing failure, validation rejection)
  - When: Failure occurs
  - Then: Full context logged (raw LLM response, input content, error details)
  - And: Source marked with `extraction_status: "failed"` and `extraction_error` message

---

## Additional Context

### Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| LangChain | Library | Already installed, need `with_structured_output` |
| LangGraph | Library | Already installed |
| Esperanto | Library | Already integrated for model abstraction |
| Pydantic | Library | Already installed for schema validation |
| Ollama | External | Optional for production, user must install |

### New ACMRecord Fields

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `disturbance_potential` | Optional[str] | Likelihood of disturbance | No |
| `sample_no` | Optional[str] | Sample identification number | No |
| `sample_result` | Optional[str] | Lab result for sample | No |
| `identifying_company` | Optional[str] | Hygiene consulting company | No |
| `quantity` | Optional[str] | Amount/extent of material | No |
| `acm_labelled` | Optional[bool] | Whether ACM is labeled | No |
| `acm_label_details` | Optional[str] | Label information | No |
| `hygienist_recommendations` | Optional[str] | Expert recommendations | No |
| `psb_supplied_acm_id` | Optional[str] | PSB identifier | No |
| `removal_status` | Optional[str] | Removal status (N/A, Pending, Complete) | No |
| `date_of_removal` | Optional[str] | When removed | No |
| `extraction_confidence` | Optional[str] | high/medium/low | No |
| `data_issues` | Optional[List[str]] | List of extraction issues | No |

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
- Identify page boundaries if present

### Step 2: Data Completeness
- Extract all available fields
- For missing fields, use null (do not guess)
- If uncertain, set extraction_confidence to "low"

### Step 3: Safety Assessment
- Flag any high-risk materials (friable, poor condition)
- Note inconsistencies in risk vs condition

### Step 4: Data Mapping
- Map product descriptions to standard categories where clear
- Preserve original text for non-standard items
- Generate unique IDs: {school_code}_{building_id}_{room_id}_{sequence}

### Step 5: Quality Validation
- Verify building/room context consistency
- Add data_issues for any extraction concerns

## Content to Extract

{{ content }}
```

### Testing Strategy

1. **Unit Tests**: Schema validation, chunking logic, prompt rendering
2. **Integration Tests**: End-to-end with mocked LLM responses
3. **Accuracy Tests**: Compare extracted data to manually verified ground truth
4. **Performance Tests**: Measure extraction time and token usage
5. **Golden File Tests** *(Added from review)*:
   - Create `tests/fixtures/acm_extraction/` directory
   - For each sample PDF, create corresponding `expected_output.json`
   - Test format: `{pdf_name}.pdf` → `{pdf_name}_expected.json`
   - Golden files contain manually verified extraction results
   - Regression tests compare LLM output against golden files
   - Threshold: >90% field-level match (allows for minor formatting differences)

### Ollama Setup (Production)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull recommended model
ollama pull qwen2.5:7b

# Verify
ollama list
```

Configure in ACM-AI Settings:
- Provider: `ollama`
- Model: `qwen2.5:7b`
- Type: `language`

---

## Next Stories After This

| Story | Description | Depends On |
|-------|-------------|------------|
| E1-S3.1 | Add extraction retry with different model | This story |
| E2-S7 | Add confidence filter to ACM grid | This story |
| E5-S1 | Batch extraction for multiple sources | This story |

---

## Review Notes

### Party Mode Review (2025-12-20)

**Participants:** Winston (Architect), Amelia (Dev), Murat (TEA), John (PM)

**Summary of Findings:**

| Focus Area | Verdict | Action Taken |
|------------|---------|--------------|
| LangGraph Approach | ✅ Sound | Follows existing codebase patterns |
| Guardrails | ⚠️ Enhanced | Added Task 5.5 (validation rules), Task 7.5 (retry logic) |
| Chunking Strategy | ⚠️ Detailed | Added Task 6.5 (context carryover, deduplication key) |
| Schema Expansion | ✅ Good | All optional, backwards compatible |
| Error Handling | ⚠️ Added | Added AC8 (empty handling), AC9 (debuggability) |
| Testing | ⚠️ Enhanced | Added golden file testing requirement |

**Key Additions from Review:**
- Task 5.5: Validation rules with required fields (`building_id`, `room_id`, `product_description`)
- Task 6.5: Context carryover mechanism and deduplication key definition
- Task 7.5: Retry logic with exponential backoff
- AC8: Empty extraction handling (distinguish "no ACM data" from "extraction failed")
- AC9: Failed extractions are debuggable with full context logging
- Golden file tests for regression testing

---

*Tech-Spec generated by create-tech-spec workflow*
*Updated with Party Mode review feedback*
