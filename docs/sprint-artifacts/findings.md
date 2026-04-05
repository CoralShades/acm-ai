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

## Root Cause Hypotheses

### B1 — Model Selection
- **Hypothesis**: `model_provisioning.py` registers models with provider-specific names but LangChain's `init_chat_model()` needs exact model ID strings. Haiku might be registered as `claude-3-haiku-20240307` (old) instead of `claude-haiku-4-5-20251001`.
- **Check**: Query `SELECT * FROM model WHERE provider = 'anthropic'` in SurrealDB.

### B2 — Chat Session Persistence
- **Hypothesis**: `MemorySaver` is in-memory only — all state lost on API restart. Session REST API (`unified_sessions.py`) stores metadata but not message history. CopilotKit `useCoAgent` doesn't replay messages from checkpointer.
- **Check**: Read `checkpointer.py` and `useUnifiedChat.ts` for message restoration logic.

### B3 — Building Record Count NULL
- **Hypothesis**: `record_count` field exists on `BuildingRecord` model but is never populated during extraction. The extraction graph saves buildings but doesn't count their items afterward.
- **Check**: Search for `record_count` assignment in `acm_extraction.py`.

### B4 — Cancel Extraction Button
- **Hypothesis**: `ExtractionStatusBanner` or `JobControls` checks `isExtracting` from SSE state which may remain stale after extraction completes if the SSE connection was interrupted.
- **Check**: Read `ExtractionStatusBanner.tsx` and trace `processing_status` prop source.
