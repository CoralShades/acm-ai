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

### Correct Approach: Stage-Specific Injection

Create `_inject_response_format(model, schema_dict, name)` helper. Apply ONLY at extraction call sites after `provision_langchain_model()` returns, before `model.ainvoke()`.

Non-extraction stages (document_structure, building_inventory, page_tagger) don't get response_format — but the wrapper was a routing artifact (non-Anthropic providers). With `provider.only: ["Anthropic"]` (E27-S3), the wrapper should be gone from ALL stages regardless.

### `with_structured_output()` Remaining Usage

`metadata_extractor.py:231` — uses `model.with_structured_output(DocumentMetaLLM)`. This is metadata extraction (NOT ACM extraction). Do NOT touch — different pipeline path, different schema.

### `_normalize_extraction_json()` — KEEP

Located at orchestrator.py:135. Coerces `data_issues: str → list`, `data_issues: null → []`. Even with schema enforcement, retain as defense-in-depth. Field validators in Pydantic handle similar logic but `_normalize_extraction_json()` catches pre-validation edge cases.

### Pydantic Schema Complexity

`ACMExtractionResult` contains:
- `records: List[ACMExtractionRecord]` — 40+ fields, many Optional
- `status: ExtractionStatus` (str Enum)
- `confidence_distribution: ConfidenceDistribution` (nested model)
- Multiple `@field_validator` decorators (`result`, `friable`, `risk_status`, `material_condition`, `area_type`, `quantity`, `data_issues`)

`model_json_schema()` will generate `$defs` for: ExtractionStatus, ExtractionConfidence, ConfidenceDistribution, ACMExtractionRecord. All must be inlined. Field validators won't appear in schema — they're post-parse Python logic.

Estimated schema size: 8-15KB (acceptable for OpenRouter requests).

### Sprint Status Location

`epic-27: done` at line 362. Need to reopen or add S4 below the existing entries.
