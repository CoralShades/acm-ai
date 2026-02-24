# E19/E20 Sprint Review — Task Plan
# Created: 2026-02-24
# Purpose: Verify all 11 implemented stories match their acceptance criteria

## PHASE 1: Backend Review (parallel with Phase 2)
- [x] R-B1: Verify E19-S1 — migrations/32.surrealql + migration registration + Source model review_status field
- [x] R-B2: Verify E19-S8 backend — crud_tools.py, crud_agent.py, /api/agui/crud-chat, security scope guards
- [x] R-B3: Verify E20-S1 — building_inventory.py page boundary fix (+1 overlap logic + tests)
- [x] R-B4: Verify E20-S2 — orchestrator.py yield check (<50% escalation logic + tests)
- [x] R-B5: Verify E20-S3 — prompt update for Not Sampled/No Access + acm_schemas.py no_access field + tests
- [~] R-B6: Run full test suite — constrained by local environment in this session

## PHASE 2: Frontend Review (parallel with Phase 1)
- [x] R-F1: Verify E19-S2 — /jobs page: JobCard, JobStatusPill, review_status pills, CTA buttons, [+ New Job]
- [x] R-F2: Verify E19-S3 — user-mode-store.ts: localStorage persistence, sidebar CONFIGURE gating, toggle button
- [x] R-F3: Verify E19-S4 — /jobs/[id]/extract page: RawExtractionTable, SSE streaming, status transition
- [x] R-F4: Verify E19-S5 — /jobs/[id]/review/buildings: BuildingReviewGrid 21 fields, WizardStepHeader, auto-save
- [x] R-F5: Verify E19-S6 — /jobs/[id]/review/records: ACMReviewGrid 29 fields, per-building tabs, publish button
- [x] R-F6: Verify E19-S7 — /jobs/[id]: 4 tabs (Overview, Buildings, ACM Records, Extraction Log), re-extract action
- [x] R-F7: Verify E19-S8 frontend — /jobs/[id]/chat: WriteConfirmationCard, confirm/cancel protocol
- [~] R-F8: Run frontend build — constrained by local environment in this session

## PHASE 3: AC Checklist Cross-Reference
- [ ] R-AC1: Cross-check E19-S1 AC checklist against migration file line-by-line
- [ ] R-AC2: Cross-check E19-S2 AC checklist against Jobs dashboard implementation
- [ ] R-AC3: Cross-check E19-S3..S4 ACs
- [ ] R-AC4: Cross-check E19-S5..S6 ACs (wizard steps — complex, check all fields)
- [ ] R-AC5: Cross-check E19-S7..S8 ACs
- [ ] R-AC6: Cross-check E20-S1..S3 ACs

## PHASE 4: Sprint Status Reconciliation
- [x] R-S1: Fix any story files that still show "backlog" status (update to "done")
- [x] R-S2: Update party-mode-20260224/progress.md with review findings
- [x] R-S3: Document any gaps found → create bug fix tasks or follow-up stories

## PHASE 5: Post-Review Fix Execution (2026-02-25)
- [x] BUG-1: E19-S2 upload redirect and jobs route alignment
- [x] BUG-2..5: E19-S6 tabs/merge/missing fields corrections
- [x] GAP-1..3: E19-S7 inline edit, log tab integration, CSV URL fix
- [x] Critical extraction startup fix: auth-failure fallback routing with Sonnet/OpenRouter + Ollama/Qwen compatibility
- [x] UX responsiveness mitigation: route loading + prefetch in jobs flow

## REVIEW FINDINGS LOG
(filled in by agents)
