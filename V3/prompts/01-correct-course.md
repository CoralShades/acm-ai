# 01: Correct Course — Archive E29/E30, Establish V3

> **BMAD Command:** `/bmad-bmm-correct-course`
> **Agent:** Bob — 🏃 Scrum Master
> **Depends On:** None (can run immediately, parallel with P0 and 02)
> **Output:** Updated sprint-status.yaml + change proposal document
> **Run in:** Fresh context window

---

## Pre-Read Documents

The agent should read these before starting:
- `docs/sprint-artifacts/sprint-status.yaml` — current sprint status
- `V3/SCP-20260301-SF-salesforce-alignment.md` — E30 proposal being archived
- `V3/sprint-change-proposal-20260301-unified-pipeline.md` — E29 original SCP
- `V3/epic-29-pipeline-unification.reconciled.yaml` — E29 reconciled plan
- `V3/output/e30-multi-agent-audit-unified.md` — E30 audit findings (preserve as V3 input)

---

## Prompt

```text
/bmad-bmm-correct-course

## Course Correction: V3 Scope Expansion

### Decision Context

After reviewing the E30 Salesforce alignment proposal and conducting multi-agent audits, the scope has expanded significantly beyond what E30 covers. The project owner (Demi) has decided to:

1. **Archive E29 remaining stories (S5-S8)** — E29 S1-S4 are done and retained. Recovery stories R1/R2 are in review — mark as archived (their fixes will be incorporated into V3 epics).
2. **Archive E30 SCP** — The Salesforce alignment requirements are APPROVED and carry forward as V3 inputs, but the E30 epic structure and story breakdown are superseded by V3 planning.
3. **Create V3 fresh epic structure** — New epics will be planned through Party Mode + full BMAD planning cycle.

### What Carries Forward (DO NOT discard)
- All SF alignment requirements (FR-1401 through FR-1412) — approved decisions
- Multi-agent audit findings (V3/output/e30-multi-agent-audit-unified.md) — validated analysis
- E29 S1-S4 completed work (JSON parser, benchmark harness, unified orchestrator, capability registry)
- SF field summaries (V3/output/building_fields_summary.md, item_fields_summary.md)

### What Gets Archived
- E29 S5-S8 (drafted, blocked by Gate 2) — superseded by V3 agent decomposition approach
- E29 R1, R2 (review status) — fixes will be incorporated into V3 extraction stories
- E30 SCP and all E30-S1 through E30-S10 backlog entries — replaced by V3 epic planning

### New V3 Scope (to be planned in subsequent steps)
- Multi-provider extraction (Docling + Google Doc AI + PaddleOCR) with consensus layer
- Salesforce Building__c + Item__c schema alignment (from E30)
- New UI: upload wizard, raw table editor, provenance viewer, record wizard
- AI batching strategy across multiple providers
- SSE streaming for all endpoints + AG-UI integration
- Full extraction lineage / provenance tracking

### Required Actions
1. Update `docs/sprint-artifacts/sprint-status.yaml`:
   - Change `e29-s5` through `e29-s8` status to `archived` with note: "Superseded by V3 scope expansion — see SCP-V3"
   - Change `e29-r1`, `e29-r2` status to `archived` with note: "Fixes incorporated into V3 extraction epics"
   - Add `epic-29-retrospective: optional` if not present
   - Do NOT add E30 entries (they were never added to sprint-status)
2. Create change proposal document at `V3/output/SCP-V3-scope-expansion.md` documenting:
   - Decision rationale
   - What's archived vs carried forward
   - V3 scope summary
   - Next steps (Party Mode → PRD → Architecture → Epics)
3. Update `_bmad-output/project-planning-artifacts/acm-ai/bmm-workflow-status.yaml` with correct-course entry

### Constraints
- Do NOT modify any E29 S1-S4 entries (they are done)
- Do NOT delete any files — only update status fields
- Do NOT create V3 epic entries yet — that happens after Party Mode planning
- Preserve all E30 SCP documents as-is (they're V3 inputs, not trash)
```

---

## Verification Checklist

After running:
- [ ] `sprint-status.yaml` shows E29 S5-S8 as `archived`
- [ ] `sprint-status.yaml` shows E29 R1, R2 as `archived`
- [ ] `V3/output/SCP-V3-scope-expansion.md` exists with decision documentation
- [ ] E29 S1-S4 status unchanged (still `done`)
- [ ] No E30 entries were added to sprint-status
