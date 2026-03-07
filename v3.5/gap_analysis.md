# Gap Analysis: Per-Row ACM Extraction Pipeline

**Date:** 2026-03-07
**Scope:** Cross-check of v3.5 planning files against actual codebase
**Status:** AUDIT ONLY — no code changes

---

## Section 1: Assumptions That Hold ✅

### 1.1 TableFormer Configuration
The plan assumes ACCURATE mode with `do_cell_matching=True`. This is **correct**.
- File: `open_notebook/extractors/providers/docling_adapter.py:105-107`
- `pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE`
- `pipeline_options.table_structure_options.do_cell_matching = True`

### 1.2 Existing Normalizer Functions
The plan correctly identifies these normalizer functions as available for reuse:
- `normalize_enum_value(raw_value, field_name)` — `open_notebook/extractors/normalizers/enums.py`
- `classify_product(item_description, friability, product)` — `open_notebook/extractors/normalizers/taxonomy.py`
- `normalize_recommendation(raw_recommendation)` — `open_notebook/extractors/normalizers/recommendations.py`

### 1.3 SalesforcePicklistValidator Exists
- `validate_acm_chain(record, policy)` exists at `open_notebook/extractors/validators/sf_picklist_validator.py:278-369`
- Validates Friability → Classification → Sub-Classification chain as the plan expects

### 1.4 PipelineEventBus Architecture
- Singleton asyncio pub/sub bus exists at `open_notebook/extractors/pipeline_event_bus.py`
- Keyed by `operation_id`, uses `asyncio.Queue` per subscriber
- SSE endpoint wiring in `api/routers/v3_streaming.py`

### 1.5 parse_json_response() Reusable
- `open_notebook/graphs/utils.py:737-783`
- Strips fences, brace-balanced extraction, handles truncation
- Returns `dict[str, Any]` — fully reusable for per-row parsing

### 1.6 ChatOllama format="json" Already Set
- `_apply_ollama_extraction_settings()` at `open_notebook/graphs/utils.py:247-291`
- Sets `format="json"` and `num_ctx` for all Ollama extraction models

### 1.7 Building-to-Item FK Pattern
- `building_record_id` FK exists on `ACMRecord` / `ACMExtractionRecord`
- `code_to_id_map` lookup in `extract_items_node` (acm_extraction.py:853) assigns building FK

### 1.8 Existing Recovery Function Patterns
- `_recover_no_access_records()` at `acm_extraction.py:1609-1821` — regex scan for "No Access"
- `_recover_not_sampled_records_ara()` at `acm_extraction.py:1824-2030` — regex scan for "Not Sampled"
- Both output `ACMExtractionRecord` — can serve as reference for Type F synthetic rows

### 1.9 Jinja Template Loading Pattern
- Uses `ai_prompter.Prompter(prompt_template="acm/template_name")`
- Templates live in `prompts/acm/` directory
- Pattern is well-established across existing extraction code

---

## Section 2: Assumptions That Don't Hold ❌

### 2.1 ❌ DoclingDocument JSON is NOT Stored

**Plan assumes:** DoclingDocument JSON (`export_to_dict()`) is available in `acm_table_section` and can be used as primary input for row segmentation.

**Reality:** Only three formats are stored:
- `raw_html` — from `table.export_to_html(doc=doc)` (line 155, docling_adapter.py)
- `raw_text` — from `df.to_markdown(index=False)` (line 156)
- `structured_json` — from `df.to_csv(index=False)` (line 157) — this is **CSV data**, NOT Docling JSON

`export_to_dict()` is **never called** anywhere in the codebase. The DoclingDocument's raw table structure (with `table_cells`, `row_span`, `col_span`, `start_row_offset_idx`, `column_header` flags) is **lost** during the DataFrame conversion.

**Impact:** This is the **single largest gap** in the plan. Without Docling JSON:
- Agent 1 (Row Segmenter) cannot parse `table_cells` with span info
- Agent 5 fixtures (DoclingDocument JSON format) have no actual data to validate against
- The entire per-row segmentation strategy is blocked

**Suggested fix:**
1. Add `docling_json` field to `acm_table_section` (new migration)
2. Modify `DoclingAdapter._run_extraction()` to also call `table.export_to_dict(doc=doc)` or equivalent and store it
3. Alternatively, use the DoclingDocument in-memory (don't store; re-extract per building) — but this is expensive
4. **Best approach:** Store `doc.export_to_dict()` (whole document JSON) once per source, then segment from it. This preserves ALL table structure.

**Affected agents:** Agent 1, Agent 4, Agent 5

### 2.2 ❌ ACMItemRowSimple Schema Conflicts with Existing ACMItemRecord

**Plan assumes:** Create a new 12-field `ACMItemRowSimple` schema with plain field names (no SF names).

**Reality:** `ACMItemRecord` already exists in `open_notebook/extractors/acm_schemas_v3.py:47-84` with **22 fields** using SF-aligned names (e.g., `friability_of_material`, `acm_classification`, `acm_sub_classification`, `room_or_area`, `internal_external`).

**Specific conflicts:**

| Plan's ACMItemRowSimple | Existing ACMItemRecord | Difference |
|------------------------|----------------------|------------|
| `room_location: str` | `room_or_area: Optional[str]` | Different name |
| `specific_location: Optional[str]` | `location_in_room: Optional[str]` | Different name |
| `item_description: str` | Uses `item_name` + `acm_sub_classification` | Plan merges two fields |
| `is_friable: bool` | `friability_of_material: Optional[str]` | bool vs string |
| `condition: Optional[str]` | `condition: Optional[str]` | ✅ Same |
| `asbestos_type: Optional[str]` | (not present) | New field |
| `sampled: Optional[bool]` | (not present) | New field |
| — | `acm_classification: Optional[str]` | Plan drops this (defers to Python) |
| — | `acm_sub_classification: Optional[str]` | Plan drops this (defers to Python) |
| — | `internal_external: Optional[str]` | Plan drops this entirely |
| — | `labelled: Optional[str]` | Plan drops this |
| — | `no_access: bool` | Plan drops this |
| — | `extraction_confidence: str` | Plan drops this |
| — | `data_issues: List[str]` | Plan drops this |
| — | `page_number: Optional[int]` | Plan drops this |

**Impact:** The plan's 12-field schema drops **10 fields** that the current pipeline extracts. The `map_row_simple_to_acm_record()` function would need to either:
- Infer these dropped fields from context (e.g., `internal_external` from room name)
- Accept losing this data
- Or expand the schema to include them

**Suggested fix:** Either:
1. Use `ACMItemRecord` as-is (already LLM-friendly, already tested)
2. Or create `ACMItemRowSimple` but include at minimum: `internal_external`, `labelled`, `no_access`, `page_number`, `level` — these are not derivable from other fields

**Affected agents:** Agent 2, Agent 3

### 2.3 ❌ classify_product() Return Type Mismatch

**Plan assumes:** `classify_product()` returns `(Classification, Sub-Classification)` tuple.

**Reality:** It returns a `ClassificationResult` object:
```python
ClassificationResult(
    product_group: str,      # e.g., "Vinyl products" (T-prefix stripped)
    product_type: str,       # e.g., "Vinyl sheet"
    confidence: float,       # 0.9 for pattern match, 0.0 for no match
    method: str              # "pattern", "llm", or "none"
)
```

Also note: `classify_product()` is **synchronous** (pattern-based only). `classify_product_async()` is the async version with LLM fallback.

**Impact:** Agent 2's `map_row_simple_to_acm_record()` needs to call `result.product_group` and `result.product_type`, not unpack a tuple.

**Affected agents:** Agent 2

### 2.4 ❌ No Existing Extraction Strategy Switch for per_row

**Plan assumes:** Add `ACM_EXTRACTION_STRATEGY` env var with values `per_row | bulk`.

**Reality:** `ExtractionStrategy` enum exists at `orchestrator.py:140-145` but has values `FULL_LLM | REGEX_ONLY | SKIP` — completely different concept (per-building routing, not pipeline-wide strategy).

**Impact:** The plan's `per_row`/`bulk` switch needs to be a **separate** concept from the existing `ExtractionStrategy`. Using the same name would cause confusion. Consider `ACM_ITEM_EXTRACTION_MODE` or similar.

**Affected agents:** Agent 4

### 2.5 ❌ num_ctx Is Global, Not Per-Step

**Plan assumes:** Separate env vars: `ACM_PRE_EXTRACTION_NUM_CTX=32768` and `ACM_ROW_EXTRACTION_NUM_CTX=4096`.

**Reality:** Single global `OLLAMA_NUM_CTX` env var (default 32768), applied by `_apply_ollama_extraction_settings()` to ALL extraction models. There's no mechanism for per-step `num_ctx`.

**Impact:** Setting `num_ctx=4096` for per-row extraction would break the existing bulk path (which needs 32768). Agent 4 would need to either:
- Pass `num_ctx` explicitly when creating the ChatOllama instance for per-row extraction
- Or create a separate model provisioning function that doesn't call `_apply_ollama_extraction_settings()`

**Affected agents:** Agent 3, Agent 4

### 2.6 ❌ _normalize_v3_records() Already Bridges V3→V2

**Plan assumes:** `map_row_simple_to_acm_record()` maps `ACMItemRowSimple` directly to `ACMRecord`.

**Reality:** The pipeline doesn't save `ACMRecord` directly. It saves `ACMExtractionRecord` (the V2 schema). The bridge function `_normalize_v3_records()` at `orchestrator.py:436-515` maps `ACMItemRecord` → `ACMExtractionRecord`. Then `save_records()` in acm_extraction.py converts `ACMExtractionRecord` → `ACMRecord` for persistence.

The mapping chain is: `LLM output → ACMItemRecord → ACMExtractionRecord → ACMRecord`

**Impact:** Agent 2's mapper should target `ACMExtractionRecord` (not `ACMRecord`), or the per-row path needs to bypass the existing save pipeline entirely. The simplest approach is to map `ACMItemRowSimple` → `ACMExtractionRecord` and reuse the existing validation/correction/save stages.

**Affected agents:** Agent 2, Agent 3, Agent 4

### 2.7 ❌ rapidfuzz Not in Dependencies

**Plan assumes:** Use `rapidfuzz` for fuzzy column header matching. Says "add to pyproject.toml."

**Reality:** Not installed. However, a **pure-Python Jaro-Winkler** implementation already exists at `open_notebook/extractors/consensus/matcher.py:69-128`.

**Impact:** Adding `rapidfuzz` as a new dependency for one function (column matching) when a pure-Python fuzzy matcher already exists is over-engineering. Consider reusing the existing Jaro-Winkler or using `difflib.SequenceMatcher` from stdlib.

**Affected agents:** Agent 1, Agent 2

### 2.8 ❌ structured_json Field Contains CSV, Not JSON

**Plan's findings.md** implies `structured_json` might contain Docling table structure.

**Reality:** `structured_json` in `acm_table_section` stores `df.to_csv(index=False)` (line 184, source_commands.py). In `raw_extraction`, it stores `{"columns": [...], "row_count": N, "col_count": N, "table_index": N}` metadata (line 221-228, source_commands.py).

**Impact:** No existing field stores DoclingDocument JSON. A new field or approach is needed.

---

## Section 3: Existing Code to Reuse ♻️

### 3.1 ACMItemRecord (acm_schemas_v3.py:47-84)
- Already a simplified LLM schema for per-item extraction
- Has 22 fields with SF-aligned names
- Already tested with the v3_item_extraction.jinja prompt
- **Recommendation:** Extend this or use as-is instead of creating ACMItemRowSimple

### 3.2 _normalize_v3_records() (orchestrator.py:436-515)
- Maps ACMItemRecord → ACMExtractionRecord
- Handles: internal_external→area_type, labelled→acm_labelled, quantity float→str
- **Recommendation:** Per-row extraction should output ACMItemRecord, then reuse this mapper

### 3.3 _apply_ollama_extraction_settings() (graphs/utils.py:247-291)
- Sets format="json" and num_ctx for Ollama models
- **Recommendation:** For per-row, create variant that sets lower num_ctx

### 3.4 provision_langchain_model() (graphs/utils.py:570-608)
- Handles Ollama/Anthropic/OpenRouter provider chain
- **Recommendation:** Reuse for per-row model provisioning

### 3.5 parse_json_response() (graphs/utils.py:737-783)
- Resilient JSON parser with truncation detection
- **Recommendation:** Reuse directly for parsing per-row LLM responses

### 3.6 _recover_no_access_records() (acm_extraction.py:1609-1821)
- Regex patterns for "No Access" / "Height Restriction" / "Restricted Access"
- Known product keywords set
- **Recommendation:** Extract regex patterns for reuse in Type F scan_text_for_synthetics()

### 3.7 _recover_not_sampled_records_ara() (acm_extraction.py:1824-2030)
- Regex patterns for "Not Sampled" / "Presumed Positive" in ARA format
- **Recommendation:** Extract patterns for reuse in Type F

### 3.8 SalesforcePicklistValidator.validate_acm_chain() (sf_picklist_validator.py:278-369)
- Chain validation: Friability → Classification → Sub-Classification
- **Recommendation:** Call this in post-processing after classify_product()

### 3.9 normalize_extraction_record() (normalizers/sf_normalizer.py:13-123)
- Applies normalize_record_to_sf() + normalize_enum_value() + Negative→N/A business rule
- Operates on ACMExtractionRecord in-place
- **Recommendation:** If per-row outputs ACMExtractionRecord, this normalizer works as-is

### 3.10 Jaro-Winkler Implementation (consensus/matcher.py:69-128)
- Pure Python, no external dependency
- Functions: `_jaro(s, t)` and `_jaro_winkler(s, t)`
- **Recommendation:** Reuse for column header fuzzy matching instead of adding rapidfuzz

### 3.11 PipelineEventBus (pipeline_event_bus.py)
- `publish(event)`, `subscribe(operation_id)` pattern
- **Recommendation:** Add `AIItemExtractedEvent` (singular) for per-row events

### 3.12 normalize_docling_text() (normalizers/content.py)
- Fixes Docling line-breaking artifacts: "Assumed\n\npositive" → "Assumed positive"
- **Recommendation:** Apply to cell text after segmentation

### 3.13 build_picklist_context() (orchestrator.py ~line 358)
- Builds picklist option strings from SF schema bundle
- **Recommendation:** May still be useful for system prompt context in per-row extraction

### 3.14 ExtractionStrategy Enum Pattern (orchestrator.py:140-145)
- Pattern for strategy routing with `FULL_LLM`, `REGEX_ONLY`, `SKIP`
- **Recommendation:** Follow this pattern but use a separate enum for item extraction mode

---

## Section 4: Missing Infrastructure 🔧

### 4.1 DoclingDocument JSON Storage (CRITICAL)

**What's needed:** Either:
- **Option A:** New field `docling_json TEXT` on `acm_table_section` + `raw_extraction` tables
- **Option B:** New table `docling_document_json` with `source_id`, `document_json` (entire doc)
- **Option C:** Don't store; re-extract from PDF on demand (expensive, ~30s per PDF)

**Recommended:** Option B — store `doc.export_to_dict()` once per source. This preserves:
- `table_cells` array with `row_span`, `col_span`, `start_row_offset_idx`, `column_header`
- `num_rows`, `num_cols` per table
- `prov.page_no` per table
- Full document structure (not just tables)

**Migration needed:** Yes — new migration file

**Code changes needed:**
- `DoclingAdapter._run_extraction()` — add `doc.export_to_dict()` call
- `source_commands._store_docling_tables()` or new storage function
- `_get_docling_tables()` — add JSON retrieval path

### 4.2 Per-Row Event Type

**What's needed:** New event class in `pipeline_event_bus.py`:
```python
class AIItemExtractedData(BaseModel):
    building_id: str
    row_index: int
    total_rows: int
    item_description: str
    status: str  # "success" | "retry" | "failed"
```

### 4.3 Per-Step num_ctx Configuration

**What's needed:** Either:
- New env var `ACM_ROW_EXTRACTION_NUM_CTX` (default 4096)
- Or parameter on model provisioning function
- Current `_apply_ollama_extraction_settings()` doesn't accept num_ctx parameter

### 4.4 DB Schema for DoclingDocument JSON

**Migration:** Add to `acm_table_section` or create new table:
```surrealql
-- Option A: field on existing table
DEFINE FIELD IF NOT EXISTS docling_json ON TABLE acm_table_section TYPE option<string>;

-- Option B: new table (preferred — one JSON per source, not per table)
DEFINE TABLE docling_document SCHEMAFULL;
DEFINE FIELD source_id ON docling_document TYPE record<source>;
DEFINE FIELD document_json ON docling_document TYPE string;
DEFINE FIELD created ON docling_document TYPE datetime DEFAULT time::now();
DEFINE INDEX doc_source ON docling_document FIELDS source_id UNIQUE;
```

### 4.5 Missing Tests Directory

`tests/fixtures/edge_case_tables/` does not exist. Must be created by Agent 5.

---

## Section 5: Plan Adjustments Needed 📝

### 5.1 Agent 1: Row Segmentation Engine — MAJOR SCOPE CHANGE

**Current scope:** Parse DoclingDocument JSON tables into RawTableRow.

**Problem:** DoclingDocument JSON is not currently stored or accessible. The plan assumes it's available.

**Adjusted scope — two options:**

**Option A (Store JSON first):**
- Add a "Phase 0" task: Modify `DoclingAdapter` to store DoclingDocument JSON
- Then Agent 1 can parse it as planned
- Requires: new migration, modified adapter, modified storage function

**Option B (Work from existing data):**
- Parse `raw_html` (HTML tables) using BeautifulSoup instead of JSON
- HTML preserves `colspan`/`rowspan` attributes (semi-lossless)
- Loses: `start_row_offset_idx`, `column_header` flag, `prov.page_no` per cell
- Gains: Works immediately without infrastructure changes

**Recommendation:** Option A is better long-term but adds a dependency (Phase 0 before Phase 1). Option B is a pragmatic fallback.

**New task to add:** "Phase 0: Store DoclingDocument JSON" — before Agent 1 can start.

### 5.2 Agent 2: Schemas + Mappers — SCHEMA REDESIGN

**Remove:** `ACMItemRowSimple` with 12 fields (too simplified, loses data)

**Replace with one of:**

1. **Reuse ACMItemRecord** (22 fields) — already exists, already tested, already has mapper to ACMExtractionRecord via `_normalize_v3_records()`. Per-row prompt would be identical format, just one record instead of array.

2. **Create ACMItemRowSimple** but with ~18 fields (add back: `internal_external`, `level`, `labelled`, `no_access`, `page_number`, `if_other_item_name`). Then write mapper to ACMExtractionRecord (not ACMRecord).

**Remove:** `open_notebook/utils/enum_matcher.py` — fuzzy matching already exists in consensus/matcher.py. Don't add rapidfuzz dependency.

**Update mapper target:** Map to `ACMExtractionRecord`, not `ACMRecord`. The existing pipeline handles `ACMExtractionRecord → ACMRecord` conversion.

### 5.3 Agent 3: Per-Row Extractor — PROMPT ADJUSTMENTS

**Update:** The row extraction prompt should output `ACMItemRecord` (or ACMItemRowSimple-expanded) format, not the simplified 12-field format.

**Update:** Use `provision_langchain_model()` for model creation, not direct ChatOllama instantiation. This preserves the Ollama→Anthropic→OpenRouter fallback chain.

**Add:** Handle the `num_ctx` override for per-row extraction (create model with lower context window).

**Update:** The per-row prompt should still include key picklist values (condition, sample_result, friability) to guide the LLM. Dropping all picklists from the prompt and relying solely on Python post-processing is risky — the LLM may produce values too far from canonical for normalization to fix.

### 5.4 Agent 4: Pipeline Integration — EXPANDED SCOPE

**Add tasks:**
1. Store DoclingDocument JSON during Phase 1 PDF processing (if Option A from 5.1)
2. Create model provisioning variant with lower num_ctx for per-row
3. Don't call it `ACM_EXTRACTION_STRATEGY` — conflicts conceptually with existing `ExtractionStrategy` enum. Use `ACM_ITEM_EXTRACTION_MODE` or `ACM_PER_ROW_ENABLED=true/false`.
4. Wire `_normalize_v3_records()` for per-row output → existing validation/correction/save pipeline

### 5.5 Agent 5: Fixtures — FORMAT MAY CHANGE

If Option B (HTML parsing) is chosen instead of JSON parsing, all fixtures need to be HTML tables instead of DoclingDocument JSON format. Keep both formats in fixtures for flexibility.

### 5.6 findings.md Updates

- §3 RawTableRow model: `cells` dict type is good, but `raw_text` should be derived from cells, not stored separately
- §4 KV prompt: Should include at least minimal picklist guidance (Condition: Stable/Fair/Poor)
- §5 Post-processing: `classify_product()` returns `ClassificationResult` object, not tuple
- §7 HTML debug: Consider storing in `raw_extraction` table instead of `acm_table_section`

### 5.7 CLAUDE_CODE_SESSION_PROMPT.md Updates

- Agent 1 prompt: Reference actual DoclingAdapter code at `providers/docling_adapter.py`, not hypothetical JSON storage
- Agent 2 prompt: Reference `acm_schemas_v3.py` for existing ACMItemRecord, not just `acm.py`
- Agent 2 prompt: Target `ACMExtractionRecord` as mapper output, reference `_normalize_v3_records()` as pattern
- Agent 3 prompt: Reference `provision_langchain_model()` not direct ChatOllama
- Agent 4 prompt: Note DoclingDocument JSON storage gap explicitly
- All agents: Note that `rapidfuzz` is NOT installed and pure-Python Jaro-Winkler exists

---

## Section 6: Risk Register ⚠️

### 6.1 HIGH: DoclingDocument JSON Not Available
**Risk:** The entire row segmentation strategy depends on data that isn't stored.
**Likelihood:** Certain (confirmed by code audit).
**Mitigation:** Implement JSON storage (Phase 0) before starting Agent 1. Alternatively, parse HTML tables.

### 6.2 HIGH: Schema Proliferation
**Risk:** Creating ACMItemRowSimple alongside ACMItemRecord alongside ACMExtractionRecord alongside ACMRecord creates 4 schemas for the same concept.
**Likelihood:** High — plan explicitly creates a new schema.
**Mitigation:** Reuse ACMItemRecord. It's already designed for LLM output and has a tested mapper.

### 6.3 MEDIUM: Per-Row = More LLM Calls = Slower
**Risk:** A 31-item building goes from 1 LLM call to 31+ calls. At ~2s per call on Ollama, that's ~62s vs ~5s.
**Likelihood:** High.
**Mitigation:** Per-row calls have tiny context (4K tokens vs 32K), so individual calls should be ~0.5-1s. Still ~15-31s per building. Consider batching 3-5 rows per call as a middle ground.

### 6.4 MEDIUM: Classification Accuracy Without LLM
**Risk:** Moving classification to deterministic Python (`classify_product()` pattern matching) may miss items that don't match patterns (confidence=0.0). Current prompt asks LLM for `acm_classification` and `acm_sub_classification` directly.
**Likelihood:** Medium — pattern match covers ~80% of items (confidence 0.9), but 20% return "none".
**Mitigation:** Use `classify_product_async()` with LLM fallback for items where pattern match fails. Or keep classification in the per-row LLM prompt (add the picklist options).

### 6.5 MEDIUM: num_ctx Conflict Between Bulk and Per-Row
**Risk:** Global `OLLAMA_NUM_CTX=32768` is needed for bulk path but wasteful for per-row (4K would suffice). Setting it to 4K breaks bulk.
**Likelihood:** High — both paths share model provisioning.
**Mitigation:** Per-row extraction must provision its own model with explicit `num_ctx=4096` parameter, bypassing the global setting.

### 6.6 LOW: HTML Parsing Fallback Loses Cell Position Data
**Risk:** If Option B (HTML parsing) is used, `start_row_offset_idx` and `column_header` flag are unavailable. Row grouping and header detection must rely on DOM structure.
**Likelihood:** Low if Option A (JSON storage) is implemented first.
**Mitigation:** HTML `<th>` tags partially replace `column_header` flag. Row position can be inferred from DOM order.

### 6.7 LOW: Existing Recovery Functions Conflict
**Risk:** Per-row pipeline adds Type F synthetic rows, but existing `_recover_no_access_records()` also runs in the same pipeline (post-LLM step). Could produce duplicates.
**Likelihood:** Medium.
**Mitigation:** If per-row mode handles Type F, skip the existing recovery step. Use the `ACM_ITEM_EXTRACTION_MODE` flag to gate recovery.

### 6.8 LOW: Prompt Regression for Bulk Path
**Risk:** Any changes to shared infrastructure (model provisioning, normalizers, validators) could break the existing bulk extraction path.
**Likelihood:** Low if Agent 4 is disciplined about not modifying shared code.
**Mitigation:** Run existing tests after every change. The bulk path has test coverage.

---

## Section 7: Recommended Execution Changes

### Original Plan
```
Phase 1 (parallel): Agent 1 + Agent 2 + Agent 5
Phase 2 (sequential): Agent 3
Phase 3 (sequential): Agent 4
Phase 4: Verification
```

### Revised Plan

```
Phase 0 (PREREQUISITE — must complete first):
  New task: Store DoclingDocument JSON
  - Modify DoclingAdapter to call doc.export_to_dict()
  - Create migration for docling_document table (or add field to acm_table_section)
  - Modify _store_docling_tables() to persist JSON
  - Modify _get_docling_tables() to retrieve JSON
  - Test with Broadmeadows PDF to verify JSON structure
  Estimated: 1 agent, ~2 hours

Phase 1 (parallel — after Phase 0):
  Agent 1: Row Segmentation — now has real JSON to parse
  Agent 2: Schemas + Mappers — REVISED:
    - Reuse ACMItemRecord OR create expanded ACMItemRowSimple (18 fields)
    - Map to ACMExtractionRecord (not ACMRecord)
    - Drop enum_matcher.py (reuse Jaro-Winkler from consensus/matcher.py)
    - Drop rapidfuzz dependency
  Agent 5: Fixtures — create BOTH JSON and HTML formats

Phase 2 (sequential — after Phase 1):
  Agent 3: Per-Row Extractor — REVISED:
    - Use provision_langchain_model() with num_ctx override
    - Include minimal picklist guidance in prompt
    - Output ACMItemRecord or expanded schema
    - Wire through _normalize_v3_records() → existing pipeline

Phase 3 (sequential — after Phase 2):
  Agent 4: Pipeline Integration — REVISED:
    - Use ACM_ITEM_EXTRACTION_MODE env var (not ACM_EXTRACTION_STRATEGY)
    - Gate existing recovery functions when per-row mode active
    - Verify bulk path unchanged

Phase 4: Verification (unchanged)
```

### Key Decision Points Before Starting

1. **DoclingDocument JSON storage:** Option A (store JSON) or Option B (parse HTML)?
   - Recommendation: Option A — the plan's value proposition is in lossless table structure

2. **Schema choice:** Reuse ACMItemRecord or create new ACMItemRowSimple?
   - Recommendation: Reuse ACMItemRecord — less code, already tested, has mapper

3. **Classification strategy:** Pattern-only in Python or keep in LLM prompt?
   - Recommendation: Keep `acm_classification` and `acm_sub_classification` in the LLM schema, then validate/override in Python post-processing. This gives the best of both worlds.

4. **Fuzzy matching library:** rapidfuzz or reuse existing Jaro-Winkler?
   - Recommendation: Reuse existing — no new dependency needed

---

## Appendix: Key File Reference

| File | Purpose | Lines |
|------|---------|-------|
| `open_notebook/extractors/providers/docling_adapter.py` | Docling extraction, TableFormer config | 1-214 |
| `open_notebook/extractors/orchestrator.py` | _get_docling_tables, _inject_docling_tables, _v3_extract_items, _normalize_v3_records | 1-515+ |
| `open_notebook/extractors/acm_schemas_v3.py` | ACMItemRecord (22 fields), BuildingExtractionResult | 1-93 |
| `open_notebook/extractors/acm_schemas.py` | ACMExtractionRecord (V2 schema with validators) | 1-350+ |
| `open_notebook/domain/acm.py` | ACMRecord (persistence model), BuildingRecord, ACMTableSection | 1-1170+ |
| `open_notebook/graphs/acm_extraction.py` | extract_items_node, recovery functions, save_records | 1-2273+ |
| `open_notebook/graphs/utils.py` | provision_langchain_model, parse_json_response, _apply_ollama_extraction_settings | 1-900+ |
| `open_notebook/extractors/normalizers/enums.py` | normalize_enum_value() | 1-128 |
| `open_notebook/extractors/normalizers/taxonomy.py` | classify_product(), ClassificationResult | 1-840 |
| `open_notebook/extractors/normalizers/recommendations.py` | normalize_recommendation() | 1-166 |
| `open_notebook/extractors/normalizers/sf_normalizer.py` | normalize_extraction_record() | 1-163 |
| `open_notebook/extractors/validators/sf_picklist_validator.py` | SalesforcePicklistValidator, validate_acm_chain() | 1-545 |
| `open_notebook/extractors/validators/acm_validator.py` | validate_acm_record() | 1-516 |
| `open_notebook/extractors/pipeline_event_bus.py` | PipelineEventBus, event types | 1-300+ |
| `open_notebook/extractors/consensus/matcher.py` | _jaro_winkler() pure-Python implementation | 69-128 |
| `commands/source_commands.py` | _store_docling_tables(), _store_raw_extractions(), _merge_provider_tables() | 130-555 |
| `prompts/acm/v3_item_extraction.jinja` | Current item extraction prompt (271 lines) | 1-271 |
| `prompts/acm/v3_building_extraction.jinja` | Building extraction prompt (141 lines) | 1-141 |
