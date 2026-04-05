# Progress — Chat & UI Bug Fix Sprint (2026-04-05)

## Phase 1 — Investigation & Root Cause
- [ ] B1: Model provisioning flow traced
- [ ] B1: SurrealDB model table audited
- [ ] B1: Root cause identified (model name format)
- [ ] B2: Session load flow traced
- [ ] B2: MemorySaver persistence gap confirmed
- [ ] B3: record_count NULL confirmed in DB
- [ ] B3: Population point identified
- [ ] B4: ExtractionStatusBanner state logic read
- [ ] B4: Root cause identified (stale state vs source status)

## Phase 2 — Implementation
- [ ] B1: Model provisioning updated (latest Anthropic + Ollama sync)
- [ ] B1: SurrealDB model dedup
- [ ] B2: Chat history restoration on session switch
- [ ] B2: Auto-load last session on refresh
- [ ] B3: record_count populated after extraction
- [ ] B3: Backfill migration for existing records
- [ ] B4: Extraction status fixed
- [ ] B4: VAEA-UI design review applied

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
| Investigation | Not Started | 9 | 0 |
| Implementation | Not Started | 8 | 0 |
| E2E Testing | Not Started | 6 | 0 |
| Documentation | Not Started | 5 | 0 |
| **Total** | **Not Started** | **28** | **0** |
