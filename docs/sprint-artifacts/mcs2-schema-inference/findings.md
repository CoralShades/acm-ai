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
