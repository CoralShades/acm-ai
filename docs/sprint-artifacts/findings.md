# Findings — Chat & UI Bug Fix Sprint (2026-04-05)

## GitHub Issue Cross-Reference

### 12 Open Issues (as of 2026-04-05)

| # | Title | Labels | User Bug Match | Action |
|---|-------|--------|----------------|--------|
| #120 | Next.js dev server crashes on WSL2 with webpack chunk errors | bug, frontend, minor | None | Skip — dev-only, workaround exists |
| #119 | building_record.record_count is NULL for all records | bug, data, v3 | **B3 (exact match)** | Fix in this sprint |
| #118 | CopilotKit HITL approve result not displayed in chat | bug, frontend, chat | **B2 (partial)** — broader session persistence issue | Fix in this sprint |
| #106 | Model selection mismatch — phi4:14b used instead of configured qwen2.5:7b | bug, extraction, ollama | **B1 (related)** — user reports broader: all non-sonnet/llama models fail | Fix in this sprint |
| #103 | Extraction Audit Findings (March 12) | bug, extraction, v3 | None | Audit — check if items resolved |
| #101 | OpenRouter fallback chain non-functional — insufficient credits | bug | None | Skip — external dependency |
| #100 | ACM extraction puts material descriptions in room_name field | bug | None | Defer — data quality, not chat |
| #98 | Test pipeline logs contaminate production log files | bug | None | Low priority |
| #94 | Anthropic Direct provider never tested — routing gap | bug | None | Related to B1 model setup |
| #90 | SSE connection falls back to polling on completed jobs | bug, frontend, minor | **B4 (related)** — stale extraction state | Investigate |
| #89 | V3 building register empty for pre-V3 sources — migration needed | bug, data, v3 | None | Defer — migration story |
| #84 | F2-F8: instructions-sample files runtime config mismatch | bug | None | Defer — config cleanup |

### New Issues to Create

| Bug | Proposed GitHub Issue |
|-----|---------------------|
| B2 (full) | "Chat sessions don't persist — empty on navigate/refresh, no auto-restore" |
| B4 | "Cancel Extraction button visible on completed jobs (Alexander)" |

## Root Causes (Confirmed 2026-04-05)

### B1 — Model Selection (CONFIRMED)
- **Root cause**: `MODEL_CATALOG` in `model_provisioning.py` had old Anthropic model IDs. `claude-3-5-haiku-20241022` (old) instead of `claude-haiku-4-5-20251001` (current). `FALLBACK_MODELS` also referenced the old haiku ID.
- **Fix**: Updated MODEL_CATALOG with latest 3 Anthropic model IDs (haiku 4.5, sonnet 4.5, opus 4.6). Updated FALLBACK_MODELS. Kept legacy IDs for existing DB references.

### B2 — Chat Session Persistence (CONFIRMED)
- **Root cause**: NOT a MemorySaver issue — `checkpointer.py` already uses `AsyncSqliteSaver` (durable). The real issue: no backend endpoint to read message history from checkpointer, and frontend `chatSessionStore.ts` never loads messages when switching sessions or on page refresh.
- **Fix**: Add `GET /{source_id}/unified-sessions/{session_id}/messages` endpoint that reads from AsyncSqliteSaver. Frontend: load messages on session switch and auto-restore recent session on page load.

### B3 — Building Record Count NULL (CONFIRMED)
- **Root cause**: Chat tool `list_acm_buildings` (acm_tools.py:395) computed `record_count` by grouping `acm_record` by `building_name` and matching to `building_record.building_name`. Name mismatches between tables caused 0 counts. The REST API (`acm.py:2623`) uses `building_record_id` FK which works correctly.
- **Fix**: Updated chat tool to use `building_record_id` FK matching (like the REST API) with fallback to name matching for records without FK.

### B4 — Cancel Extraction Button (CONFIRMED)
- **Root cause**: `page.tsx:312-313` passed `reviewStatus` directly from `source?.review_status`. If the `review_status` update in `acm_commands.py:597-603` failed silently (wrapped in try/except), the DB value stayed as `'extracting'`. Frontend had no defensive check for stale status.
- **Fix**: Added `effectiveReviewStatus` computed value in page.tsx that treats `'extracting'` as `'pending_review'` when `panelPhase` indicates extraction is done (idle/completed/failed).
