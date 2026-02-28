# Progress — E27-S4: Native JSON Schema Structured Outputs

## Session: 2026-02-28
### Status: COMPLETE — Ready to commit

### Reboot Check
1. **Last completed milestone**: All tasks T0-T7 complete
2. **Current active task**: Commit
3. **Blockers**: None
4. **Files last modified**: All files below
5. **Next planned action**: Commit and close story

### Final Results
- Broadmeadows: **31/31 (100%)** in 144.4s
- Alexander: **29/43 (67.4%)** — pre-existing baseline, no regression from E27-S4
- Tests: **1000 passed** (1 pre-existing fail, 10 deleted, 12 new)
- Lint: clean
- Frontend build: PASS

### Files Changed
- `open_notebook/graphs/utils.py` — Added pydantic_to_openrouter_schema, _get_acm_extraction_schema, _inject_response_format. Deleted _unwrap_completion_state. Removed temp debug logging.
- `open_notebook/extractors/orchestrator.py` — Added _inject_response_format call. Removed _unwrap_completion_state (2 sites).
- `open_notebook/graphs/acm_extraction.py` — Removed _unwrap_completion_state (2 sites). No _inject_response_format (legacy path excluded).
- `open_notebook/extractors/document_structure.py` — Removed _unwrap_completion_state (1 site).
- `open_notebook/extractors/building_inventory.py` — Removed _unwrap_completion_state (1 site).
- `open_notebook/extractors/page_tagger.py` — Removed _unwrap_completion_state (1 site).
- `tests/test_completion_state_unwrap.py` — DELETED (function removed)
- `tests/test_openrouter_provider_routing.py` — Added 5 new test classes (12 tests)
- `docs/sprint-artifacts/e27-s4-native-json-schema-structured-outputs.md` — Story file
- `docs/sprint-artifacts/sprint-status.yaml` — e27-s4 marked done
