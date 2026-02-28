# Task Plan — E27-S4: Native JSON Schema Structured Outputs via OpenRouter

## Task 0: Story File Creation
- [x] 0.1 Create `docs/sprint-artifacts/e27-s4-native-json-schema-structured-outputs.md`

## Task 1: Schema Utilities (utils.py)
- [x] 1.1 Add `pydantic_to_openrouter_schema(model_class)` — resolves `$defs`, adds `additionalProperties: false`, normalizes Optional fields
- [x] 1.2 Add `_get_acm_extraction_schema()` — lazy-cached schema getter (module-level cache)
- [x] 1.3 Add `_inject_response_format(model, schema_dict, schema_name)` — injects `response_format: json_schema` into model's `extra_body` (OpenRouter only, stage-specific)
- [x] 1.4 Verify generated schema: no `$ref`, has `additionalProperties: false`, 8.3 KB size (acceptable)

## Task 2: Apply response_format to Extraction Call Sites
- [x] 2.1 `orchestrator.py:_llm_extract_building()` — call `_inject_response_format()` after `provision_langchain_model()`, before `model.ainvoke()`
- [x] 2.2 `acm_extraction.py:extract_records()` — call `_inject_response_format()` after model provisioning, before `model.ainvoke()`
- [x] 2.3 Verify: document_structure, building_inventory, page_tagger NOT modified (git diff confirms)

## Task 3: Spike Validation — Observe Wrapper Behavior
- [x] 3.1 Add temporary debug logging to `parse_json_response()` (gated by `ACM_DEBUG_RAW_RESPONSE` env var)
- [ ] 3.2 Run single Broadmeadows extraction with debug enabled — RUNNING (background task b3tt7la1q)
- [ ] 3.3 Evaluate: completionState present? Schema-valid JSON? New errors?
- [ ] 3.4 Remove temporary debug logging

## Task 4a: Remove Workaround Code (IF wrapper gone — Scenario A)
- [ ] 4a.1 Delete `_unwrap_completion_state()` from `utils.py`
- [ ] 4a.2 Remove call + import from `orchestrator.py` (2 sites: line 552, line 618)
- [ ] 4a.3 Remove call + import from `document_structure.py` (line 170)
- [ ] 4a.4 Remove call + import from `building_inventory.py` (line 504)
- [ ] 4a.5 Remove call + import from `page_tagger.py` (line 381)
- [ ] 4a.6 Remove call + import from `acm_extraction.py` (2 sites: line 1302, line 1451)
- [ ] 4a.7 Remove dead `with_structured_output()` try/except blocks if any remain

## Task 4b: Document and Retain (IF wrapper persists — Scenario B)
- [ ] 4b.1 Update `_unwrap_completion_state()` docstring with E27-S4 investigation notes
- [ ] 4b.2 Create `docs/architecture/e27-s4-json-schema-investigation.md`
- [ ] 4b.3 Remove `response_format` from extraction calls (no benefit if wrapper persists)
- [ ] 4b.4 Keep `_inject_response_format()` utility for future use but don't call it

## Task 5: Full Validation Run
- [ ] 5.1 Create `research-output/e27-s4/` directory — DONE
- [ ] 5.2 Run Broadmeadows validation — expect 31/31 (100%)
- [ ] 5.3 Run Alexander validation — expect >=40/43
- [ ] 5.4 Measure total extraction duration — target <=180s (was ~220s)

## Task 6: Tests
- [ ] 6.1 Add `TestResponseFormat` class to `test_openrouter_provider_routing.py`
- [ ] 6.2 Add `TestInjectResponseFormat` class
- [ ] 6.3 Handle `test_completion_state_unwrap.py` (Scenario A: delete, Scenario B: update)

## Task 7: Lint, Test Suite, Sprint Status
- [ ] 7.1 `ruff check . --fix` + `ruff check .`
- [ ] 7.2 `pytest tests/ -x --ignore=tests/test_broadmeadows_e2e.py`
- [ ] 7.3 `cd frontend && npm run build`
- [ ] 7.4 Update `sprint-status.yaml` — add e27-s4, mark done/partial
- [ ] 7.5 Commit + push

## Guard Rails (Pre-Commit Checklist)
- [ ] G1: Broadmeadows 31/31 — no regression
- [ ] G2: Alexander >=40/43 — no regression
- [ ] G3: Schema has no $ref — VERIFIED
- [ ] G4: Schema has additionalProperties: false — VERIFIED
- [ ] G5: Schema is cached (identity check) — VERIFIED
- [ ] G6: _unwrap_completion_state() only removed if AC-1 confirmed
- [ ] G7: provider.only: ["Anthropic"] preserved (E27-S3) — VERIFIED (not modified)
- [ ] G8: Response Healing plugin preserved (E27-S3) — VERIFIED (not modified)
- [ ] G9: ZDR preserved (E27-S3) — VERIFIED (not modified)
- [ ] G10: No with_structured_output() calls in extraction path (Scenario A)
- [ ] G11: All tests pass (1078+ pass, 0 regressions)
- [ ] G12: Extraction duration <=180s (Scenario A)
- [ ] G13: No ACM_DEBUG_RAW_RESPONSE in committed code
