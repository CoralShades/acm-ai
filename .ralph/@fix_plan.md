# E19/E20 Sprint — Fix Plan
# SCP: docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260224-stakeholder-ux-redesign.md
# Per-story prompts: docs/sprint-artifacts/e19-e20-implementation-prompts.md
# Updated: 2026-02-24

## Epic 19: Standard User UX Redesign (P0)

- [x] E19-S1: Migration 032 — add review_status to source, delete all acm_records — spec: docs/sprint-artifacts/e19-s1-migration-32-review-status.md
- [x] E19-S2: Jobs Dashboard — replace Documents library with Jobs dashboard, review_status pills — spec: docs/sprint-artifacts/e19-s2-jobs-dashboard.md
- [x] E19-S3: Feature Gating — Standard/Admin mode toggle, hide CONFIGURE for standard users — spec: docs/sprint-artifacts/e19-s3-feature-gating.md
- [x] E19-S4: Raw Extraction Table — live AG Grid during and after extraction — spec: docs/sprint-artifacts/e19-s4-raw-extraction-table.md
- [x] E19-S5: Building Review Wizard Step 1 — 21-field building mapping AG Grid — spec: docs/sprint-artifacts/e19-s5-building-review-wizard.md
- [x] E19-S6: ACM Schema Mapping Wizard Step 2 — 29-field ACM grid, publish endpoint — spec: docs/sprint-artifacts/e19-s6-acm-schema-mapping-wizard.md
- [x] E19-S7: Job Detail Page — 4-tab permanent job page (Overview, Buildings, ACM Records, Extraction Log) — spec: docs/sprint-artifacts/e19-s7-job-detail-page.md
- [x] E19-S8 (P1): Conversational CRUD Chat — job-scoped CRUD chat with preview_write confirmation — spec: docs/sprint-artifacts/e19-s8-conversational-crud-chat.md

## Epic 20: Extraction Completeness & 100% Record Capture (P0)

- [x] E20-S1: Page Boundary Fix — page_end +1 overlap to capture boundary page records — spec: docs/sprint-artifacts/e20-s1-page-boundary-fix.md
- [ ] E20-S2: REGEX_ONLY Yield Check — escalate to FULL_LLM if <50% yield — spec: docs/sprint-artifacts/e20-s2-regex-yield-check.md
- [ ] E20-S3: Not Sampled / No Access Capture — update prompt + confirm no_access schema field — spec: docs/sprint-artifacts/e20-s3-not-sampled-capture.md
- [ ] E20-S4: E2E Accuracy Validation — 32/32 Broadmeadows PDF (ONE real extraction, after S1+S2+S3 pass) — spec: docs/sprint-artifacts/e20-s4-e2e-accuracy-validation.md
