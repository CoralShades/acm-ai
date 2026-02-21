# Bug Fix: Auth Loading UX — Skeleton Layout

Status: done

## Story

As a **user**,
I want **to see a meaningful skeleton layout while the app loads instead of a blank spinner**,
so that **the application feels responsive and I have visual context during initial load**.

## Acceptance Criteria

1. Dashboard layout shows skeleton UI (sidebar outline + content placeholders) instead of blank LoadingSpinner
2. `authRequired` state is cached in Zustand persistent store across page loads
3. Subsequent visits with cached auth state skip redundant API call
4. Skeleton layout matches dashboard structure (sidebar + content area)
5. No regressions in authentication flow

## Tasks / Subtasks

- [x] Task 1: Replace LoadingSpinner with skeleton layout (AC: #1, #4)
  - [x] 1.1 Update `layout.tsx` loading state to render sidebar outline + content skeleton
  - [x] 1.2 Remove unused `LoadingSpinner` import
- [x] Task 2: Cache authRequired in Zustand (AC: #2, #3)
  - [x] 2.1 Add `authRequired` to `partialize` in `auth-store.ts` persist config
- [x] Task 3: Build verification (AC: #5)
  - [x] 3.1 Frontend build passes

## Dev Notes

### Root Cause

Triple blocking pattern in auth initialization:
1. Zustand hydration blocks render (synchronous)
2. `checkAuthRequired()` makes API call to `/api/auth/status`
3. `LoadingSpinner` shows blank animation with no visual context

Users saw a blank screen with a generic spinner for 1-3 seconds on every page load.

### Fix

Replaced `<LoadingSpinner />` with a structured skeleton layout that mirrors the actual dashboard structure:
- Left sidebar outline with nav item placeholders
- Content area with header, description, grid, and panel skeletons
- Uses `animate-pulse` for shimmer effect

Cached `authRequired` in Zustand's persisted state so subsequent visits don't need the API call.

### Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/app/(dashboard)/layout.tsx` | MODIFY | Skeleton layout replacing LoadingSpinner |
| `frontend/src/lib/stores/auth-store.ts` | MODIFY | Persist authRequired in Zustand |

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Completion Notes List
- Part of Bug Triage Plan Phase 2 (Frontend UX)
- Maps to original bug #2 from triage

### File List
- frontend/src/app/(dashboard)/layout.tsx (loading state skeleton)
- frontend/src/lib/stores/auth-store.ts (partialize config)
