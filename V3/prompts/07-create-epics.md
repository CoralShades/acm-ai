# 07: Create Epics & Stories — V3 Epic Structure

> **BMAD Command:** `/bmad-bmm-create-epics-and-stories`
> **Agent:** John — 📋 Product Manager
> **Depends On:** 05-create-architecture + 06-create-ux (both must be complete)
> **Output:** Updated `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md`
> **Run in:** Fresh context window

---

## Pre-Read Documents

### Planning Artifacts (all updated by previous steps)
- `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md` — Updated PRD with V3 FRs
- `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` — V3 architecture
- `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` — Current epics (to be extended)
- UX design output from Step 06

### V3 Context
- `V3/output/v3-party-mode-plan.md` — Epic boundary recommendations from Party Mode
- `V3/output/e30-multi-agent-audit-unified.md` — Story estimates from John's findings (J1-J22)
- `V3/output/SCP-V3-scope-expansion.md` — Course correction decision (from Step 01)
- `V3/output/tech-research-extraction-providers.md` — Provider implementation estimates

---

## Prompt

```text
/bmad-bmm-create-epics-and-stories

## V3 Epics & Stories

### Context
Create the V3 epic structure. Epics 1-28 are complete/archived, E29 S1-S4 are done (S5-S8 archived), E30 is archived. New V3 epics start from the next available number.

### Epic Boundary Guidelines (from Party Mode)

Refer to `V3/output/v3-party-mode-plan.md` section "Epic Boundary Recommendations" for the agreed structure. The general shape should be:

#### Suggested Epic Structure (adjust based on Party Mode output)

**Epic 30: V3 Foundation — Schema + Config**
- SF schema config loader (Building__c + Item__c JSON configs)
- Building record table + domain model (split from flat acm_record)
- ACM record SF field alignment (Pydantic aliases, additive migration)
- Data migration script (BAR → SF vocabulary, "Good" → "Stable")
- Dependent picklist validator (Friability chain + Building Type chain)
- SF field_schema table evolution
~5-7 stories, foundation for everything else

**Epic 31: V3 Extraction — Multi-Provider Pipeline**
- Provider adapter interface + base class
- Docling provider adapter (wrap existing)
- Second provider adapter (Google Doc AI or PaddleOCR per tech research)
- Consensus layer + confidence scoring
- Raw extraction storage (before AI processing)
- Extraction provenance tracking (page, bbox, provider metadata)
- Upload flow with provider selection
~6-8 stories

**Epic 32: V3 AI Processing — Batching + Model Routing**
- Two-phase extraction prompts (Building__c → Item__c)
- AI batching strategy (token-aware chunking)
- Multi-provider model routing (extend capability registry)
- AI-filled records mapped to raw building records
- Building ID generation (BLD#001 pattern)
- Prompt templates with SF field names + dynamic picklist injection
~5-7 stories

**Epic 33: V3 Frontend — UI Flows + Streaming**
- Upload wizard (multi-step)
- Raw extracted table view (AG Grid + inline editing)
- Building list + detail view (two-level navigation)
- ACM item grid with dependent picklist cascading
- Record editing wizard
- Provenance viewer panel (click-to-source)
- Bulk operations
- SSE streaming for all operations + AG-UI integration
~8-10 stories

**Epic 34: V3 Integration — Export + E2E**
- SF Data Loader export (Building__c.csv + Item__c.csv)
- Two-sheet Excel export with external ID linkage
- E2E test suite (full pipeline: upload → extract → validate → export)
- Benchmark validation (Broadmeadows + Alexander at V3 accuracy)
- Canonical artifact updates (PRD, architecture, docs alignment)
~4-6 stories

### Story Requirements

For each story, provide:
1. **Title** in user story format: "As a [role], I want [feature] so that [benefit]"
2. **Story points** (1, 2, 3, 5, 8 scale)
3. **Acceptance criteria** (testable, specific)
4. **Dependencies** (which stories must complete first)
5. **Files affected** (key files from Amelia's impact matrix in the audit)
6. **Risk level** (HIGH/MEDIUM/LOW)

### Dependency Rules
- Foundation epic must complete before Extraction and AI Processing
- Extraction epic must complete before AI Processing (needs raw data)
- Foundation + Extraction + AI must complete before Frontend (needs data contracts)
- All epics must complete before Integration/E2E
- Include a **SCHEMA FREEZE GATE** between Foundation and downstream epics

### Constraints
- Do NOT re-create E29 S1-S4 stories — they're done
- Story point estimates should account for the audit's upward revisions (J1-J10 showed SCP underestimated by ~70%)
- Each story should be completable in 1-3 days by a single developer
- Stories >5 SP should be split
- Include explicit migration/cutover stories (audit finding J11, J12)
- Include canonical artifact update story (audit finding J13)
- Include frontend building detail page (audit finding J14)
```

---

## Verification Checklist

After running:
- [ ] `05-epics-and-stories.md` updated with V3 epics
- [ ] Each epic has 5-10 well-defined stories
- [ ] Each story has acceptance criteria, SP, and dependencies
- [ ] Schema freeze gate is present between foundation and downstream
- [ ] Migration/cutover stories exist (BAR→SF, data migration)
- [ ] Total SP estimate is realistic (expect 80-120 SP total)
- [ ] Dependency graph is clear and acyclic
- [ ] No story exceeds 5 SP
