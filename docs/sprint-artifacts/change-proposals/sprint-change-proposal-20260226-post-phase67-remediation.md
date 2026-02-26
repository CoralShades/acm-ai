# Sprint Change Proposal - Epic 22 Post-Phase 6+7 Remediation

**Date:** 2026-02-26
**ID:** SCP-20260226B
**Status:** PROPOSED
**Priority:** P0/P1
**Scope:** Large
**Risk:** Medium
**Path:** Story Additions (new Epic 22 with 5 stories)
**Trigger:** User testing with the Clutch Alexander District Hospital PDF surfaced 10 remaining issues after Phase 6+7 completion.

---

## 1. Motivation

Epic 21 closed key UX gaps (loading states, layout consistency work, SSE wiring), but post-audit testing identified unresolved issues in four areas:

1. Backend schema resilience (enum normalization currently rejects recoverable records)
2. Dashboard layout regression (route wrapper inconsistency)
3. Job detail feature completeness (content + inline chat parity with source detail)
4. Cross-page UX consistency (building tabs and extraction progress polish)

This proposal creates Epic 22 as a focused remediation sprint to close those gaps without broadening scope beyond audited findings.

---

## 2. Proposed Change - New Epic 22

### Epic 22: Post-Audit Remediation & Feature Completion

| Story | Title | Priority | Area | Outcome |
|------|-------|----------|------|---------|
| E22-S1 | Schema Resilience - Normalize Instead of Reject | P0 | Backend | Prevent record loss from enum mismatches |
| E22-S2 | Dashboard Layout Regression Fix | P0 | Frontend | Restore shared dashboard shell consistency |
| E22-S3 | Job Detail Page = Source Detail Layout (PDF + Chat + Content) | P1 | Frontend | Deliver in-context review layout parity |
| E22-S4 | Building Tabs in ACM Register + Job ACM Records | P1 | Frontend | Add reusable per-building filtering tabs |
| E22-S5 | Extraction Streaming & Navigation Polish | P1 | Frontend (+ optional backend) | Improve perceived responsiveness and extraction visibility |

---

## 3. Dependency Chain

Implementation order for lowest risk and fastest feedback:

1. **E22-S1 first (backend blocker)**
   - Stabilizes extraction output so downstream UI pages receive resilient data.
2. **E22-S2, E22-S3, E22-S4 in parallel (frontend tracks)**
   - Independent enough to ship in the same sprint lane after S1 is merged.
3. **E22-S5 last (polish/integration pass)**
   - Depends on stable extraction states and updated job surfaces from S2-S4.

---

## 4. Story Artifacts Created

- `docs/sprint-artifacts/e22-s1-schema-resilience.md`
- `docs/sprint-artifacts/e22-s2-dashboard-layout-fix.md`
- `docs/sprint-artifacts/e22-s3-job-detail-source-layout.md`
- `docs/sprint-artifacts/e22-s4-building-tabs-everywhere.md`
- `docs/sprint-artifacts/e22-s5-extraction-streaming-polish.md`

---

## 5. Impact Analysis

### Product Impact
- Eliminates post-audit blockers to production-ready demo flow.
- Restores expected dashboard navigation consistency.
- Completes job-detail workflow parity with source-detail UX.

### Technical Impact
- Backend validators move from reject-on-variance to normalize-and-log behavior.
- Frontend route/layout and reusable tab filtering patterns are consolidated.
- Extraction progress and navigation feedback become visibly deterministic.

### Quality Impact
- Regression risk is moderate due to shared layout and extraction state wiring.
- Mitigated by explicit story-level guard rails and existing test/build checks.

---

## 6. Files Changed by This Proposal

| File | Change |
|------|--------|
| `docs/sprint-artifacts/change-proposals/sprint-change-proposal-20260226-post-phase67-remediation.md` | New SCP document |
| `docs/sprint-artifacts/e22-s1-schema-resilience.md` | New story |
| `docs/sprint-artifacts/e22-s2-dashboard-layout-fix.md` | New story |
| `docs/sprint-artifacts/e22-s3-job-detail-source-layout.md` | New story |
| `docs/sprint-artifacts/e22-s4-building-tabs-everywhere.md` | New story |
| `docs/sprint-artifacts/e22-s5-extraction-streaming-polish.md` | New story |
| `docs/sprint-artifacts/sprint-status.yaml` | Added Epic 22 and story draft statuses |
| `_bmad-output/project-planning-artifacts/acm-ai/bmm-workflow-status.yaml` | Added SCP-20260226B change-log entry |
| `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` | Added Epic 22 section and story summaries |

---

## 7. Guard Rails

- Planning only: this SCP adds and updates planning artifacts only, no product code modifications.
- Story scope locked to the 10 audited issues and explicitly listed acceptance criteria.
- Dependency order enforced: E22-S1 first, E22-S2/S3/S4 parallel, E22-S5 final integration polish.
