# 08: Check Implementation Readiness — V3 Gate

> **BMAD Command:** `/bmad-bmm-check-implementation-readiness`
> **Agent:** Winston — 🏗️ Architect
> **Depends On:** 04 + 05 + 06 + 07 (all planning artifacts complete)
> **Output:** `_bmad-output/planning-artifacts/v3-readiness-report.md`
> **Run in:** Fresh context window
> **NOTE:** Consider using a DIFFERENT high-quality LLM for this validation step

---

## Pre-Read Documents (ALL planning artifacts)

- `_bmad-output/project-planning-artifacts/acm-ai/03-prd.md` — V3 PRD
- `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` — V3 Architecture
- `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` — V3 Epics & Stories
- UX Design output from Step 06
- `V3/output/v3-party-mode-plan.md` — Party Mode consensus (source of truth for decisions)
- `V3/output/tech-research-extraction-providers.md` — Technical research
- `V3/output/SCP-V3-scope-expansion.md` — Course correction record

---

## Prompt

```text
/bmad-bmm-check-implementation-readiness

## V3 Implementation Readiness Gate

### Check all alignment criteria:

1. **PRD ↔ Architecture Alignment**
   - Every FR in the PRD (FR-1401–1412, FR-1500–1900 series) has a corresponding architecture section
   - No architecture decisions contradict PRD requirements
   - AI model strategy in architecture matches Party Mode consensus

2. **PRD ↔ Epics Alignment**
   - Every FR has at least one story that delivers it
   - No orphan FRs (requirements without implementation stories)
   - No orphan stories (stories without PRD backing)

3. **Architecture ↔ Epics Alignment**
   - Architecture components map to specific epics/stories
   - Migration strategy has explicit stories
   - Provider adapter interface has stories for each provider
   - Data model changes have migration stories

4. **UX ↔ Epics Alignment**
   - Every UX flow has stories that implement it
   - Frontend component hierarchy maps to story breakdown
   - AG Grid configurations specified in stories

5. **Dependency Coherence**
   - Schema freeze gate is properly positioned
   - No circular dependencies
   - Foundation stories don't depend on downstream stories
   - Frontend stories don't start before data contracts are stable

6. **Completeness Check**
   - Multi-agent audit findings (W1-W12, M1-M14, J11-J14, B1-B12, Q1-Q14) are all addressed
   - Provenance data model is fully specified
   - SSE event types are enumerated
   - Export formats are specified
   - Migration rollback plan exists

7. **Risk Assessment**
   - Top 5 risks identified with mitigation strategies
   - Provider dependency risks (Google Cloud, PaddlePaddle)
   - Data migration risks (existing BAR records)
   - Accuracy regression risk (benchmark targets defined)

8. **Testability**
   - Each story has testable acceptance criteria
   - E2E test strategy covers multi-provider scenarios
   - Benchmark validation criteria defined (Broadmeadows + Alexander targets)

### Output Format
Produce a readiness report with:
- **GO / NO-GO recommendation** with rationale
- **Alignment matrix** — FR ↔ Architecture ↔ Story traceability
- **Gap list** — anything missing or misaligned
- **Risk register** — prioritized risks with status
- **Remediation actions** — what needs fixing before implementation starts (if NO-GO)
```

---

## Verification Checklist

After running:
- [ ] Readiness report exists with GO/NO-GO recommendation
- [ ] Alignment matrix covers all FRs
- [ ] Any gaps identified have remediation actions
- [ ] If NO-GO: fix gaps and re-run this step before proceeding to Sprint Planning
