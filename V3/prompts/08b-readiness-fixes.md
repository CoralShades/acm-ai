# 08b: Readiness Fixes — Resolve 4 Critical Issues Before Sprint Planning

> **Type:** Document fix (no BMAD command — direct edits)
> **Depends On:** 08-readiness-check (CONDITIONAL GO)
> **Output:** Updated epics, PRD, and architecture docs
> **Run in:** Fresh context window
> **Time:** ~15 minutes

---

## Context

Implementation Readiness Assessment (Step 08) returned **CONDITIONAL GO** with 4 critical issues and 6 minor issues. This prompt resolves all 4 critical issues and the relevant minor ones so we can proceed to Sprint Planning (Step 09).

### Pre-Read Documents
- `_bmad-output/planning-artifacts/implementation-readiness-report-2026-03-03.md` — Full readiness report
- `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` — Epics doc (primary edit target)
- `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md` — PRD (SP update)
- `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` — Architecture (story ref fix)

---

## Prompt

```text
The Implementation Readiness Assessment returned CONDITIONAL GO with 4 critical issues. Fix them all in the documents listed below. Read each document fully before editing.

### FIX 1: FR-1406/FR-1407 Orphan FRs (Epics doc)

**File:** `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md`

**Problem:** FR-1406 (Building__c CSV export) and FR-1407 (Item__c CSV export) are P0 requirements in the PRD but not declared in any epic's FR list. The export story E33-S8 covers the work but lacks the FR traceability.

**Fix:** In the Epic 33 section header (where it lists FRs covered), add FR-1406 and FR-1407 to the FR list. Also add to E33-S8's story description that it fulfills FR-1406 and FR-1407.

### FIX 2: SSE Timing Dependency — Move E34-S1 to E31 (Epics doc + Architecture)

**File:** `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md`

**Problem:** E33-S1 (Upload Wizard + Extraction Progress) requires SSE infrastructure (PipelineEventBus, SSE endpoints) that currently lives in E34-S1. E33 is before E34, creating a dependency violation.

**Decision:** Move E34-S1 (PipelineEventBus + SSE Endpoints) into Epic 31 as a new foundational infra story. SSE is needed for provider extraction progress, so E31 is the natural home.

**Fix steps:**
1. In **Epic 31**, add a new story **E31-S7: PipelineEventBus + SSE Infrastructure** (3 SP):
   - Description: "In-memory PipelineEventBus (asyncio.Queue). Three SSE endpoint categories: extraction pipeline, AI processing, bulk operations. Zustand streaming store. SSE triggers React Query refetch. Extends existing E27 SSE infrastructure (/api/agui/extraction/{id}/stream)."
   - Dependencies: E31-S5 (Pipeline Integration) — SSE events need providers wired in
   - Satisfies: FR-1701, FR-1704
2. Update **Epic 31** totals: stories 6→7, SP 17→20
3. In **Epic 34**, remove S1 (PipelineEventBus + SSE) — renumber E34-S2→S1, E34-S3→S2, etc.
4. Update **Epic 34** totals: stories 5→4, SP 12→9
5. Update the **dependency graph** — E33-S1 now depends on E31-S7 (not E34-S1)
6. Update total summary: stories stay 33, SP stays ~95 (moved, not added)

**Also update in Architecture doc** (`04-architecture.md`):
- Any references to "E34-S1 for SSE infrastructure" should now point to "E31-S7"

### FIX 3: SP Discrepancies (PRD + Epics doc)

**File:** `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md` + `05-epics-and-stories.md`

**Problem:** PRD §11.2 says 89 SP/32 stories. Epics doc has different totals (95 SP/33 stories). Epics doc header claims 97 SP.

**Fix:**
1. In the **Epics doc**, recalculate the ACTUAL SP by summing all stories in E30-E34. Update the header to match the real total.
2. After Fix 2 above (moving E34-S1 to E31-S7), recalculate:
   - E30: count actual SP
   - E31: count actual SP (now includes S7)
   - E32: count actual SP
   - E33: count actual SP
   - E34: count actual SP (now minus old S1)
   - Update the summary table with correct totals
3. In the **PRD** §11.2, update the SP/story counts to match the epics doc actuals.
4. In the **Party Mode plan** (`V3/output/v3-party-mode-plan.md`) §4, update the story count table to match.

### FIX 4: Architecture Story Reference Error (Architecture doc)

**File:** `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md`

**Problem:** Architecture §14.10.1 maps SF Export API endpoints to E33-S7, but the export story is E33-S8. This happened because E33-S7 ("Building Detail Page") was inserted after architecture was written.

**Fix:** In §14.10.1, change all references from E33-S7 to E33-S8 for export-related endpoints.

### MINOR FIXES (do these too)

**Fix 5: Alexander benchmark consistency**
In `05-epics-and-stories.md`, align all Alexander targets to: "≥40/43 as baseline (post-completionState fix), ≥42/43 as stretch goal". Update E31-S6 and E32-S5 acceptance criteria.

**Fix 6: E33-S7 FR backing**
E33-S7 "Building Detail Page" has no PRD FR. Add `FR-1611: Building detail page with editable Building__c fields and child ACM item grid` to the PRD's FR-1600 series (P1 priority), and reference it in E33-S7.

**Fix 7: E30-S8 underspecified AC**
In E30-S8 acceptance criteria, change "Benchmarks pass" to "Broadmeadows 31/31 accuracy maintained. Alexander ≥40/43 baseline. No regression from current pipeline."

**Fix 8: Readiness report R1 correction**
Note: The readiness report marks R1 (MinerU torch constraint) as "UNVALIDATED, HIGH likelihood, HIGH impact." This is OUTDATED — the party mode plan already resolved this. MinerU requires `torch>2.6.0,<3`, our torch 2.10.0 is compatible. R1 was ELIMINATED per party mode correction on 2026-03-02. No document change needed but be aware the readiness report has stale data on this point.

### Verification After All Fixes

1. Recount all SP across E30-E34 — totals must match header, PRD, and party mode plan
2. Verify E33-S1 dependency now points to E31-S7 (not E34-S1)
3. Verify FR-1406, FR-1407 appear in E33's FR list
4. Verify architecture §14.10.1 references E33-S8 for export
5. Verify all Alexander targets say "≥40/43 baseline, ≥42/43 stretch"
6. Verify E34 has been renumbered correctly (old S2→S1, S3→S2, etc.)
```

---

## Verification Checklist

After running:
- [ ] FR-1406, FR-1407 added to E33 FR list
- [ ] E31-S7 (SSE infra) exists with 3 SP
- [ ] E34 renumbered (now 4 stories, ~9 SP)
- [ ] All SP totals consistent across PRD, Epics doc, Party Mode plan
- [ ] Architecture §14.10.1 → E33-S8
- [ ] Alexander benchmark targets aligned
- [ ] FR-1611 added to PRD for E33-S7
- [ ] E30-S8 AC has specific benchmark targets
