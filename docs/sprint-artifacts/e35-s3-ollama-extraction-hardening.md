# E35-S3: Ollama Extraction Hardening

## Story
**ID**: E35-S3 | **Epic**: E35 | **Sprint**: V3-8 | **Points**: 3 SP | **Risk**: MEDIUM | **Type**: backend

## Summary

Harden Ollama extraction settings: fix a stale test, add missing test coverage for `_apply_ollama_extraction_settings()`, and document the num_ctx approach. Most functionality is already implemented — this story is primarily test hardening.

## Acceptance Criteria Status

| AC | Description | Current State | Work Needed |
|----|-------------|---------------|-------------|
| AC1 | format=json on all Ollama models | IMPLEMENTED (`object.__setattr__`) | Add tests |
| AC2 | num_ctx at model creation, not post-hoc | Post-hoc via `object.__setattr__` (Esperanto limitation) | Document; add test for early injection |
| AC3 | char-based multi-chunking (no hard truncation) | IMPLEMENTED | Fix stale test |
| AC4 | reads actual num_ctx from model | Reads configured value from model attr | Add test |
| AC5 | Non-Ollama bypass | IMPLEMENTED (3 guards) | Add test |
| AC6 | OLLAMA_MAX_CONTENT_CHARS override | IMPLEMENTED | Already tested |
| AC7 | Unit tests cover all scenarios | 13 tests, 1 stale | Fix + add new tests |

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `tests/test_ollama_chunking.py` | MODIFY | Fix stale test, add `_apply_ollama_extraction_settings` tests |
| `open_notebook/graphs/utils.py` | NO CHANGE | Already correct — document num_ctx approach |

## Implementation Details

### 1. Fix stale test: `test_split_no_boundaries_over_budget` (line 56-62)

Current (wrong — asserts old hard-truncation behavior):
```python
assert len(chunks) == 1
assert len(chunks[0]) == 100
mock_log.warning.assert_called_once()
```

Fixed (matches current multi-chunking behavior):
```python
assert len(chunks) == 2
assert len(chunks[0]) == 100
assert len(chunks[1]) == 100
mock_log.info.assert_called()  # info, not warning
```

### 2. Add tests for `_apply_ollama_extraction_settings()`

New test class `TestApplyOllamaExtractionSettings` with:

1. **`test_sets_format_json_on_ollama`** — verify `format` field set to `"json"` after calling the function
2. **`test_sets_num_ctx_on_ollama`** — verify `num_ctx` set to 32768 (default) when not set
3. **`test_num_ctx_env_override`** — verify `OLLAMA_NUM_CTX=16384` env var is used
4. **`test_num_ctx_not_lowered`** — verify num_ctx is NOT lowered if already higher than target
5. **`test_non_ollama_bypass`** — verify non-Ollama model is returned unchanged

Import `_apply_ollama_extraction_settings` from `open_notebook.graphs.utils`.

### 3. AC2 Note

Esperanto's `OllamaLanguageModel.to_langchain()` does not accept `num_ctx` as a constructor parameter. The post-hoc `object.__setattr__` approach is the correct workaround because:
- It runs immediately after model creation (in `_inject_response_format`)
- It executes BEFORE any API call to Ollama
- `ChatOllama` reads `self.num_ctx` at invocation time, not construction time

This is a vendor limitation, not a design defect.

## Testing

```bash
uv run pytest tests/test_ollama_chunking.py -v
uv run ruff check tests/test_ollama_chunking.py
```
