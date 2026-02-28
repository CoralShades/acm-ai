# Progress — E27-S4: Native JSON Schema Structured Outputs

## Session: 2026-02-28
### Status: IN PROGRESS — Spike Running

### Reboot Check
1. **Last completed milestone**: T0 (story file), T1 (schema utilities), T2 (response_format injection at call sites)
2. **Current active task**: T3 — Spike validation running in background (task b3tt7la1q)
3. **Blockers**: Waiting for spike extraction to complete (~5-10 min)
4. **Files last modified**:
   - `open_notebook/graphs/utils.py` — added `pydantic_to_openrouter_schema()`, `_get_acm_extraction_schema()`, `_inject_response_format()`, temp debug logging in `parse_json_response()`
   - `open_notebook/extractors/orchestrator.py` — added `_inject_response_format()` call after model provisioning
   - `open_notebook/graphs/acm_extraction.py` — added `_inject_response_format()` call after model provisioning
   - `docs/sprint-artifacts/e27-s4-native-json-schema-structured-outputs.md` — story file created
5. **Next planned action**: Check spike results → decide Scenario A (remove workaround) vs Scenario B (retain)

### Implementation Log

#### T0: Story File (DONE)
- Created `docs/sprint-artifacts/e27-s4-native-json-schema-structured-outputs.md`

#### T1: Schema Utilities (DONE)
- `pydantic_to_openrouter_schema()` — resolves $defs, adds additionalProperties:false
- `_get_acm_extraction_schema()` — lazy-cached, 8.3 KB schema
- `_inject_response_format()` — stage-specific OpenRouter-only injection
- All verification checks passed (no $ref, additionalProperties, caching, size)

#### T2: Call Site Injection (DONE)
- `orchestrator.py:_llm_extract_building()` — injected after `provision_langchain_model()`
- `acm_extraction.py:extract_records()` — injected after model provisioning
- document_structure, building_inventory, page_tagger: NOT modified (confirmed via git diff)

#### T3: Spike Validation (RUNNING)
- Temporary debug logging added to `parse_json_response()` (ACM_DEBUG_RAW_RESPONSE env gate)
- Full Broadmeadows extraction running with debug enabled
- Output: `research-output/e27-s4/spike_broadmeadows.log`
- Background task: b3tt7la1q

### Key Decision: Stage-Specific Injection
Instead of modifying shared `_apply_openrouter_preferences()` (which would break non-extraction stages), created `_inject_response_format()` called only at extraction sites. This is architecturally correct because each stage uses a different schema.
