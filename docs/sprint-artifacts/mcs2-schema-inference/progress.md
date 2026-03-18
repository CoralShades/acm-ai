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
