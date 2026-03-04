# Ollama Extraction Hardening

> **GitHub Issue**: #93
> **Discovered**: 2026-03-05 (E30-S8 verification)
> **Story**: E35-S3 (Sprint V3-8)
> **Priority**: P0
> **Status**: Ad-hoc fixes applied (commit 170fec16), needs formalization

## Problem

Multiple Ollama extraction issues discovered during E30-S8 end-to-end verification:

### BUG-2: Content Chunking Hard-Truncation

`_split_content_by_char_budget()` had a bug where content with no room/page boundary markers was truncated to a single chunk instead of being split into multiple chunks. Records beyond the first chunk were silently dropped.

**Ad-hoc fix applied**: Character-based loop `content[i:i+max_chars]` replaces hard truncation.

### BUG-4: Ollama format=json Not Set

Ollama models (qwen2.5:7b, qwen2.5:32b) return conversational text instead of structured JSON without the `format="json"` parameter on `ChatOllama`.

**Ad-hoc fix applied**: `_apply_ollama_extraction_settings()` now sets `format="json"`.

### num_ctx Default Too Low

Ollama defaults to `num_ctx=8192`, resulting in only ~28K character budget (8192 * 3.5 chars/token). This causes excessive content chunking for large documents.

**Workaround**: Set `OLLAMA_NUM_CTX=32768` environment variable.

## Impact

- Without format=json: LLM returns prose instead of JSON → extraction fails
- Without proper chunking: records silently dropped → incomplete extraction
- With default num_ctx: excessive chunking → slow extraction, potential accuracy loss

## Fix (E35-S3)

Formalize ad-hoc fixes with proper testing:

1. `_apply_ollama_extraction_settings()` always sets `format="json"` on Ollama models
2. `num_ctx` set to 32768 (or `OLLAMA_NUM_CTX` env) at model creation time, not post-hoc
3. `_split_content_by_char_budget()` uses character-based multi-chunking
4. `_ollama_split_by_budget()` reads actual num_ctx from model
5. Non-Ollama models bypass all Ollama-specific settings
6. `OLLAMA_MAX_CONTENT_CHARS` env override takes priority

## Key Files

| File | Change |
|------|--------|
| `open_notebook/graphs/utils.py` | `_apply_ollama_extraction_settings()`, `_split_content_by_char_budget()`, `_ollama_split_by_budget()` |
| `open_notebook/extractors/orchestrator.py` | Consume new chunking API |
| `tests/test_ollama_chunking.py` | Comprehensive unit tests |

## Related

- Memory note: "Ollama Extraction Issues" section in MEMORY.md
- E32-S8 (Ollama Token-Budget Content Chunking) — original story for chunking, now needs hardening
