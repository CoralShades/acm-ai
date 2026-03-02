# 10: Create Story — Reusable Template

> **BMAD Command:** `/bmad-bmm-create-story`
> **Agent:** Bob — 🏃 Scrum Master
> **Depends On:** 09-sprint-planning (sprint plan exists)
> **Output:** `docs/sprint-artifacts/{story-file}.md`
> **Run in:** Fresh context window (one per story)
> **Repeat:** For each story in the sprint plan

---

## Pre-Read Documents

- `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` — Story definition
- `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` — Architecture context
- `docs/sprint-artifacts/sprint-status.yaml` — Current status
- Sprint plan from Step 09

### Story-Specific Context (varies per story — update {PLACEHOLDERS})
- Any prerequisite stories that are already `done` — read their tech specs
- Relevant source files from Amelia's impact matrix in the audit

---

## Prompt Template

Copy this template and replace `{PLACEHOLDERS}` for each story:

```text
/bmad-bmm-create-story

## Create Story: {EPIC_ID}-{STORY_ID} — {STORY_TITLE}

### Story Context
- **Epic:** {EPIC_NUMBER} — {EPIC_TITLE}
- **Story:** {STORY_ID} — {STORY_TITLE}
- **SP:** {STORY_POINTS}
- **Dependencies:** {DEPENDENCY_LIST or "None — first story in epic"}
- **Sprint:** {SPRINT_NUMBER}

### Pre-Read for Context
Read these files before creating the story tech spec:
- `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` — Find the story definition for {EPIC_ID}-{STORY_ID}
- `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` — Section: {RELEVANT_ARCHITECTURE_SECTION}
{ADDITIONAL_PREREADS}

### V3-Specific Instructions

This story is part of the V3 scope expansion. Key context:

1. **Salesforce alignment**: All field names must use SF API names (e.g., `Item_Name__c`, `Friability_of_Material__c`). Reference `V3/output/item_fields_summary.md` and `V3/output/building_fields_summary.md` for exact field definitions.

2. **Multi-provider design**: If this story touches extraction, it must work with the provider adapter interface. No provider-specific code outside adapter implementations.

3. **Provenance tracking**: If this story creates or modifies records, ensure provenance metadata (source page, provider, confidence) is captured.

4. **SSE events**: If this story involves long-running operations, include SSE event emission in acceptance criteria.

5. **Dependent picklists**: If this story touches ACM Classification or Building Type fields, include picklist dependency validation in acceptance criteria.

### Tech Spec Requirements

The story tech spec must include:
1. **User Story** — "As a [role], I want [feature] so that [benefit]"
2. **Acceptance Criteria** — Numbered, testable, specific
3. **Technical Design** — Implementation approach, key decisions
4. **File Changes Table** — Every file created/modified with change description
5. **Database Changes** — Migrations, new tables/fields, indexes
6. **API Changes** — New/modified endpoints with request/response schemas
7. **Frontend Changes** — Components, stores, queries affected
8. **Test Plan** — Unit tests, integration tests, E2E tests to write
9. **Dev Agent Record** — Template for tracking implementation status
10. **Dependencies** — Blocked by / Blocks relationships

### Constraints
- Story must be completable in 1-3 days
- All acceptance criteria must be independently testable
- Include rollback plan for database changes
- Reference exact SF field names (not BAR names)
```

---

## Example Usage

For the first foundation story:

```text
/bmad-bmm-create-story

## Create Story: E30-S1 — Salesforce Schema Config Loader

### Story Context
- **Epic:** 30 — V3 Foundation
- **Story:** S1 — Salesforce Schema Config Loader
- **SP:** 5
- **Dependencies:** None — first story in epic
- **Sprint:** Sprint 1

### Pre-Read for Context
- `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md` — E30-S1 definition
- `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md` — Section: Data Model, Dependent Picklist Validation
- `V3/output/building_fields_summary.md` — Building__c fields and picklist values
- `V3/output/item_fields_summary.md` — Item__c fields, dependency chains, 294 Item_Name values
- `open_notebook/extractors/parsers/config_loader.py` — Current config loader (to be evolved)
- `V3/output/e30-multi-agent-audit-unified.md` — Findings W5, W6, M8, B8
...
```
