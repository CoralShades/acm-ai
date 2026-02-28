# Task Plan — E27-S3: Hard-Lock OpenRouter to Anthropic + Production Features

## Phase 1: Replace Soft Routing Constants (CRITICAL)
- [x] 1.1 Remove `OPENROUTER_IGNORED_PROVIDERS` and `OPENROUTER_PROVIDER_ORDER` constants
- [x] 1.2 Add `OPENROUTER_ALLOWED_PROVIDERS = ["Anthropic"]` constant
- [x] 1.3 Rewrite `_apply_openrouter_preferences()` with: provider.only, allow_fallbacks=false, zdr=true, data_collection=deny, require_parameters=true, Response Healing plugin, request metadata, transforms
- [x] 1.4 Add deep merge logic: preserve existing extra_body fields, deep merge provider dict, append plugins array (no duplicates)
- [x] 1.5 Add optional kwargs: source_id, building_name, stage_name for metadata tagging
- [x] 1.6 Update log message to reflect new routing (provider.only, not provider.order)

## Phase 2: Provider Verification Helper
- [x] 2.1 Add `_verify_provider_routing()` async function to utils.py (Generation API + response_metadata)
- [x] 2.2 Import `httpx` and `os` at top of utils.py

## Phase 3: Instrument Extraction Stages with Verification
- [x] 3.1 Add `_verify_provider_routing` import and call after ainvoke in `document_structure.py`
- [x] 3.2 Add verification call in `building_inventory.py`
- [x] 3.3 Add verification call in `page_tagger.py` (per-batch)
- [x] 3.4 Add verification call in `orchestrator.py` (`_invoke` inner function)
- [x] 3.5 Add verification call in `acm_extraction.py` (main extract_records + correction path)

## Phase 4: App Attribution Headers
- [x] 4.1 Metadata-based observability (app, pipeline, source_id, building, stage tags in extra_body)

## Phase 5: Prompt Caching Prep — DEFERRED
- [ ] 5.1 Update SystemMessage content format with cache_control (deferred — needs LangChain/Esperanto testing)

## Phase 6: Clean Up
- [x] 6.1 Remove all references to old constants (grep confirms zero remaining)
- [x] 6.2 Verify provision_extraction_fallback_model() also uses hard lock (it calls _apply_openrouter_preferences)
- [x] 6.3 Update .env.example OpenRouter section comments

## Phase 7: Unit Tests
- [x] 7.1 Create `tests/test_openrouter_provider_routing.py` — 30 tests, 7 classes, all pass

## Phase 8: Validation
- [x] 8.1 Ruff lint pass
- [x] 8.2 Run new tests: 30/30 pass
- [x] 8.3 Run full test suite: 1078 pass, 0 regressions
- [x] 8.4 Old constants grep: zero references

## Phase 9: Sprint Status + Commit
- [x] 9.1 Update sprint-status.yaml
- [ ] 9.2 Commit (awaiting user approval)
