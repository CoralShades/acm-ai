# 15: Retrospective — Epic Completion Review

> **BMAD Command:** `/bmad-bmm-retrospective`
> **Agent:** Bob — 🏃 Scrum Master
> **Depends On:** All stories in the epic are `done`
> **Output:** `docs/sprint-artifacts/v3-retrospective-{epic}.md`
> **Run in:** Fresh context window
> **Repeat:** After each V3 epic completes

---

## Pre-Read Documents

- `docs/sprint-artifacts/sprint-status.yaml` — Sprint status showing completed stories
- All story tech specs for the completed epic
- `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` — Original story definitions
- V3 readiness report from Step 08 (compare planned vs actual)

---

## Prompt Template

```text
/bmad-bmm-retrospective

## Epic Retrospective: {EPIC_ID} — {EPIC_TITLE}

### Context
Epic {EPIC_ID} ({EPIC_TITLE}) is complete. All stories are in `done` status. Conduct a retrospective to capture learnings for the remaining V3 epics.

### Retrospective Areas

#### 1. Velocity Analysis
- Planned SP vs actual effort
- Stories that took longer than estimated — why?
- Stories that were easier than expected — why?
- Accuracy of V3 Party Mode estimates

#### 2. Technical Learnings
- What V3 patterns worked well? (provider adapters, SF aliases, provenance tracking, etc.)
- What patterns need improvement for the next epic?
- Any architectural decisions that should be revisited?
- Dependency issues discovered during implementation

#### 3. Quality Assessment
- Test coverage achieved (unit, integration, E2E)
- Bugs found during code review — patterns?
- Benchmark results: Broadmeadows + Alexander accuracy at this point
- SF picklist validation accuracy

#### 4. Process Improvements
- BMAD workflow effectiveness — did the prompt pack work well?
- Story tech spec quality — were ACs clear enough?
- Code review findings — common issues?
- Documentation gaps discovered

#### 5. Next Epic Preparation
- What should the next epic account for based on learnings?
- Are there stories that need re-scoping?
- Are there new risks discovered?
- Recommended changes to SP estimates for remaining epics

### Sprint Status Update
- Set `epic-{N}-retrospective: completed` in sprint-status.yaml
- Add retrospective notes to the epic comment

### Output Format
Markdown document with:
- What went well (keep doing)
- What didn't go well (stop/change)
- Action items for next epic
- Updated risk register
- Velocity data (planned SP, actual time, stories/sprint)
```

---

## When to Run

Run this after each V3 epic completes:
- After Epic 30 (Foundation) — critical learnings for downstream epics
- After Epic 31 (Extraction) — provider integration learnings
- After Epic 32 (AI Processing) — batching/routing learnings
- After Epic 33 (Frontend) — UI pattern learnings
- After Epic 34 (Integration) — final V3 retrospective

The Foundation epic retrospective (first one) is especially important — it sets patterns for all subsequent epics.
