# E36 Technical Findings

## Format
Each finding follows:
- **Date**: When discovered
- **Category**: E35-verify / benchmark / functional / ux-audit / adversarial
- **Severity**: BLOCKER / CONCERN / NITPICK / INFO
- **Description**: What was found
- **Evidence**: Path to screenshot or log
- **Recommendation**: Suggested action

---

---

## Finding 001 — 2026-03-05

- **Date**: 2026-03-05 (E36-S2 browser verification session)
- **Category**: E35-verify
- **Severity**: INFO
- **Description**: No asyncio.run() errors detected in live API logs during E36-S2 browser test window. All `asyncio.runners.Runner` traces in `api-error.log` originate exclusively from pytest test runs of `test_broadmeadows_all_records_extracted`, not from live upload path. E35-S1 fix confirmed holding.
- **Evidence**: `D:/ailocal/acm-ai/docs/sprint-artifacts/e36/evidence/log-sentinel-e36s2.md`
- **Recommendation**: No action needed. Continue monitoring across next extraction run.

---

## Finding 002 — 2026-03-05

- **Date**: 2026-03-05 (E36-S2 browser verification session)
- **Category**: E35-verify
- **Severity**: INFO
- **Description**: Model defaults provisioning succeeds cleanly on API startup. `update_defaults_if_needed` correctly updates only changed fields; `provision_default_models` succeeds with all 6 roles configured. E35-S2 SurrealDB persistence fix is confirmed working.
- **Evidence**: `D:/ailocal/acm-ai/docs/sprint-artifacts/e36/evidence/log-sentinel-e36s2.md` (AC3 section)
- **Recommendation**: No action needed.

---

## Finding 003 — 2026-03-05

- **Date**: 2026-03-05 (E36-S2 browser verification session)
- **Category**: E35-verify
- **Severity**: CONCERN
- **Description**: During real Broadmeadows extraction at 07:05, `llama3.1:8b` returned empty JSON bodies in the correction stage 39 times across 3 rounds (`Expecting value: line 1 column 1 (char 0)`). Records were still stored (18 records) but correction stage was entirely ineffective. The `format="json"` fix from E35-S4 may apply only to the extraction prompt, not the correction prompt. Correction-stage Ollama format enforcement needs verification.
- **Evidence**: `D:/ailocal/acm-ai/logs/worker.log` lines 1–163 (07:05 extraction run)
- **Recommendation**: Verify `_apply_ollama_extraction_settings()` is also applied to the correction LLM invocation in `acm_extraction.py:correct_records`. If not, apply `format="json"` there too.

---

## Finding 004 — 2026-03-05

- **Date**: 2026-03-05 (E36-S2 browser verification session)
- **Category**: E35-verify
- **Severity**: CONCERN
- **Description**: OpenRouter account has insufficient credits (HTTP 402 errors). Four extraction attempts using `openrouter/anthropic/claude-sonnet-4` failed between 00:03 and 07:18. The fallback chain from Ollama to Anthropic direct to OpenRouter is correctly ordered (E35-S5), but the OpenRouter node in the chain is non-functional due to billing. Any extraction relying on OpenRouter as final fallback will fail silently.
- **Evidence**: `D:/ailocal/acm-ai/logs/api-error.log` lines 9-17 (00:03 and 00:05 errors)
- **Recommendation**: Top up OpenRouter credits before running full benchmarks. Alternatively, configure benchmark runs to use Ollama-only or Anthropic-direct.

---

## Finding 005 — 2026-03-05

- **Date**: 2026-03-05 (E36-S2 browser verification session)
- **Category**: functional
- **Severity**: INFO
- **Description**: Frontend returned 500 errors on `/jobs` and `/notebooks` during a stale-build window when webpack chunk IDs shifted after a code hot-reload. Errors cleared after full recompile. This is a transient dev-mode artifact, not a functional regression.
- **Evidence**: `D:/ailocal/acm-ai/frontend/dev-server.log` (MODULE_NOT_FOUND errors for chunks 5873.js, 5611.js)
- **Recommendation**: No code change needed. If browser tester hit `/jobs` or `/notebooks` during this window, retry those page navigations.

---

## Finding 006 — 2026-03-05

- **Date**: 2026-03-05 (E36-S2 browser verification session)
- **Category**: E35-verify
- **Severity**: INFO
- **Description**: SSE streaming (AC6) could not be confirmed from server-side logs alone. No `/api/v3/stream/` or `/api/acm/extraction-progress/` endpoint hits appeared in the observation window. Browser console capture or a dedicated SSE connection test is required.
- **Evidence**: Absence of SSE log entries in `api.log` during 15:27-15:31 window
- **Recommendation**: Browser tester should explicitly navigate to the extraction progress view during an active extraction job to verify SSE events reach the frontend.

---

## Finding 007 — 2026-03-05

- **Date**: 2026-03-05 (E36-S2 browser verification session)
- **Category**: E35-verify
- **Severity**: BLOCKER
- **Description**: POST /api/acm/backfill-buildings returns HTTP 500 with error "'Source' object has no attribute 'name'". This is a pre-existing bug in the building backfill endpoint (E35-S6), not a regression from E35 fixes. The endpoint exists but crashes when invoked.
- **Evidence**: API error log from backfill attempt during AC7 verification
- **Recommendation**: Either (a) remove POST endpoint from E35-S6 AC and mark as partial completion, or (b) fix the Source.name AttributeError in the backfill handler. GET /api/acm/buildings works correctly for pre-V3 sources.

---

## Finding 008 — 2026-03-05

- **Date**: 2026-03-05 (E36-S2 browser verification session)
- **Category**: E35-verify
- **Severity**: CONCERN
- **Description**: llama3.1:8b in correction stage fails to return valid JSON bodies 39 times during Broadmeadows extraction. Errors: "Expecting value: line 1 column 1 (char 0)" indicating empty response bodies. E35-S3 added `format="json"` to extraction prompt, but correction stage LLM invocation in `acm_extraction.py:correct_records` may not have the same format enforcement.
- **Evidence**: `D:/ailocal/acm-ai/logs/worker.log` lines 1–163 (Broadmeadows run 07:05, 39 correction failures)
- **Recommendation**: Audit `correct_records()` function to ensure `format="json"` is applied to the correction LLM call, not just extraction. Test correction stage with llama3.1:8b after fix.

---

## Finding 009 — 2026-03-05

- **Date**: 2026-03-05 (E36-S2 browser verification session)
- **Category**: E35-verify
- **Severity**: BLOCKER
- **Description**: OpenRouter account has insufficient credits (HTTP 402 errors). Four extraction attempts failed between 00:03 and 07:18 when the fallback chain reached openrouter/anthropic/claude-sonnet-4. This blocks full benchmark runs that depend on OpenRouter as a fallback provider.
- **Evidence**: `D:/ailocal/acm-ai/logs/api-error.log` lines 9-17 (HTTP 402 payment required)
- **Recommendation**: Top up OpenRouter credits before E36-S4 benchmarking, or configure benchmark runs to use Ollama+Anthropic-direct only (skip OpenRouter).

---

## Finding 010 — 2026-03-05

- **Date**: 2026-03-05 (E36-S3 log sentinel session)
- **Category**: functional
- **Severity**: CONCERN
- **Description**: Test pipeline runs (pytest and manual test invocations) write their logs — including `AsyncMock` errors and `PROVIDER MISMATCH` warnings — to the shared production log files `logs/api-error.log` and `logs/api.log`. Today's scan found 24 `AsyncMock` occurrences and 203 `PROVIDER MISMATCH` entries, the vast majority originating from test runs (source IDs like `source:test_e2e_123`). This contaminates production logs and makes automated error pattern detection unreliable.
- **Evidence**: `D:/ailocal/acm-ai/docs/sprint-artifacts/e36/evidence/log-sentinel-e36s3.md` section 3.1 and 3.5
- **Recommendation**: Configure pytest log handlers (or a `conftest.py` fixture) to redirect log output to a separate `logs/api-test.log` file, or suppress file handler output during test runs. No functional impact on extraction correctness.

---

## Finding 011 — 2026-03-05

- **Date**: 2026-03-05 (E36-S3 log sentinel session)
- **Category**: E35-verify
- **Severity**: INFO
- **Description**: E35-S1 asyncio.run() fix remains confirmed holding. No asyncio.run() errors observed in the E36-S3 window (14:00–16:00) or in any of today's production log entries. No Python tracebacks, no unhandled exceptions, no 500 HTTP responses from the API layer. The API initialized cleanly at the 06:56 restart and remained stable throughout the session.
- **Evidence**: `D:/ailocal/acm-ai/docs/sprint-artifacts/e36/evidence/log-sentinel-e36s3.md` section 4 and 7
- **Recommendation**: No action needed. Continue monitoring across E36-S4 benchmark runs.

---

## Finding 012 — 2026-03-05

- **Date**: 2026-03-05 (E36-S4 benchmark run)
- **Category**: benchmark
- **Severity**: BLOCKER
- **Description**: The `extraction_progress` SurrealDB table does NOT reliably update to "completed" status after the worker finishes extraction. 7 of 12 benchmark runs "timed out" at 600s despite the worker completing the extraction and saving records. The pipeline logger writes initial "running" status but fails to write the terminal "completed" status for most runs. This makes the polling-based completion detection unreliable.
- **Evidence**: `docs/sprint-artifacts/e36/benchmark-results/summary.md`, benchmark script output
- **Recommendation**: Debug pipeline logger terminal status write in `open_notebook/extractors/pipeline_logger.py`. Check if the graph's final node correctly invokes `stage_exit` with terminal status. Consider adding a worker-side status update as fallback.

---

## Finding 013 — 2026-03-05

- **Date**: 2026-03-05 (E36-S4 benchmark run)
- **Category**: benchmark
- **Severity**: CONCERN
- **Description**: All Alexander PDF extraction runs show 0% record recall despite models extracting 33-42 records (vs 43 ground truth). Root cause: the extraction places material/product descriptions in the `room_name` field instead of actual room names. Example: extracted `room_name="Infill Panels - Flat Cement Sheeting"` vs ground truth `room_name="Shower Room"`. The fuzzy matching cannot pair records when the primary matching field is fundamentally wrong.
- **Evidence**: `docs/sprint-artifacts/e36/benchmark-results/summary.md`, Alexander ground truth CSV vs API `GET /api/acm/records?source_id=source:ubbsh2i0b6ypy64vs1hh`
- **Recommendation**: Fix room_name extraction in the ACM extraction prompt to distinguish room/location names from material descriptions. Consider adding a separate `location_detail` field for material-specific location info.

---

## Finding 014 — 2026-03-05

- **Date**: 2026-03-05 (E36-S4 benchmark run)
- **Category**: benchmark
- **Severity**: CONCERN
- **Description**: Correction stage fails 100% for all Ollama models tested. The `format="json"` setting (E35-S3 fix) is applied to the extraction LLM call but NOT to the correction LLM call. All correction attempts return empty JSON bodies (`Expecting value: line 1 column 1 (char 0)`). This means validated field corrections never succeed with Ollama.
- **Evidence**: `docs/sprint-artifacts/e36/evidence/log-sentinel-e36s4.md`, worker.log correction failure entries
- **Recommendation**: Apply `_apply_ollama_extraction_settings()` to the correction LLM call in `acm_extraction.py:_llm_correct_records`. Reconfirms Finding 003/008.

---

## Finding 015 — 2026-03-05

- **Date**: 2026-03-05 (E36-S4 benchmark run)
- **Category**: benchmark
- **Severity**: INFO
- **Description**: qwen2.5:7b is the best-performing Ollama model for ACM extraction. It was the only model to complete both PDFs within 600s timeout. Broadmeadows: 20/31 records (64.5%) in 252s. Alexander: 37/43 records (86.0%) in 82s. Fastest average time across all models (167s). llama3.1:8b extracted fewer records (3 for Broadmeadows) and was slower (403s). mistral:7b showed promise for Alexander (~42 detected) but timed out for Broadmeadows.
- **Evidence**: `docs/sprint-artifacts/e36/benchmark-results/summary.md`
- **Recommendation**: Set qwen2.5:7b as the default Ollama extraction model. Consider increasing timeout to 900s for production to accommodate larger PDFs.
