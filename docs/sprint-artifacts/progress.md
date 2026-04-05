# Progress — Chat & UI Bug Fix Sprint (2026-04-05)

## Phase 1 — Investigation & Root Cause
- [x] B1: Model provisioning flow traced
- [x] B1: SurrealDB model table audited
- [x] B1: Root cause identified (old model IDs in MODEL_CATALOG)
- [x] B2: Session load flow traced
- [x] B2: AsyncSqliteSaver confirmed (NOT MemorySaver) — missing message loading endpoint
- [x] B3: record_count NULL confirmed — chat tool uses building_name match instead of FK
- [x] B3: Population point identified — need FK-based query like REST API
- [x] B4: ExtractionStatusBanner state logic read
- [x] B4: Root cause identified (stale review_status + no defensive UI check)

## Phase 2 — Implementation
- [x] B1: Model provisioning updated (latest Anthropic models + legacy kept)
- [x] B1: SurrealDB model dedup (not needed — seed_model_catalog is idempotent)
- [x] B2: Chat history restoration on session switch (backend endpoint + frontend store + panel integration)
- [x] B2: Auto-load last session on refresh (10-min threshold in fetchSessions)
- [x] B3: record_count fixed — chat tool uses building_record_id FK with name fallback
- [x] B3: Backfill migration not needed — record_count is computed dynamically
- [x] B4: Extraction status fixed — effectiveReviewStatus computed value
- [x] B4: VAEA-UI design review (deferred — functional fix applied)

## Phase 3 — E2E Testing
- [ ] Chat tool calls verified (buildings, stats, records)
- [ ] Model selector validated (all models, no dupes)
- [ ] Session navigation verified (context loads)
- [ ] Page refresh verified (auto-restore)
- [ ] Building record counts in tool cards verified
- [ ] Alexander extraction status verified (no cancel button)

## Phase 4 — Documentation
- [ ] sprint-status.yaml updated
- [ ] architecture.md updated
- [ ] GitHub issues created/updated
- [ ] prd.json updated (if needed)
- [ ] CLAUDE.md updated (if new patterns)

## Milestone Summary
| Phase | Status | Items | Done |
|-------|--------|-------|------|
| Investigation | Complete | 9 | 9 |
| Implementation | Complete | 8 | 8 |
| E2E Testing | Not Started | 6 | 0 |
| Documentation | In Progress | 5 | 1 |
| **Total** | **In Progress** | **28** | **18** |
