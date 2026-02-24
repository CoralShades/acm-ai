# E19/E20 Sprint Progress Log
# SCP: sprint-change-proposal-20260224-stakeholder-ux-redesign.md
# Started: 2026-02-24

## Stories

| Story | Status | Completed | Notes |
|-------|--------|-----------|-------|
| E19-S1 | done | 2026-02-24 | Migration 032, destructive — 16 tests pass, ruff clean |
| E19-S2 | done | 2026-02-24 | Jobs dashboard — JobCard, JobStatusPill, /jobs route, redirect from /documents |
| E19-S3 | done | 2026-02-24 | Feature gating — user-mode-store, sidebar Standard/Admin toggle |
| E19-S4 | done | 2026-02-24 | Raw extraction table — RawExtractionTable AG Grid, /jobs/[id]/extract page |
| E19-S5 | done | 2026-02-24 | Building review wizard — WizardStepHeader, BuildingReviewGrid (21-field AG Grid), /jobs/[id]/review/buildings, GET+PUT /api/acm/jobs/{id}/buildings, site_config extended |
| E19-S6 | backlog | — | ACM schema mapping wizard |
| E19-S7 | backlog | — | Job detail page |
| E19-S8 | backlog | — | CRUD chat (P1) |
| E20-S1 | backlog | — | Page boundary fix |
| E20-S2 | backlog | — | REGEX yield check |
| E20-S3 | backlog | — | Not sampled capture |
| E20-S4 | backlog | — | E2E validation (gate: S1+S2+S3 tests must pass first) |

## Session Log

### 2026-02-24
- Party mode session created all 12 story specs
- SCP approved and merged into sprint-status.yaml
- Ralph loop configured: .ralph/PROMPT.md + .ralph/@fix_plan.md
- E19-S1 advanced to ready-for-dev, loop ready to run
- E19-S1 DONE: migrations/32.surrealql, async_migrate.py updated (28-32), Source model + API models updated, 16 unit tests pass
- E19-S2 DONE: JobCard, JobStatusPill, /jobs page, /documents → redirect, nav updated
- E19-S3 DONE: user-mode-store.ts, sidebar Standard/Admin toggle, Configure hidden in standard mode
