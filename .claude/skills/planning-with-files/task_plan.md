# Task Tracker (2026-03-07)

## Completed This Session
- [x] S7: Deterministic SF Normalization + BAR System Removal (committed d4d6bae4, pushed)
  - Part A: `normalize_to_sf` graph node before validation (sf_normalizer.py, 22 tests)
  - Part C: BAR template system removal (14 files deleted, migration 46)
  - Part B: BAR→SF/ACM/legacy terminology purge across extraction codebase

## Pending Tasks (User Requested)

### Task 1: Observability Stack Validation
- [ ] Spawn subagents to verify Langfuse (self-hosted), LangSmith (via LangGraph API), Logfire+Pydantic setup
- [ ] Use Context7 MCP for up-to-date LangChain/Pydantic/LangGraph docs
- [ ] Use LangChain skills, Pydantic skills for validation
- [ ] Run E2E tester agents to validate observability works end-to-end
- [ ] Spawn subagents and use /planning-with-files to manage context/memory
- **Scope**: Verify all three observability tools are configured correctly per CLAUDE.md observability section
- **Agents**: acm-observability-debugger, acm-trace-analyst, acm-e2e-tester
- **Key files**: `open_notebook/observability/langfuse_config.py`, `open_notebook/observability/logfire_config.py`
- **Refs**: `docs/development/observability.md`, CLAUDE.md Observability Stack table

### Task 2: Frontend SSE/AG-UI Verification
- [ ] Spawn subagent to check frontend SSE endpoints work after S7 changes
- [ ] Verify AG-UI endpoints reflect new `normalize_to_sf` stage
- [ ] Check processing/extraction logs shown in frontend are updated
- [ ] Verify no references to deleted BAR template/field-mapping pages remain in frontend runtime
- [ ] Use /skills for specialized testing
- **Scope**: Ensure S7 graph changes (new normalize node) and BAR removal don't break live SSE streaming or AG-UI display
- **Agents**: acm-e2e-tester, acm-ui-tester, frontend-specialist
- **Key files**: `api/routers/v3_streaming.py`, `api/routers/agui_extraction.py`, `frontend/src/lib/hooks/useV3SSE.ts`, `frontend/src/lib/stores/streamingStore.ts`, `frontend/src/lib/types/pipeline.ts`

## Prior V3 Sprint Backlog
- [ ] E31-S3 — Consensus Layer Core (V3-3, 3SP) — CRITICAL PATH
- [ ] E30-S7 — Two-Phase Extraction Prompts (V3-3, 3SP)
- [ ] E33-S2 — Building Grid + Item Grid (V3-3, 5SP) — needs architect
- [ ] E32-S4 — Classifier Update SF Taxonomy (V3-4, 2SP) — parallel safe
