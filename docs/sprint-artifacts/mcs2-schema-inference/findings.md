# MCS2: Schema Inference Node — Findings

## Architecture Decisions

### Graph Wiring
- Schema inference goes between `save_intelligence` and `extract_building`
- Current flow: `save_intelligence → extract_building → extract_items → ...`
- New flow: `save_intelligence → schema_inference → extract_building → extract_items → ...`

### ExtractionState Addition
- Add `inferred_schema: Optional[InferredSchema]` (default None for backward compat)
- InferredSchema is Optional because: (1) no docling_json tables, (2) inference skipped

### Header Source
- Headers come from `acm_table_section` records in SurrealDB
- Each has `docling_document_json` field with table cells including `column_header=True`
- Query: `SELECT docling_document_json FROM acm_table_section WHERE source_id = $source_id`

### Graceful Degradation
- If no `docling_document_json` tables → skip inference, return state unchanged
- If LLM call fails → log warning, skip inference, continue pipeline
- Pipeline must work identically to current behavior when `inferred_schema` is None

### Bug: DocumentMeta .get() AttributeError (Found in MCS7, Fixed in MCS13)
- **Root cause**: `schema_inference_node` accessed `state["document_metadata"]` using `.get("format_name")` — but the value is a Pydantic `DocumentMeta` model, not a dict
- Pydantic BaseModel has no `.get()` method → `AttributeError` silently caught by graceful degradation
- **Impact**: Schema inference never ran for any extraction — no format profiles created, no cache hits
- **Fix (2026-03-20)**: Replaced 3 `.get()` calls (lines 463, 487, 547) with `getattr(doc_meta, "format_name", None)`
- **Lesson**: Graceful degradation can mask real bugs — the error was silently swallowed, making the feature appear to work (no crash) while actually being completely non-functional
