# Bug Fix: Extraction Progress Panel — Semantic Design Tokens

Status: done

## Story

As a **user**,
I want **the extraction progress panel to use the application's design system colors**,
so that **the UI is consistent with the rest of the application and adapts to light/dark themes**.

## Acceptance Criteria

1. ExtractionProgressPanel uses semantic CSS tokens (`border-primary`, `bg-primary`) instead of hardcoded blue/green/red
2. StageProgressPill uses `bg-primary`, `bg-emerald-500`, `bg-destructive` for running/complete/failed states
3. Colors adapt correctly in both light and dark modes
4. No regressions in progress panel functionality

## Tasks / Subtasks

- [x] Task 1: Fix ExtractionProgressPanel colors (AC: #1)
  - [x] 1.1 Replace `border-blue-500/50 bg-blue-50/50` → `border-primary/50 bg-primary/5`
  - [x] 1.2 Replace `text-blue-700 dark:text-blue-300` → `text-primary`
  - [x] 1.3 Replace `bg-blue-500` → `bg-primary`
- [x] Task 2: Fix StageProgressPill colors (AC: #2)
  - [x] 2.1 Running: `bg-blue-500 text-white` → `bg-primary text-primary-foreground`
  - [x] 2.2 Complete: `bg-green-500 text-white` → `bg-emerald-500 text-white`
  - [x] 2.3 Failed: `bg-red-500 text-white` → `bg-destructive text-destructive-foreground`
- [x] Task 3: Build verification (AC: #3, #4)
  - [x] 3.1 Frontend build passes

## Dev Notes

### Root Cause

Hardcoded Tailwind color classes (`bg-blue-500`, `bg-green-500`, `bg-red-500`) were used instead of the project's semantic design tokens from the VAEA design system (Epic 14). This caused visual inconsistency and broke dark mode theming.

### Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/components/acm/ExtractionProgressPanel.tsx` | MODIFY | Semantic border/bg tokens |
| `frontend/src/components/acm/StageProgressPill.tsx` | MODIFY | Semantic state colors |

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Completion Notes List
- Part of Bug Triage Plan Phase 2 (Frontend UX)
- Maps to original bugs #4 and #6 from triage

### File List
- frontend/src/components/acm/ExtractionProgressPanel.tsx (lines 54-56, 127-128)
- frontend/src/components/acm/StageProgressPill.tsx (lines 32-37)
