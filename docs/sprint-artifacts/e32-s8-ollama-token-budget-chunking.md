# E32-S8: Ollama Token-Budget Content Chunking -- Tech Spec (Retrospective)

## Overview

This story replaced the naive `_truncate_content_for_ollama()` in `open_notebook/graphs/utils.py` with a budget-aware content splitter `_ollama_split_by_budget()` that splits large building content at room/item boundaries instead of hard-truncating mid-record. This prevented silent data loss when building content exceeded Ollama's token budget.

**Status**: Done (2026-03-05) | **SP**: 2 | **Risk**: LOW | **Type**: backend

---

## Problem

When building content exceeded Ollama's context window (`num_ctx`), records in the truncated portion were silently lost. For example, a building with 15 rooms might only extract 9 rooms because the content was hard-cut at the character limit.

## Solution

- `_ollama_split_by_budget()` splits content at room/item boundaries into budget-sized chunks
- Each chunk is passed through the LLM independently; `all_records` is extended with each result
- Non-Ollama models return `[content]` unchanged (passthrough)
- Content within budget returns `[content]` unchanged (no split)
- Single room exceeding budget is hard-truncated with WARNING log (graceful degrade)
- `OLLAMA_MAX_CONTENT_CHARS` env var overrides auto-calculated budget (`num_ctx * 3.5`)

## Key Files

| File | Change |
|------|--------|
| `open_notebook/graphs/utils.py` | Replaced `_truncate_content_for_ollama()` with `_ollama_split_by_budget()` |
| `open_notebook/extractors/orchestrator.py` | Updated to iterate over chunks from splitter |
| `tests/test_ollama_chunking.py` | 11 unit tests covering all scenarios |

## Acceptance Criteria (All Met)

- AC1: `_ollama_split_by_budget()` replaces `_truncate_content_for_ollama()`
- AC2: Large content split at room/item boundaries
- AC3: Each chunk processed independently, results merged
- AC4: Non-Ollama passthrough
- AC5: Within-budget passthrough
- AC6: Single oversized room hard-truncated with WARNING
- AC7: `OLLAMA_MAX_CONTENT_CHARS` env override
- AC8: 11 unit tests passing (exceeded AC target of 6)
