# Claude Code Session: Per-Row ACM Extraction Pipeline

## Session Setup

Load skills:
```
/planning-with-files
/dispatching-parallel-agents
/subagent-driven-development
/langgraph-fundamentals
/pydantic-models-py
/systematic-debugging
```

Read planning files FIRST:
- `task_plan.md` — Master plan, agent assignments, execution order
- `findings.md` — Edge cases (8 types), DoclingDocument JSON structure, KV prompt design
- `progress.md` — Track completion per agent task

---

## Context

ACM-AI extracts two record types from PDF asbestos registers:

**Building records:** Building Name, Type (114 options), Category (13 options, dependent on Type), Year Built, Construction Type, Roof Type

**Item records:** Room/Location, Item Description, Friability → ACM Classification (18 options) → Sub-Classification (133 options), Condition, Disturbance Potential, Sample Number, Sample Result, Quantity, Recommendation

Critical constraint: **three-level dependent picklist chain** — Friability → Classification → Sub-Classification. If any level is wrong, Salesforce rejects the import.

---

## Key Decisions Already Made

1. **Primary input:** DoclingDocument JSON (lossless — has `row_span`, `col_span`, `page_no`, `column_header` flags)
2. **LLM prompt format:** Key-value pairs (simplest for small Ollama models)
3. **Debug export:** HTML secondary (generated from parsed rows for visual inspection)
4. **TableFormer:** ACCURATE mode with `do_cell_matching=True`
5. **Architecture:** One LLM call per table ROW (not per building). Classification/normalization in deterministic Python.

---

## What We're Changing

**Current:** One LLM call per building → all items at once (40+ fields × N items). Fails on Ollama.

**New:** One LLM call per TABLE ROW → one item (12 plain fields). Then deterministic Python does classification, normalization, and picklist validation.

### New Step 4 Flow

```
For each building:
  4a. Get DoclingDocument JSON tables for building's page range
  4b. Row Segmentation:
      - Parse JSON table_cells → group by start_row_offset_idx
      - Handle: merged cells (row_span), multi-page (merge tables), sub-headers, notes
      - Detect: multi-item cells → flag needs_llm_split
      - Text scan for "Not Sampled" / "No Access" → synthetic rows
      - Generate HTML debug table
  4c. Per-row LLM extraction:
      - Build key-value prompt from RawTableRow cells + building context
      - Call ChatOllama (format="json", temperature=0) → ACMItemRowSimple
      - If needs_llm_split: split first, then extract each sub-item
  4d. Deterministic post-processing (NO LLM):
      - is_friable bool → "Friable"/"Non-friable"
      - item_description → classify_product() → Classification + Sub-Classification
      - condition → normalize_enum_value() → SF picklist
      - Negative → N/A business rule
      - Dependency chain validation
  4e. Save ACMRecord with building_id FK
      - If validation fails → retry this row only (max 2)
      - Generate HTML debug row with data-flags attributes
```

---

## Sub-Agent Dispatch

### Phase 1 — Parallel (dispatch all three simultaneously)

**Agent 1 — Row Segmentation Engine:**
```
You are building a Row Segmentation Engine that parses DoclingDocument JSON tables into individual rows.

Read findings.md for the complete edge case catalog and JSON structure examples.

Create `open_notebook/extractors/row_segmenter.py`:

1. `class RawTableRow(BaseModel)` — see findings.md §3 for full model definition

2. `def segment_docling_table(table_data: dict, building_id: str, source_id: str, page_number: int) -> list[RawTableRow]`
   Input: A single Docling table JSON object with keys: table_cells (list of cell dicts with text, row_span, col_span, start_row_offset_idx, start_col_offset_idx, end_row_offset_idx, end_col_offset_idx, column_header), num_rows, num_cols
   
   Logic:
   a. Extract header cells (column_header=true), build ordered header list
   b. Fuzzy-match headers to canonical names using COLUMN_ALIASES + rapidfuzz (Type G)
   c. Build span registry: for cells with row_span>1, register (row_idx, col_idx) → text for all spanned positions
   d. Group non-header cells by start_row_offset_idx
   e. For each row group:
      - If single cell spans all cols → check if E2 (note) or E3 (sub-header), handle accordingly
      - If any cell text contains \n + material keywords → flag needs_llm_split (E1)
      - Fill missing columns from span registry (Type C merged cells)
      - Build RawTableRow with cells dict, column_mapping, carried_forward_fields
   f. Generate debug_html for each row

3. `def segment_multiple_tables(tables: list[dict], building_page_range: tuple[int,int]) -> list[RawTableRow]`
   a. Filter tables to building's page range
   b. Group by num_cols
   c. Same num_cols → multi-page merge (Type B): concat rows, deduplicate overlaps
   d. Different num_cols → detect shared key column (Type H): JOIN on key
   e. Return flat list of RawTableRow

4. `def scan_text_for_synthetics(markdown: str, building_id: str, source_id: str) -> list[RawTableRow]`
   Regex for Type F ("Not Sampled"/"No Access") and Type D (hierarchical text items)

5. `def detect_column_mapping(header_cells: list[dict]) -> dict[str, str]`
   Fuzzy match against COLUMN_ALIASES using rapidfuzz.fuzz.ratio at 70% threshold

6. `def generate_debug_table(rows: list[RawTableRow], building_name: str) -> str`
   Full HTML debug table with caption, data-flags attributes on rows

Use NO LLM calls. Use rapidfuzz for matching. Use standard library only for HTML generation (no BeautifulSoup needed for OUTPUT — only for potential HTML input fallback).

Create `tests/test_row_segmenter.py` with tests for each edge case type.
```

**Agent 2 — Schemas + Mappers:**
```
You are creating simplified Pydantic schemas for LLM output and deterministic mapping functions.

Read findings.md §4 and §5 for prompt design and post-processing pipeline.

Read existing code (DO NOT MODIFY these files, only read):
- open_notebook/domain/acm.py → ACMRecord model with AliasChoices + SF field names
- open_notebook/extractors/validators/sf_picklist_validator.py → SalesforcePicklistValidator
- open_notebook/extractors/normalizers/enums.py → normalize_enum_value()
- open_notebook/extractors/normalizers/taxonomy.py → classify_product()
- open_notebook/extractors/normalizers/recommendations.py → normalize_recommendation()

Create `open_notebook/domain/acm_llm_schemas.py`:
- `class ACMItemRowSimple(BaseModel)` with exactly these 12 fields:
  room_location: str (e.g. "Room 101")
  specific_location: Optional[str] (e.g. "Ceiling")
  item_description: str (e.g. "Vinyl floor tiles")
  is_friable: bool (True=friable, False=non-friable)
  condition: Optional[str] (e.g. "Good", "Poor")
  disturbance_potential: Optional[str] (e.g. "Low", "High")
  asbestos_type: Optional[str] (e.g. "Chrysotile")
  sampled: Optional[bool]
  sample_number: Optional[str]
  sample_result: Optional[str]
  quantity: Optional[str] (e.g. "50 m²")
  recommendation: Optional[str]
  
  EVERY field has Field(description=...) with a concrete example.
  NO AliasChoices. NO Literal enums. NO Salesforce API names.

Create `open_notebook/domain/schema_mappers.py`:
- `def map_row_simple_to_acm_record(simple: ACMItemRowSimple, building_id: str, source_id: str, dependency_chains: dict) -> ACMRecord`
  This does ALL the hard work:
  a. is_friable bool → "Friable" / "Non-friable"
  b. item_description → classify_product() → (Classification, Sub-Classification)
  c. condition → normalize_enum_value("Condition__c") → SF value
  d. disturbance_potential → normalize_enum_value("Disturbance_Potential_of_Material__c")
  e. recommendation → normalize_recommendation() → canonical
  f. sample_result → normalize_enum_value("Sample_Analysis_Result_Material_Status__c")
  g. Business rule: if "negative" in sample_result → condition="N/A (negative)", disturbance="N/A (negative)"
  h. Validate dependency chain: friability→classification→sub_classification using SalesforcePicklistValidator
  i. Return full ACMRecord with SF field names

Create `open_notebook/utils/enum_matcher.py`:
- `def fuzzy_match_picklist(raw_value: str, valid_options: list[str], threshold: float = 0.8) -> Optional[str]`

Create `tests/test_schema_mappers.py` with comprehensive tests.
```

**Agent 5 — Edge Case Fixtures:**
```
You are creating test fixtures for all 8 edge case types in DoclingDocument JSON format.

Read findings.md §2 for the complete edge case catalog.

Create `tests/fixtures/edge_case_tables/` directory with:

JSON fixtures (DoclingDocument table format — must have table_cells array with: text, row_span, col_span, start_row_offset_idx, end_row_offset_idx, start_col_offset_idx, end_col_offset_idx, column_header bool, plus num_rows, num_cols):
- type_a_standard.json — 5-row standard table, Room|Location|Material|Friable|Condition|Sample|Result|Quantity
- type_b_multipage.json — two table objects with same columns (continuation)
- type_b_overlap.json — two table objects where last row of table 1 = first row of table 2
- type_c_merged_room.json — room cell with row_span=3
- type_c_merged_level.json — both level (row_span=5) and room (row_span=3) merged
- type_e1_multiitem.json — one cell containing "Ceiling: Vinyl tiles\nFloor: Cement sheet\nWalls: Fibro"
- type_e2_note.json — note row with col_span=8, text "Note: All items accessible via ladder"
- type_e3_subheader.json — sub-header row with col_span=8, text "LEVEL 2 — FIRST FLOOR"
- type_g_consultant_a.json — headers: Room, Location, Material, Friable, Condition, Sample#, Result, Qty
- type_g_consultant_b.json — same data, headers: Ref, Room/Area, Product Description, F/NF, Assessment, NATA No, Analysis, Amount
- type_h_split.json — two table objects, different num_cols, shared Room column

Markdown fixtures:
- type_d_hierarchical.md — Building/Level/Room/Item hierarchy (no table)
- type_f_not_sampled.md — inline "Not Sampled" and "No Access" entries

HTML debug fixtures (for visual comparison):
- One .html file per JSON fixture showing expected rendered table

Use realistic Australian school ACM data (Broadmeadows Primary, Main Block, etc.).
Include comments explaining each edge case.
```

### Phase 2 — Sequential (after Phase 1)

**Agent 3 — Per-Row Extractor:**
```
You are building the per-row LLM extraction orchestrator.

Read:
- open_notebook/extractors/row_segmenter.py (Agent 1 output)
- open_notebook/domain/acm_llm_schemas.py (Agent 2 output)
- open_notebook/domain/schema_mappers.py (Agent 2 output)
- findings.md §4 for KV prompt design

Create `prompts/acm/row_extraction.jinja`:
  SystemMessage template (~200 chars): "Extract one ACM item. Fill JSON using ONLY row data. Null if absent. ONLY valid JSON."
  NOTE: Document content goes in HumanMessage, NOT in this template.

Create `prompts/acm/row_split.jinja`:
  For splitting multi-item cells (Type E1).

Create `open_notebook/extractors/row_extractor.py`:
1. `def build_kv_prompt(row: RawTableRow, building_context: str) -> str`
   Build key-value string from row.cells + building context + current_level.
   Use ORIGINAL column headers from row.column_mapping (more natural for LLM).

2. `async def extract_single_row(row: RawTableRow, building: BuildingRecord, model, langfuse_span=None) -> ACMItemRowSimple`
   - Render system prompt from row_extraction.jinja
   - Build KV human message from build_kv_prompt()
   - Call model.ainvoke([SystemMessage, HumanMessage])
   - parse_json_response() → ACMItemRowSimple.model_validate()
   - On failure: retry with error message in prompt (max 2)

3. `async def split_multi_item_row(row: RawTableRow, model) -> list[RawTableRow]`
   - For Type E1 rows where needs_llm_split=True
   - Send cell content to LLM with row_split.jinja prompt
   - Parse response into multiple RawTableRow objects (one per sub-item)

4. `async def extract_all_rows(rows: list[RawTableRow], building: BuildingRecord, model, config: dict, event_bus=None) -> list[ACMRecord]`
   Main loop:
   a. For each row:
      - If needs_llm_split → split_multi_item_row() → get sub-rows
      - For each (sub-)row: extract_single_row() → ACMItemRowSimple
      - map_row_simple_to_acm_record() → ACMRecord
      - If validation fails → retry extract (max 2, with error feedback)
      - If still fails → save with validation_status="failed"
   b. Emit SSE event: "Row {i}/{total} extracted for {building_name}"
   c. Log to Langfuse: child span per row with input/output/duration

   Use temperature=0. Use format="json" on ChatOllama.
   Use num_ctx from ACM_ROW_EXTRACTION_NUM_CTX env var (default 4096).

Create `tests/test_row_extractor.py` — mock ChatOllama, test full flow.
```

### Phase 3 — Integration (after Phase 2)

**Agent 4 — Pipeline Wiring:**
```
You are wiring per-row extraction into the existing LangGraph pipeline.

Read:
- open_notebook/graphs/acm_extraction.py — find extract_items_node
- open_notebook/extractors/orchestrator.py — find _v3_extract_items()
- open_notebook/extractors/row_segmenter.py (Agent 1)
- open_notebook/extractors/row_extractor.py (Agent 3)

Modify extract_items_node in acm_extraction.py:

1. Read ACM_EXTRACTION_STRATEGY env var (default: "per_row")
2. If "per_row":
   a. Get DoclingDocument tables for building's page range:
      - Existing _get_docling_tables() returns HTML — need to also get JSON
      - If DoclingDocument JSON stored in acm_table_section, load it
      - If only HTML available, fall back to existing bulk path
   b. Call segment_multiple_tables(tables_json, page_range) → list[RawTableRow]
   c. Call scan_text_for_synthetics(markdown, building_id, source_id) → append
   d. Call extract_all_rows(rows, building, model, config, event_bus) → list[ACMRecord]
   e. Generate debug HTML: generate_debug_table(rows, building.name)
   f. Save each ACMRecord with building_id FK
3. If "bulk":
   - Use existing _v3_extract_items() unchanged

Add to .env.example:
  ACM_EXTRACTION_STRATEGY=per_row
  ACM_ROW_EXTRACTION_MODEL=qwen2.5:14b-instruct-q4_K_M
  ACM_ROW_EXTRACTION_NUM_CTX=4096

Do NOT modify Steps 1-3 (metadata, inventory, building extraction).
Do NOT modify existing bulk path — it must still work for cloud providers.
Ensure acm_table_section stores DoclingDocument JSON (not just HTML) during Phase 1 PDF processing.
```

---

## Verification

```bash
uv run pytest tests/ -v
uv run ruff check .

# E2E test with per-row strategy
ACM_EXTRACTION_STRATEGY=per_row uv run python -m pytest tests/test_v3_e2e_pipeline.py -v

# Langfuse trace check
curl -s -u "$LANGFUSE_PUBLIC_KEY:$LANGFUSE_SECRET_KEY" \
  "$LANGFUSE_BASE_URL/api/public/traces?sessionId=extraction-{source_id}&limit=1" | jq '.data[0]'
```

Update `progress.md` after each agent completes.

---

## Constraints

- Do NOT modify ACMRecord, BuildingRecord, or SalesforcePicklistValidator
- Do NOT break the bulk extraction path (cloud providers need it)
- All new code: type hints, async functions, Pydantic models, Jinja2 templates
- ChatOllama: `format="json"`, `temperature=0`
- Log every row extraction to Langfuse as child span
- Use rapidfuzz for fuzzy matching (add to pyproject.toml)
- Docling config: `TableFormerMode.ACCURATE`, `do_cell_matching=True`
