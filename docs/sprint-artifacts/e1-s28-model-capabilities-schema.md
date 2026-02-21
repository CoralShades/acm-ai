# Story 1.28: Model Capabilities Schema & Configuration

Status: done

## Story

As a **system administrator**,
I want **AI models to have capability metadata (token limits, embedding dimensions, feature support)**,
so that **the extraction pipeline can dynamically adapt to different models without hardcoded assumptions**.

## Acceptance Criteria

1. SurrealDB `model` table has new fields: `max_output_tokens`, `context_window`, `supports_structured_output`, `supports_tool_calling`, `embedding_dimensions`
2. `Model` domain class exposes capability lookup methods with provider-default fallbacks
3. Model provisioning auto-populates capability fields based on known model families
4. Migration 20 creates fields, migration 20_down removes them
5. Anthropic model ID typo fixed: `claude-haiku-3-5-20241022` → `claude-3-5-haiku-20241022`

## Tasks / Subtasks

- [x] Task 1: Create database migration (AC: #1, #4)
  - [x] 1.1 Create `migrations/20.surrealql` with 5 new DEFINE FIELD statements
  - [x] 1.2 Create `migrations/20_down.surrealql` with REMOVE FIELD rollback
- [x] Task 2: Update Model domain class (AC: #2)
  - [x] 2.1 Add capability fields to `Model` class in `models.py`
  - [x] 2.2 Add `_PROVIDER_DEFAULTS` class variable with known model family defaults
  - [x] 2.3 Add `_EMBEDDING_DEFAULTS` class variable for embedding dimensions
  - [x] 2.4 Add `get_max_output_tokens(fallback=8192)` method
  - [x] 2.5 Add `get_context_window(fallback=128000)` method
  - [x] 2.6 Add `get_embedding_dimensions(fallback=1024)` method
- [x] Task 3: Update model provisioning (AC: #3, #5)
  - [x] 3.1 Fix Anthropic model ID typo in `model_provisioning.py`
  - [x] 3.2 Auto-populate `max_output_tokens`, `context_window`, `embedding_dimensions` during creation
  - [x] 3.3 Auto-detect `supports_structured_output` and `supports_tool_calling` from model name
- [x] Task 4: Verification (all ACs)
  - [x] 4.1 Backend lint passes

## Dev Notes

### Provider Defaults

The `_PROVIDER_DEFAULTS` lookup table covers major model families:

| Model Family | Max Output | Context Window |
|---|---|---|
| claude-sonnet-4 | 16384 | 200000 |
| claude-opus-4 | 32768 | 200000 |
| claude-3-5-haiku | 8192 | 200000 |
| gpt-4o | 16384 | 128000 |
| qwen3 | 8192 | 32768 |

### Embedding Defaults

| Model | Dimensions |
|---|---|
| mxbai-embed-large | 1024 |
| text-embedding-3-small | 1536 |
| text-embedding-3-large | 3072 |
| nomic-embed-text | 768 |

### Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `migrations/20.surrealql` | CREATE | Define capability fields on model table |
| `migrations/20_down.surrealql` | CREATE | Rollback migration |
| `open_notebook/domain/models.py` | MODIFY | Capability fields + lookup methods |
| `api/model_provisioning.py` | MODIFY | Auto-populate capabilities + fix typo |

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Completion Notes List
- Part of Bug Triage Plan Phase 4 (Model Abstraction Layer)
- Maps to original bugs #1 and #9 from triage (multi-model compatibility)
- Foundation story for E1-S29 and E1-S30

### File List
- migrations/20.surrealql (new)
- migrations/20_down.surrealql (new)
- open_notebook/domain/models.py (Model class, capability fields + methods)
- api/model_provisioning.py (provisioning + typo fix)
