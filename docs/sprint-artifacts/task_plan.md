# Task Plan — Chat & UI Bug Fix Sprint (2026-04-05)

## Objective
Fix 5 bugs (4 user-reported + GitHub cross-check), update all documentation, and run full E2E verification with team-based approach.

## Bug Registry

| # | Bug | Severity | GitHub Issue | Status |
|---|-----|----------|-------------|--------|
| B1 | Model selection — most models unrecognized in LangChain workflow (haiku fails, sonnet/llama3.1:8b work) | P1 | #106 (related) | NEW — broader scope than #106 |
| B2 | Previous chat sessions don't load context — empty on navigate, no auto-restore on refresh | P1 | #118 (partial) | NEW — #118 is about HITL display only |
| B3 | Buildings show 6+1 correctly but tool cards/messages show 0 records | P1 | #119 (exact match) | OPEN — `record_count` NULL in DB |
| B4 | Alexander job page shows "Cancel Extraction" button after extraction is already finished | P2 | None | NEW — needs `/vaea-ui` root cause analysis |
| B5 | Cross-check: remaining open GitHub issues (#84, #89, #90, #94, #98, #100, #101, #103, #106, #118, #119, #120) | P3 | Multiple | AUDIT |

## Phases

### Phase 1 — Investigation & Root Cause (Team: UX + Logs + Devil's Advocate)
1. [ ] B1: Trace model provisioning flow — `model_provisioning.py` → `esperanto` → LangChain ChatModel registry
2. [ ] B1: Audit `GET /api/models` and `GET /api/models/defaults` — check which models are in SurrealDB `model` table
3. [ ] B1: Identify why haiku/opus fail but sonnet works — likely model name format mismatch
4. [ ] B2: Trace session load flow — `chatSessionStore.fetch()` → REST API → `MemorySaver` checkpointer
5. [ ] B2: Check if `MemorySaver` loses state on API restart (expected) — plan durable persistence
6. [ ] B3: Query `SELECT record_count FROM building_record WHERE source_id = X` — confirm NULL
7. [ ] B3: Find where `record_count` should be populated — extraction vs post-extraction
8. [ ] B4: Read `ExtractionStatusBanner.tsx` + `JobControls.tsx` — find extraction state logic
9. [ ] B4: Trace extraction status lifecycle — when does `isExtracting` get set to false?

### Phase 2 — Implementation (Team: Frontend + Backend specialists)
10. [ ] B1: Update model provisioning to support latest Anthropic models (claude-sonnet-4-5-20250514, claude-haiku-4-5-20251001, claude-opus-4-6-20250610)
11. [ ] B1: Deduplicate models in SurrealDB — remove stale entries, update provider mappings
12. [ ] B1: Sync available Ollama models from `GET /api/tags` — auto-register/dedup
13. [ ] B2: Implement chat history loading from checkpointer when switching sessions
14. [ ] B2: Auto-load last conversation (within 10 min) or create new on page refresh
15. [ ] B3: Populate `record_count` via COUNT query after extraction completes
16. [ ] B3: Add migration to backfill existing building records
17. [ ] B4: Fix extraction status check — use `source.processing_status` not stale SSE state
18. [ ] B4: Apply `/vaea-ui` design review for proper state transitions

### Phase 3 — E2E Testing (Team: Browser tester + Observability)
19. [ ] Send test messages: "list all buildings", "show ACM stats", "how many records?"
20. [ ] Verify model selector shows all valid models (no duplicates, no unrecognized)
21. [ ] Navigate between sessions — verify context loads
22. [ ] Refresh page — verify last session auto-loads or new session created
23. [ ] Verify building tool cards show correct record counts
24. [ ] Verify Alexander job page shows correct extraction status (no cancel button)

### Phase 4 — Documentation & Cleanup (Team: Docs specialist)
25. [ ] Update `sprint-status.yaml` with all fixes
26. [ ] Update `docs/development/architecture.md` with chat session persistence changes
27. [ ] Create/update GitHub issues for each bug
28. [ ] Update `prd.json` if new stories needed
29. [ ] Update CLAUDE.md if new patterns established

## Team Assignment

| Role | Model | Responsibilities |
|------|-------|-----------------|
| **Team Lead** | opus | Coordinates all teams, makes architectural decisions, reviews fixes |
| **UX Specialist** | opus | B4 root cause via /vaea-ui, extraction status UI audit |
| **Log Auditor** | opus | Tail SurrealDB/API/worker/frontend logs, trace failures |
| **Devil's Advocate** | opus | Review all fixes for edge cases, false positives, regressions |
| **Browser Tester** | sonnet | /agent-browser E2E testing, user message simulation |
| **Docs Specialist** | haiku | Sprint-status, architecture, prd updates |
