# Task Plan — Bug Triage Sprint Artifacts + Sprint Status Reconciliation

Updated: 2026-02-21 (Bug Triage BMAD Artifacts)
Source of truth: `docs/sprint-artifacts/sprint-status.yaml`
Bug triage plan: `docs/dumplog/lovely-stirring-wilkinson.md`

---

## ACTIVE: Bug Triage BMAD Artifacts (2026-02-21)

### Context
All 10 bug fix stories from the Bug Triage Plan have been **implemented** (code changes done, frontend builds, lint passes). However, the BMAD project management artifacts (story files, sprint tracking updates, planning file updates) were NOT created. This task creates those artifacts to maintain project governance.

### Phase 1: Create Story Files in docs/sprint-artifacts/ [DONE]
Story files for all 10 completed stories:

**Bug Fix Stories (7):**
- [x] `bug-site-config-query-fix.md` — XS, Epic Standalone
- [x] `bug-grid-column-fixes.md` — S, Epic 2
- [x] `bug-post-upload-navigation.md` — S, Epic 7
- [x] `bug-ui-ux-vaea-branding.md` — S, Epic 14
- [x] `bug-auth-loading-ux.md` — S, Epic 14
- [x] `bug-extraction-progress-fix.md` — M, Epic 15
- [x] `bug-negative-results-regression.md` — M, Epic 1

**New Feature Stories (3):**
- [x] `e1-s28-model-capabilities-schema.md` — L, Epic 1
- [x] `e1-s29-replace-hardcoded-token-limits.md` — L, Epic 1
- [x] `e1-s30-dynamic-embedding-dimensions.md` — M, Epic 1

### Phase 2: Sprint Status YAML Reconciliation [DONE]
- [x] E1-S28, E1-S29, E1-S30 added under Epic 1 (Bug Fixes section)
- [x] All 7 BUG-* stories added under Bug Fixes section
- [x] Summary counts updated: 114 total stories, 85 done (75%)
- [x] Epic 1 count updated: 29/30 done
- [x] E15 moved from backlog to in-progress (E15-S1 done)
- [x] Ready-for-dev count: 8 (E15-S1 removed, was already done)
- [x] KEY CHANGES section added with phase summary

### Phase 3: Planning File Updates [DONE]
- [x] `task_plan.md` — Updated with bug triage artifacts task (this file)
- [x] `progress.md` — Updated with bug triage session log
- [x] `findings.md` — Updated with bug investigation findings

### Phase 4: Sprint Status YAML Structural Fix [DONE]
- [x] E1-S28/S29/S30 stories should be under Epic 1 section (not standalone bug fixes)
- [x] Bug stories should be grouped by originating epic
- [x] NEXT RECOMMENDED ACTIONS updated (E15-S1 done, removed from list)

---

## Remaining Stories (from sprint-status.yaml)

### P0 — Tier 1: Ready for Dev (8 stories, reordered for Ralph sprint)
| # | Story | Title | Size |
|---|-------|-------|------|
| 1 | E2-S8 | Column Visibility Management | S |
| 2 | E10-S1 | Simplify Navigation | S |
| 3 | E16-S3 | Empty States & Onboarding Hints | S |
| 4 | E2-S11 | BAR Field Type Safety | M |
| 5 | E1-S23 | Token Limit Quality Validation | M |
| 6 | E9-S3 | Document Actions & Bulk Operations | M |
| 7 | E5-S3 | BAR Template Management | M |
| 8 | E16-S1 | Dashboard Home Page with ACM Stats | L |

### P1 — Tier 2: Drafted (need promotion)
| # | Story | Title | Blocked By |
|---|-------|-------|------------|
| 9 | E12-S1 | Extraction Method Settings UI | — |
| 10 | E13-S1 | SurrealDB Graph Entity Schema | — |
| 11 | E15-S2 | Extraction Monitor Page | E15-S1 (done) |
| 12 | E5-S4 | Export Field Mapping Config | E5-S3 |
| 13 | E12-S2..S4 | Settings UI suite | E12-S1 |
| 14 | E11-S2 | Hybrid Search Service | — |
