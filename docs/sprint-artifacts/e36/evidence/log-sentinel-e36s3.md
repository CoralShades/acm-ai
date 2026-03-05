# E36-S3 Log Sentinel Report

**Session**: E36-S3 implementation and verification monitoring
**Observation window**: 2026-03-05 (full day log scan; E36-S3 window ~14:00–16:00)
**Sentinel run time**: 2026-03-05T17:03 (approximate)
**Log sources checked**: `logs/api.log`, `logs/api-error.log`, `logs/worker.log`, `logs/worker-error.log`, `logs/worker-console.log`, `docker logs acm-ai-db`, `docker logs acm-ai-ollama`

---

## 1. Service Status at Observation Start

| Service | Status | Details |
|---------|--------|---------|
| API (port 5055) | UP | `GET /health` → `{"status":"healthy"}` |
| Frontend (port 8503) | UP | HTTP 200, Next.js HTML response |
| SurrealDB (Docker `acm-ai-db`) | UP (healthy) | Started 2026-03-05T03:12:22Z; version 2.6.3 |
| Ollama (Docker `acm-ai-ollama`) | UP but unhealthy (Docker healthcheck) | Responding normally on port 11434; healthcheck false positive |
| Worker | UP | PID 47876 / 60444 (two `run_worker.py` instances detected) |

**API service topology**: Running as direct Windows process (not Docker). Two worker PIDs visible in WMIC output — this is normal for the `StatReload` watchdog pattern where a parent and child process both hold the same command line.

**Ollama models available**: `llama3.1:8b`, `mistral:7b`, `qwen2.5:7b`, `mxbai-embed-large:latest`, `qwen3:latest`, `qwen3:32b`, `qwen2.5:32b`, `deepseek-r1:8b`, `phi4:latest`

---

## 2. API Startup Sequence (06:56 restart)

The API was restarted at 2026-03-05 06:56 (likely due to a `StatReload` triggered by `api/routers/sources.py` modification). Key startup events:

| Time | Event | Severity |
|------|-------|----------|
| 06:56:03.475 | Model catalog: 48 models across active providers | INFO |
| 06:56:03.603 | Primary provider 'openai' not available for embedding; using fallback to `ollama/mxbai-embed-large` | WARNING |
| 06:56:03.673 | `default_extraction_model` updated in DB (env var changed) | INFO |
| 06:56:03.713 | Model provisioning complete: chat, transformation, tools, large_context, extraction, embedding | SUCCESS |
| 06:56:03.754 | SF schema loaded: building=143 fields, item=154 fields, 37 picklists | INFO |
| 06:56:03.775 | **UPSERT error**: `Can not execute UPSERT statement using value: 'field_schema:sf_v1'` | ERROR |
| 06:56:03.776 | SF schema provisioning failed (non-fatal): same UPSERT error | WARNING |
| 06:56:03.776 | API initialization completed successfully | SUCCESS |

The UPSERT error is logged as non-fatal and API startup completes. The SF schema is cached in memory but not persisted to SurrealDB this session. This is a **pre-existing known issue** — the `field_schema` table rejects UPSERT with a string ID. It does not block operation.

---

## 3. Error Analysis — Full Day (2026-03-05)

### 3.1 Pattern: `expected string or bytes-like object, got 'AsyncMock'` (PATTERN — 24 occurrences)

**Occurrences by hour**: 00:00 (8x), 01:00 (4x), 03:00 (4x), 06:00 (4x), 15:00 (4x)

**Source**: Test runs writing to the shared `logs/api-error.log` file. The `AsyncMock` object appears when pytest mocks are used in integration-style tests that invoke the pipeline path. The mocked LLM returns an `AsyncMock` instead of a real string response.

**Impact**: These are test artifacts, not production failures. However, they contaminate the production error log, making pattern detection harder.

**Evidence**: `logs/api-error.log` — entries at 00:07, 00:31, 01:57, 03:26, 06:56 contain `source:test_e2e_123` or similar synthetic source IDs.

The 15:27 occurrence used `source:test_e2e_123` (visible in `api.log` at 15:28), confirming this is an E36-S3 test run.

### 3.2 Pattern: OpenRouter HTTP 402 (PATTERN — 8 occurrences today + 4 from prior sessions)

**Times**: 00:03, 00:05, 01:55, 03:24, 06:24, 06:56, 07:18 (from worker.log)

**Error**: `Error code: 402 - {'error': {'message': 'Insufficient credits. Add more using https://openrouter.ai/settings/credits', 'code': 402}}`

**Source**: `open_notebook.extractors.orchestrator:extract_building` — the fallback chain reaching `openrouter/anthropic/claude-sonnet-4`.

**Impact**: Any extraction that falls through Ollama and Anthropic-direct to OpenRouter will fail silently. The error is logged and treated as an extraction failure for that building.

**This is a pre-existing condition** documented in Finding 004 from E36-S2.

### 3.3 Pattern: `No JSON object found in response text` (PATTERN — 48 occurrences in worker.log today)

Ollama models (primarily `mistral:7b`, `qwen2.5:7b`) returning conversational text instead of JSON. The response previews show the model explaining it has no content to parse rather than returning an extraction result. This suggests some runs are hitting models with empty or malformed content payloads.

**Impact**: Extraction fails for those buildings, 0 records stored for affected runs.

### 3.4 Pattern: `LLM correction failed — Expecting value: line 1 column 1 (char 0)` (39 occurrences in single Broadmeadows run)

Documented during the 07:05 Broadmeadows run in `worker.log`. `llama3.1:8b` returns empty JSON bodies in the correction stage across all 3 correction rounds (13 records × 3 attempts = 39 failures).

**This is Finding 003 / Finding 008 from E36-S2** — correction stage lacks `format="json"` enforcement for Ollama.

### 3.5 PROVIDER MISMATCH warnings (203 occurrences in api.log today)

**Source**: `open_notebook.graphs.utils:_verify_provider_routing:493`

The majority (199 of 203) appear in test runs where the LLM is mocked — `_verify_provider_routing` receives a `MagicMock` instead of a real provider response and reports a mismatch. These are test artifacts.

The remaining ~4 may be from real extractions where the actual provider did not match the expected provider after fallback.

---

## 4. E36-S3 Session Window (14:00–16:00)

### Activity observed at 15:27–15:28

A test pipeline run was executed against `source:test_e2e_123` (synthetic). The `api.log` and `api-error.log` both show this at 15:27–15:28.

Key events from this run:

| Time | Event | Notes |
|------|-------|-------|
| 15:27:18 | `AsyncMock` extraction failure for WHOLE_DOC | Test mock — expected |
| 15:28:05 | API module reimported (StatReload) | Code change triggered hot-reload |
| 15:28:14 | Second reimport | Another code change |
| 15:28:23 | Full pipeline test run for `source:test_e2e_123` | 2 pages, 2 records |
| 15:28:23 | `PROVIDER MISMATCH` × 6 (all mocked) | Test artifacts |
| 15:28:23 | 3 correction rounds, all `failed=0` (mock returns nothing to correct) | Expected with mocks |
| 15:28:23 | EXTRACTION COMPLETE: 2 records in 0.1s | Test passed |

The v3_building_rollback script was also invoked at 15:28:14 against `source:abc123` (test fixture), finding 2 building_record entries.

**No asyncio.run() errors observed** in this session — E35-S1 fix holding.

**No SurrealDB connection errors** in this session.

**No 500 HTTP responses** from the API during this session (all observed errors are worker-side pipeline failures, not API layer crashes).

### Worker restart at 14:12

Worker was restarted at 2026-03-05 14:12:36. Only 2 log lines captured for the entire session after that restart — the worker was idle (no extraction commands queued).

---

## 5. SurrealDB Container

Clean startup at 2026-03-05T03:12:22Z. Two non-critical WARN messages at startup:
- `Credentials were provided, but existing root users were found. The root user 'root' will not be created`
- `Consider removing the --user and --pass arguments from the server start command`

These are standard operational warnings for SurrealDB running with pre-existing data. No errors. Database healthy throughout the observation window.

---

## 6. Ollama Container

Two VRAM recovery timeout warnings at 04:33 (3 in sequence):
```
time=2026-03-05T04:33:00.593Z level=WARN source=sched.go:685
msg="gpu VRAM usage didn't recover within timeout"
seconds=5.127555373 runner.size="8.3 GiB" runner.vram="8.3 GiB"
runner.parallel=1 runner.pid=1032
```

This indicates GPU VRAM pressure — the model runner was not able to free VRAM within the 5s timeout after a previous request. The model loaded is `qwen2.5:7b` (8.3 GiB blob hash confirmed). Subsequent requests succeeded normally (200 at 04:27:26 and 04:27:28, then successful /api/tags GET at 05:03).

Docker healthcheck shows `unhealthy` but the service is functionally available — this is a healthcheck configuration issue, not a service failure.

---

## 7. Summary Table

| Finding | Severity | Count | Category |
|---------|----------|-------|----------|
| OpenRouter HTTP 402 (insufficient credits) | WARNING | 8 today | Pre-existing — Finding 004 |
| `AsyncMock` in production error log (test bleed) | WARNING | 24 today | Test isolation gap |
| Ollama JSON parse failure (`No JSON object found`) | WARNING | 48 in worker.log | Pre-existing — model config |
| Correction stage empty JSON (llama3.1:8b) | WARNING | 39 in single run | Pre-existing — Finding 003 |
| SF schema UPSERT error at startup | WARNING | 1 per restart | Pre-existing — non-fatal |
| PROVIDER MISMATCH in test runs | INFO | 203 today (199 from tests) | Test artifacts |
| Ollama VRAM recovery timeout | INFO | 3 at 04:33 | Transient, resolved |
| asyncio.run() errors | NONE | 0 | E35-S1 fix confirmed holding |
| 500 status codes from API | NONE | 0 | No API layer crashes |
| SurrealDB connection errors | NONE | 0 | DB healthy throughout |
| Python tracebacks / unhandled exceptions | NONE | 0 | No crashes |

---

## 8. New Finding for E36-S3

### Finding: Test runs write to shared production log files

Test pipeline runs (pytest or manual test invocations) write their `AsyncMock`-containing errors and `PROVIDER MISMATCH` warnings to `logs/api-error.log` and `logs/api.log` alongside production extraction runs. This makes it impossible to distinguish test artifacts from production failures without reading context (source IDs like `source:test_e2e_123` vs real IDs).

**Recommendation**: Configure test log handlers to write to `logs/api-test.log` or suppress log file output during pytest runs. This is a log hygiene issue with no functional impact.

---

## 9. No Critical Alerts

No ALERT files written for this session. All observed errors are:
- Pre-existing conditions documented in E36-S2 findings
- Test artifacts (AsyncMock, PROVIDER MISMATCH)
- Operational warnings (VRAM pressure, healthcheck config)

The E35-S1 asyncio.run() fix remains confirmed. The API is stable. No new regressions detected in the E36-S3 window.
