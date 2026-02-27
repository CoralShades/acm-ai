# Story E27-S1: Fix completionState Wrapper Parsing in Orchestrator

Status: drafted

<!-- GitHub Issue: https://github.com/CoralShades/acm-ai/issues/81 -->

## Story

As a **user uploading multi-building ACM documents (e.g., Alexander District Hospital)**,
I want **the orchestrator's building-level extraction to handle the completionState JSON envelope from OpenRouter**,
so that **all ACM records are extracted from every building instead of returning 0 records**.

## Acceptance Criteria

1. **AC-1: Alexander Extraction Recovers** — Alexander District Hospital extraction returns >= 40/43 records (currently 0/43 due to completionState wrapper failure across all 6 buildings)
2. **AC-2: Broadmeadows No Regression** — Broadmeadows Police Station extraction maintains 31/31 (100%) accuracy — no regression from E26-S4 validated result
3. **AC-3: Envelope Unwrapping Utility** — New `_unwrap_completion_state()` function handles:
   - `{"completionState": "complete", "result": {"records": [...]}}` → unwraps to `{"records": [...]}`
   - `{"records": [...]}` → passes through unchanged (no-op)
   - Unknown/other formats → passes through unchanged (safe fallback)
4. **AC-4: Orchestrator Fallback Path** — `_invoke()` in `_llm_extract_building()` catches `ValidationError` from `with_structured_output()` and falls back to direct `ainvoke()` + `parse_json_response()` + `_unwrap_completion_state()`, matching the proven pattern in legacy `extract_records` (acm_extraction.py:1430-1449)
5. **AC-5: Pre-extraction Intelligence Recovery** — Apply the same unwrapping to `document_structure.py`, `building_inventory.py`, and `page_tagger.py` so they can use LLM results instead of heuristic fallback when only the envelope is the issue
6. **AC-6: Unit Tests** — Unit tests cover:
   - `_unwrap_completion_state()` with envelope, without envelope, and edge cases
   - Orchestrator fallback path triggers on ValidationError
   - Integration test: Alexander extraction returns > 0 records

## Tasks / Subtasks

- [ ] Task 1: Create `_unwrap_completion_state()` utility (AC: #3)
  - [ ] 1.1 Add function to `open_notebook/graphs/utils.py` (central location used by all callers)
  - [ ] 1.2 Handle `{"completionState": ..., "result": {...}}` pattern
  - [ ] 1.3 Handle pass-through for normal JSON (no completionState key)
  - [ ] 1.4 Handle edge cases: nested completionState, missing result key, non-dict input
- [ ] Task 2: Fix orchestrator `_invoke()` fallback (AC: #4) — **Critical path**
  - [ ] 2.1 In `orchestrator.py:_invoke()` (line 557-558), wrap `with_structured_output()` call in try/except
  - [ ] 2.2 On `ValidationError` or `Exception`, fall back to `model.ainvoke(messages)` + `parse_json_response()` + `_unwrap_completion_state()` + `_normalize_extraction_json()` + `ACMExtractionResult.model_validate()`
  - [ ] 2.3 Log warning when fallback is triggered (for observability)
  - [ ] 2.4 Ensure the existing `is_auth_error()` and `is_provider_schema_error()` checks still apply first (don't break existing retry logic)
- [ ] Task 3: Fix pre-extraction intelligence modules (AC: #5)
  - [ ] 3.1 `document_structure.py:_llm_extract_structure()` — add envelope unwrapping before Pydantic validation
  - [ ] 3.2 `building_inventory.py:_llm_compile_inventory()` — add envelope unwrapping
  - [ ] 3.3 `page_tagger.py:_llm_tag_batch()` — add envelope unwrapping
  - [ ] 3.4 For each: try `with_structured_output()` → on failure, fall back to `ainvoke()` + `parse_json_response()` + `_unwrap_completion_state()` + `Model.model_validate()`
- [ ] Task 4: Update legacy `extract_records` fallback (AC: #3)
  - [ ] 4.1 Add `_unwrap_completion_state()` call to `acm_extraction.py:1447` after `parse_json_response()` and before `ACMExtractionResult.model_validate()` — defensive improvement even though current fallback works
- [ ] Task 5: Unit tests (AC: #6)
  - [ ] 5.1 Test `_unwrap_completion_state()` with completionState envelope
  - [ ] 5.2 Test `_unwrap_completion_state()` with normal JSON (pass-through)
  - [ ] 5.3 Test `_unwrap_completion_state()` with edge cases (empty dict, non-dict, missing result key)
  - [ ] 5.4 Test orchestrator `_invoke()` fallback triggers on ValidationError
  - [ ] 5.5 Verify existing `is_auth_error()` and `is_provider_schema_error()` paths unchanged
- [ ] Task 6: Integration validation (AC: #1, #2)
  - [ ] 6.1 Run `scripts/research/e26_s4_accuracy_validation.py` — Alexander must return > 0 records
  - [ ] 6.2 Verify Broadmeadows maintains 31/31
  - [ ] 6.3 Document results in validation report
- [ ] Task 7: Lint and build verification
  - [ ] 7.1 Run `uv run ruff check .`
  - [ ] 7.2 Run `uv run pytest tests/test_acm_ai_extraction.py tests/test_acm_extractor.py -v`
  - [ ] 7.3 Run `cd frontend && npm run build`

## Dev Notes

### Root Cause Analysis

OpenRouter + `claude-sonnet-4` wraps `with_structured_output()` responses in a `completionState` JSON envelope:

```json
{"completionState": "complete", "result": {"records": [...]}, "type": "Object"}
```

This is not a standard LangChain response format. Pydantic's `model_validate()` (called internally by `with_structured_output()`) expects the raw model schema, e.g.:

```json
{"records": [...], "stats": {...}}
```

The result is a `ValidationError` on every structured output call. The single-chunk legacy extraction path (acm_extraction.py) has a fallback that retries with direct `ainvoke()` (which does NOT use structured output grammar, so the model returns unwrapped JSON). The orchestrator path has no such fallback.

### Failure Evidence (E26-S4 validation, 2026-02-28)

```
Broadmeadows (legacy path):  31/31 (100%) ✓
Alexander (orchestrator):     0/43 (0%)   ✗

Errors logged:
- document_structure.py:243  → heuristic fallback (recoverable)
- building_inventory.py:576  → heuristic fallback (recoverable)
- page_tagger.py:446         → heuristic fallback (recoverable)
- acm_extraction.py:1400     → fallback parser   (recovered, 31 records)
- orchestrator.py:965        → NO FALLBACK        (FATAL, 0 records per building)
```

### Proposed Fix Architecture

```
_invoke() in orchestrator.py
├── Try: with_structured_output(ACMExtractionResult).ainvoke()
│   └── Success → return result
├── Catch ValidationError:
│   ├── Fallback: model.ainvoke(messages)  ← no structured output grammar
│   ├── response_text = raw_response.content
│   ├── parsed = parse_json_response(response_text)
│   ├── parsed = _unwrap_completion_state(parsed)  ← NEW
│   ├── _normalize_extraction_json(parsed)
│   └── ACMExtractionResult.model_validate(parsed) → return result
├── Catch auth error → existing retry logic (unchanged)
└── Catch provider schema error → existing fallback (unchanged)
```

### Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `open_notebook/graphs/utils.py` | MODIFY | Add `_unwrap_completion_state()` utility |
| `open_notebook/extractors/orchestrator.py` | MODIFY | Add fallback path in `_invoke()` for ValidationError |
| `open_notebook/extractors/document_structure.py` | MODIFY | Add envelope unwrapping to LLM extraction |
| `open_notebook/extractors/building_inventory.py` | MODIFY | Add envelope unwrapping to LLM compilation |
| `open_notebook/extractors/page_tagger.py` | MODIFY | Add envelope unwrapping to LLM tagging |
| `open_notebook/graphs/acm_extraction.py` | MODIFY | Add `_unwrap_completion_state()` to legacy fallback (defensive) |
| `tests/test_completion_state_unwrap.py` | CREATE | Unit tests for unwrapping utility + fallback path |

### Key Code Locations

| What | File | Lines | Notes |
|------|------|-------|-------|
| WORKING fallback (model) | `acm_extraction.py` | 1430-1449 | Direct `ainvoke()` + `parse_json_response()` — succeeds |
| FAILING path (critical) | `orchestrator.py` | 530-558 | `_invoke()` — no fallback for ValidationError |
| Exception handler | `orchestrator.py` | 560-632 | Catches auth/schema errors but not completionState |
| `parse_json_response()` | `graphs/utils.py` | 213-252 | Brace-depth JSON extractor — works but returns envelope |
| `_normalize_extraction_json()` | `orchestrator.py` | 133-152 | Handles `data_issues:null` but not completionState |
| Building extraction caller | `orchestrator.py` | 797-813 | `extract_building()` — catches all exceptions, logs error, returns 0 records |

### References

- GitHub Issue: https://github.com/CoralShades/acm-ai/issues/81
- E26-S4 Validation Report: `docs/reviews/e26-s4-validation-results.md`
- E26-S4 Results JSON: `research-output/e26-s4/validation_results.json`
- E1-S22: Token limit fix (similar orchestrator bug pattern)
- E1-S20: Agentic Extraction Orchestrator (original implementation)

## Dev Agent Record

### Agent Model Used

(to be filled during implementation)

### Completion Notes List

(to be filled during implementation)

### File List

(to be filled during implementation)
