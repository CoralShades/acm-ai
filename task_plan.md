# Task Plan — E27-S3: Hard-Lock OpenRouter to Anthropic + Production Features

## Phase 1: Replace Soft Routing Constants (CRITICAL)
- [ ] 1.1 Remove `OPENROUTER_IGNORED_PROVIDERS` and `OPENROUTER_PROVIDER_ORDER` constants
- [ ] 1.2 Add `OPENROUTER_ALLOWED_PROVIDERS = ["Anthropic"]` constant
- [ ] 1.3 Rewrite `_apply_openrouter_preferences()` with: provider.only, allow_fallbacks=false, zdr=true, data_collection=deny, require_parameters=true, Response Healing plugin, request metadata, transforms
- [ ] 1.4 Add deep merge logic: preserve existing extra_body fields, deep merge provider dict, append plugins array (no duplicates)
- [ ] 1.5 Add optional kwargs: source_id, building_name, stage_name for metadata tagging
- [ ] 1.6 Update log message to reflect new routing (provider.only, not provider.order)

## Phase 2: Provider Verification Helper
- [ ] 2.1 Add `_verify_provider_routing()` async function to utils.py (Generation API + response_metadata)
- [ ] 2.2 Import `httpx` and `os` at top of utils.py (httpx for async HTTP, os for API key)

## Phase 3: Instrument Extraction Stages with Verification
- [ ] 3.1 Add `_verify_provider_routing` import and call after ainvoke in `document_structure.py`
- [ ] 3.2 Add verification call in `building_inventory.py`
- [ ] 3.3 Add verification call in `page_tagger.py` (per-batch)
- [ ] 3.4 Add verification call in `orchestrator.py` (`_invoke` inner function)
- [ ] 3.5 Add verification call in `acm_extraction.py` (main extract_records + correction path)

## Phase 4: App Attribution Headers
- [ ] 4.1 Inject `default_headers` with HTTP-Referer and X-OpenRouter-Title into model via model_kwargs (if LangChain supports), OR add to extra_body metadata

## Phase 5: Prompt Caching Prep (SHOULD-HAVE)
- [ ] 5.1 Update SystemMessage content format to use list with cache_control in document_structure.py (try + log TODO if unsupported)
- [ ] 5.2 Similarly update building_inventory.py, page_tagger.py, orchestrator.py system prompts

## Phase 6: Clean Up
- [ ] 6.1 Remove all references to old constants (grep and fix any remaining OPENROUTER_IGNORED/ORDER refs)
- [ ] 6.2 Verify provision_extraction_fallback_model() also uses hard lock
- [ ] 6.3 Update .env.example OpenRouter section comments

## Phase 7: Unit Tests
- [ ] 7.1 Create `tests/test_openrouter_provider_routing.py` with test classes:
  - TestProviderHardLock (provider.only not order, allow_fallbacks=false, Anthropic only, zdr, data_collection, require_parameters)
  - TestResponseHealing (plugin present, no duplication on merge)
  - TestRequestMetadata (default metadata, source_id, building, stage, truncation)
  - TestDeepMerge (preserves existing extra_body, preserves existing provider fields)
  - TestOldConstantsRemoved (no OPENROUTER_IGNORED_PROVIDERS, no OPENROUTER_PROVIDER_ORDER)
  - TestProviderVerification (function exists, handles missing metadata, handles None, detects provider)

## Phase 8: Validation
- [ ] 8.1 Ruff lint pass
- [ ] 8.2 Run new tests: `pytest tests/test_openrouter_provider_routing.py -v`
- [ ] 8.3 Run full test suite: `pytest tests/ -x --ignore=tests/test_broadmeadows_e2e.py`
- [ ] 8.4 Frontend build check (no frontend changes expected, but verify)

## Phase 9: Sprint Status + Commit
- [ ] 9.1 Update sprint-status.yaml: add e27-s3 line as done
- [ ] 9.2 Commit with conventional commit message
