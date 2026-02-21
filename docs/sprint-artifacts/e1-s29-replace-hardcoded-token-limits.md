# Story 1.29: Replace Hardcoded Token Limits

Status: done

## Story

As a **system administrator**,
I want **all hardcoded `max_tokens` values in the extraction pipeline replaced with dynamic model capability lookups**,
so that **different AI models (qwen, deepseek, llama, gemini, Claude, GPT) work without manual token configuration**.

## Acceptance Criteria

1. `acm_extraction.py` uses dynamic `max_tokens` from model capabilities instead of `8192 if "haiku"... else 32768` pattern
2. `utils.py` has None guard for missing `large_context_model` with fallback to default model
3. Extractor files have TODO comments marking hardcoded values for future dynamic replacement
4. Graph agent files have TODO comments marking hardcoded values
5. No regression in extraction pipeline functionality

## Tasks / Subtasks

- [x] Task 1: Fix critical extraction path (AC: #1)
  - [x] 1.1 Replace string-match token limit in `acm_extraction.py` with `Model.get()` + `get_max_output_tokens()`
  - [x] 1.2 Import `Model` class for dynamic lookup
- [x] Task 2: Fix utils.py None guard (AC: #2)
  - [x] 2.1 Add fallback when `large_context_model` is None — use default model type instead of crashing
- [x] Task 3: Add TODO markers to extractors (AC: #3)
  - [x] 3.1 `orchestrator.py` — mark `max_tokens=32768`
  - [x] 3.2 `metadata_extractor.py` — mark `max_tokens=2048`
  - [x] 3.3 `building_inventory.py` — mark `max_tokens=4096`
  - [x] 3.4 `document_structure.py` — mark `max_tokens=4096`
  - [x] 3.5 `page_tagger.py` — mark `max_tokens=2048`
- [x] Task 4: Add TODO markers to graph agents (AC: #4)
  - [x] 4.1 `supervisor_agent.py` — mark `max_tokens=8192`
  - [x] 4.2 `acm_analyst_agent.py` — mark `max_tokens=8192`
  - [x] 4.3 `source_chat.py` — mark multiple hardcoded values
  - [x] 4.4 `chat.py` — mark `max_tokens=8192`
- [x] Task 5: Verification (AC: #5)
  - [x] 5.1 Backend lint passes

## Dev Notes

### Root Cause

The extraction pipeline had 15+ hardcoded `max_tokens` values across different files. The critical bug was in `acm_extraction.py` where token limits were selected using string matching on the model ID (`"haiku" in str(model_id).lower()`), which tested against SurrealDB record IDs (e.g., `model:h2ucwvxqwo76y7vqw1bz`) rather than model names, making the check useless.

### Fix Strategy

- **Critical path** (`acm_extraction.py`): Full dynamic replacement using `Model.get()` + `get_max_output_tokens()`
- **Other files**: TODO comments added because these extractors receive models through complex dependency injection patterns that make async DB access non-trivial. A future refactor should pass model capabilities through the extractor context.

### Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `open_notebook/graphs/acm_extraction.py` | MODIFY | Dynamic max_tokens from model capabilities |
| `open_notebook/graphs/utils.py` | MODIFY | None guard for large_context_model |
| `open_notebook/extractors/orchestrator.py` | MODIFY | TODO comment |
| `open_notebook/extractors/metadata_extractor.py` | MODIFY | TODO comment |
| `open_notebook/extractors/building_inventory.py` | MODIFY | TODO comment |
| `open_notebook/extractors/document_structure.py` | MODIFY | TODO comment |
| `open_notebook/extractors/page_tagger.py` | MODIFY | TODO comment |
| `open_notebook/graphs/supervisor_agent.py` | MODIFY | TODO comment |
| `open_notebook/graphs/acm_analyst_agent.py` | MODIFY | TODO comment |
| `open_notebook/graphs/source_chat.py` | MODIFY | TODO comment |
| `open_notebook/graphs/chat.py` | MODIFY | TODO comment |

### References

- Depends on: E1-S28 (Model Capabilities Schema)
- Supersedes: E1-S22 (which increased hardcoded values from 8192 to 32768)

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Completion Notes List
- Part of Bug Triage Plan Phase 4 (Model Abstraction Layer)
- 11 files modified, critical path fully dynamic, remaining files marked for future refactor
- The "haiku" string-match pattern was fundamentally broken (tested record IDs not model names)

### File List
- open_notebook/graphs/acm_extraction.py (dynamic max_tokens)
- open_notebook/graphs/utils.py (None guard)
- open_notebook/extractors/orchestrator.py (TODO)
- open_notebook/extractors/metadata_extractor.py (TODO)
- open_notebook/extractors/building_inventory.py (TODO)
- open_notebook/extractors/document_structure.py (TODO)
- open_notebook/extractors/page_tagger.py (TODO)
- open_notebook/graphs/supervisor_agent.py (TODO)
- open_notebook/graphs/acm_analyst_agent.py (TODO)
- open_notebook/graphs/source_chat.py (TODO)
- open_notebook/graphs/chat.py (TODO)
