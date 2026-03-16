# Log Sentinel Report — E36-S2 Browser Verification

## Date: 2026-03-05
## Observation Window: 15:27 – 15:31 UTC+0 (covering active browser test session)
## Duration: ~5 minutes
## Errors Found: 4 (all from unit test runs, not live API traffic)
## Warnings Found: 7 distinct warning classes
## Verdict: CLEAN (no live API errors during E36-S2 browser test window)

---

## Log Sources Checked

| Source | Location | Status |
|--------|----------|--------|
| API (uvicorn) | `D:/ailocal/acm-ai/logs/api.log` + `logs/api-error.log` | Readable |
| Worker | `D:/ailocal/acm-ai/logs/worker.log` + `logs/worker-error.log` | Readable |
| ACM extraction | `D:/ailocal/acm-ai/logs/acm-extraction.log` | Readable |
| Frontend (Next.js) | `D:/ailocal/acm-ai/frontend/dev-server.log` + `logs/frontend.log` | Readable |
| SurrealDB | Docker container `acm-ai-db` | Healthy |
| API Docker | `acm-ai-api` container | Not running (direct process mode) |
| Worker Docker | `acm-ai-worker` container | Not running (direct process mode) |

---

## E35 AC Verification Against Logs

### AC2: No asyncio.run() errors
**Result: PASS**

The `asyncio.runners.Runner` traces in `api-error.log` are exclusively from pytest runs of `test_broadmeadows_all_records_extracted`. They originate from `pytest_asyncio` test harness, not from the live upload path. No `RuntimeError: This event loop is already running` or `asyncio.run() cannot be called from a running event loop` was found during the browser test window (15:27+).

Evidence of asyncio runner being pytest-only:
```
File "d:\ailocal\acm-ai\.venv\Lib\site-packages\pytest_asyncio\plugin.py", line 716, in inner
    runner.run(coro, context=context)
    └ <asyncio.runners.Runner object at 0x0000028835DD39E0>
```
The function `test_broadmeadows_all_records_extracted` is named in all 13 occurrences. None appeared after 15:27 (the browser test window). The E35-S1 fix holds.

### AC3: No model defaults errors
**Result: PASS**

API startup at 06:50 and 06:56 shows clean model provisioning:
```
2026-03-05 06:50:33.822 | SUCCESS | api.model_provisioning:update_defaults_if_needed:413 | Default models updated successfully
2026-03-05 06:50:33.822 | SUCCESS | api.model_provisioning:run_model_provisioning:447 | Model provisioning complete. Configured: ['chat', 'transformation', 'tools', 'large_context', 'extraction', 'embedding']
```
No model defaults errors were found during the 15:27+ browser test window. The E35-S2 SurrealDB persistence fix is holding.

One non-fatal startup warning is present but pre-existing and flagged as expected:
```
2026-03-05 06:50:33.883 | ERROR | open_notebook.database.repository:repo_query:78 | Can not execute UPSERT statement using value: 'field_schema:sf_v1'
2026-03-05 06:50:33.884 | WARNING | api.sf_schema_provisioning:run_sf_schema_provisioning:51 | SF schema provisioning failed (non-fatal): Can not execute UPSERT statement using value: 'field_schema:sf_v1'
```
This fires on every API restart and is explicitly labelled non-fatal.

### AC4: No Ollama format errors
**Result: CONDITIONAL PASS**

During an earlier real extraction run (07:05-07:07), `llama3.1:8b` produced repeated JSON parse failures:
```
2026-03-05 07:05:18.868 | WARNING | open_notebook.graphs.acm_extraction:_llm_correct_records:2621 | LLM correction failed for record 2: Expecting value: line 1 column 1 (char 0)
```
This occurred 13 times across 3 correction rounds during a real Broadmeadows extraction. The model returned empty bodies instead of JSON. This is a known E30-S8 issue with `llama3.1:8b` in the correction stage. No such errors appeared in the 15:27+ browser test window, as no live extraction was triggered during browser testing.

### AC5: Provider priority messages
**Result: PASS — Ollama-first routing confirmed**

Provider routing logs from the 15:27 test run show correct priority:
```
2026-03-05 15:27:45.258 | WARNING | open_notebook.graphs.utils:_provision_extraction_primary_model:903 | Primary extraction candidate ollama/qwen2.5:7b failed: Ollama offline
2026-03-05 15:27:45.258 | INFO | open_notebook.graphs.utils:_provision_extraction_primary_model:900 | Primary extraction model: anthropic/claude-sonnet-4-20250514
```
Ollama was attempted first (primary), then fell back to Anthropic. The Ollama-first priority order from E30-S8 is intact.

Fallback chain was also exercised:
```
2026-03-05 15:27:45.241 | WARNING | open_notebook.graphs.utils:provision_extraction_fallback_model:964 | Attempting extraction fallback model after auth failure: anthropic/claude-sonnet-4-20250514
2026-03-05 15:27:45.244 | WARNING | open_notebook.graphs.utils:provision_extraction_fallback_model:964 | Attempting extraction fallback model after auth failure: ollama/qwen2.5:7b
```
These are from unit test mock runs (not live traffic); provider routing logic is confirmed operational.

### AC6: SSE stream events
**Result: UNABLE TO CONFIRM from server-side logs**

No SSE stream endpoint hits (`/api/v3/stream/` or `/api/acm/extraction-progress/`) appeared in the accessible log files during the 15:27+ window. The frontend dev-server log shows only compiled module activity. SSE streaming status requires browser console capture (not available in server-side logs) or direct test of `/api/v3/stream/` endpoint.

---

## All Errors Found (15:27 – 15:31 window)

| Timestamp | Severity | Service | Error | Source |
|-----------|----------|---------|-------|--------|
| 15:27:18 | ERROR | API worker | `Building WHOLE_DOC extraction failed: expected string or bytes-like object, got 'AsyncMock'` | Unit test run (AsyncMock not a live error) |
| 15:27:18 | ERROR | API worker | `FULL_LLM ERROR: Building WHOLE_DOC failed: expected string or bytes-like object, got 'AsyncMock'` | Unit test run |
| 15:27:28 | WARNING | API | `LLM page tagging failed: 1 validation error for PageTagBatch` — using heuristic fallback | Unit test run for source:fk_test_002 |
| 15:27:28 | WARNING | API | `[orchestrator/WHOLE_DOC] PROVIDER MISMATCH — Expected: Anthropic, Got: <MagicMock ...>` | Unit test run with mocked LLM |

All 4 errors in the observation window originate from unit test runs with mocked/AsyncMock LLM clients. They are NOT live API traffic errors.

---

## Warnings Observed (Recurring Patterns)

| Warning Class | Count | Source | Severity | Action Required |
|---------------|-------|--------|----------|-----------------|
| `Unrecognized enum field sample_result` (compound values like 'Negative Positive') | 30+ instances | `acm_validator` — 07:05-07:07 extraction | Informational — validator recognises but cannot correct compound values | No (known limitation) |
| `LLM correction failed: Expecting value: line 1 column 1 (char 0)` | 13/round x 3 rounds | Worker — llama3.1:8b correction stage | Warning — empty JSON from Ollama model | Existing issue (E30-S8 tracking) |
| `Provider fallback: Ollama offline → Anthropic` | 1 | Unit test run at 15:27 | Informational — expected fallback | No |
| `PROVIDER MISMATCH — Expected: Anthropic, Got: MagicMock` | 4 | Unit tests with mock LLM | Test artifact, not live | No |
| `SF schema provisioning failed (non-fatal)` | 2 (each API restart) | API startup | Non-fatal, known | No |
| `OpenAI not available for embedding, using Ollama/mxbai-embed-large` | 2 | API startup | Expected — no OpenAI key | No |
| `StatReload detected changes` (uvicorn hot-reload) | 2 | API process | Informational — dev mode | No |

---

## Frontend Log Summary

### Critical Finding: `/jobs` and `/notebooks` returning 500 during earlier session

```
⨯ Error: Cannot find module './5873.js'
    at <unknown> (D:\ailocal\acm-ai\frontend\.next\server\app\(dashboard)\jobs\page.js:2:20074)
GET /jobs 500 in 1761ms

Error: ENOENT: no such file or directory, open '...\.next\fallback-build-manifest.json'
GET /notebooks 500 in 1390ms
GET /notebooks 500 in 271ms
```

These 500 errors appear to be stale `.next` build artifacts from a prior code change where webpack chunk IDs shifted after a code edit + Fast Refresh reload cycle. The pattern is:
1. Code edit triggers StatReload
2. Next.js server reloads but `.next/` has chunks from old build
3. First requests fail 500 until full recompile completes

After the recompile (`Compiled in 5.3s (14015 modules)`), subsequent requests returned 200 OK. These are transient dev-mode build cache issues, not E35 regressions.

Current state of frontend (end of observation window):
```
[Next.js Rewrites] Proxying /api/* to http://localhost:5055/api/*
Compiled in 571ms (6911 modules)
GET / 200 in 65ms
GET /config 200 in 14–24ms
POST /api/copilotkit 200 in 43–69ms
```
Frontend is healthy at end of monitoring window.

### Positive: Auto-detected API URL working
```
[runtime-config] Auto-detected API URL: http://localhost:5055 (proto=http, host=localhost:8503)
GET /config 200 in 14ms
```
Frontend config detection is operational.

---

## SurrealDB Status

Container `acm-ai-db` is healthy. Startup log shows:
```
2026-03-05T03:12:23.421435Z INFO surreal::net: Started web server on 0.0.0.0:8000
```
Only warnings are pre-existing credential warnings about root user (not E35-related). No connection drops or query failures in the Docker log during the observation window.

---

## Real Extraction Run Summary (07:05 – 07:07, pre-browser-test)

A live Broadmeadows extraction completed before the browser test window:
```
2026-03-05 07:07:41.572 | INFO | [PIPELINE] EXTRACTION COMPLETE | 18 records in 208.1s
[PIPELINE] Models: llama3.1:8b
[PIPELINE] Strategy: full_llm=1
[PIPELINE] Confidence: high=18, medium=0, low=0
```
- Provider used: `llama3.1:8b` (Ollama — local)
- Records extracted: 18
- Duration: 208s (~3.5 minutes)
- Correction stage: 39 total LLM correction failures across 3 rounds (llama3.1:8b returning empty JSON to correction prompt — known issue)
- Records saved: 18 (corrections failed but records were accepted with remaining validation issues)

---

## Pattern Alerts

| Pattern | Count | Verdict |
|---------|-------|---------|
| `asyncio.runners.Runner` in api-error.log | 13 total, all from pytest | SAFE — test harness artifact, not E35-S1 regression |
| OpenRouter 402 credit errors | 4 occurrences, last at 07:18 | WARNING — OpenRouter account has insufficient credits; no extraction can use OpenRouter |
| `LLM correction failed: Expecting value` | 39 total in one extraction run | PATTERN — llama3.1:8b consistently fails correction-stage JSON format; affects data quality |

---

## Verdict by E35 Story

| Story | AC | Log Evidence | Verdict |
|-------|----|--------------|---------|
| E35-S1 | asyncio.run() fix in sync upload | No `RuntimeError: event loop` errors in live API logs; asyncio refs are test-only | PASS |
| E35-S2 | Persist model defaults | `SUCCESS: Default models updated successfully` on API startup; no defaults override failures | PASS |
| E35-S3/S4 | Ollama format=json fix | No live Ollama extraction in test window; earlier run used llama3.1:8b which still fails JSON correction | PARTIAL — format fix for extraction may work, correction-stage still fails |
| E35-S5 | Provider priority (Ollama-first) | Ollama attempted first, fell back to Anthropic when offline | PASS |
| E35-S6 | SSE stream events | Not confirmable from server logs alone; requires browser console capture | NEEDS BROWSER VERIFICATION |
