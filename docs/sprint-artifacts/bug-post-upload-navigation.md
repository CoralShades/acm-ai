# Bug Fix: Post-Upload Navigation to Source Detail

Status: done

## Story

As a **user**,
I want **to be automatically navigated to the source detail page after uploading a document**,
so that **I can immediately see and interact with the uploaded document without manual navigation**.

## Acceptance Criteria

1. After single-file upload via AddSourceDialog, user is navigated to `/sources/{id}`
2. After single-file upload via Upload wizard, "Done" button navigates to `/sources/{id}`
3. After multi-file upload, "Done" button navigates to `/sources` list
4. No regressions in upload flow or dialog behavior

## Tasks / Subtasks

- [x] Task 1: Add navigation to AddSourceDialog (AC: #1)
  - [x] 1.1 Import `useRouter` from `next/navigation`
  - [x] 1.2 Add `router.push(\`/sources/${createdSource.id}\`)` after source creation
- [x] Task 2: Update UploadProgressStep navigation (AC: #2, #3)
  - [x] 2.1 Detect single-success upload and navigate to specific source
  - [x] 2.2 Multi-file uploads still navigate to `/sources` list
- [x] Task 3: Build verification (AC: #4)
  - [x] 3.1 Frontend build passes

## Dev Notes

### Root Cause

Both `AddSourceDialog` and `UploadProgressStep` had generic navigation to `/sources` list regardless of how many files were uploaded. Users had to manually find their just-uploaded document in the list.

### Fix

Added conditional navigation logic:
- Single file: navigate to `/sources/{sourceId}` for immediate access
- Multiple files: navigate to `/sources` list (can't open all at once)

### Files Changed

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/components/sources/AddSourceDialog.tsx` | MODIFY | Add useRouter + post-creation navigation |
| `frontend/src/components/upload/UploadProgressStep.tsx` | MODIFY | Smart Done button navigation |

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Completion Notes List
- Part of Bug Triage Plan Phase 1 (Quick Wins)
- Maps to original bugs #3 and #5 from triage

### File List
- frontend/src/components/sources/AddSourceDialog.tsx (added useRouter, navigation)
- frontend/src/components/upload/UploadProgressStep.tsx (smart handleDone navigation)
