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
