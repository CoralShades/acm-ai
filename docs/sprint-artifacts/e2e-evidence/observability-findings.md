# Observability Findings: SSE Events + Pipeline Changes

**Date:** 2026-03-20
**Investigator:** acm-observability-debugger
**Scope:** New SSE events, grouped save, full pipeline event flow, cross-layer consistency.

---

## 1. SSE Event Bus -- New Events

### 1a. extraction.docling_complete

**Status:** DEFINED but WILL FAIL at runtime due to invalid SurrealQL query.

**BUG FOUND -- Invalid SurrealQL query (Severity: HIGH)**

The query at acm_commands.py:267 references a non-existent column page_numbers.
The acm_table_section schema (migration 18.surrealql) only defines page_start (int) and page_end (int).
No page_numbers array column exists. The query fails silently (caught by except Exception at line 292).
The extraction.docling_complete event will NEVER be emitted in practice.

### 1b. ai.building_saved

**Status:** PROPERLY DEFINED and CORRECTLY WIRED. No issues found.

### 1c. Enriched AIBuildingExtractedData

**Status:** PROPERLY DEFINED with optional metadata fields. No issues found.

---

## 2. Grouped Save in save_records()

**Status:** CORRECTLY IMPLEMENTED.

- Sort key matches groupby key. itertools.groupby works correctly.
- building_id=None is safely coalesced to the string unknown.
- Per-building ai.building_saved emitted after each group saves. Correct.
- Existing ai.save_progress events (every 10 records) preserved. No interference.
- No race condition: save_records() is single-threaded LangGraph node.

---

## 3. Pipeline Event Flow Trace

| Step | Event | Status |
|------|-------|--------|
| 1. Upload | sets review_status=extracting | OK |
| 4. extraction.started | acm_commands.py:217 | OK |
| 5. extraction.docling_complete | acm_commands.py:258 | WILL FAIL (bad query) |
| 6. ai.building_extracted | acm_extraction.py:810 | OK |
| 7. ai.save_started | acm_extraction.py:2772 | OK |
| 8. ai.save_progress | acm_extraction.py:2861 | OK |
| 9. ai.building_saved | acm_extraction.py:2885 | OK |
| 10. ai.save_complete | acm_extraction.py:2954 | OK |
| 11. extraction.complete | acm_extraction.py:3403 | OK |
| 12. review_status=pending_review | acm_commands.py:537 | OK |

---

## 4. Frontend Terminal Event Consistency

**BUG FOUND -- Terminal event set mismatch (Severity: MEDIUM)**

Backend v3_streaming.py terminal events include extraction.complete and extraction.failed.
Frontend useV3SSE.ts TERMINAL_EVENT_TYPES is MISSING both of these.
This causes unnecessary SSE reconnect attempts after backend closes the stream.

ExtractionLiveView.tsx and extract/page.tsx have the same gap.

extraction.docling_complete and ai.building_saved have no dedicated frontend rendering.
They fall through to generic label rendering. Acceptable for now.

---

## 5. Database State

- review_status transitions are covered for all terminal paths.
- extraction_progress terminal status written by UPSERT. Handles edge cases.

---

## 6. Observability Stack Status

| Component | Status |
|-----------|--------|
| Langfuse (localhost:3000) | DOWN |
| LangGraph API (127.0.0.1:2024) | DOWN |
| API (localhost:5055) | UP |
| Logfire | DISABLED |

---

## 7. Summary

### Bugs

| # | Severity | Component | Description |
|---|----------|-----------|-------------|
| 1 | HIGH | acm_commands.py:267 | SurrealQL references non-existent page_numbers column. extraction.docling_complete never fires. |
| 2 | MEDIUM | useV3SSE.ts:16-21 | TERMINAL_EVENT_TYPES missing extraction.complete and extraction.failed. Unnecessary reconnect loop. |
| 3 | LOW | ExtractionLiveView.tsx:126 | Local TERMINAL_EVENT_TYPES also missing extraction.complete, extraction.failed, ai.save_complete. |
| 4 | LOW | extract/page.tsx:86 | Same terminal event gap as ExtractionLiveView. |

### Recommendations

1. Fix Bug 1: Replace page_numbers query with page_start/page_end columns.
2. Fix Bug 2: Add extraction.complete and extraction.failed to useV3SSE.ts TERMINAL_EVENT_TYPES.
3. Fix Bugs 3-4: Update TERMINAL_EVENT_TYPES in ExtractionLiveView.tsx and extract/page.tsx.
4. (Optional) Add dedicated rendering for new events in ExtractionLiveView.tsx.
5. Start Langfuse before next E2E extraction run.