# Epic 19: Standard User UX Redesign

**Status:** backlog
**Priority:** P0 (S1-S7), P1 (S8)
**Change Proposal:** SCP-20260224 (2026-02-24)
**Trigger:** Post-demo stakeholder feedback — Issues 1, 2, 3

---

## Summary

Redesign the complete compliance officer user experience. Introduces the "Jobs" mental model, a mandatory post-extraction two-step review wizard (building mapping → ACM schema mapping), feature gating to simplify the interface for standard users, and (P1) a conversational CRUD chat interface scoped to individual jobs.

---

## User Personas

**Primary:** Standard Compliance Officer
- Uploads SAMP/BAR documents, reviews extraction output, exports BAR register
- Does NOT need: extraction monitoring, AI model config, knowledge graph, advanced settings

**Secondary:** Power User / Administrator
- All features accessible via Configure section

---

## Epic Stories

| Story | Title | Priority | Size | Status |
|-------|-------|----------|------|--------|
| E19-S1 | Migration 32 — review_status + delete acm_records | P0 | S | backlog |
| E19-S2 | Jobs Dashboard — rename Documents → Jobs | P0 | S | backlog |
| E19-S3 | Feature Gating — hide admin features for standard users | P0 | XS | backlog |
| E19-S4 | Raw Extraction Table — live raw records during/after extraction | P0 | M | backlog |
| E19-S5 | Building Review Wizard Step 1 — 21-field building mapping | P0 | L | backlog |
| E19-S6 | ACM Schema Mapping Wizard Step 2 — 29-field per-building review | P0 | L | backlog |
| E19-S7 | Job Detail Page — permanent review tabs + per-building export | P0 | M | backlog |
| E19-S8 | Conversational CRUD Chat — LangGraph CRUD agent | P1 | XL | backlog |

---

## Key Architecture Constraints

1. `source` table internal naming UNCHANGED. Frontend surfaces it as "Job."
2. Migration 32 runs first — all existing `acm_record` rows deleted (data clean-slate)
3. Building data maps to existing `site_config` + `acm_record` building fields (no new DB table)
4. CRUD chat writes scoped to current job only; global register chat is read-only
5. Existing `BuildingTabs.tsx` reused in Step 2 wizard

---

## Implementation Sequence

```
E19-S1 → E19-S2 + E19-S3 (parallel safe) → E19-S4 → E19-S5 → E19-S6 → E19-S7 → E19-S8 (P1)
```

---

## Key Files Created/Modified (Expected)

| File | Change |
|------|--------|
| `migrations/032_review_status.surql` | New — adds review_status to source, deletes acm_record |
| `api/routers/acm.py` | Add /jobs/{id}/buildings, /jobs/{id}/review-status, /jobs/{id}/publish |
| `frontend/src/app/jobs/page.tsx` | New — Jobs dashboard |
| `frontend/src/app/jobs/[id]/page.tsx` | New — Job detail page with tabs |
| `frontend/src/components/acm/BuildingReviewWizard.tsx` | New — Step 1 building wizard |
| `frontend/src/components/acm/ACMReviewWizard.tsx` | New — Step 2 ACM mapping wizard |
| `frontend/src/components/acm/RawExtractionTable.tsx` | New — live raw records grid |
| `frontend/src/components/layout/AppSidebar.tsx` | Feature gating logic |
| `frontend/src/app/upload/UploadResults.tsx` | Redirect to review wizard instead of source detail |

---

## Acceptance Criteria Summary

- Compliance officers see: Jobs, Register, Chat (3 nav items)
- Admin/Power users see all existing features in CONFIGURE section
- After upload: user is directed to Building Review wizard (not source detail)
- All extracted records (including No Access, Not Sampled) appear in raw table before mapping
- Step 1 wizard: 21 building fields editable, live update on table as user confirms
- Step 2 wizard: 29 ACM fields per-building tabs, inline editable AG Grid with live updates
- Job detail page: permanent tabs for re-review, re-extract, per-building export
- Export: combined CSV (43 BAR columns) + per-building Excel sheets
