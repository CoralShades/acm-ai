# Multi-Consultant Story 2: Schema Inference Node
# Generated via /generate-prompt --save --with-plan --tmux

**SP: 8 | Wave: 2 | Dependencies: Story 1 complete**
**Design doc: `docs/architecture/multi-consultant-format-design.md` Section 5.2, Section 7 Story 2**

## Skills to Load

/planning-with-files — persistent markdown plan
/langgraph-fundamentals — LangGraph node/state/edge patterns
/prompt-engineering — design schema inference LLM prompt
/pydantic-models-py — InferredSchema dataclass design
/test-driven-development — TDD for inference logic
/verification-before-completion — verify before claiming done

---

## Prerequisites

- Branch: `git checkout ACMV3`
- Story 1 complete (format detectors fixed)
- SurrealDB running (for `acm_table_section` queries)
- Read design doc Sections 5.2 (Schema Inference Node) and 5.5 (Recovery Config)

---

## Glossary

| Term | Definition |
|------|-----------|
| Schema inference | Auto-detecting table structure and mapping column headers to SF fields from unknown PDFs |
| InferredSchema | New dataclass: column_mapping, canonical_mapping, level_regex, recovery_config, confidence, consultant_name |
| Header signature | Sorted hash of unique column header text — used as cache key for format profiles |
| ExtractionState | LangGraph TypedDict carrying all pipeline data between nodes |
| PREFLIGHT | Pipeline stage before ORCHESTRATOR — schema inference node goes after this |
| `acm_table_section` | SurrealDB table storing extracted table data including `docling_document_json` |
| RecoveryConfig | New dataclass for format-specific recovery settings (not_sampled_terms, restriction_terms, etc.) |

---

## Key Files

**Read:**
- `docs/architecture/multi-consultant-format-design.md` — Sections 5.2, 5.4, 5.5
- `open_notebook/graphs/acm_extraction.py` — existing graph nodes, ExtractionState TypedDict
- `open_notebook/extractors/row_segmenter.py` — COLUMN_ALIASES, detect_column_mapping()
- `open_notebook/extractors/format_detectors/__init__.py` — detector registry pattern
- `open_notebook/extractors/providers/docling_adapter.py` — how docling_document_json is structured

**Create:**
- `open_notebook/extractors/schema_inference.py` — SchemaInferenceNode, InferredSchema, header collection, LLM prompt
- `open_notebook/extractors/recovery_config.py` — RecoveryConfig dataclass
- `prompts/acm/schema_inference.jinja` — LLM schema inference prompt template
- `tests/test_schema_inference.py` — unit tests with mock Docling table data

**Modify:**
- `open_notebook/graphs/acm_extraction.py` — add schema inference node between PREFLIGHT and ORCHESTRATOR, add `inferred_schema` to ExtractionState

---

## Plan

Create `docs/sprint-artifacts/mcs2-schema-inference/task_plan.md`:
- [ ] Design `InferredSchema` dataclass (Section 5.2 of design doc)
- [ ] Design `RecoveryConfig` dataclass (Section 5.5 of design doc)
- [ ] Implement header collection from `acm_table_section.docling_document_json`
- [ ] Design LLM schema inference prompt (`schema_inference.jinja`)
- [ ] Implement `SchemaInferenceNode` — header collection → cache check → LLM inference → InferredSchema
- [ ] Add `inferred_schema: InferredSchema | None` to `ExtractionState` TypedDict
- [ ] Wire as LangGraph node: PREFLIGHT → schema_inference → ORCHESTRATOR
- [ ] Write unit tests: mock Docling tables → verify InferredSchema construction
- [ ] Write unit tests: mock LLM responses → verify column mapping
- [ ] Write unit tests: verify graceful degradation (no docling_json → skip inference)
- [ ] Run full test suite
- [ ] Run lint

---

## Agent Strategy: TMUX

```
Pane 0 (left-top):    Implementation — schema_inference.py, recovery_config.py
Pane 1 (left-bottom): Graph wiring — acm_extraction.py node addition
Pane 2 (right-top):   Prompt design — schema_inference.jinja
Pane 3 (right-bottom): Test runner — continuous pytest
```

---

## Context7 Directives

1. resolve-library-id for "langgraph" → query-docs for "node conditional edges state typing add_node add_edge"
2. resolve-library-id for "pydantic" → query-docs for "dataclass model_validate field_validator"
3. resolve-library-id for "langchain" → query-docs for "prompt template jinja2 structured output ChatPromptTemplate"

---

## Verification Checklist

- [ ] `InferredSchema` dataclass created with all fields from design doc Section 5.2
- [ ] `RecoveryConfig` dataclass created with all fields from design doc Section 5.5
- [ ] Schema inference node wired in graph: PREFLIGHT → schema_inference → ORCHESTRATOR
- [ ] `ExtractionState` has `inferred_schema` field
- [ ] LLM prompt returns valid JSON with column mappings
- [ ] Graceful degradation: pipeline works when no `docling_document_json` available
- [ ] `uv run pytest tests/test_schema_inference.py -v` — all tests pass
- [ ] `uv run pytest tests/ -x` — full suite passes
- [ ] `uv run ruff check .` — lint clean

---

## Commit Template

```
feat(extraction): add schema inference node — auto-detect column mappings from PDF headers

- Create InferredSchema + RecoveryConfig dataclasses
- Implement header collection from acm_table_section docling_document_json
- Design LLM schema inference prompt (schema_inference.jinja)
- Wire as LangGraph node between PREFLIGHT and ORCHESTRATOR
- Graceful degradation when docling_json unavailable
- Multi-Consultant Story 2 of 7

Co-Authored-By: Claude <noreply@anthropic.com>
```
