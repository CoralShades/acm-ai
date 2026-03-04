# 09: Sprint Planning — V3 Implementation Kickoff

> **BMAD Command:** `/bmad-bmm-sprint-planning`
> **Agent:** Bob — 🏃 Scrum Master
> **Depends On:** 08-readiness-check (must be GO)
> **Output:** Updated `docs/sprint-artifacts/sprint-status.yaml` + sprint plan
> **Run in:** Fresh context window

---

## Pre-Read Documents

- `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` — V3 epics & stories
- `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` — V3 architecture (for dependency understanding)
- `docs/sprint-artifacts/sprint-status.yaml` — Current sprint status (updated by Step 01)
- V3 readiness report from Step 08
- `V3/output/v3-party-mode-plan.md` — Party Mode story count estimates

---

## Prompt

```text
/bmad-bmm-sprint-planning

## V3 Sprint Planning

### Context
V3 implementation readiness has been approved (Step 08). Generate the sprint plan for the V3 epics.

### Sprint Structure
- Plan stories in execution order respecting dependencies
- Group into sprints of ~15-20 SP each
- First sprint MUST be the foundation epic (schema + config + migration)
- Schema freeze gate must be an explicit milestone between foundation and downstream sprints
- Parallel opportunities: identify stories that can run concurrently (different files/domains)

### Sprint Status YAML
Add all V3 epic and story entries to `docs/sprint-artifacts/sprint-status.yaml`:
- New epics: `epic-30` through `epic-34` (or whatever numbers the epics doc specifies)
- All stories in `backlog` status
- Include dependency notes as comments
- Add V3 reconciliation note

### Story Prioritization
1. Foundation stories first (schema, config, migration) — these unblock everything
2. Extraction provider stories next — these produce raw data
3. AI processing stories — these produce enriched records
4. Frontend stories — these expose data to users
5. Integration/E2E last — these validate everything

### Sprint Velocity
- Based on E29 velocity: ~15-20 SP per sprint (1-2 week sprints)
- Account for complexity: V3 stories touch more files and have more cross-cutting concerns
- First sprint will be slower (new patterns, new tables, new models)

### Deliverables
1. Sprint-by-sprint plan with story assignments
2. Updated `sprint-status.yaml` with all V3 entries
3. Critical path identification
4. Parallel execution opportunities
5. Gate milestones (schema freeze, extraction complete, AI complete, UI complete)

### Constraints
- Do NOT plan stories from archived epics
- First story to be created (via Step 10) should be the most foundational
- Each sprint should produce demonstrable progress (not just infrastructure)
```

---

## Verification Checklist

After running:
- [ ] `sprint-status.yaml` has all V3 epic and story entries
- [ ] Sprint plan document exists with story sequencing
- [ ] Schema freeze gate milestone identified
- [ ] Critical path identified
- [ ] First story for Create Story (Step 10) is clear
