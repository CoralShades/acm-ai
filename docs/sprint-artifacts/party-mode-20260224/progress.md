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
| E19-S6 | done | 2026-02-24 | ACM schema mapping wizard — ACMReviewGrid (29-field AG Grid), RecordMergeModal, /jobs/[id]/review/records, POST /api/acm/jobs/{id}/publish, no_access+smf_present fields |
| E19-S7 | done | 2026-02-24 | Job detail page — /jobs/[id] with 4 tabs (Overview, Buildings, ACM Records, Extraction Log), JobDetailHeader, JobOverviewTab, re-extract + export actions |
| E19-S8 | done | 2026-02-24 | CRUD chat — crud_tools.py, crud_agent.py, /api/agui/crud-chat, WriteConfirmationCard, /jobs/[id]/chat, copilot-crud runtime |
| E20-S1 | done | 2026-02-24 | Page boundary fix — _apply_boundary_overlap(), 5 new unit tests, 48/48 pass |
| E20-S2 | done | 2026-02-24 | REGEX yield check — acm_item_count_estimate on plan, escalation logic, 5 new tests, 52/52 pass |
| E20-S3 | done | 2026-02-24 | Not Sampled / No Access — no_access field on ACMExtractionRecord, prompt updated (rules 7-8, controlled vocab, output fields), 5 new tests, 1001/1001 pass |
| E20-S4 | blocked | — | E2E validation — BLOCKED: OpenRouter + Anthropic API credits exhausted. Test threshold updated to 31/31 (100%). Log: e20-broadmeadows-validation.log |

## Session Log

### 2026-02-24
- Party mode session created all 12 story specs
- SCP approved and merged into sprint-status.yaml
- Ralph loop configured: .ralph/PROMPT.md + .ralph/@fix_plan.md
- E19-S1 advanced to ready-for-dev, loop ready to run
- E19-S1 DONE: migrations/32.surrealql, async_migrate.py updated (28-32), Source model + API models updated, 16 unit tests pass
- E19-S2 DONE: JobCard, JobStatusPill, /jobs page, /documents → redirect, nav updated
- E19-S3 DONE: user-mode-store.ts, sidebar Standard/Admin toggle, Configure hidden in standard mode

### 2026-02-25
- Post-review stabilization started from `docs/reviews/e19-e20-review/findings.md` priority list.
- E19-S2 fixed: upload completion redirect now goes to `/jobs/{id}/review/buildings`; Jobs cards now route to `/jobs/{id}` and include building counts.
- E19-S6 fixed: `BuildingTabs` now includes `Unassigned` + `All Records`; `RecordMergeModal` wired into `ACMReviewGrid`; missing ACM fields added.
- E19-S7 fixed: job title inline-edit added; Extraction Log tab now renders `ExtractionProgressPanel`; CSV export URL aligned to `/api/acm/export/csv`.
- Extraction reliability fix implemented: runtime auth-failure fallback model routing in extraction/orchestrator paths while preserving Sonnet/OpenRouter and Ollama/Qwen compatibility.
- Perceived navigation freeze mitigations added: jobs route loading UI + route prefetching.
- Verification status: static diagnostics clean on changed files; full frontend/backend command verification partially constrained by shell/runtime environment (WSL service instability and UV environment re-sync).
