# MCS2: Schema Inference Node — Progress

## Session 1 — 2026-03-18

### Completed
- [x] T1: Created `RecoveryConfig` dataclass in `recovery_config.py`
- [x] T2: Created `InferredSchema`, `ColumnMapping` dataclasses + `compute_header_signature()` + `SF_FIELD_CATALOG` in `schema_inference.py`
- [x] T3: Implemented header collection from `acm_table_section.docling_document_json`
- [x] T4: Created LLM schema inference prompt (`prompts/acm/schema_inference.jinja`)
- [x] T5: Implemented `schema_inference_node()` — header collection → LLM inference → InferredSchema
- [x] T6: Added `inferred_schema: Optional[InferredSchema]` to `ExtractionState` TypedDict
- [x] T7: Wired as LangGraph node: `save_intelligence → schema_inference → extract_building`
- [x] T8-T10: 24 unit tests (19 dataclass/signature + 5 async node tests with mocked DB/LLM)
- [x] T11: Full test suite passes (pre-existing failures only)
- [x] T12: Lint clean (`ruff check` passes)
- [x] Updated `test_page_tagger.py` graph wiring test for new schema_inference node

### Files Created
- `open_notebook/extractors/recovery_config.py`
- `open_notebook/extractors/schema_inference.py`
- `prompts/acm/schema_inference.jinja`
- `tests/test_schema_inference.py`
- `docs/sprint-artifacts/mcs2-schema-inference/` (planning files)

### Files Modified
- `open_notebook/graphs/acm_extraction.py` (ExtractionState + node + wiring)
- `tests/test_page_tagger.py` (graph wiring test updated)

### Key Decisions
- Deferred imports inside `schema_inference_node()` to avoid circular deps
- `SF_TO_CANONICAL` reverse lookup enables building canonical_mapping from LLM response
- Graceful degradation: any failure → log warning, return empty dict, pipeline continues
- Header signature: SHA-256 truncated to 16 hex chars for readability

## Session 2 — 2026-03-20 (MCS13 DocumentMeta Bug Fix)

### Bug Found & Fixed
- **Root cause**: `schema_inference_node` called `.get()` on Pydantic `DocumentMeta` model at 3 locations (lines 463, 487, 547). Pydantic BaseModel has no `.get()` method, causing `AttributeError` that was silently caught by graceful degradation — making schema inference **never run** for any extraction.
- **Fix**: Replaced all 3 `.get()` calls with `getattr()`:
  - Line 465: `getattr(doc_meta, "format_name", None) if doc_meta else None`
  - Line 486: `getattr(state.get("document_metadata"), "format_name", None)`
  - Line 547: same pattern
- **Tests**: 2 regression tests added (Pydantic model in state for both LLM path and cache hit path)
- **Result**: 26/26 tests pass, ruff lint clean

### Impact
- Schema inference now actually runs during extraction
- New format profiles will be created and cached in `consultant_format_profile` table
- Cache hits for previously seen consultant formats will work
- Column mapping inference for multi-consultant support is now functional
- Prior to this fix, only 1 format profile existed (from manual testing during MCS7)

### Files Modified
- `open_notebook/extractors/schema_inference.py` — fixed 3 `.get()` calls
- `tests/test_schema_inference.py` — added 2 regression tests

### Audit Reference
- Identified in: MCS7 validation trace-analysis.md (line 214, 226, 256, 325, 371)
- Dependencies: MCS8 (ghost save fix)
