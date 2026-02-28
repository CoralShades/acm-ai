# Findings — E27-S4: Native JSON Schema Structured Outputs

## Code Audit (2026-02-28)

### `_unwrap_completion_state()` — Definition + 7 Call Sites

| # | File | Line | Context |
|---|------|------|---------|
| 0 | `open_notebook/graphs/utils.py` | 342 | **Definition** |
| 1 | `open_notebook/extractors/orchestrator.py` | 552 | `_invoke()` inside `_llm_extract_building` |
| 2 | `open_notebook/extractors/orchestrator.py` | 618 | Schema-error fallback path |
| 3 | `open_notebook/extractors/document_structure.py` | 170 | `_llm_extract_structure()` |
| 4 | `open_notebook/extractors/building_inventory.py` | 504 | `_llm_compile_inventory()` |
| 5 | `open_notebook/extractors/page_tagger.py` | 381 | `_llm_tag_batch()` |
| 6 | `open_notebook/graphs/acm_extraction.py` | 1302 | `extract_records()` main path |
| 7 | `open_notebook/graphs/acm_extraction.py` | 1451 | `extract_records()` fallback path |

Import sites: orchestrator.py:45, document_structure.py:145, building_inventory.py:479, page_tagger.py:357, acm_extraction.py:79

Test file: `tests/test_completion_state_unwrap.py` — 105 lines, 10 tests

### CRITICAL DESIGN ISSUE: Shared Chokepoint

Task spec says add `response_format: json_schema` with `ACMExtractionResult` to `_apply_openrouter_preferences()`. **This would BREAK non-extraction stages.**

`_apply_openrouter_preferences()` is called by ALL stages via `provision_langchain_model()`:

| Stage | Schema | Breaks if ACMExtractionResult enforced? |
|-------|--------|----------------------------------------|
| document_structure | `DocumentStructureLLM` | YES |
| building_inventory | `BuildingInventory` | YES |
| page_tagger | `PageTagBatch` | YES |
| metadata_extractor | `DocumentMetaLLM` (with_structured_output) | YES |
| orchestrator extraction | `ACMExtractionResult` | NO — correct |
| acm_extraction extract_records | `ACMExtractionResult` | NO — correct |

### Solution: Stage-Specific Injection (Implemented)

Created `_inject_response_format(model, schema_dict, name)` helper. Applied ONLY at extraction call sites (orchestrator.py + acm_extraction.py) after `provision_langchain_model()` returns, before `model.ainvoke()`.

Non-extraction stages keep existing behavior. The completionState wrapper was a routing artifact — with `provider.only: ["Anthropic"]` (E27-S3), it should be gone from ALL stages.

### Schema Generation Results

- `pydantic_to_openrouter_schema(ACMExtractionResult)` generates 8,489 chars (8.3 KB)
- All `$defs` inlined (ExtractionStatus enum, ConfidenceDistribution, ACMExtractionRecord)
- `additionalProperties: false` on root + ACMExtractionRecord
- Schema is lazily cached (`_get_acm_extraction_schema()` — identity check confirmed)
- `anyOf` patterns for Optional fields preserved (OpenRouter handles these)

### `with_structured_output()` Remaining Usage

`metadata_extractor.py:231` — uses `model.with_structured_output(DocumentMetaLLM)`. Different pipeline path, different schema. Do NOT touch.

### `_normalize_extraction_json()` — KEEP

Located at orchestrator.py:135. Coerces `data_issues: str -> list`, `data_issues: null -> []`. Retain as defense-in-depth even with schema enforcement.

### Sprint Status

`epic-27: done` at sprint-status.yaml line 362. Need to add S4 entry.

### Spike Validation (In Progress)

Running `ACM_DEBUG_RAW_RESPONSE=1` with full Broadmeadows extraction. Background task b3tt7la1q. Will reveal whether completionState wrapper appears with response_format: json_schema + Anthropic direct routing.
