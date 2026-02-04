# Task Plan: Commit Uncommitted Files & Fix Worker Unicode Issue

## Goal
Commit 278 uncommitted files in logical sets to a feature branch, merge to main, create GitHub issue for worker Unicode crash, and implement the fix.

## Current Phase
Phase 2

## Phases

### Phase 1: Analyze Uncommitted Files ✅
**Status**: complete
**Goal**: Understand what files need to be committed and group them logically

**Actions**:
- [x] Run git status to see all uncommitted files
- [x] Categorize files by type/purpose
- [x] Identify temp directories to exclude

**Outcome**:
- 278 files found
- Categorized into 7 logical groups
- ~30 temp directories identified for .gitignore

---

### Phase 2: Create Feature Branch & Clean Git State
**Status**: in_progress
**Goal**: Create a new branch and prepare clean commit state

**Actions**:
- [ ] Update .gitignore to exclude temp directories
- [ ] Create feature branch: `feature/epic8-complete-with-testing`
- [ ] Verify we're on the new branch

---

### Phase 3: Commit Files in Logical Sets
**Status**: pending
**Goal**: Commit files grouped by functionality

**Planned Commits**:
1. **Update .gitignore** - Add temp directory patterns
2. **BMAD Framework Updates** - All _bmad-output/ changes
3. **Documentation Cleanup** - Remove old docs, add new framework docs
4. **Test Artifacts** - _debug/ ACM prompt files
5. **Sample PDFs** - Test files
6. **Configuration** - .claude/ changes, CLAUDE.md updates
7. **Planning Files** - task_plan.md, findings.md, progress.md

---

### Phase 4: Merge to Main
**Status**: pending
**Goal**: Merge feature branch into main branch

**Actions**:
- [ ] Switch to main branch
- [ ] Merge feature branch
- [ ] Verify no conflicts
- [ ] Push to remote (if applicable)

---

### Phase 5: Create GitHub Issue
**Status**: pending
**Goal**: Document the worker Unicode crash issue

**Issue Details**:
- **Title**: "Worker crashes with Unicode encoding error on Windows"
- **Labels**: bug, critical, windows
- **Body**: Include test report, error logs, screenshots
- **Assign**: To be determined

---

### Phase 6: Fix Worker Unicode Issue
**Status**: pending
**Goal**: Implement fix for Unicode encoding in worker

**Approach**:
1. Locate worker startup/logging code
2. Implement UTF-8 encoding fix (3 options):
   - Option A: Remove emoji from logs (quick fix)
   - Option B: Set PYTHONIOENCODING=utf-8 env var
   - Option C: Configure logger with UTF-8 explicitly
3. Test on Windows
4. Verify PDF processing completes
5. Commit fix

---

### Phase 1: Update PRD Document (ARCHIVED - PREVIOUS SESSION)
- [x] Expand Section 5.1 ACM Record Schema (20→50 fields)
- [x] Add organization hierarchy fields
- [x] Add location metadata fields
- [x] Add building characteristics fields
- [x] Add ACM classification fields
- [x] Add removal tracking fields
- [x] Update Section 2.2 Data Model requirements
- [x] Update Section 2.3 Spreadsheet View columns (FR-308 to FR-312)
- [x] Update Section 4.3 AG Grid Config (7 column groups)
- [x] Add new section for BAR export format (Section 5.3)
- [x] Add new section for site configuration (Section 5.1.1)
- [x] Updated API endpoints (Section 5.2)
- [x] Updated test data and scenarios (Section 7)
- [x] Updated glossary with Victorian terms
- **Status:** complete

### Phase 2: Update Architecture Document
- [x] Expand Section 3.1 Database Schema (50 fields + site_config table)
- [x] Update Section 4.2 API Types (ACMRecord, SiteConfig, BARExportOptions)
- [x] Update Section 5.2 Table Detection Patterns (Prensa, Greencap formats)
- [x] Update Section 6.1 AG Grid Column Config (7 column groups, presets)
- [x] Added new frontend components (SiteConfigForm, ColumnVisibility, BARExportDialog)
- **Status:** complete

### Phase 3: Update Epics & Stories Document
- [x] Updated Epic Overview table (story counts, statuses)
- [x] Add E1-S8: Site Configuration Data Entry (NEW)
- [x] Add E1-S9: ACM Product Classification (NEW)
- [x] Add E2-S8: Column Visibility Management (NEW)
- [x] Modify E5 section - promote to P0, update S1, S2
- [x] Add E5-S3: BAR Template Management (NEW)
- [x] Add E5-S4: Export Field Mapping (NEW)
- [x] Add E7-S7: Site Configuration During Upload (NEW)
- [x] Update story dependencies (added new dependency table)
- [x] Update MVP scope summary (✅ markers for done items)
- **Status:** complete

### Phase 4: Update Workflow Status
- [x] Update bmm-workflow-status.yaml
- [x] Record course correction completion
- [x] Note document updates
- **Status:** complete

### Phase 5: Update Sprint Planning
- [x] Update sprint-status.yaml with new stories
- [x] Add new stories from approved change proposals
- [x] Update story counts and progress
- [x] Set priorities for new stories (added to existing epics E1, E2, E5, E7)
- [x] Update recommendations for next actions
- **Status:** complete

### Phase 6: Create Progress File & Verification
- [x] Create progress.md with session log
- [x] Verify all files updated correctly
- [x] Summary of changes made
- **Status:** complete

## Implementation Complete
All 6 phases completed successfully on 2026-02-04.

## Key Questions
1. Should new stories be added to existing epics or create new Epic 11?
   - ANSWER: Add to existing epics (E1, E2, E5, E7) per approved proposals
2. What's the priority of remaining E8 stories vs new stories?
   - ANSWER: Complete E8 first, then new stories
3. Should E5-S2 (Excel export) be marked as needing update?
   - ANSWER: Yes, expand scope per CP#3

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Add stories to existing epics | Maintains epic coherence |
| Complete E8 before new stories | Don't disrupt in-progress work |
| Union schema (50 fields) | Supports both NSW SAMP and Victorian BAR |
| E5-S2 promoted to P0 | BAR Excel export is critical |

## Current State Summary
| Epic | Status | Completed Stories |
|------|--------|-------------------|
| E1 | done | 7/7 (needs modification for new requirements) |
| E2 | done | 7/7 (needs modification) |
| E3 | done | 4/4 |
| E4 | done | 4/4 |
| E5 | done | 2/2 (needs expansion) |
| E6 | done | 4/4 |
| E7 | done | 6/6 (needs expansion) |
| E8 | in-progress | 7/10 done, 3 drafted |
| E9 | backlog | 0/3, all drafted |
| E10 | backlog | 0/1, drafted |

## New Stories to Add
| Story ID | Title | Epic | Priority |
|----------|-------|------|----------|
| E1-S8 | Site Configuration Data Entry | E1 | P0 |
| E1-S9 | ACM Product Classification | E1 | P0 |
| E2-S8 | Column Visibility Management | E2 | P1 |
| E5-S3 | BAR Template Management | E5 | P1 |
| E5-S4 | Export Field Mapping Configuration | E5 | P1 |
| E7-S7 | Site Configuration During Upload | E7 | P0 |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|

## Notes
- Sprint Change Proposal approved: `_bmad-output/sprint-change-proposal-20260204.md`
- All 5 change proposals approved by user
- Completed Epics 1-7, Epic 8 in progress (7/10)
- Must add 6 new stories across 4 epics
- Must modify acceptance criteria for ~6 existing stories
