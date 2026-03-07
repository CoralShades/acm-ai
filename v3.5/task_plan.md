# Task Plan: Per-Row ACM Extraction Pipeline

**Date:** 2026-03-07 (Updated)
**Goal:** Redesign Item__c extraction from bulk-per-building to per-row, using DoclingDocument JSON as primary input with HTML debug export.

---

## Pipeline (4 Steps)

```
Step 1: Metadata + Structure   →  What is this PDF? Where does the register start?
Step 2: Building Inventory     →  How many buildings? What page ranges?
Step 3: Building Extraction    →  Per building: one Building__c record
Step 4: Item Extraction (NEW)  →  Per building → per ROW: one Item__c record
         ├── 4a. Get DoclingDocument JSON tables for building's pages
         ├── 4b. Row Segmentation: JSON cells → list[RawTableRow] + text scan for Type F
         ├── 4c. Per-row LLM: key-value prompt → ACMItemRowSimple (12 plain fields)
         ├── 4d. Deterministic post-processing: classify, normalize, validate (no LLM)
         ├── 4e. Retry failed rows only (max 2 per row)
         └── 4f. Generate HTML debug export per building
```

**Outputs:** `building_record` + `acm_record` tables, mapped to `raw_extraction_table` and PDF source.

---

## Sub-Agent Assignments

### Agent 1: Row Segmentation Engine (DoclingDocument JSON)
**Scope:** Parse Docling JSON table objects into `list[RawTableRow]`, handling all edge cases. Generate HTML debug output.
**Files:**
- `open_notebook/extractors/row_segmenter.py` — NEW
- `tests/test_row_segmenter.py` — NEW

**Tasks:**
1. `segment_docling_table(table_data: dict, building_id, source_id, page_number) -> list[RawTableRow]`
   - Group `table_cells` by `start_row_offset_idx`
   - Skip header rows (`column_header: true`)
   - Build span registry from `row_span`/`col_span` for merged cells (Type C)
   - Detect E2 (note) and E3 (sub-header) rows, skip/extract context
   - Flag E1 (multi-item cells) with `needs_llm_split=True`
2. `segment_multiple_tables(tables: list[dict], building_page_range: tuple) -> list[RawTableRow]`
   - Detect multi-page continuations (Type B) by `num_cols` match
   - Deduplicate overlap rows at page boundaries
   - Detect split tables (Type H) by different `num_cols` + shared key
   - JOIN split tables on shared column
3. `scan_text_for_synthetics(markdown: str, building_id, source_id) -> list[RawTableRow]`
   - Regex for "Not Sampled" / "No Access" (Type F)
   - Regex for hierarchical text items (Type D)
4. `detect_column_mapping(header_cells: list[dict]) -> dict[str, str]`
   - Fuzzy match headers to `COLUMN_ALIASES` using rapidfuzz (Type G)
5. `generate_debug_html(row: RawTableRow) -> str` and `generate_debug_table(rows, building_name) -> str`

**Dependencies:** None. Pure parsing, no LLM.

---

### Agent 2: Simplified Pydantic Schemas + Mappers
**Scope:** LLM-friendly schema + deterministic mapping to full ACMRecord.
**Files:**
- `open_notebook/domain/acm_llm_schemas.py` — NEW
- `open_notebook/domain/schema_mappers.py` — NEW
- `open_notebook/utils/enum_matcher.py` — NEW
- `tests/test_schema_mappers.py` — NEW

**Tasks:**
1. `ACMItemRowSimple` — 12 plain fields, `Field(description=...)` with examples, no AliasChoices
2. `map_row_simple_to_acm_record(simple, building_id, source_id, dependency_chains) -> ACMRecord`
   - bool→string, classify_product, normalize_enum_value, normalize_recommendation
   - Business rule: Negative→N/A
   - Dependency chain validation
3. `fuzzy_match_picklist(raw_value, valid_options, threshold=0.8) -> Optional[str]` using rapidfuzz

**Dependencies:** Reads existing `ACMRecord`, `SalesforcePicklistValidator`, `normalize_enum_value`, `classify_product`.

---

### Agent 3: Per-Row Extraction Orchestrator
**Scope:** LLM call per row using key-value prompts, with retry and LLM-split for Type E1.
**Files:**
- `open_notebook/extractors/row_extractor.py` — NEW
- `prompts/acm/row_extraction.jinja` — NEW
- `prompts/acm/row_split.jinja` — NEW
- `tests/test_row_extractor.py` — NEW

**Tasks:**
1. `build_kv_prompt(row: RawTableRow, building_context: str) -> str` — key-value format
2. `extract_single_row(row, building, model, langfuse_span) -> ACMItemRowSimple`
3. `split_multi_item_row(row, model) -> list[RawTableRow]` — for Type E1
4. `extract_all_rows(rows, building, model, config) -> list[ACMRecord]`
   - For each row: if E1→split first, then extract, then post-process, then validate
   - Retry failed rows with error feedback (max 2)
   - Emit SSE per row via PipelineEventBus
   - Log each row to Langfuse as child span

**Dependencies:** Agent 1 (segmenter) + Agent 2 (schemas/mappers).

---

### Agent 4: Pipeline Integration
**Scope:** Wire per-row extraction into LangGraph pipeline.
**Files:**
- `open_notebook/graphs/acm_extraction.py` — MODIFY
- `open_notebook/extractors/orchestrator.py` — MODIFY
- `.env.example` — UPDATE

**Tasks:**
1. Add `ACM_EXTRACTION_STRATEGY` env var: `per_row` | `bulk`
2. In `extract_items_node`: if `per_row` → segmenter → per-row extractor; if `bulk` → existing path
3. Wire SSE progress events (row X of Y for building Z)
4. Ensure `building_id` FK on each `acm_record`
5. Store HTML debug tables in `acm_table_section.debug_html` or separate field

**Dependencies:** All other agents complete.

---

### Agent 5: Edge Case Test Suite + Fixtures
**Scope:** Test fixtures (JSON + Markdown) for all 8 edge case types.
**Files:**
- `tests/test_edge_cases_row_segmentation.py` — NEW
- `tests/fixtures/edge_case_tables/` — NEW directory

**Tasks:**
1. Create **DoclingDocument JSON fixtures** (not HTML!) for each edge case:
   - `type_a_standard.json` — 5-row table, standard columns
   - `type_b_multipage.json` — two table objects, same columns, continuation
   - `type_b_overlap.json` — overlap row at page boundary
   - `type_c_merged_room.json` — `row_span: 3` on room column
   - `type_c_merged_level.json` — nested spans on level + room
   - `type_d_hierarchical.md` — Markdown (no table, hierarchical text)
   - `type_e1_multiitem.json` — cell with `\n`-separated items
   - `type_e2_note.json` — colspan note row
   - `type_e3_subheader.json` — colspan "LEVEL 2" row
   - `type_f_not_sampled.md` — inline "Not Sampled" text
   - `type_g_consultant_a.json` — Room|Location|Material columns
   - `type_g_consultant_b.json` — Ref|Room/Area|Product Description columns
   - `type_h_split.json` — two tables, different columns, shared Room key
2. Also create corresponding HTML debug files for visual comparison
3. Parameterized tests for segmenter against each fixture

**Independence:** Can start fixtures immediately. Test code depends on Agent 1 + 2.

---

## Execution Order

```
Phase 1 (parallel — no dependencies between these):
  Agent 1: Row Segmentation (DoclingDocument JSON)
  Agent 2: Schemas + Mappers
  Agent 5: Test Fixtures (JSON + HTML)

Phase 2 (after Phase 1):
  Agent 3: Per-Row Extraction Orchestrator

Phase 3 (after Phase 2):
  Agent 4: Pipeline Integration

Phase 4 (verification):
  Full test suite
  E2E on Broadmeadows PDF
  Langfuse trace check
```

---

## Ollama Model Config

```bash
ACM_PRE_EXTRACTION_MODEL=qwen2.5:14b-instruct-q4_K_M
ACM_PRE_EXTRACTION_NUM_CTX=32768
ACM_ROW_EXTRACTION_MODEL=qwen2.5:14b-instruct-q4_K_M
ACM_ROW_EXTRACTION_NUM_CTX=4096
ACM_EXTRACTION_STRATEGY=per_row
ACM_MAX_CONCURRENT_BUILDINGS=1
```

---

## Verification Checklist

- [ ] Row segmenter handles all 8 edge case types from JSON input
- [ ] HTML debug tables generated for each building
- [ ] `ACMItemRowSimple` → `ACMRecord` mapping valid for SF picklists
- [ ] Dependency chain enforced in Python (Friability→Classification→Sub-Classification)
- [ ] Per-row extraction works with qwen2.5:14b at num_ctx=4096
- [ ] Failed rows retry independently
- [ ] Building↔Item FK maintained
- [ ] Bulk path unchanged for cloud providers
- [ ] Langfuse traces show per-row spans
- [ ] `uv run pytest tests/` passes
- [ ] Broadmeadows ≥31/31, Alexander ≥36/43
