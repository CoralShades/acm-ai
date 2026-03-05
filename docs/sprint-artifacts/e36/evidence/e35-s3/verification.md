# E35-S3 Verification: Ollama Extraction Hardening

## Status: PASS

## Code Verification

### 1. _apply_ollama_extraction_settings() Sets format="json"

In `open_notebook/graphs/utils.py` (lines 247-291):

- **Detection**: `is_ollama = any("ollama" in c.__name__.lower() for c in type(lc_model).__mro__)` (line 261)
- **format="json"**: `object.__setattr__(lc_model, "format", "json")` (line 273)
- **num_ctx**: Defaults to 32768 or `OLLAMA_NUM_CTX` env var, only raises (never lowers): `if num_ctx_target > current_num_ctx` (line 283)
- **No-op for non-Ollama**: Returns early if `is_ollama` is False (line 263)

The comment at line 269-272 explains why `object.__setattr__` is used instead of `model_kwargs["format"]`:

```python
# ChatOllama.format is a first-class Pydantic field -- NOT part of
# model_kwargs. Setting model_kwargs["format"] is silently ignored because
# ChatOllama builds its request payload from self.format directly
```

### 2. _split_content_by_char_budget() Uses Character-Based Multi-Chunking

In `open_notebook/graphs/utils.py` (lines 365-431):

The **no-boundary fallback** (lines 379-388) now uses character-based chunking instead of hard truncation:

```python
if not boundaries:
    if len(content) > max_chars:
        logger.info(
            f"Content ({len(content)} chars) exceeds budget "
            f"({max_chars} chars) and no room boundaries found. "
            f"Splitting into character-based chunks."
        )
        return [
            content[i : i + max_chars] for i in range(0, len(content), max_chars)
        ]
    return [content]
```

This list comprehension produces multiple chunks of `max_chars` size each, instead of the previous bug that truncated to a single chunk.

### 3. _ollama_split_by_budget() Integration

In `open_notebook/graphs/utils.py` (lines 434-465):

- Returns `[content]` unchanged for non-Ollama models (line 449)
- Returns `[content]` if within budget (line 459)
- Calls `_split_content_by_char_budget(content, max_chars)` for oversized content (line 465)
- Limit priority: `OLLAMA_MAX_CONTENT_CHARS` > `num_ctx * 3.5` > `8192 * 3.5 = 28672`

### 4. Ollama Settings Applied to Both Primary and Fallback Models

- **Primary path**: `_provision_extraction_primary_model()` at line 899: `lc_model = _apply_ollama_extraction_settings(lc_model)`
- **Fallback path**: `provision_extraction_fallback_model()` at line 990: `lc_model = _apply_ollama_extraction_settings(lc_model)`
- **Schema injection path**: `_inject_response_format()` at line 325: delegates to `_apply_ollama_extraction_settings(lc_model)` for Ollama models

## Test Results

```
22 passed, 2100 deselected, 6 warnings in 5.91s
```

All 22 Ollama-related tests pass. No failures.

## Evidence

Key code confirming the fix:

```python
# No-boundary character-based multi-chunking (line 386-388)
return [
    content[i : i + max_chars] for i in range(0, len(content), max_chars)
]

# format="json" via first-class Pydantic field (line 273)
object.__setattr__(lc_model, "format", "json")

# num_ctx override with floor guard (lines 282-284)
current_num_ctx = getattr(lc_model, "num_ctx", None) or 0
if num_ctx_target > current_num_ctx:
    object.__setattr__(lc_model, "num_ctx", num_ctx_target)
```

## Notes

- The `format="json"` fix prevents qwen2.5/phi4 from returning conversational text instead of JSON extraction data
- The character-based multi-chunking fix ensures no content is silently dropped when documents lack room/page boundaries
- The `num_ctx` override (default 32768) replaces Ollama's default 8192, which was too small for SAMP documents
- All three call sites (primary, fallback, schema injection) consistently apply Ollama settings
