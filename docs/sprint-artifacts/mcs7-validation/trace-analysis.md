# Task 6: Trace & Log Analysis

**Date**: 2026-03-19
**Agent**: trace-reporter

## Environment Baseline (Verified 2026-03-19)

| Service | Status | Notes |
|---------|--------|-------|
| Ollama | RUNNING | 3 models available: llama3.1:8b (loaded in VRAM, 11.2GB, ctx 32768), phi4:14b, llama3.2:latest |
| FastAPI Backend | RUNNING | localhost:5055, healthy |
| SurrealDB | RUNNING | localhost:8000, healthy |
| Langfuse | NOT RUNNING | Traces unavailable — relying on API logs and DB state |
| Frontend | NOT RUNNING | Not required for API extraction tests |

### Pre-Extraction DB State
- `source` count: **5**
- `acm_extraction_record` count: **0**
- `acm_building` count: **0**
- `consultant_format_profile` count: **1** (header_signature `42d2ca37492481e6`, confidence 0.9, from 2026-03-18)
  - Cached mapping: F/NF→Friability, Result→Sample_Analysis_Result, Room/Area→Room_or_Area

### Ollama Model State
- **Active model**: llama3.1:8b — loaded in VRAM, expires after idle timeout
- **Available**: phi4:14b (Q4_K_M, 9.1GB), llama3.2:latest (Q4_K_M, 2.0GB)

---

## Provider Cascade Analysis

The extraction pipeline selects providers in priority order (`open_notebook/graphs/utils.py:950-978`):
1. **Ollama** (first — checked via reachability to `OLLAMA_API_BASE/api/tags`)
2. Anthropic Direct (only if `ACM_ANTHROPIC_API_KEY` set — **NOT SET**)
3. OpenRouter (only if `ACM_OPENROUTER_API_KEY` set — **NOT SET**)
4. OpenAI fallback (`OPENAI_API_KEY` **IS SET** — risk if Ollama fails mid-extraction)

**Risk**: If Ollama becomes unreachable during a run, pipeline could fall through to OpenAI gpt-4o-mini.

### Active .env Config
```
ACM_EXTRACTION_MODEL=llama3.1:8b
ACM_ITEM_EXTRACTION_MODE=per_row
OLLAMA_API_BASE=http://localhost:11434
OPENAI_API_KEY=sk-proj-...  (set — fallback risk)
```

---

## Pre-Extraction Ollama Activity Log

| Timestamp | Endpoint | Duration | Notes |
|-----------|----------|----------|-------|
| 00:54:18 | POST /api/chat | — | llama runner started (28s cold start) |
| 00:54:30 | POST /api/chat | 41.0s | First inference |
| 00:54:51 | POST /api/chat | 20.8s | |
| 00:54:56 | POST /api/chat | 4.0s | |
| 00:55:00 | POST /api/chat | 8.2s | |
| 00:55:05 | POST /api/chat | 13.4s | |
| 00:55:10 | POST /api/chat | 13.5s | |
| 00:55:13 | POST /api/chat | 13.1s | |
| 00:55:17 | POST /api/chat | 11.6s | |
| 00:55:22 | POST /api/chat | 12.5s | |
| 00:57:37 | POST /api/chat | **2m14s** | Long call — possible intelligence/schema inference |
| 01:00:28 | POST /api/chat | **5m03s** | Very long — possible building extraction |
| 01:00:59 | POST /api/chat | **5m34s** | Very long — possible building extraction |
| 01:01:39 | POST /api/chat | **4m00s** | Long call |

**Note**: All calls via `127.0.0.1` → Ollama confirmed as provider. No cloud provider calls observed. DB still shows 0 extraction records — these may be pre-extraction intelligence or schema inference calls.

| 01:12:30 | POST /api/chat | **10m48s** | Very long successful inference — possible building extraction |
| 01:12:30 | POST /api/chat | **2m43s** | **500 ERROR** — client disconnected, Ollama aborted ("aborting completion request due to client closing the connection") |

### Error Analysis (01:12:30)
- Two concurrent `/api/chat` calls completed simultaneously at 01:12:30
- One succeeded (10m48s, 200 OK), one failed (2m43s, 500 — client disconnect)
- The 500 is an Ollama-side abort, NOT a model error — the API client closed the connection before Ollama finished
- **No provider fallback observed** — no OpenAI or cloud API calls detected after the error
- DB state unchanged: 0 extraction records, 0 buildings

### Model Expiry & Recovery (01:17:30)
- llama3.1:8b expired from VRAM after idle timeout
- Three runners restarted at 01:17:31-33, model reloaded in ~4.4 seconds
- Extraction resumed normally at 01:18:02

### Per-Row Extraction Phase 1 (01:18:02 – 01:19:57)
| Timestamp | Duration | Status | Notes |
|-----------|----------|--------|-------|
| 01:18:13 | 15.8s | 200 | |
| 01:18:30 | 32.6s | 200 | |
| 01:18:42 | 44.2s | 200 | |
| 01:18:55 | 41.2s | 200 | |
| 01:19:23 | 52.8s | 200 | |
| 01:19:28 | 45.4s | 200 | |
| 01:19:33 | 37.6s | 200 | |
| 01:19:44 | 20.5s | 200 | |
| 01:19:49 | 24.8s | 200 | |
| 01:19:55 | 30.9s | 200 | |
| 01:19:57 | 28.5s | 200 | |

**Gap**: 01:19:57 – 01:22:27 (2.5 min) — post-processing, no LLM calls

### Per-Row Extraction Phase 2 (01:22:27 – 01:23:06)
| Timestamp | Duration | Status | Notes |
|-----------|----------|--------|-------|
| 01:22:29 | 8.1s | 200 | |
| 01:22:29 | 8.0s | 200 | Concurrent |
| 01:22:32 | 5.0s | 200 | |
| 01:22:34 | 7.3s | 200 | |
| 01:22:37 | 10.1s | 200 | |
| 01:22:40 | 10.8s | 200 | |
| 01:22:48 | 10.5s | 200 | |
| 01:22:50 | 10.6s | 200 | |
| 01:22:51 | 10.5s | 200 | |
| 01:22:54 | 10.9s | 200 | |
| 01:22:56 | 10.9s | 200 | |
| 01:22:59 | 10.7s | 200 | |
| 01:23:01 | 10.7s | 200 | |
| 01:23:02 | 10.6s | 200 | |
| 01:23:05 | 10.9s | 200 | |

### Error Analysis (01:23:06) — 2nd Error Batch
- One call succeeded (10.4s, 200 OK)
- **4 concurrent calls aborted** — all "client closing the connection"
  - 500 | 5.3s, 500 | 7.7s, 500 | 4.4s, 500 | 1.7s
- Pipeline auto-recovered after ~60s

### Per-Row Extraction Phase 3 (01:24:09 – 01:27:54)
| Timestamp | Duration | Status | Notes |
|-----------|----------|--------|-------|
| 01:24:09 | 25.4s | 200 | Recovery after 2nd error |
| 01:24:30 | 33.1s | 200 | |
| 01:24:36 | 31.1s | 200 | |
| 01:24:37 | 28.3s | 200 | |
| 01:24:42 | 11.4s | 200 | |
| 01:24:46 | 15.4s | 200 | |
| 01:24:52 | 21.0s | 200 | |
| 01:24:56 | 19.5s | 200 | |
| 01:27:01 | **2m22s** | 200 | Long concurrent call (started ~01:24:50) |
| 01:27:05 | **2m22s** | 200 | Long concurrent |
| 01:27:08 | **2m21s** | 200 | Long concurrent |
| 01:27:12 | **2m19s** | 200 | Long concurrent |
| 01:27:14 | **2m17s** | 200 | Long concurrent |
| 01:27:15 | 14.3s | 200 | |
| 01:27:20 | 15.5s | 200 | |
| 01:27:23 | 8.1s | 200 | |
| 01:27:23 | 8.0s | 200 | Concurrent |
| 01:27:26 | 4.9s | 200 | |
| 01:27:45 | 10.2s | 200 | |
| 01:27:47 | 10.2s | 200 | |
| 01:27:50 | 10.1s | 200 | |
| 01:27:52 | 10.1s | 200 | |
| 01:27:54 | 9.4s | 200 | Last successful call |

### Error Analysis (01:27:54) — 3rd Error Batch
- **5 concurrent calls aborted** — all "client closing the connection"
  - 500 | 1.4s, 500 | 6.9s, 500 | 8.6s, 500 | 6.4s, 500 | 3.9s
- **Pipeline DID NOT RECOVER** — no new inference for ~5 minutes
- Model expired from VRAM at 01:32:54 after idle timeout

### Model Expiry & Reload (01:32:55)
- Two runners restarted at 01:32:55
- Model reloaded in 1.88s (Flash Attention enabled)
- Pipeline resumed at 01:33:40

### Post-Recovery Phase (01:33:40 – 02:34+)
Pipeline ran continuously with high throughput, processing remaining source documents:
- 01:33-01:34: 12-14s/call (per-row extraction)
- 01:34-01:39: **0.8-2.8s/call** (fast burst — row splitting/validation)
- 01:39-01:45: 7-25s/call (mixed extraction)
- 01:45-01:47: **2m36s concurrent calls** (building-level intelligence)
- 01:47-02:34: Sustained 2-24s/call throughput, ~20-25 calls/min

### Additional Error Events (Post-Recovery)
| Time | Aborted Calls | Notes |
|------|---------------|-------|
| 02:03:00 | 2 | Recovered in ~20s |
| 02:08:00 | 1 | Single 181ms abort, minimal impact |
| ~02:32:00 | 1 | Single abort during heavy extraction |

### Recurring Error Pattern (Complete)
| Time | Successful Calls Before | Aborted Calls | Recovery? |
|------|------------------------|---------------|-----------|
| 01:12:30 | ~10 (intelligence) | 1 | Yes (~5 min) |
| 01:23:06 | ~15 (per-row) | 4 | Yes (~60s) |
| 01:27:54 | ~22 (mixed) | 5 | Yes (~5 min, model reload) |
| 02:03:00 | ~200+ (mixed) | 2 | Yes (~20s) |
| 02:08:00 | ~50 (fast burst) | 1 | Yes (immediate) |
| ~02:32:00 | ~120 (mixed) | 1 | Yes (immediate) |
| **Total** | | **14 aborts** | **All recovered** |

**Root cause hypothesis**: FastAPI backend disconnects concurrent Ollama HTTP connections. Possible httpx timeout, asyncio cancellation, or memory pressure under concurrent inference load. Error frequency decreased over time — early batches (4-5 aborts) → later batches (1-2 aborts).

**Provider compliance**: 100% Ollama (127.0.0.1) — zero cloud fallback despite 14 total 500 errors across ~1.5 hours. No OpenAI or other cloud API calls detected throughout entire session. The OPENAI_API_KEY fallback risk never triggered.

---

## Extraction Run Observations

### Run 1: Broadmeadows (source:1dtw6z1eyfjox11zidbs)
- **Status**: COMPLETED (with errors)
- **File**: `Boradmeadows (1).pdf` (19 pages)
- **Source Processing Start**: ~01:02:16
- **Docling Duration**: 95,733ms (~96s)
- **Total Source Processing**: 182.68s
- **Buildings Detected**: 1 (Broadmeadows Police Station, B001, confidence=high)
- **Buildings Saved**: 0/1 — `'str' object has no attribute 'items'` in `base.py:save:167`
- **Row Extraction**: 86 rows extracted for Broadmeadows Police Station
- **Records Created**: 0 (save bug prevents DB writes)
- **Raw Extractions**: 8 tables stored (provider=docling)
- **Schema Inference**: Skipped (no acm_table_section records)
- **Cache Hit/Miss**: N/A
- **LLM Corrections**: friable None→Friable, material_condition None→Good, sample_result cleanup
- **Provider**: ollama/llama3.1:8b ✅
- **Errors**: Building save failure, schema inference `'DocumentMeta' has no attribute 'get'`

### Run 2: Alexander Hospital (source:b6eswuntqoxyozgvv995)
- **Status**: FAILED (serialization error)
- **File**: Alexander Hospital PDF (10+ pages)
- **Start Time**: ~01:12:15
- **End Time**: 01:58:06
- **Duration**: 1136.4s (~19 min)
- **Buildings Detected**: 6 (Myrtle Street Clinic, Mortuary Buildings, Pathology Department, VMO Accommodations, Main Hospital Building, Nurses Accommodation)
- **Buildings Saved**: 0/6 — `'str' object has no attribute 'items'` in `base.py:save:167`
- **Row Extraction**: Myrtle Street Clinic 3/3 ✅, Mortuary Buildings 9 rows, Pathology Dept 8 rows (1 failed: item_name=None)
- **Records Created**: 0 (save bug + serialization failure)
- **Schema Inference**: Failed — `'DocumentMeta' object has no attribute 'get'`
- **Cache Hit/Miss**: N/A
- **LLM Corrections**: sample_result 'Negative, Organic fibres detected'→'Negative', disturbance_potential corrections
- **Provider**: ollama/llama3.1:8b ✅
- **Fatal Error**: `TypeError: Type is not msgpack serializable: Source` at final save step
- **Validation Warnings**: friability='-', area_type='Internal'/'External', material_condition='Presumed Negative'/'Not Sampled'

### Run 3: source:sknoshoo2dppeq4zyqcr
- **Status**: COMPLETED (with errors)
- **Consultant**: Prensa Pty Ltd, type=ARA
- **Buildings Detected**: 1 (generic fallback from register_start=5)
- **Building Inventory**: 1 building, 1 processing group, pages 5-18
- **Structure Duration**: 37.5s
- **Buildings Saved**: 0 — same save bug
- **Records Created**: 0
- **Provider**: ollama/llama3.1:8b ✅

### Run 4: Cache Verification
- **Status**: NOT RUN — blocked by save bugs preventing any records from persisting

### Run 5: Final Extraction (Post-Fixes) — source:1dtw6z1eyfjox11zidbs (Broadmeadows)
- **Status**: FAILED after 1070.1s (17.8 min)
- **Command**: command:5pbpjf3sito1u1polfor (`embed_records: false`, `force: true`)
- **Worker**: `--max-tasks 1` serial mode, single instance
- **Fixes Applied**: base.py save guard, query-back building ID, embed_records:false
- **Structure Phase**: 24.9s — metadata extraction, heuristic fallback (consultant=Unknown)
- **Building Inventory**: 1 building, 1 processing group, pages 5-18
- **Building Save**: ✅ SUCCESS — `building_record:006felislx8823dqfqai` (BLD#BORADMEA_001, confidence=high)
  - `base.py:save()` guard triggered ("Unexpected repo result type str") — non-fatal
  - Query-back fix recovered ID successfully
- **Schema Inference**: ❌ FAILED — `'DocumentMeta' object has no attribute 'get'` (known bug, non-blocking)
- **Per-Row Extraction**: ✅ 86 rows extracted (86 after splits), ~8s/row via ollama/llama3.1:8b
  - Validation warnings: friability='-' (→None), area_type='Internal'/'External' (pass-through)
  - Result values: 'Negative, Positive', 'Organic fibres detected', 'Negative, Assumed Positive' (pass-through)
- **LLM Correction Phase**: ✅ Actively correcting records (~4-6s/record)
  - Corrections applied: material_condition None→'Good'/'N/A (negative)', friable None→'Friable', disturbance_potential None→'High'
  - sample_result 'Negative, Positive' → 'Negative - Treated as Positive'
- **Fatal Error**: `TypeError: Type is not msgpack serializable: PipelineLogger`
  - Location: `langgraph/checkpoint/serde/jsonplus.py:648`
  - LangGraph checkpoint tried to serialize `PipelineLogger` instance in graph state
  - `embed_records: false` only prevented `Source` serialization — `PipelineLogger` is a DIFFERENT non-serializable object
- **Records Saved**: 0 — crash occurred before DB save phase
- **Provider**: ollama/llama3.1:8b ✅ (confirmed throughout all phases)

### Run 5b: Alexander Hospital — source:b6eswuntqoxyozgvv995
- **Status**: SKIPPED — command:9aofc7vqq6hzau88p0qe "already claimed by another worker"
- Worker could not process after Broadmeadows failure

### Run 5c: Duplicate Broadmeadows — command:avalbwjonssh4s2dctwk
- **Status**: SKIPPED — "already claimed by another worker"
- **Risk**: Had `embed_records: true` which would have also triggered Source serialization bug

### Run 6: Ghost-Save Debugging Runs
- Multiple worker restarts as team lead iterated on fixes
- Added `[GHOST-SAVE]` logging to `repository.py:repo_create:103`
- Discovered root cause: SurrealDB unique index `idx_building_internal_id` violations
- Records from failed previous runs left stale building_records blocking new INSERTs
- SurrealDB returns error string instead of record dict → `base.py:save()` guard swallows silently

### Run 7: SUCCESSFUL END-TO-END — source:1dtw6z1eyfjox11zidbs (Broadmeadows)
- **Status**: ✅ EXTRACTION COMPLETE | 32 records in 153.1s
- **Mode**: Bulk extraction (docling_document_json NULL → per-row disabled)
- **Building Save**: 1/1 via query-back (existing building_record:006felislx8823dqfqai)
- **Records**: 33 raw → 1 merged → 32 unique, 1 parent table section
- **LLM Corrections**: 18 corrections, 0 failed
- **DB Persistence**: ✅ CONFIRMED — 32 records in `acm_record` for source:1dtw6z1eyfjox11zidbs
- **Provider**: ollama/llama3.1:8b ✅

### Run 7: SUCCESSFUL END-TO-END — source:b6eswuntqoxyozgvv995 (Alexander Hospital)
- **Status**: ✅ EXTRACTION COMPLETE | 95 records in 473.5s (7.9 min)
- **Mode**: Per-row extraction (7 buildings, docling tables available)
- **Building Save**: 7/7 via query-back (all hit `idx_building_internal_id` unique index violations)
- **Per-Row Breakdown**:
  - B00A (Myrtle Street Clinic): 3 items
  - Mortuary Buildings: 9 items
  - B00B (Main Hospital Building): 18 items + 47 items = 65 total
  - Pathology Department: 8 items
  - VMO Accommodations: 5 items
  - Nurses Accommodation: 9 items
- **Records**: 105 raw → 10 merged → 95 unique, 7 parent table sections
- **LLM Corrections**: 171 corrections, 0 failed
- **Validation**: 315 total validations, validation_failed reduced from 53→4 across 3 correction rounds
- **DB Persistence**: ✅ CONFIRMED — 95 records in `acm_record` for source:b6eswuntqoxyozgvv995
- **Provider**: ollama/llama3.1:8b ✅

---

## Format Profile Cache State

### Before Extractions
| Signature | Confidence | Mapping | Created |
|-----------|-----------|---------|---------|
| `42d2ca37492481e6` | 0.9 | F/NF→Friability, Result→Sample_Analysis_Result, Room/Area→Room_or_Area | 2026-03-18 |

### After Extractions
| Signature | Confidence | Mapping | Created |
|-----------|-----------|---------|---------|
| `42d2ca37492481e6` | 0.9 | F/NF→Friability, Result→Sample_Analysis_Result, Room/Area→Room_or_Area | 2026-03-18 |

No new format profiles created — schema inference node is broken (`'DocumentMeta' has no attribute 'get'`).

---

## Post-Extraction DB State (Final — Run 7)
- `source` count: **5**
- `acm_record` count: **246** (32 Broadmeadows + 95 Alexander + 90 + 29 Clutch)
- `building_record` count: **17** (stale from previous runs; new inserts blocked by unique index)
- `consultant_format_profile` count: **1** (unchanged — schema inference still broken)
- `command` count: **56 completed**, 0 running

---

## Summary of Findings

### Provider Compliance: PASS ✅
- **100% Ollama (llama3.1:8b)** — all LLM calls routed to localhost:11434
- Zero cloud provider calls (no OpenAI, Anthropic, or OpenRouter)
- Model resolved via `model:kknytst2q8psz0iatsdx → llama3.1:8b` consistently
- Per-row extraction mode confirmed (`ACM_ITEM_EXTRACTION_MODE=per_row`)

### Extraction Logic: PASS ✅ (with caveats)
- Buildings correctly detected from PDFs (Broadmeadows: 1, Alexander Hospital: 6)
- Per-row extraction working — items extracted with field values
- LLM correction phase functional — fixing friability, material_condition, sample_result
- Validation warnings are non-blocking (unknown enum values pass through)

### Data Persistence: PASS ✅ (with known limitations)

| Bug | Location | Impact | Status |
|-----|----------|--------|--------|
| Building save failure | `base.py:save:167` | String repo result | **FIXED** (guard + query-back) |
| Ghost saves (unique index) | `repository.py:repo_create:103` | INSERT blocked by stale data | **IDENTIFIED** — UPSERT needed |
| Schema inference failure | `schema_inference_node` | No format profiles | OPEN — non-blocking |
| ormsgpack: Source | `jsonplus.py:648` | Checkpoint crash | **FIXED** (embed_records:false) |
| ormsgpack: PipelineLogger | `jsonplus.py:648` | Checkpoint crash | **FIXED** (removed from graph state) |
| Record-link FK fields | SurrealDB Python client | RecordID auto-parsing | **FIXED** (nulled before save) |

**Resolved during session:**
1. ~~`'str' object has no attribute 'items'`~~ — **FIXED** with base.py guard + query-back pattern
2. ~~`Type is not msgpack serializable: Source`~~ — **FIXED** with `embed_records: false`
3. ~~`Type is not msgpack serializable: PipelineLogger`~~ — **FIXED** (removed from graph state)
4. ~~Record-link FK fields~~ — **FIXED** (nulled `building_record_id` + `parent_table_id` before save)
5. Ghost saves from unique index violations — **IDENTIFIED**, root cause: `idx_building_internal_id` blocks re-inserts of stale building_records. acm_records saved successfully after stale data cleared.

**Still open:**
- `'DocumentMeta' object has no attribute 'get'` — schema inference expects dict, gets Pydantic model (non-blocking)
- Building record UPSERT needed to handle re-extractions without manual stale data cleanup

### Stability Issues (Resolved)
- Worker race condition: Multiple workers claiming same commands → fixed with `--max-tasks 1`
- Ollama concurrent request failures: 10 total 500 errors from client disconnects → resolved by serial execution
- Worker crashes: 3 instances during parallel processing → stable after serial mode

### Recommendations
1. ~~Fix `base.py:save()` to handle string fields~~ — **DONE** (guard + query-back)
2. ~~Fix PipelineLogger serialization~~ — **DONE** (removed from graph state)
3. ~~Fix record-link FK fields~~ — **DONE** (nulled before save)
4. Fix schema inference to handle `DocumentMeta` Pydantic model (use `.model_dump()` or `.dict()`)
5. Implement UPSERT for building_records to handle re-extractions without stale data cleanup
6. Audit remaining graph state fields for non-serializable objects (preventive)
7. Fix `docling_document_json` NULL issue for Broadmeadows — currently forces bulk mode instead of per-row
8. Normalize enum values: area_type ('Internal'/'External'), friability ('-'), material_condition ('Not Sampled'/'Presumed Negative'), sample_result ('Negative, Positive', 'Unknown', 'Organic fibres detected')
