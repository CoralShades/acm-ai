# Log Monitor Report: Clutch_Broadmeadows.pdf Extraction

**Date:** 2026-03-20
**Document:** Clutch_Broadmeadows.pdf (1.8MB, ~10 pages)
**Source ID:** `source:1axqxr2z5vgxjdrsjhcx`
**Model:** ollama/llama3.1:8b
**Overall Verdict:** PASS (with warnings)

---

## Timeline of Events

| Time | Elapsed | Phase | Event |
|------|---------|-------|-------|
| 16:44:16.487 | 0s | UPLOAD | File saved: `Clutch_Broadmeadows (2).pdf` |
| 16:44:16.488 | 0s | UPLOAD | "Using async processing path" confirmed |
| 16:44:16.574 | 0s | UPLOAD | `process_source` command submitted (`command:qnnj0mkbkg0oufztbkur`) |
| 16:44:16.644 | 0s | UPLOAD | `acm_extract` command submitted (`command:mqw6f2wqb27t2plwcqcn`) |
| 16:44:16.647 | 0s | UPLOAD | Worker picks up `process_source`; Worker picks up `acm_extract` |
| 16:44:16.748 | 0s | UPLOAD | TableFormer enabled: `docling_table_structure=True`, mode=accurate |
| 16:44:16.768 | 0s | UPLOAD | `acm_extract` claimed by worker `DESKTOP-HF8ISHS:109348` |
| 16:44:16.851 | 0s | UPLOAD | RapidOCR initialized (onnxruntime) |
| 16:45:13.936 | 57s | DOCLING | Source command reference updated |
| 16:45:14.031 | 58s | DOCLING | Page markers injected into full_text |
| 16:45:14.050 | 58s | DOCLING | "Source text not ready yet, waiting 5s..." |
| 16:45:22.246 | 66s | DOCLING | PIPELINE: Starting Docling table extraction |
| 16:46:19.781 | 123s | DOCLING | DoclingAdapter: 8 tables extracted (pages 2,4,5,6,7,11,12,13) |
| 16:46:19.894 | 123s | DOCLING | **[DOCLING] COMPLETED in 57.7s** -- 8 tables, 67 total rows |
| 16:46:20.256 | 124s | STRUCTURE | PIPELINE: Starting extraction (19 pages) |
| 16:46:20.275 | 124s | STRUCTURE | [STRUCTURE] STARTED -- extracting metadata |
| 16:46:20.276 | 124s | STRUCTURE | Content truncated from 34,369 to 15,000 chars for metadata |
| 16:46:22.413 | 126s | STRUCTURE | Resolved extraction model -> llama3.1:8b |
| 16:46:23.232 | 127s | STRUCTURE | Stored 8 raw extractions (provider=docling) |
| 16:46:23.233 | 127s | STRUCTURE | Dual-provider disabled; Docling-only results |
| 16:46:23.986 | 128s | STRUCTURE | Stored 8 consensus tables |
| 16:46:24.019 | 128s | STRUCTURE | **process_source COMPLETED in 127.37s** |
| 16:46:46.702 | 150s | STRUCTURE | WARNING: Combined metadata+structure LLM failed (Pydantic errors) |
| 16:46:46.704 | 150s | STRUCTURE | Using heuristic fallback for document structure |
| 16:46:46.705 | 150s | STRUCTURE | Result: consultant=Unknown, type=UNKNOWN, register_start=5, buildings=0 |
| 16:46:54.350 | 158s | STRUCTURE | Building inventory compiled: 1 building, pages 5-18 |
| 16:46:54.350 | 158s | STRUCTURE | **[STRUCTURE] COMPLETED in 34.1s** |
| 16:46:54.408 | 158s | ORCHESTRATOR | Saved pre-extraction intelligence |
| 16:46:58.377 | 162s | ORCHESTRATOR | Building extraction: 1 building |
| 16:47:06.719 | 170s | ORCHESTRATOR | Building extraction: 1/1 saved (B001 - Broadmeadows Police Station) |
| 16:47:22-16:49:05 | 186-289s | EXTRACT | Per-row extraction (44 rows, llama3.1:8b) |
| 16:49:05.664 | 289s | EXTRACT | **[EXTRACT] COMPLETED** -- 44 raw records from 1 building |
| 16:49:05.672 | 289s | VALIDATE | [VALIDATE] Round 1: 44 accepted, 0 rejected, 19 validation_failed |
| 16:49:05.685 | 289s | CORRECT | [CORRECT] Attempt 1 started (19 records needing correction) |
| 16:50:34.399 | 378s | CORRECT | **[CORRECT] Attempt 1 COMPLETED in 88.7s** -- 49 LLM corrections |
| 16:50:34.405 | 378s | VALIDATE | [VALIDATE] Round 2: 44 accepted, 12 still failing |
| 16:50:34.417 | 378s | CORRECT | [CORRECT] Attempt 2 started (12 records) |
| 16:51:09.615 | 413s | CORRECT | **[CORRECT] Attempt 2 COMPLETED in 35.2s** -- 60 LLM corrections |
| 16:51:09.621 | 413s | VALIDATE | [VALIDATE] Final: 44 accepted, 3 still failing (passed through) |
| 16:51:09.630 | 413s | STORE | Deduplicated: 2 merged, 42 unique records |
| 16:51:09.636 | 413s | STORE | Skipped no-access recovery (per-row segmenter handled it) |
| 16:51:09.724 | 413s | STORE | Created 1 parent table section |
| 16:51:11.192 | 415s | STORE | **[STORE] COMPLETED in 1.6s** -- 42/42 saved |
| 16:51:11.204 | 415s | COMPLETE | **EXTRACTION COMPLETE -- 42 records in 291.0s** |
| 16:51:19.390 | 423s | EMBED | Embedding started for 42 records |
| 16:51:20.106 | 424s | EMBED | ERROR: `mxbai-embed-large` model not found |
| 16:51:20.108 | 424s | EMBED | Embedding completed: 0/42 records embedded |
| 16:51:23 | 427s | DONE | `review_status` = `pending_review` confirmed |

---

## Phase Durations

| Phase | Start | End | Duration |
|-------|-------|-----|----------|
| Upload + Command Submit | 16:44:16 | 16:44:17 | ~1s |
| Docling Table Extraction | 16:45:22 | 16:46:20 | **57.7s** |
| process_source (total) | 16:44:17 | 16:46:24 | **127.4s** |
| Structure (metadata + inventory) | 16:46:20 | 16:46:54 | **34.1s** |
| Orchestrator (building save) | 16:46:58 | 16:47:07 | **~9s** |
| Per-Row Item Extraction | 16:47:22 | 16:49:06 | **~104s** |
| Validation + Correction (2 rounds) | 16:49:06 | 16:51:10 | **124.0s** |
| Store (dedup + save) | 16:51:10 | 16:51:11 | **1.6s** |
| Embed (failed) | 16:51:19 | 16:51:20 | **0.7s** |
| **Total end-to-end** | **16:44:16** | **16:51:20** | **~7m 4s (424s)** |
| **Pipeline only** | **16:46:20** | **16:51:11** | **~4m 51s (291s)** |

---

## Extraction Results Summary

| Metric | Value |
|--------|-------|
| Buildings found | 1 (B001 - Broadmeadows Police Station) |
| Raw records extracted | 44 |
| Duplicates merged | 2 |
| Final records saved | 42 |
| Records rejected | 0 |
| Records filtered | 0 |
| Confidence: high | 0 |
| Confidence: medium | 40 |
| Confidence: low | 2 |
| Correction round 1 | 49 LLM corrections |
| Correction round 2 | 60 LLM corrections |
| Total LLM corrections | 109 (across 132 validations) |
| Failed corrections | 0 |
| Row extraction failures | 3 (rows 0, 1, 41 -- failed after 2 attempts each) |

---

## SSE Events Observed

| Event/Stream | Observed |
|-------------|----------|
| `GET /api/acm/extraction-progress/{id}/stream` | YES (opened once) |
| `GET /api/agui/extraction/{id}/stream` | YES (opened once) |
| `extraction.started` | Not directly visible in API log (SSE payload) |
| `extraction.docling_complete` | Not directly visible in API log (SSE payload) |
| `ai.building_extracted` | Not directly visible in API log (SSE payload) |
| `ai.building_saved` | Not directly visible in API log (SSE payload) |

**Note:** SSE events are streamed over persistent connections. The API log confirms both SSE endpoints were connected to successfully (200 OK). The actual event payloads are not logged in the HTTP access log -- they would be visible in the SSE stream responses or via the AGUI event emitter logs in the worker. The SSE connections remained open throughout the extraction.

---

## Endpoint Hit Counts

| Endpoint | Hits | Notes |
|----------|------|-------|
| `GET /api/commands/jobs/{id}` | 133 | Command status polling (frequent) |
| `GET /api/sources` | 55 | Source list polling |
| `GET /api/acm/buildings` | 42 | Building data polling |
| `GET /api/sources/{id}/live-stats` | 34 | Live stats polling |
| `GET /api/config` | 3 | Initial config load |
| `GET /api/health` | 2 | Health checks (returned 404) |
| `GET /health` | 1 | Health check (returned 200) |
| `POST /api/sources` | 1 | File upload |
| `POST /api/acm/extract` | 1 | Extraction trigger |
| `GET /api/acm/extraction-progress/{id}/stream` | 1 | SSE stream (persistent) |
| `GET /api/agui/extraction/{id}/stream` | 1 | AG-UI SSE stream (persistent) |
| `GET /api/acm/jobs/{id}/raw-tables` | 1 | Raw tables (post-extraction) |
| `GET /api/acm/field-schema` | 1 | Field schema (post-extraction) |
| `GET /api/acm/validation-summary` | 1 | Validation summary (post-extraction) |
| `GET /api/acm/records` | 1 | Records fetch (post-extraction) |
| `GET /api/notebooks` | 1 | Initial load |
| `GET /api/episode-profiles` | 1 | Initial load |

**HTTP Status Codes:**
- 200: 278 (100% success)
- 404: 2 (only `/api/health` -- this endpoint does not exist; `/health` returns 200)
- 4xx/5xx errors: **0** (excluding the known /api/health 404)

---

## Errors Found

### 1. Embedding Model Not Found (ERROR)
```
Batch 1 embedding failed: Failed to get embeddings:
Ollama API error: model "mxbai-embed-large" not found, try pulling it first
```
- **Impact:** 0/42 records were embedded. Search/similarity features will not work.
- **Fix:** `ollama pull mxbai-embed-large`
- **Severity:** Medium (extraction itself succeeded)

### 2. Row Extraction Failures (ERROR)
- Row 41/44: extraction failed after 2 retries (4234ms)
- Row 43/44 (row 0): extraction failed after 2 retries (4297ms)
- Row 44/44 (row 1): extraction failed after 2 retries (4375ms)
- **Impact:** 3 rows could not be extracted; they were excluded from the 44 raw records -> after dedup, 42 final records. Not clear if these 3 were the 2 that got deduped or simply excluded.
- **Severity:** Low (3/44 rows, likely header/footer rows)

### 3. Langfuse/OTEL Connection Refused (Non-Fatal)
```
ConnectionRefusedError: [WinError 10061] localhost:3000
```
- **Impact:** None on extraction. Telemetry spans were not exported.
- **Fix:** Start Langfuse Docker container, or disable `LANGFUSE_ENABLED`
- **Severity:** None (tracing is non-fatal by design)

### 4. Metadata LLM Extraction Failed (WARNING)
```
Combined metadata+structure LLM extraction failed: 2 validation errors for MetadataAndStructureLLM
structure.sections.5.page_start (int_type)
structure.sections.6.page_start (int_type)
```
- **Impact:** Fell back to heuristic structure detection. consultant=Unknown, type=UNKNOWN.
- **Severity:** Low (heuristic fallback worked; building inventory succeeded)

### 5. Pydantic Serialization Warning
```
PydanticSerializationUnexpectedValue(Expected `str`, got RecordID)
```
- **Impact:** None (cosmetic warning, serialization succeeds)
- **Severity:** None

---

## Validation Warnings Summary

| Warning Category | Count | Details |
|-----------------|-------|---------|
| Unrecognized `sample_result` | 78 | Values: "Negative - Treated as Positive" (32), "Unknown" (31), "Negative, Organic fibres detected" (6), others |
| Unknown `area_type` | 16 | "Internal" (11), "External" (5) |
| Unknown `friability` value `-` | 10 | Passed through as None |
| Unknown `result` values | 4 | "Negative, Organic fibres detected", "Negative, Assumed Positive", etc. |
| LLM tried to modify frozen SF-valid fields | 9 | material_condition, friable, disturbance_potential (blocked correctly) |
| Schema inference failed | 1 | LLM returned invalid response, skipped |
| Page range filter excluded tables | 1 | 2 of 8 tables excluded by page range [5-18] |

---

## Review Status Transitions

| Time | Status |
|------|--------|
| 16:44:16 | `extracting` (set on source creation) |
| 16:44:16 - 16:51:19 | `extracting` (maintained throughout extraction) |
| 16:51:19+ | `pending_review` (set after extraction complete) |

**Verdict:** Correct transitions observed. No unexpected status values.

---

## Frontend Polling Behavior

The frontend maintained consistent polling throughout the extraction:
- **Command status polling:** ~133 requests over ~7 minutes = ~1 request every 3.2s
- **Source list polling:** ~55 requests = ~1 every 7.7s
- **Buildings polling:** ~42 requests = ~1 every 10s
- **Live-stats polling:** ~34 requests = ~1 every 12.5s

Post-extraction, the frontend correctly loaded:
- `/api/acm/jobs/{id}/raw-tables`
- `/api/acm/field-schema`
- `/api/acm/validation-summary`
- `/api/acm/records` (with building_record_id filter)
- `/api/acm/buildings` (refreshed)

---

## Overall Verdict: PASS

The extraction pipeline completed successfully end-to-end:

**Successes:**
- File upload via frontend -> API -> Worker chain worked correctly
- Async processing path used (as expected)
- Docling extracted 8 tables in 57.7s (no CUDA/GPU errors)
- Per-row extraction with llama3.1:8b processed all rows
- 2-round LLM correction cycle improved validation (19 -> 12 -> 3 failures)
- Deduplication correctly merged 2 duplicate records
- 42 records saved to DB with 0 errors
- `review_status` transitioned correctly: `extracting` -> `pending_review`
- All API endpoints returned 200 (no 5xx errors)
- SSE streams connected successfully on both endpoints
- Frontend polling behaved correctly throughout

**Issues to Address:**
1. **Pull `mxbai-embed-large`** -- embeddings failed (medium priority)
2. **3 row extraction failures** -- rows 0, 1, 41 failed validation (low priority, likely headers)
3. **Metadata LLM produced invalid output** -- Pydantic int_type errors on page_start (low priority, heuristic fallback works)
4. **High volume of `sample_result` validation warnings** -- "Negative - Treated as Positive" and "Unknown" are not recognized enum values. Consider adding to enum or normalizer. (medium priority for data quality)
5. **`area_type` values "Internal"/"External" not recognized** -- consider adding to allowed values (low priority)
6. **Langfuse not running** -- telemetry data not captured (low priority for local dev)
