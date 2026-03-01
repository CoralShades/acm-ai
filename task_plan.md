# Task Plan — E29: Pipeline Unification — Phase 4: Story File Split & Sprint Setup

## Objective
Split the monolithic e29-story-specs.md into 8 individual story files, create gate decisions tracking doc, update sprint status, and produce clean dev handoff for S1+S2.

## Phases

### Phase 1-3: COMPLETE (prior session)
- [x] Research & Analysis
- [x] Story Spec Generation (8 stories in monolithic file)
- [x] Cross-Cutting Outputs (gates, parallelization)

### Phase 4: Story File Split + Sprint Housekeeping (CURRENT)
- [x] T1: Read master story specs + sprint-status + bmm-workflow-status
- [x] T2: Split into 8 individual story files with standard template sections
- [x] T3: Rewrite master file as index with links
- [x] T4: Resolve threshold wording drift (Gate 2: >=36/43, S7: >=40/43 stretch)
- [x] T5: Create e29-gate-decisions.md with empty Gate 1..4 check sections
- [x] T6: Update sprint-status.yaml (epic-29 in-progress, S1/S2 ready-for-dev)
- [x] T7: Append CHANGE LOG to bmm-workflow-status.yaml
- [x] T8: Final summary — changed files list, status, dev handoff

## Threshold Decision (wording drift fix)
- **Gate 2**: Alexander baseline >=36/43 (ENTRY threshold for Gate 2 pass)
- **S7**: Alexander stretch target >=40/43 OR PM-approved lower threshold (EXIT threshold for S7 AC-2)
- Must be consistent across: execution contract, story specs, gate decisions doc

## Standard Story Template Sections
Each story file gets:
1. Story header (title, SP, phase, owner, status)
2. User Story
3. Story Status (status field + notes)
4. Dependencies
5. Acceptance Criteria
6. Tasks/Subtasks
7. Test Strategy
8. Touched Files
9. Risks
10. QA Checklist (empty, for QA to fill)
11. Post-Dev Notes (empty, for dev to fill)
12. Post-QA Notes (empty, for QA to fill)
