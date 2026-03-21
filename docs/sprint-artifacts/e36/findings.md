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

---

## Finding 016 — 2026-03-16

- **Date**: 2026-03-16 (CRUD audit fix E2E session)
- **Category**: functional
- **Severity**: BLOCKER
- **Description**: SurrealDB v2.6.3 wire protocol incompatibility. The `surrealdb/surrealdb:v2` Docker tag with `pull_policy: always` pulled v2.6.3, which uses CBOR revision 157. Neither Python SDK 1.0.6 nor 1.0.8 can deserialize this revision. The `source` table is unreadable via the Python SDK. The `acm_record` table has intermittent corrupt records. The `validation-summary` endpoint returns HTTP 500 due to this deserialization failure on the source table.
- **Evidence**: `docs/sprint-artifacts/crud-audit-fix/audit-fix-report.md` (Pre-existing Issues, Issue P1)
- **Recommendation**: Pin the Docker image to a specific patch version (e.g., `surrealdb/surrealdb:v2.2.1`) and remove `pull_policy: always` from `docker-compose.yml`. This is the root cause of Issues P1 and P3 in the audit session.

---

## Finding 017 — 2026-03-16

- **Date**: 2026-03-16 (CRUD audit fix E2E session)
- **Category**: functional
- **Severity**: CONCERN
- **Description**: ACM Records grid renders empty when navigated by building record ID. `useACMItems` hook passes the building record ID (`building_record:xxx`) as the `building_id` query parameter, but `acm_record.building_id` stores string codes such as `"B00L"`. The API exposes a separate `building_record_id` parameter for record-based lookups, but the hook does not use it.
- **Evidence**: `docs/sprint-artifacts/crud-audit-fix/audit-fix-report.md` (Pre-existing Issues, Issue P2)
- **Recommendation**: Change `useACMItems` to pass `building_record_id` instead of `building_id` when the caller holds a record ID.

---

## Finding 018 — 2026-03-16

- **Date**: 2026-03-16 (CRUD audit fix E2E session)
- **Category**: functional
- **Severity**: BLOCKER
- **Description**: Missing `EventEncoder` in the custom `/api/agui/crud-chat` SSE endpoint. The endpoint was streaming raw AG-UI event objects without serializing them to SSE `data:` format. Every message returned `RUN_ERROR: "Run ended without emitting a terminal event" (INCOMPLETE_STREAM)`. The fix wraps the event generator with `EventEncoder` from `ag_ui.encoder`. This was a prerequisite for the HITL write flow (T10) to function.
- **Evidence**: `docs/sprint-artifacts/e2e-chat-test/e2e-crud-chat-test-report.md` (Critical Bug Found section); `api/routers/agui_chat.py`
- **Recommendation**: Fixed in this session (2026-03-16). No further action needed. Add an SSE smoke test to the test suite to catch similar regressions.

---

## Finding 019 — 2026-03-17

- **Date**: 2026-03-17 (Dogfood extraction session)
- **Category**: functional
- **Severity**: BLOCKER (was blocking all extractions)
- **Description**: `_get_db_extraction_model()` in `open_notebook/graphs/utils.py` resolved a SurrealDB model record ID to a non-Ollama model name (`anthropic/claude-sonnet-4` from OpenRouter provider) and passed it to the Ollama candidate in `_provision_extraction_primary_model()`. Ollama returned 404 for `anthropic/claude-sonnet-4`, causing 0 records extracted. The function queried `SELECT name FROM model:{id}` but did not check the `provider` field.
- **Evidence**: Worker log: `Primary extraction model: ollama/anthropic/claude-sonnet-4` → `model "anthropic/claude-sonnet-4" not found (status code: 404)` → `0 items`
- **Recommendation**: Fixed in commit `6fd92aaf`. Now queries `SELECT name, provider FROM model:{id}` and rejects non-Ollama models.

---

## Finding 020 — 2026-03-17

- **Date**: 2026-03-17 (Dogfood extraction session)
- **Category**: functional
- **Severity**: BLOCKER
- **Description**: `validate_records_strict()` in `acm_extraction.py` hard-rejected records where `material_description` was `None`, even when `product` was populated. The rejection gate at line 1362 treated `material_description` as equally critical as `building_id` and `product`. All 30 LLM-extracted records were rejected, leaving only 3 no-access recovery records.
- **Evidence**: Worker log: `Validated 0 records, rejected 30` — all with `Missing required field: material_description`
- **Recommendation**: Fixed in commit `6fd92aaf`. Auto-fills `material_description` from `product` (same pattern as no-access recovery).

---

## Finding 021 — 2026-03-17

- **Date**: 2026-03-17 (Dogfood extraction session)
- **Category**: functional
- **Severity**: BLOCKER
- **Description**: `ACMItemRecord.quantity` in `acm_schemas_v3.py` was typed as `Optional[float]`, but LLMs return measurement strings like `"2m 2"` and `"10 lm"`. Pydantic's float coercion rejected these, and the `except` handler in `_v3_extract_items` discarded ALL records for the entire building — not just the 2 malformed rows. Every other layer (domain model, legacy schemas, orchestrator) uses `Optional[str]` for quantity.
- **Evidence**: Worker log: `V3 Phase 2 [B001] failed — 2 validation errors for ACMItemExtractionResult: records.12.quantity float_parsing "2m 2", records.18.quantity float_parsing "10 lm"`
- **Recommendation**: Fixed in commit `c0832fa8`. Changed to `Optional[str]`. Removed redundant float→str conversion in orchestrator.py.

---

## Finding 022 — 2026-03-17

- **Date**: 2026-03-17 (Dogfood extraction session)
- **Category**: functional
- **Severity**: CONCERN
- **Description**: `JobOverviewTab.tsx` crashed with `Cannot read properties of undefined (reading 'length')` when navigating to `/jobs/{source_id}` after extraction. The guard `buildingInventory && buildingInventory.buildings.length` only checked the outer object, not the `buildings` property which can be `null`/`undefined` when `building_inventory` dict in SurrealDB lacks the key. The safe pattern `inventory?.buildings?.length` was already used in `SourceIntelligencePanel.tsx`.
- **Evidence**: Browser error: "Failed to load Job Detail — Cannot read properties of undefined (reading 'length')". Screenshot: `dogfood-output/screenshots/09-job-detail-error.png`
- **Recommendation**: Fixed in commit `c0832fa8`. Added optional chaining.

---

## Finding 023 — 2026-03-17

- **Date**: 2026-03-17 (Dogfood extraction session)
- **Category**: data-hygiene
- **Severity**: CONCERN
- **Description**: Source deletion (`DELETE /api/sources/{id}`) only deleted the source record from SurrealDB (triggering 9 DB cascade events) but left behind: (1) uploaded PDF file on disk, (2) `reference` relation edges, (3) `command` records, (4) `agui_events`, (5) `chat_session`/`refers_to` edges. Additionally, 92 orphaned PDF files (149MB) existed in `data/uploads/` from previous DB volumes with no matching source records.
- **Evidence**: `data/uploads/` contained 93 files (149MB) but only 1 source in DB. After cleanup: 1 file (1.8MB).
- **Recommendation**: Fixed in commit `0785f1b8`. Delete endpoint now cascades all 5 gaps. New `POST /api/sources/cleanup-orphaned-files` endpoint for batch cleanup.

---

## Finding 024 — 2026-03-20

- **Date**: 2026-03-20 (pipeline accuracy fix session)
- **Category**: benchmark
- **Severity**: CONCERN
- **Description**: Row segmenter was not filtering repeated column header rows that Docling re-emits at multi-page table boundaries. These headers were extracted as data records, inflating record counts and degrading F1. The live E2E test on Clutch_Broadmeadows.pdf confirmed the issue with 8 tables across 18 pages.
- **Evidence**: Commit 1c6026d5 — `open_notebook/extractors/row_segmenter.py` `_is_header_row()` with 37 header texts
- **Recommendation**: Fixed. Monitor recurrence when processing multi-page tables from non-standard formats.

---

## Finding 025 — 2026-03-20

- **Date**: 2026-03-20 (pipeline accuracy fix session)
- **Category**: functional
- **Severity**: CONCERN
- **Description**: SF Picklist validator was routing `needs_user_review` issues (Not Sampled, No Access, Unknown) to the blocking `all_issues` list, causing ~79 false validation failures per extraction run. These values are valid ARA data that have no Salesforce equivalent — they should be flagged for user review, not treated as extraction errors.
- **Evidence**: Commit 1c6026d5 — `open_notebook/extractors/validators/sf_picklist_validator.py`; retest report shows validation failures dropped from 23 → 5 after fix
- **Recommendation**: Fixed. `needs_user_review` issues now route to `chain_warnings` (non-blocking).

---

## Finding 026 — 2026-03-20

- **Date**: 2026-03-20 (benchmark baseline capture)
- **Category**: benchmark
- **Severity**: INFO
- **Description**: Benchmark baseline established after pipeline accuracy fixes. Broadmeadows: P=93.1%, R=87.1%, F1=90.0% (27/31 GT matched, 29 extracted). Alexander: P=22.2%, R=46.5%, F1=30.1% (20/43 GT matched, 90 extracted). Alexander low score is caused by room_name/location field misalignment — the model conflates location descriptions with room names in ARA-format pipe tables.
- **Evidence**: `docs/sprint-artifacts/e2e-evidence/live/benchmark-results.json`
- **Recommendation**: Alexander room_name extraction needs prompt engineering to distinguish structural room names from material location descriptions. Track F1 against this baseline on subsequent extraction changes.

---

## Finding 027 — 2026-03-20

- **Date**: 2026-03-20 (chat system fix session)
- **Category**: functional
- **Severity**: CONCERN
- **Description**: `crud_tools.py` fallback queries used `risk_status` field which was renamed to `sample_result` during the Salesforce schema alignment work. High-risk queries returned no results because the field did not exist in extracted records.
- **Evidence**: Commit dfaf91ee — `open_notebook/graphs/crud_tools.py`; tested via Query mode in jobs page chat sidebar
- **Recommendation**: Fixed. All fallback queries now use `sample_result`. Added "positive" keyword matching for high-risk queries.

---

## Finding 028 — 2026-03-21

- **Date**: 2026-03-21 (SmartChatPanel stabilization)
- **Category**: functional
- **Severity**: BLOCKER (was causing page crashes)
- **Description**: SmartChatPanel caused an infinite re-render loop because `useCopilotReadable` received a new object literal on every render as its value argument. Additionally, `useCopilotChatSuggestions` and `useCoAgentStateRender` hooks triggered AG-UI `TEXT_MESSAGE_CONTENT` errors on every connection, causing unhandled exceptions.
- **Evidence**: Commit aded56d2 — `frontend/src/components/chat/SmartChatPanel.tsx`; screenshots at `docs/sprint-artifacts/e2e-evidence/live/query-edit-toggle.png`
- **Recommendation**: Fixed. Value memoized via `useMemo`. Problematic hooks removed. `SmartChatErrorBoundary` added as safety net for future CopilotKit regressions.

---

## Finding 029 — 2026-03-21

- **Date**: 2026-03-21 (package evaluation)
- **Category**: functional
- **Severity**: INFO
- **Description**: `@copilotkit/*` v1.54.0 (latest) has breaking API changes incompatible with the current SmartChatPanel and CopilotKit runtime integration. Evaluation was performed and upgrade rejected. Python packages `ag-ui-langgraph`, `copilotkit`, and `ag-ui-protocol` were upgraded to their latest compatible versions.
- **Evidence**: Commit aded56d2 — `frontend/package.json` pinned at v1.51.3; commit message documents reason
- **Recommendation**: Re-evaluate @copilotkit/* v1.54.0 upgrade in a future sprint when breaking changes are understood. Track upstream changelog for stable release.

---

## Finding 030 — 2026-03-21

- **Date**: 2026-03-21 (job page crash / counts fix session)
- **Category**: functional
- **Severity**: BLOCKER (job cards showed all-zero counts; chat panel froze browser tab)
- **Description**: Three defects on the jobs page fixed in commit ad3379ef. (1) `api/routers/sources.py` — four aggregate queries used plain string source IDs against `record<source>`-typed columns. SurrealDB's INSIDE operator silently returns 0 rows when comparing `record<source>` fields with uncast strings; wrapping with `type::thing()` resolved building_count, records_count, and tables_count returning null/0 on all job cards. (2) `useSmartChat.ts` — CopilotKit's `useCoAgent` returns a new `setState` reference on every render; placing it in a `useEffect` dependency array caused an infinite re-render loop that froze the page. Fixed with `useRef` stable reference + `didSyncRef` guard. (3) `JobOverviewTab.tsx` — Document Metadata card rendered when `document_meta` was a truthy empty object `{}`; fixed by checking individual field values.
- **Evidence**: Commit ad3379ef — `api/routers/sources.py`, `frontend/src/components/jobs/JobOverviewTab.tsx`, `frontend/src/lib/hooks/useSmartChat.ts`; artifact at `docs/sprint-artifacts/bug-fix-job-page-crash-counts.md`
- **Recommendation**: Fixed. SurrealDB `type::thing()` pattern documented in CLAUDE.md. CopilotKit `useRef`/`didSyncRef` stabilization is the canonical pattern for all `useCoAgent` hooks.
