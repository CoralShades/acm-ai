# Story E27-S4: Native JSON Schema Structured Outputs via OpenRouter

Status: in-progress

## Story

As a **compliance officer running ACM extractions**,
I want **the extraction pipeline to use OpenRouter's native JSON Schema enforcement**,
so that **the LLM always returns schema-valid JSON directly, eliminating the
completionState wrapper workaround and ~43s of wasted latency per extraction**.

## Background

E27-S1 fixed the `completionState` wrapper problem with a workaround:
`ainvoke()` + `parse_json_response()` + `_unwrap_completion_state()`. This works
but bypasses schema enforcement entirely — the LLM can return any JSON structure.

E27-S3 locked routing to `provider.only: ["Anthropic"]`. With Anthropic direct,
OpenRouter's native `response_format: json_schema` enforcement should return clean
schema-valid JSON with no wrapper. This story tests that hypothesis and — if
confirmed — removes the workaround code.

## Acceptance Criteria

1. **AC-1: No completionState wrapper** — With `response_format: json_schema` +
   `provider.only: ["Anthropic"]`, confirm the response contains clean JSON
   matching `ACMExtractionResult` schema with NO `completionState` envelope.
2. **AC-2: Broadmeadows 31/31** — No accuracy regression from E26-S6 baseline.
3. **AC-3: Alexander ≥40/43** — No regression from E27-S1/S2 baseline.
4. **AC-4: `_unwrap_completion_state()` removed** — If AC-1 confirmed, delete
   the function and all call sites. If NOT confirmed, document the finding and
   retain as-is with updated comments.
5. **AC-5: `with_structured_output()` dead calls removed** — All stages use direct
   `ainvoke()` + schema-validated path. No try/except around dead structured output
   attempts adding latency.
6. **AC-6: Latency improvement** — Extraction duration ≤180s per run (vs ~220s
   baseline with failed structured output attempts).
7. **AC-7: Tests updated** — Tests for `_unwrap_completion_state()` either deleted
   (if function removed) or updated to document the retained-as-workaround state.

## Decision Gate

| Finding | Action |
|---------|--------|
| No wrapper + schema-valid JSON returned | Remove `_unwrap_completion_state()`, update comments, close story as full success |
| Wrapper still present with json_schema | Retain workaround, document OpenRouter behavior, close as partial — file E28 for native SDK |
| New error type introduced | Revert `response_format` addition, keep E27-S1 path, investigate separately |

## Tasks / Subtasks

- [x] Task 0: Create story file (this file)
- [ ] Task 1: Generate JSON Schema from Pydantic models + injection helper
- [ ] Task 2: Add `response_format: json_schema` to extraction call sites
- [ ] Task 3: Spike validation — single Broadmeadows extraction to observe wrapper behavior
- [ ] Task 4a (if wrapper gone): Remove `_unwrap_completion_state()` and dead `with_structured_output()` calls
- [ ] Task 4b (if wrapper persists): Document, update comments, retain workaround
- [ ] Task 5: Full validation run (Broadmeadows + Alexander)
- [ ] Task 6: Update tests
- [ ] Task 7: Lint, full test suite, sprint status update

## Dev Notes

### Design Decision: Stage-Specific Injection

`_apply_openrouter_preferences()` is shared by ALL extraction stages. Each stage
uses a DIFFERENT Pydantic schema (DocumentStructureLLM, BuildingInventory,
PageTagBatch, ACMExtractionResult). Adding ACMExtractionResult to the shared
function would BREAK non-extraction stages.

Solution: `_inject_response_format(model, schema_dict, name)` — called ONLY at
extraction call sites (orchestrator + acm_extraction), after model provisioning,
before `model.ainvoke()`.

### Files to Change

| File | Change | Condition |
|------|--------|-----------|
| `open_notebook/graphs/utils.py` | Add `pydantic_to_openrouter_schema()`, `_get_acm_extraction_schema()`, `_inject_response_format()` | Always |
| `open_notebook/extractors/orchestrator.py` | Call `_inject_response_format()` before ainvoke; remove `_unwrap_completion_state()` | Always / AC-1 |
| `open_notebook/graphs/acm_extraction.py` | Call `_inject_response_format()` before ainvoke; remove `_unwrap_completion_state()` | Always / AC-1 |
| `open_notebook/graphs/utils.py` | Remove `_unwrap_completion_state()` | Only if AC-1 confirmed |
| `open_notebook/extractors/document_structure.py` | Remove `_unwrap_completion_state()` call + import | Only if AC-1 confirmed |
| `open_notebook/extractors/building_inventory.py` | Remove `_unwrap_completion_state()` call + import | Only if AC-1 confirmed |
| `open_notebook/extractors/page_tagger.py` | Remove `_unwrap_completion_state()` call + import | Only if AC-1 confirmed |
| `tests/test_completion_state_unwrap.py` | Delete or update | AC-1 dependent |
| `tests/test_openrouter_provider_routing.py` | Add TestResponseFormat, TestInjectResponseFormat | Always |
| `docs/sprint-artifacts/sprint-status.yaml` | Mark e27-s4 done/partial | Always |

## File List

- docs/sprint-artifacts/e27-s4-native-json-schema-structured-outputs.md (this file)

## Dev Agent Record

### Implementation Log
- 2026-02-28: Story file created. Pre-read complete for all mandatory files. Design decision: stage-specific injection (not shared function modification).
