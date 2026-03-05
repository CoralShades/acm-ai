# Issue: Ollama Extraction Drops Records When Content Exceeds Token Budget

**Story:** E32-S8
**Status:** Fixed (2026-03-05)
**Severity:** P1 — Silent data loss

---

## Problem Statement

When extracting ACM records using an Ollama model (e.g. `qwen2.5:7b`), building content that exceeds the model's effective context window is silently hard-truncated before the LLM call. Any ACM records in the truncated portion are **never seen by the model** and are permanently lost without warning to the user.

---

## Current Behaviour (Before Fix)

`_truncate_content_for_ollama()` in `open_notebook/graphs/utils.py` was called before prompt rendering in `_llm_extract_building()`. It cut content at `num_ctx * 3.5` characters and discarded the rest. A single `WARNING` log entry was emitted, but:

- No record of how many records were potentially dropped
- No retry or multi-pass attempt for the truncated content
- Extraction appeared successful (returned partial record list)

For a building with 30 rooms where the token budget fits 20, the last 10 rooms' records would never be extracted.

---

## Root Cause

The existing pipeline already handles **output** token overflow via `_split_building_by_rooms()`, which splits content at room boundaries before the LLM call to avoid hitting the 32k `max_tokens` output limit. However, no equivalent mechanism existed for **input** token budget constraints specific to Ollama.

---

## Fix (E32-S8)

### `open_notebook/graphs/utils.py`

Replaced `_truncate_content_for_ollama()` with two new functions:

- **`_split_content_by_char_budget(content, max_chars)`** — splits content at SAMP room headers (`B###-R####`) or ARA numbered items (`1.`, `2.`, ...) into chunks that each fit within `max_chars`. If a single room exceeds the budget, it is hard-truncated with a WARNING (graceful degrade).

- **`_ollama_split_by_budget(content, lc_model)`** — detects Ollama models, computes the char budget from `OLLAMA_MAX_CONTENT_CHARS` env var or `num_ctx * 3.5`, and delegates to `_split_content_by_char_budget`. Non-Ollama models receive `[content]` unchanged.

### `open_notebook/extractors/orchestrator.py`

In `_llm_extract_building()`, replaced the single `_truncate_content_for_ollama` call with an inner loop over `budget_chunks = _ollama_split_by_budget(chunk_content, model)`. All records from all budget chunks are merged into `all_records`.

---

## Files Changed

| File | Change |
|------|--------|
| `open_notebook/graphs/utils.py` | Remove `_truncate_content_for_ollama`; add `_split_content_by_char_budget`, `_ollama_split_by_budget`, `_BUDGET_ROOM_RE`, `_BUDGET_ARA_RE` |
| `open_notebook/extractors/orchestrator.py` | Replace truncation call with budget-chunk inner loop; update import |
| `tests/test_ollama_chunking.py` | 11 unit tests covering all scenarios |

---

## Testing

```bash
uv run pytest tests/test_ollama_chunking.py -v
```

11 tests covering:
- Non-Ollama passthrough
- Content within budget (no split)
- Two rooms split across two chunks
- Oversized single room truncated with warning
- ARA-format item boundaries
- Preamble included in first chunk
- `num_ctx` controls budget
- `OLLAMA_MAX_CONTENT_CHARS` env override
