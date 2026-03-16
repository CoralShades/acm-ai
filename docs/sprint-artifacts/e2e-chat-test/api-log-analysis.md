# E2E Chat Test — API Log Analysis

**Monitoring period:** 2026-03-16 15:37:55 → 15:42:57 (5 minutes)
**Log file:** `logs/api.log` (7.13 MB, last updated 15:06:13 prior to monitoring)
**API process PID:** 125920 (listening on 127.0.0.1:5055, 4 active ESTABLISHED connections)
**Analysis generated:** 2026-03-16

---

## 1. Monitoring Summary

No live E2E chat requests were received during the 5-minute monitoring window.
The `api.log` and `api-error.log` files added **0 bytes** across all 10 polling intervals (30-second cadence).

The most recent API log entry before monitoring began was at **15:06:13**, showing `podcast_creator.graph` initialization — a test module warm-up, not a real user request.

All events in `api.log` between 14:42 and 15:02 were produced by **pytest test runs**, not by live browser/frontend interactions.

---

## 2. AG-UI / CopilotKit Endpoint Registration

Two startup registrations confirmed across multiple API boot cycles today:

| Timestamp | Event | Endpoint |
|-----------|-------|----------|
| 2026-03-16 14:42:29.671 | AG-UI chat endpoint registered | `/api/agui/chat` |
| 2026-03-16 14:42:29.680 | AG-UI CRUD chat endpoint registered | `/api/agui/crud-chat` |
| 2026-03-16 14:57:20.589 | AG-UI chat endpoint registered | `/api/agui/chat` |
| 2026-03-16 14:57:20.604 | AG-UI CRUD chat endpoint registered | `/api/agui/crud-chat` |
| 2026-03-16 15:01:09.464 | AG-UI chat endpoint registered | `/api/agui/chat` |
| 2026-03-16 15:01:09.483 | AG-UI CRUD chat endpoint registered | `/api/agui/crud-chat` |

**Status:** Both endpoints registered successfully on every API startup. No registration failures logged.

The adapter used: `ag_ui_langgraph.LangGraphAgent` + `add_langgraph_fastapi_endpoint`.
- Supervisor graph (`supervisor_graph`) exposed at `/api/agui/chat`
- CRUD graph (`crud_graph`) exposed at `/api/agui/crud-chat`

No `/api/copilotkit` or `/copilot-crud` routes appeared in logs — the old CopilotKit routes appear to have been superseded by the AG-UI endpoints.

---

## 3. LangGraph Graph Invocations

No live graph invocations observed during the monitoring window.

The following **test-generated** graph-related events were recorded earlier today (from pytest runs):

### Supervisor / Extraction Graph (test context)
- Model provisioning for `ollama/phi4:14b-q4_K_M` (primary extraction model, resolved from DB record ID)
- Multiple `[E32-S1] Saved BuildingRecord` events at 14:42:30
- `[E32-S1] Building extraction complete for source source:test123: 2/2 buildings saved`

### CRUD Agent
No CRUD agent invocations observed in any log segment (test or live). The `crud_agent.py` module is loaded (import confirmed via `register_crud_agui_endpoint` success) but was not called during the analysis period.

---

## 4. Tool Calls

No live tool call events captured.

Tool-adjacent events from test context (pytest):

| Timestamp | Tool/Event | Detail |
|-----------|-----------|--------|
| 15:01:09.995 | `semantic_search_acm` | query='high risk asbestos', 1 result (vector mode) |
| 15:01:10.013 | `semantic_search_acm` | query='asbestos', 1 result |
| 15:01:10.020 | `semantic_search_acm` | query='test', 0 results |
| 15:02:13.343 | `semantic_search_acm` | query='ceiling tiles', 1 result |

These are direct API endpoint calls from pytest (`api.routers.acm:semantic_search_acm`), not tool calls dispatched through the LangGraph agent.

---

## 5. Model Provisioning — model_id from State

### Feature Status: IMPLEMENTED but NOT exercised live

The `crud_agent.py` `call_crud_agent()` node (line 67) reads `model_id` from state with the following logic:

```python
model_id = state.get("model_id") or config.get("configurable", {}).get("model_id")
```

This means:
1. State-level `model_id` takes priority over config-level `model_id`
2. Falls through to `provision_langchain_model_with_tools()` which resolves the DB default if both are None

**Log evidence during tests (14:42:30):**
- `Resolved extraction model model:t58qz9neoqg8x35hoyqs -> phi4:14b-q4_K_M`
  This shows the DB record-ID resolution path working correctly for extraction models.
- `Primary extraction model: ollama/phi4:14b-q4_K_M`

**No live CRUD agent call was observed**, so the `model_id` from state path was not exercised during monitoring.

**Model provisioning table from today's test runs:**

| Timestamp | Model Provisioned | Context |
|-----------|------------------|---------|
| 14:42:30.710 | `phi4:14b-q4_K_M` (resolved from `model:t58qz9neoqg8x35hoyqs`) | DB ID resolution |
| 14:43:11.662 | `model:env_provisioned` | Default chat model set |
| 14:43:11.666 | `model:env_embed` | Default embedding model set |
| 14:43:39.023 | `gpt-4o` (extraction), `gemini-2.0-flash` (extraction) | Multi-model test |

---

## 6. Errors and Warnings

### Errors (from test context)

| Timestamp | Location | Error |
|-----------|----------|-------|
| 15:02:15.149 | pipeline_logger | `[EXTRACT] FAILED in 0.0s | [ExtractionError] Model timeout` |
| 15:02:15.161 | pipeline_logger | `EXTRACTION FAILED in 0.0s | Pipeline exploded` |
| 15:02:15.200 | pipeline_logger | `[DOCLING] FAILED in 0.0s | [ExtractionError] Docling import failed` |
| 15:02:15.474 | `api.routers.acm:list_raw_extractions:1883` | `DB connection failed` |
| 15:02:15.650 | `row_extractor:extract_all_rows:403` | Row extraction failed after retries |
| 15:02:16.995 | `scripts.v3_data_migration:verify_schema:53` | `building_record table does not exist` |

All errors appear to be **intentional test scenarios** (mocked failures exercising error-handling paths). The same error signatures appear at consistent times across multiple test run sessions (10:47, 14:43, 14:58, 15:01, 15:02), confirming they are pytest-generated.

### Warnings (from test context — notable recurring patterns)

| Warning | Frequency | Significance |
|---------|-----------|-------------|
| `Embedding dimension 3 differs from vector index (1024)` | 7× at 15:01:09-10 | Test embeddings use 3-dim mocks; production index expects 1024 dims. Non-fatal but index may need re-creation. |
| `[E32-S2] Building B1: N table(s) in DB but none have docling_document_json. Per-row disabled` | Many | Per-row extraction cannot activate without Docling JSON. Tests using mock data. |
| `LLM page tagging failed: 1 validation error for PageTagBatch` | 4× (15:01:47–15:02:13) | LLM mock returning invalid schema in test. |
| `MinerU extraction failed — falling back to Docling-only` | Multiple | MinerU disabled or GPU not available in test environment. Expected fallback. |
| `PROVIDER MISMATCH — Expected: Anthropic, Got: Google` | At 14:58:00, 15:01:44 | Provider routing validation in tests. One instance used MagicMock (indicates test mock leak). |
| `Primary extraction candidate ollama/phi4:14b-q4_K_M failed: Ollama offline` | Multiple | Ollama not running during test execution. Expected in CI context. |

### Errors in `api-error.log`
All errors in the error log are identical to those in `api.log` — all from test runs. No runtime production errors logged.

---

## 7. HITL Interrupt Events

No interrupt events captured.

The `check_write_approval` node in `crud_agent.py` calls `langgraph.types.interrupt()` when a `preview_write` tool result is found. This would only appear in logs when:
1. A user sends a write request via the CRUD chat
2. The agent calls `preview_write`
3. LangGraph interrupts the graph

No such flow was triggered during the monitoring window.

---

## 8. Tool Call Sequence Analysis

No chat interactions were captured. Expected log pattern for a typical CRUD chat interaction would be:

```
[POST /api/agui/crud-chat]
  → crud_agent.call_crud_agent(): model_id from state = <value>
  → provision_langchain_model_with_tools() → model selected
  → tool call: query_job_records (source_id=X)
  → [response streamed to client]

[POST /api/agui/crud-chat] (write request)
  → crud_agent.call_crud_agent()
  → tool call: preview_write (operation=UPDATE, ...)
  → check_write_approval(): interrupt() called
  → [client receives interrupt event, shows approval UI]
  → [user approves]
  → execute_pending_write()
  → [success response streamed]
```

---

## 9. Overall Health Assessment

| Component | Status | Notes |
|-----------|--------|-------|
| API process (PID 125920) | RUNNING | Port 5055, 4 established connections |
| `/api/agui/chat` | REGISTERED | Supervisor graph wired correctly |
| `/api/agui/crud-chat` | REGISTERED | CRUD graph wired correctly |
| `model_id` from state | IMPLEMENTED | `crud_agent.py:67` — reads `state.model_id` before `config.model_id` |
| DB record-ID resolution | WORKING | `model:t58qz9neoqg8x35hoyqs → phi4:14b-q4_K_M` confirmed |
| Embedding dimension mismatch | WARNING | Test mocks use 3-dim vectors; production index expects 1024 |
| Per-row extraction | DEGRADED (test) | No `docling_document_json` in test tables — falls back to bulk |
| Ollama availability | OFFLINE (test) | Not running during pytest; expected |
| Live chat traffic | NONE | No requests in 5-minute window or in today's log |

**Conclusion:** The API is healthy and correctly registered. Both AG-UI endpoints are live. The `model_id` from state feature is implemented in `crud_agent.py`. No live E2E chat traffic was observed — the monitoring window coincided with an idle period between test runs. To capture live chat events, the monitoring should be run while an active user session is open in the frontend at port 8503.

---

## 10. Log Infrastructure Notes

- **Primary log:** `logs/api.log` — loguru, level=INFO (or `$LOG_LEVEL`), 10MB rotation, 7-day retention
- **Error log:** `logs/api-error.log` — loguru, level=ERROR, 30MB rotation, 30-day retention, diagnose=True
- **Extraction run logs:** `logs/runs/<timestamp>_<source_id>/extraction.log` — per-run structured logs
- **Log format:** `{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | {name}:{function}:{line} | {message}`
- **Uvicorn access logs:** Not routed to file — go to stdout/stderr. The `start-all.bat` routes API output to `logs/api.log` via redirect but uvicorn's own HTTP access log lines (`INFO: 127.0.0.1:PORT - "POST /api/... HTTP/1.1" 200 OK`) were not observed, suggesting either access logging is suppressed or the redirect captures stdout only.

To capture live HTTP access logs, add `access_log=True` to the `uvicorn.run()` call in `run_api.py` and ensure stdout is redirected to the log file.
