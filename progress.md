# Progress — E27-S3: Hard-Lock OpenRouter Provider Routing

## Session: 2026-02-28
### Status: COMPLETE

### Implementation Summary

#### Phase 1: Replace Soft Routing (utils.py)
- Removed `OPENROUTER_IGNORED_PROVIDERS` and `OPENROUTER_PROVIDER_ORDER`
- Added `OPENROUTER_ALLOWED_PROVIDERS = ["Anthropic"]`
- Rewrote `_apply_openrouter_preferences()` with 6 OpenRouter features:
  1. `provider.only` — hard allowlist (Anthropic ONLY)
  2. `allow_fallbacks=False` — fail, don't silently reroute
  3. `zdr=True` — Zero Data Retention for government data
  4. `data_collection="deny"` — don't train on government data
  5. Response Healing plugin — auto-fix malformed JSON
  6. Request metadata — app/pipeline/source_id/building/stage tagging
- Deep merge logic: preserves existing extra_body, deep merges provider dict, appends plugins without duplicates
- Added optional kwargs: source_id, building_name, stage_name

#### Phase 2: Provider Verification (utils.py)
- Added `_verify_provider_routing()` async function
- Two methods: response_metadata (fast path) + Generation API (definitive)
- Non-blocking — extraction continues if verification fails

#### Phase 3: Instrument Extraction Stages
- `document_structure.py` — verification after ainvoke
- `building_inventory.py` — verification after ainvoke
- `page_tagger.py` — verification after ainvoke (per batch)
- `orchestrator.py` — verification inside _invoke() per building
- `acm_extraction.py` — verification after main extract + correction ainvoke

#### Phase 4: Supporting Files
- `.env.example` — updated OpenRouter section with routing documentation

### Tests
- 30 new tests in `tests/test_openrouter_provider_routing.py` — all pass
- 7 test classes: ProviderHardLock(8), ResponseHealing(3), RequestMetadata(6), DeepMerge(3), OldConstantsRemoved(3), ProviderVerification(6), Transforms(1)
- Full suite: 1078 pass, 0 fail (1 pre-existing docling storage test excluded)

### Validation
- Ruff lint: PASS
- New tests: 30/30 PASS
- Full suite: 1078 pass, 0 regressions
- Old constants: grep confirms zero references to OPENROUTER_IGNORED/ORDER
