# Task Plan: Parallel BMad Code Review for E1-S15, E1-S16, E1-S17

## Goal
Run the BMad adversarial code review workflow for 3 stories currently in `review` status, auto-fix all HIGH/MEDIUM issues, mark stories as `done`, and update sprint-status.yaml.

## User Answers (Clarification)

## Workflow Per Story (BMad code-review workflow)
Each reviewer agent executes these steps:
1. **Load story** - Read complete story file, parse ACs, tasks, file list
2. **Discover changes** - `git status/diff` to find actual changed files
3. **Cross-reference** - Compare story claims vs git reality
4. **Build attack plan** - AC validation, task audit, code quality, test quality
5. **Execute adversarial review** - Find 3-10 specific issues minimum
6. **Auto-fix** - Fix all HIGH and MEDIUM issues in code
7. **Run tests** - Verify fixes don't break anything
8. **Update story status** - Mark as `done` in story file
9. **Update sprint-status.yaml** - Sync status to `done`

## Phases

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | pending | Create agent team and tasks |
| 2 | pending | Launch 3 parallel code review agents (E1-S15, E1-S16, E1-S17) |
| 3 | pending | Monitor progress, handle any escalations |
| 4 | pending | Verify all 3 stories marked done, sprint-status updated |
| 5 | pending | Update sprint-status.yaml summary counts |

## Key Files
- Workflow config: `_bmad/bmm/workflows/4-implementation/code-review/workflow.yaml`
- Workflow instructions: `_bmad/bmm/workflows/4-implementation/code-review/instructions.xml`
- Validation checklist: `_bmad/bmm/workflows/4-implementation/code-review/checklist.md`
- Sprint status: `docs/sprint-artifacts/sprint-status.yaml`
- Architecture: `_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md`
- Epics: `_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md`

## Agent Team Design
- **Team Lead** (this agent): Coordinates reviews, handles sprint-status updates
- **Reviewer-S15**: Reviews E1-S15 (Corrective RAG Validation Loop)
- **Reviewer-S16**: Reviews E1-S16 (Document Structure & TOC Extraction)
- **Reviewer-S17**: Reviews E1-S17 (Building Inventory Compilation)

## Constraints
- Agents must NOT edit sprint-status.yaml (team lead does this to avoid conflicts)
- Agents auto-fix code issues and update story files
- Each agent runs `uv run pytest` on affected test files after fixes
- If a story has unresolvable CRITICAL issues, agent reports back instead of marking done

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| (none yet) | | |
