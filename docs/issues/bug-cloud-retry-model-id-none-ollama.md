# Cloud Retry Fires with model_id=None in Ollama-Only Mode (N5)

> **Discovered**: 2026-03-12
> **Priority**: P1
> **Status**: Open

## Problem

When truncation is detected during extraction, the code attempts a cloud retry. In Ollama-only mode, the `cloud_available` guard exists at the single-chunk level but the chunk-level retry code path still fires with `model_id=None`. The retry is a no-op (no model to call) but wastes log space and creates confusion.

## Evidence

- `worker-debug.log` 20:15: `retrying chunk with cloud provider (model_id=None)`
- `worker-debug.log` 20:24: same pattern repeated
- `worker-debug.log` 20:33: same pattern repeated
- All three retries produce no output (model_id=None → no LLM call possible)

## Impact

- Misleading log output — suggests cloud retry is happening when it can't
- Wasted code path execution (though fast since no actual API call)
- Confuses debugging when investigating extraction failures

## Fix Approach

1. Add `cloud_available` guard check before the chunk-level retry code path (same pattern as single-chunk guard)
2. When guard blocks retry, log: `Truncation detected but no cloud API keys configured — skipping chunk retry`
3. Include current `OLLAMA_NUM_CTX` value in the skip warning

## Files to Modify

| File | Change |
|------|--------|
| `open_notebook/graphs/acm_extraction.py` | Add `cloud_available` check before chunk-level cloud retry |
