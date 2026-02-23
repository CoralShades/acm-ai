# Task Plan — Feature Complete

Updated: 2026-02-22 (Final Reconciliation)
Source of truth: `docs/sprint-artifacts/sprint-status.yaml`

---

## Project Summary

- **Total Stories**: 122
- **Done**: 112 (92%)
- **Archived**: 10 (E8)
- **Completed Epics**: E1, E2, E3, E4, E5, E6, E7, E9, E10, E11, E12, E13, E14, E15, E16, E17 (16/17)
- **Archived Epics**: E8

**All feature stories are complete.** The project is feature-complete.

---

## Deferred Items

1. **Test coverage**: No test coverage for new backend endpoints (source_bulk.py, graph.py, settings.py stage models)
2. **DocumentActions dropdown**: Individual document action dropdown component not created (functionality exists in BulkActions.tsx)
3. **Runtime ACM mode toggle**: Settings UI toggle for ACM mode not implemented (env-var control works)
4. **Epic retrospectives**: All optional, none completed

---

## 2026-02-23 Release Task: Cross-Site Navigation + Domain Cutover

- [x] Add marketing -> app `Open App` CTAs (header, hero, footer) using `NEXT_PUBLIC_APP_URL`
- [x] Add app -> marketing links in sidebar + command palette using `NEXT_PUBLIC_MARKETING_URL`
- [x] Update env examples (`frontend/.env.example`, `marketing-site/.env.local.example`, root `.env.example`)
- [x] Update deployment docs with two-project Vercel domain mapping
- [x] Update BMAD planning artifacts (PRD, architecture, epics/stories, sprint status, workflow status)

---

## Sprint History

### Final Reconciliation (2026-02-22): 7 stories verified & marked done
E10-S1, E9-S3, E12-S2, E12-S3, E12-S4, E13-S2, E13-S3
(All were implemented in prior Ralph sprint but tracking artifacts never updated)

### Epic 17 (2026-02-22): 6 stories implemented
E17-S1..S6 (AG-UI extraction, A2A agent card, OpenRouter models)

### Ralph Sprint (2026-02-22): 11 stories completed
E2-S8, E2-S11, E16-S3, E1-S23, E5-S3, E16-S1, E12-S1, E13-S1, E15-S2, E5-S4, E11-S2

### Bug Triage (2026-02-21): 10 stories completed
7 bug fixes + E1-S28/S29/S30 (model capabilities, dynamic token limits)
