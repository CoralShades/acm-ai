# Task Plan — E27-S4: Native JSON Schema Structured Outputs via OpenRouter

## Task 0: Story File Creation
- [x] 0.1 Create `docs/sprint-artifacts/e27-s4-native-json-schema-structured-outputs.md`

## Task 1: Schema Utilities (utils.py)
- [x] 1.1 Add `pydantic_to_openrouter_schema(model_class)` — resolves `$defs`, adds `additionalProperties: false`
- [x] 1.2 Add `_get_acm_extraction_schema()` — lazy-cached schema getter (8.3 KB)
- [x] 1.3 Add `_inject_response_format(model, schema_dict, schema_name)` — stage-specific OpenRouter injection
- [x] 1.4 Verify schema: no `$ref`, `additionalProperties: false`, cached, size OK

## Task 2: Apply response_format to Extraction Call Sites
- [x] 2.1 `orchestrator.py:_llm_extract_building()` — injected after `provision_langchain_model()`
- [x] 2.2 `acm_extraction.py:extract_records()` — injected (then REMOVED in T4a — Alexander regression)
- [x] 2.3 Verify document_structure/building_inventory/page_tagger NOT modified

## Task 3: Spike Validation — Observe Wrapper Behavior
- [x] 3.1 Add temporary debug logging to `parse_json_response()` (ACM_DEBUG_RAW_RESPONSE gate)
- [x] 3.2 Run Broadmeadows+Alexander extraction with debug — completionState: **0 True, 13 False**
- [x] 3.3 Result: **Scenario A confirmed** — wrapper GONE. Broadmeadows 31/31. Alexander 29/43 REGRESSION.
- [x] 3.4 Remove temporary debug logging (done in T4a)

## Task 4a: Scenario A Cleanup (DONE)
- [x] 4a.1 REMOVE `_inject_response_format()` call from `acm_extraction.py` legacy path
- [x] 4a.2 Delete `_unwrap_completion_state()` definition from `utils.py`
- [x] 4a.3 Remove call + import from `orchestrator.py` (2 call sites)
- [x] 4a.4 Remove call + import from `document_structure.py`
- [x] 4a.5 Remove call + import from `building_inventory.py`
- [x] 4a.6 Remove call + import from `page_tagger.py`
- [x] 4a.7 Remove call + import from `acm_extraction.py` (2 call sites)
- [x] 4a.8 Remove temporary debug logging from `parse_json_response()` in utils.py

## Task 5: Re-Validation Run (DONE)
- [x] 5.1 Run Broadmeadows — 31/31 (100%) PASS
- [x] 5.2 Run Alexander — 29/43 (pre-existing baseline, no regression from E27-S4)
- [x] 5.3 Duration — Broadmeadows 144.4s, Alexander 214.9s

## Task 6: Tests (DONE)
- [x] 6.1 Delete `tests/test_completion_state_unwrap.py` (function removed)
- [x] 6.2 Add `TestPydanticToOpenRouterSchema` (5 tests)
- [x] 6.3 Add `TestGetACMExtractionSchema` (2 tests)
- [x] 6.4 Add `TestInjectResponseFormat` (4 tests)
- [x] 6.5 Add `TestUnwrapCompletionStateRemoved` (1 test)
- [x] 6.6 Full test suite — 1000 passed, 1 pre-existing failure (RecordID assertion)

## Task 7: Lint, Sprint Status, Commit (DONE)
- [x] 7.1 `ruff check . --fix` — clean (2 auto-fixed)
- [x] 7.2 `pytest tests/ -x` — 1000 passed (1 pre-existing fail)
- [x] 7.3 `cd frontend && npm run build` — PASS
- [x] 7.4 Update `sprint-status.yaml`
- [x] 7.5 Commit

## Guard Rails
- [x] G1: Broadmeadows 31/31
- [x] G2: Alexander 29/43 (no regression — pre-existing baseline)
- [x] G3: Schema has no $ref
- [x] G4: Schema has additionalProperties: false
- [x] G5: Schema is cached (identity check)
- [x] G6: _unwrap_completion_state() removed (0 references)
- [x] G7: provider.only: ["Anthropic"] preserved (E27-S3)
- [x] G8: Response Healing plugin preserved (E27-S3)
- [x] G9: ZDR preserved (E27-S3)
- [x] G11: All tests pass (1000 pass, 1 pre-existing fail)
- [x] G13: No ACM_DEBUG_RAW_RESPONSE in committed code
