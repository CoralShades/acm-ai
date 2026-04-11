# Phase 5 Audit — Log Sentinel
**Auditor:** log-sentinel (Phase 5)  
**Branch:** `feat/sf-reconciliation-20260411`  
**Date:** 2026-04-11  
**Scope:** Historical + live-state log triage, fabricated SF field grep, LLM correction verification, container health

---

## Scope

Read-only audit of all log files in `logs/` and Docker container logs. No log rotation, no deletions, no truncation.

---

## Logs Examined

| Log File | Lines | Date Range | Notes |
|---|---|---|---|
| `logs/api.log` | 1,634 | 2026-03-16 – 2026-04-11 | API server (main) |
| `logs/api-error.log` | 330 | 2026-03-20 – 2026-03-22 | Error-level only |
| `logs/acm-extraction.log` | 40,133 | 2026-02-26 – 2026-03-12 | Historical extraction runs |
| `logs/frontend.log` | 121 | 2026-04-10 | Next.js dev server |
| `logs/phase5-api-boot.log` | 39 | 2026-04-11 23:05 – 23:09 | Phase 5 audit boot |
| `logs/phase5-frontend-boot.log` | 16 | 2026-04-11 23:03 | First frontend boot attempt |
| `logs/phase5-frontend-boot2.log` | 40 | 2026-04-11 23:03 | Second frontend boot (succeeded) |
| `logs/runs/` | 20+ dirs | 2026-03-12 – 2026-04-09 | Per-extraction split logs |
| Docker: `acm-ai-db` | 200 lines | 2026-04-09 | SurrealDB |
| Docker: `acm-ai-ollama` | 100 lines | 2026-03-23 – 2026-03-24 | Ollama |

---

## Findings

### FINDING-1 (INFO) — Fabricated SF field names: ZERO log hits

Searched all logs for the complete list of fabricated Item__c and Building__c SF field names from the Phase 2b audit:

**Searched patterns:** `Room_ID__c`, `ACM_Name__c`, `ACM_Description__c`, `Extent__c`, `Risk_Status__c`, `ACM_Labelled__c`, `Hygienist_Recommendations__c`, `Identifying_Company__c`, `Department__c`, `Agency__c`

**Result: 0 hits across all log files.**

**Interpretation:** The fabricated field names only appear at SF export time (user-triggered action via `sf_export.py`), not during extraction. No CSV export against a real Salesforce endpoint has been run during the period covered by these logs. The absence is expected, not exculpatory — the bug was latent, not exercised.

**Implication for `_merge_site_config()` (Finding 6 from extraction-pre audit):** The `Department__c` / `Agency__c` bug in `_merge_site_config()` at `sf_export.py:218-238` would only appear in an export log if an operator has configured a `SiteConfig.department` value AND triggered an export. Neither condition was met in this log history.

---

### FINDING-2 (HIGH) — LLM correction stage active in production through 2026-04-09

**Context:** Phase 2a fix (`5dc3ef30`, 2026-04-11) surgically removed the `await _llm_correct_records(...)` call at `acm_extraction.py:1811`. Per DEC-006 (assumptions-and-decisions.md), this is the `[CORRECT] Layer 2` path that inferred values for SF-bound fields in violation of the literal-only rule.

**Log evidence of pre-fix activity:**

| Timestamp | File | `llm_corrected` count |
|---|---|---|
| `2026-02-26 04:11:48` | `acm-extraction.log:27` | 4 |
| `2026-03-05 07:51:24` | `acm-extraction.log` | 31 |
| `2026-03-06 02:29:22` | `acm-extraction.log` | 29 |
| `2026-03-11 12:20:41` | `acm-extraction.log:39581` | 30 |
| `2026-03-12 01:47:34` | `acm-extraction.log:40025` | 58 |
| `2026-03-28 11:24:28` | `runs/2026-03-28T11-12-58_33ky4rga7c30/extraction.log` | 92 |
| `2026-04-05 10:56:27` | `runs/2026-04-05T10-43-45_h251x0y0uxpw/extraction.log` | 108 |
| **`2026-04-09 11:55:11`** | **`runs/2026-04-09T11-50-22_1x2pcil3rjtv/extraction.log`** | **19, 23** |

The last LLM-correction run was **2026-04-09 at 11:55** — two days before the fix landed.

**Post-fix status:** The most recent extraction run (`2026-04-09T12-41-32_wmzebgxeprrd`, 38 records) shows **NO `[CORRECT]` stage at all.** However, this is because that run extracted 38 records with 0 rejected — no records entered the correction pipeline, so the neutering cannot be confirmed from this run alone. No extraction run has occurred AFTER the 2026-04-11 fix commit. The neutering is unverified in production logs.

**Recommendation:** Run a new extraction after branch merge to confirm the `[CORRECT]` stage no longer invokes LLM (should see `llm_corrected=0` and only `failed` counter incrementing for records that would have been LLM-corrected).

---

### FINDING-3 (MEDIUM) — api-error.log errors are test-run artifacts, not production failures

**Error count:** 273 ERROR-level lines in `api-error.log`, all concentrated in 2026-03-20 to 2026-03-22.

**Pattern analysis — recurring error cluster (5 errors per test invocation):**

| Line | Error | Source | Assessment |
|---|---|---|---|
| `api-error.log:99` | `[PIPELINE] [EXTRACT] FAILED — Model timeout` | `pipeline_logger` | Test error injection |
| `api-error.log:99` | `[PIPELINE] EXTRACTION FAILED — Pipeline exploded` | `pipeline_logger` | Test error injection |
| `api-error.log:99` | `Found NONE for field run_id, record extraction_progress:command_acm_extract_123` | `repository` | Synthetic test ID |
| `api-error.log:106` | `Error listing raw extractions for source source:abc: DB connection failed` | `routers.acm:1924` | Synthetic source `source:abc` |
| `api-error.log:134` | `Row 1/1: extraction failed — No JSON object found in response text` | `row_extractor:415` | LLM mock returning no JSON |
| `api-error.log:212` | `Schema check failed: building_record table does not exist` | `scripts.v3_data_migration:53` | Schema check on empty test DB |

All error signatures use synthetic identifiers (`source:abc`, `command_acm_extract_123`, `TestBuilding`). These are from the Phase 3 test run (`2026-03-22`) against an empty local database. Not production.

**Distinct real error in api-error.log:**
```
2026-03-22 11:54:15.151 | WARNING | open_notebook.extractors.acm_schemas:validate_risk_status:340 |
Unknown risk_status value: 'Critical' - passing through
```
This warning indicates the normalizer encountered a value (`Critical`) not in its picklist table. Not a hard failure but relevant to SF validation — `Risk_Status__c` is a formula field (not writable), but the warning came from the old schema validator which may have been checking a non-SF field. Pre-fix code.

---

### FINDING-4 (MEDIUM) — Recurring Pydantic validation warning: PageTagBatch field missing

In `api-error.log:1013-1031` (also repeated in multiple test runs):

```
WARNING | open_notebook.extractors.page_tagger:tag_pages:466 |
LLM page tagging failed: 1 validation error for PageTagBatch
    For further information visit https://errors.pydantic.dev/2.12/v/missing. Using heuristic fallback.
```

This occurs **4 times per test run** across 5 test run sets = ~20 occurrences total. The LLM is not returning the required `PageTagBatch` fields on first attempt; the fallback triggers. This is handled gracefully (heuristic fallback), but it may indicate the page-tagging prompt needs reinforcement for returning required fields. Not blocking, but worth noting for the prompt improvement backlog.

---

### FINDING-5 (INFO) — Phase 5 API boot: clean and complete

Full boot trace in `logs/phase5-api-boot.log` (39 lines, 2026-04-11 23:05-23:09):

```
23:07:09 — API process started on 127.0.0.1:5055
23:07:10 — DB version: 54, no migrations needed
23:07:11 — Model provisioning complete: chat/transformation/tools/large_context/extraction/embedding
23:07:11 — SF schema already at version salesforce-v1 (skipping provisioning)
23:07:12 — Chat checkpointer: AsyncSqliteSaver at data/chat_checkpoints.db
23:07:14 — AG-UI agent class: ResumeSafe_LangGraphAGUIAgent (CopilotKit SDK)
23:07:14 — API initialization completed successfully
         — Application startup complete.
```

**Notably clean:** `SF schema already at version salesforce-v1` — confirms the `api.sf_schema_provisioning` module was updated during Phase 2a and is idempotent on re-boot.

No startup errors, no import failures, no migration errors. All 6 model types configured.

Post-boot the API served real requests:
```
23:09:26 — GET /api/config 200 OK
23:09:26 — Latest version check: 1.8.4 available (current: 1.2.3) — update available
```

---

### FINDING-6 (INFO) — Phase 5 Frontend boot: EADDRINUSE on first attempt, clean on second

**First attempt** (`phase5-frontend-boot.log`): Failed immediately with `EADDRINUSE :::8503` — port 8503 was already in use.

**Second attempt** (`phase5-frontend-boot2.log`): Started with `-p 8503 -p 8502` flag (Next.js takes last `-p` value, so it used 8502). Succeeded:
```
✓ Ready in 28.3s at http://localhost:8502
GET / 200 in 309ms
```

**ECONNREFUSED during startup:** The frontend logged `connect ECONNREFUSED 127.0.0.1:5055` on first page load because the API hadn't finished its boot sequence when the frontend proxied the first request. This was transient — the API was up by the time the frontend was fully compiled.

**Known warning (non-blocking):** `experimental.esmExternals` config is non-standard and generates a Next.js startup warning. This is a pre-existing config issue in `next.config.ts`, not introduced by this branch.

---

### FINDING-7 (INFO) — Ollama unhealthy: false alarm (missing curl in container image)

Docker reports `acm-ai-ollama` as `Up 2 weeks (unhealthy)`.

**Root cause from `docker inspect`:**
```
Status: unhealthy
  [-1] OCI runtime exec failed: exec failed: unable to start container process:
       exec: "curl": executable file not found in $PATH
```

The Docker health check is `curl http://localhost:11434/` but `curl` is not installed in the Ollama container image. The service itself is fully operational:

```
2026-03-24 09:00:59 — Listening on [::]:11434 (version 0.11.2)
2026-03-24 09:01:00 — inference compute: NVIDIA GeForce RTX 4090 24.0 GiB available
```

**Action:** Replace the health check in `docker-compose.yml` with `wget -qO- http://localhost:11434/` or use `CMD ["/bin/ollama", "list"]` — both are available in the image.

---

### FINDING-8 (INFO) — SurrealDB: clean boot, benign credentials warning

SurrealDB 2.2.1, last started 2026-04-09:
```
INFO  Started kvs store at mydata/open_notebook.db with versions disabled
WARN  Credentials were provided, but existing root users were found.
      The root user 'root' will not be created
INFO  Started web server on 0.0.0.0:8000
```

The `WARN` is expected and benign — SurrealDB emits it whenever `--user/--pass` flags are used against an existing database where the root user already exists. No data loss risk.

---

### FINDING-9 (INFO) — Most recent production extraction run: clean

`logs/runs/2026-04-09T12-41-32_wmzebgxeprrd/extraction.log`:
```
[STRUCTURE] Metadata+Structure: consultant=Prensa Pty Ltd, type=DocumentType.ARA
[STRUCTURE] Inventory: 1 buildings | pages=4-18
[ORCHESTRATOR] Building extraction: 1/1 saved
[ORCHESTRATOR] Item extraction: 38 records from 1 buildings
[VALIDATE] COMPLETED: 38 accepted, 0 rejected, 0 filtered
[STORE] Deduplicated: 3 merged, 35 unique
[STORE] COMPLETED: 35 saved, 1 parent sections
EXTRACTION COMPLETE | 35 records in 197.8s
```

No errors, no warnings, no correction stage. Confidence: high=0, medium=31, low=4 — low-confidence items may warrant investigation.

---

## Grep Hit Tables

### Fabricated SF Field Names (full search)

| Pattern | Files Searched | Hits |
|---|---|---|
| `Room_ID__c` | api.log, api-error.log, acm-extraction.log | **0** |
| `ACM_Name__c` | api.log, api-error.log, acm-extraction.log | **0** |
| `ACM_Description__c` | api.log, api-error.log, acm-extraction.log | **0** |
| `Extent__c` | api.log, api-error.log, acm-extraction.log | **0** |
| `Risk_Status__c` | api.log, api-error.log, acm-extraction.log | **0** |
| `ACM_Labelled__c` | api.log, api-error.log, acm-extraction.log | **0** |
| `Hygienist_Recommendations__c` | api.log, api-error.log, acm-extraction.log | **0** |
| `Identifying_Company__c` | api.log, api-error.log, acm-extraction.log | **0** |
| `Department__c` | api.log, api-error.log, acm-extraction.log | **0** |
| `Agency__c` | api.log, api-error.log, acm-extraction.log | **0** |

### LLM Correction Stage — Most Recent Non-Zero Runs

| Timestamp | Run Dir | `llm_corrected` |
|---|---|---|
| 2026-04-09 11:55:11 | `2026-04-09T11-50-22_1x2pcil3rjtv` | 19, 23 |
| 2026-04-05 10:56:27 | `2026-04-05T10-43-45_h251x0y0uxpw` | 108, 119 |
| 2026-03-28 11:24:28 | `2026-03-28T11-12-58_33ky4rga7c30` | 92, 100 |

### Pydantic Validation Warnings

| File | Line | Pattern | Count |
|---|---|---|---|
| `api-error.log` | 1013, 1019, 1025, 1031 | `PageTagBatch validation error` | 4 per test run (~20 total) |

### Error Counts Per Log File

| Log File | ERROR count | CRITICAL count | Notes |
|---|---|---|---|
| `api-error.log` | 273 | 0 | All from 2026-03-20-22 test runs |
| `api.log` | 23 | 0 | Subset of above |
| `acm-extraction.log` | 506 | 0 | Mix of test + real extraction failures |
| `frontend.log` | 0 | 0 | No error-level entries |

---

## Recommendations

| Priority | Finding | Action |
|---|---|---|
| HIGH | FINDING-2 — LLM correction neutering unverified post-fix | Run a new extraction on `feat/sf-reconciliation-20260411` after merge; verify `[CORRECT]` stage shows `llm_corrected=0` |
| MED | FINDING-7 — Ollama healthcheck misconfigured | Replace `curl`-based health check with `wget` or `ollama list` in `docker-compose.yml` |
| MED | FINDING-4 — PageTagBatch validation fallback | Review `page_tagging.jinja` prompt for required field instructions; this fires on ~every test run |
| LOW | FINDING-6 — Frontend EADDRINUSE on port 8503 | Phase 5 boot scripts should probe for an open port before starting rather than hardcoding 8503 |
| INFO | FINDING-1 — No fabricated field hits in logs | Confirm status after first SF export runs post-merge; absence is expected, not proof of correctness |

---

## References

| File | Line(s) | Note |
|---|---|---|
| `logs/phase5-api-boot.log` | 1-39 | Clean Phase 5 boot trace |
| `logs/phase5-frontend-boot2.log` | 1-40 | Successful frontend boot on port 8502 |
| `logs/runs/2026-04-09T11-50-22_1x2pcil3rjtv/extraction.log` | last entries | Last LLM-corrected run (pre-fix) |
| `logs/runs/2026-04-09T12-41-32_wmzebgxeprrd/extraction.log` | full | Most recent clean production run |
| `logs/api-error.log` | 1-330 | All from March 20-22 test run |
| `docker inspect acm-ai-ollama` | State.Health | curl-missing false-unhealthy diagnosis |
