# Progress — E27-S3: Hard-Lock OpenRouter Provider Routing

## Session: 2026-02-28
### Status: IN PROGRESS — Planning Complete

### Pre-Read Complete
All mandatory files read and analyzed:
- `open_notebook/graphs/utils.py` — Current routing (lines 22-100), provision functions
- `open_notebook/graphs/acm_extraction.py` — ainvoke at lines 1287, 2025
- `open_notebook/extractors/orchestrator.py` — ainvoke at line 534 (inner _invoke)
- `open_notebook/extractors/document_structure.py` — ainvoke at line 152
- `open_notebook/extractors/building_inventory.py` — ainvoke at line 486
- `open_notebook/extractors/page_tagger.py` — ainvoke at line 363
- `api/model_provisioning.py` — Model catalog, no OpenRouter-specific routing
- `docs/sprint-artifacts/e18-s1-extraction-provider-compatibility.md` — Original fix context

### Key Findings
- Single chokepoint: ALL extraction paths flow through `provision_langchain_model()` → `_apply_openrouter_preferences()`
- Only 2 call sites for `_apply_openrouter_preferences()` (utils.py:134, utils.py:413)
- Current shallow merge in extra_body needs deepening for provider dict + plugins array
- 6 ainvoke() call sites need provider verification instrumentation

### Next Steps
1. Implement Phase 1 (replace constants + rewrite function)
2. Implement Phase 2 (verification helper)
3. Implement Phase 3 (instrument stages)
4. Implement Phase 7 (tests)
5. Validate (Phase 8)
