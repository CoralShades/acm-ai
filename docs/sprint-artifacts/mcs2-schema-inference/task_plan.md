# MCS2: Schema Inference Node — Task Plan

**Story:** Multi-Consultant Story 2 | **SP:** 8 | **Wave:** 2
**Design:** `docs/architecture/multi-consultant-format-design.md` Sections 5.2, 5.5

## Tasks

- [ ] T1: Create `RecoveryConfig` dataclass in `open_notebook/extractors/recovery_config.py`
- [ ] T2: Create `InferredSchema` dataclass in `open_notebook/extractors/schema_inference.py`
- [ ] T3: Implement header collection from `acm_table_section.docling_document_json`
- [ ] T4: Design LLM schema inference prompt (`prompts/acm/schema_inference.jinja`)
- [ ] T5: Implement `SchemaInferenceNode` — header collection → cache check → LLM inference → InferredSchema
- [ ] T6: Add `inferred_schema: InferredSchema | None` to `ExtractionState` TypedDict
- [ ] T7: Wire as LangGraph node: `save_intelligence → schema_inference → extract_building`
- [ ] T8: Write unit tests — mock Docling tables → verify InferredSchema construction
- [ ] T9: Write unit tests — mock LLM responses → verify column mapping
- [ ] T10: Write unit tests — verify graceful degradation (no docling_json → skip inference)
- [ ] T11: Run full test suite (`uv run pytest tests/ -x`)
- [ ] T12: Run lint (`uv run ruff check .`)

## Agent Assignment

| Agent | Tasks | Files |
|-------|-------|-------|
| agent-1 (dataclasses) | T1, T2 | `recovery_config.py`, `schema_inference.py` (dataclasses only) |
| agent-2 (node+graph) | T3, T5, T6, T7 | `schema_inference.py` (node logic), `acm_extraction.py` |
| agent-3 (prompt) | T4 | `prompts/acm/schema_inference.jinja` |
| agent-4 (tests) | T8, T9, T10 | `tests/test_schema_inference.py` |
| main thread | T11, T12 | verification |
