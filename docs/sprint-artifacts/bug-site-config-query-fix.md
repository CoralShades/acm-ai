# Bug Fix: Site Config Query Undefined Return

Status: done

## Story

As a **user**,
I want **the site configuration step in the upload wizard to not crash with undefined data**,
so that **I can reliably configure site settings during document upload**.

## Acceptance Criteria

1. `getConfigTemplates()` returns an empty array `[]` instead of `undefined` when no templates exist
2. Upload wizard Site Configuration step renders without errors
3. No React Query "data is undefined" console errors

## Tasks / Subtasks

- [x] Task 1: Add null guard to API return (AC: #1)
  - [x] 1.1 Update `frontend/src/lib/api/acm.ts:145` — add `?? []` fallback
- [x] Task 2: Verify no console errors (AC: #2, #3)
  - [x] 2.1 Frontend build passes

## Dev Notes

### Root Cause

`getConfigTemplates()` in `acm.ts` returned `response.data.templates` directly, which could be `undefined` when the API returns no templates property. Downstream React Query consumers expected an array and crashed.

### Fix

Single-line change: `return response.data.templates ?? []`

### Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/lib/api/acm.ts` | MODIFY | Add `?? []` null guard on line 145 |

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Completion Notes List
- XS fix, single line change
- Part of Bug Triage Plan Phase 1 (Quick Wins)

### File List
- frontend/src/lib/api/acm.ts (modified line 145)
