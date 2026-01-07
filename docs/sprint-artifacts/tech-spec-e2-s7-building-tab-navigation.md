# Story E2-S7: Implement Building Tab Navigation

Status: done

## Story

**As a** user
**I want** ACM data organized by building tabs
**So that** I can quickly navigate between buildings in a school

## Acceptance Criteria

- [x] Tab bar above spreadsheet showing all buildings (e.g., B00A, B00B, B00C)
- [x] Tab shows building code and record count (e.g., "B00A (4)")
- [x] Clicking tab filters grid to show only that building's records
- [x] "All Buildings" tab option to show combined view
- [x] Active tab visually highlighted
- [x] Tabs auto-generated from ACM data (no hardcoding)
- [x] Smooth transition when switching tabs
- [x] Remember last selected tab per source (session persistence)

## Tasks / Subtasks

- [x] **Task 1: Create BuildingTabs component**
  - [x] Create `frontend/src/components/acm/BuildingTabs.tsx`
  - [x] Extract unique buildings from records with counts
  - [x] Sort buildings alphabetically by building code
  - [x] Include "All Buildings" tab with total count
  - [x] Add high-risk indicator (AlertTriangle icon) for buildings with high-risk records
  - [x] Use Radix UI Tabs from shadcn/ui

- [x] **Task 2: Create useSessionStorage hook**
  - [x] Create `frontend/src/lib/hooks/use-session-storage.ts`
  - [x] Implement sessionStorage persistence with SSR safety
  - [x] Support generic types with JSON serialization

- [x] **Task 3: Integrate BuildingTabs into ACMTab**
  - [x] Add building tab state with session persistence
  - [x] Filter records by selected building
  - [x] Update toolbar totalCount to use filtered count
  - [x] Place BuildingTabs above toolbar in card content

- [x] **Task 4: Verify implementation**
  - [x] TypeScript compilation passes (npx tsc --noEmit)
  - [x] All imports resolve correctly
  - [x] Component integration complete

## Senior Developer Review (AI)

**Review Date:** 2026-01-07
**Reviewer:** Claude Opus 4.5 (code-review workflow)
**Outcome:** Approve (after fixes)

### Action Items

- [x] [HIGH] Reset selectedBuilding when riskFilter changes [ACMTab.tsx:51-62]
- [x] [HIGH] Handle invalid building selection after data refresh [ACMTab.tsx:143-151]
- [x] [HIGH] Correct misleading comment in BuildingTabs [BuildingTabs.tsx:55]
- [x] [Medium] Use building_name for display fallback instead of building_id twice [BuildingTabs.tsx:36-50]
- [x] [Medium] Fix hydration mismatch in useSessionStorage hook [use-session-storage.ts]
- [x] [Medium] Stage new files for commit
- [x] [Low] Fix misleading comment about single building edge case

### Review Summary

Initial implementation had UX issues with filter state management and a potential hydration mismatch. All HIGH and MEDIUM issues were fixed:

1. **Filter Reset**: Building selection now resets when risk filter changes to prevent confusing state
2. **Invalid Selection**: Added effect to auto-reset building selection if selected building no longer exists in data
3. **Display Names**: Tab labels now prefer `building_name` over `building_id` for human-readable display
4. **Hydration Safety**: Rewrote useSessionStorage to prevent React hydration mismatches by reading from storage only after mount
5. **Files Staged**: New files properly staged for commit

## Dev Notes

### Technical Design

Implemented building tab navigation above the ACM spreadsheet to enable quick filtering between buildings in a school. This matches the existing MVP pattern at acm.coralshades.ai.

### Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Tab component | Radix UI Tabs (shadcn/ui) | Consistent with existing UI components |
| State location | ACMTab (not ACMGrid) | ACMTab already manages filtering state |
| Persistence | sessionStorage | Per-session persistence, cleared on browser close |
| Risk indicators | AlertTriangle icon + border | Visual cue for buildings with high-risk records |

### Edge Cases Handled

| Case | Behavior |
|------|----------|
| No ACM records | Tabs not rendered |
| Building code missing | Uses building_name, then building_id as fallback |
| Large number of buildings | Tabs wrap to multiple lines (flex-wrap) |
| Selected building no longer exists | Auto-reset to "All Buildings" |
| Risk filter changes | Reset building selection to avoid confusion |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- TypeScript compilation: PASS (npx tsc --noEmit)
- Build verification: Environment issue (Turbopack lockfile) - unrelated to code changes
- Code review: 7 issues found (3 HIGH, 4 MEDIUM), all fixed

### Completion Notes List

1. **BuildingTabs Component**: Created with building extraction, sorting, counting, and high-risk indicators
2. **useSessionStorage Hook**: Created with SSR/hydration safety and generic type support
3. **ACMTab Integration**: Added building state, filtering logic, filter reset, and invalid selection handling
4. **Implementation follows existing patterns**: Uses Radix UI Tabs, follows hook naming conventions
5. **Code Review Fixes**: All 7 review items addressed (3 HIGH, 4 MEDIUM)

### File List

**New Files:**
- `frontend/src/components/acm/BuildingTabs.tsx` - Building tabs component
- `frontend/src/lib/hooks/use-session-storage.ts` - Session storage hook (hydration-safe)

**Modified Files:**
- `frontend/src/components/acm/ACMTab.tsx` - Integrated BuildingTabs, added filtering, filter reset, invalid selection handling
- `docs/sprint-artifacts/sprint-status.yaml` - Updated story status

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-19 | Tech spec created | create-story workflow |
| 2026-01-07 | Promoted to ready-for-dev | workflow-status |
| 2026-01-07 | Implementation complete - all tasks done | dev-story workflow (Claude Opus 4.5) |
| 2026-01-07 | Code review: 7 issues found and fixed (3 HIGH, 4 MEDIUM) | code-review workflow (Claude Opus 4.5) |
