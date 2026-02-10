# Bug Fix: Extraction Status Tracking Gap on Upload

Status: done

## Story

As a **user**,
I want **to see extraction progress when I upload a document with ACM extraction enabled**,
so that **I'm not confused by "No ACM Records Found" while extraction is still running in the background**.

## Problem

When uploading a document via `AddSourceDialog` with "Enable ACM extraction" toggled on:
1. The extraction triggers successfully via `acmApi.extract()`
2. The `command_id` from the response was **discarded** (not stored)
3. When navigating to the source's ACM tab, `useExtractionStatus` found no tracking data
4. The tab showed "No ACM Records Found" while extraction was actively running (30s-3min)

The manual "Extract ACM" button from within the ACM tab worked correctly because `useExtractACM` was properly wired to `startTracking()`.

## Root Cause

In `AddSourceDialog.tsx`, the `acmApi.extract()` response containing `command_id` was awaited but the response was never captured or stored. The `useExtractionStatus` hook relies on `sessionStorage` key `acm-extraction-{sourceId}` to restore tracking state across page navigations.

## Fix

Capture the extract response and write the `command_id` to sessionStorage in both upload flows (single-file and batch):

```typescript
const extractResponse = await acmApi.extract(createdSource.id)
if (extractResponse.command_id) {
  sessionStorage.setItem(`acm-extraction-${createdSource.id}`, extractResponse.command_id)
}
```

When the user navigates to the source page, `useExtractionStatus` now:
- Finds the `command_id` in sessionStorage
- Initializes with `phase = 'extracting'`
- Shows the extraction progress banner
- Polls for completion and auto-refreshes records

## Files Changed

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/components/sources/AddSourceDialog.tsx` | Modified | Store extraction command_id in sessionStorage for both single and batch upload flows |

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6 (claude-opus-4-6)

### Completion Notes
1. Two code locations fixed: single-file upload (~line 347) and batch upload (~line 422)
2. Uses same sessionStorage key pattern as `useExtractionStatus` hook: `acm-extraction-{sourceId}`
3. Frontend build passes cleanly
4. No backend changes needed — the API already returns `command_id` in the response

### Change Log

| Date | Change | Reason |
|------|--------|--------|
| 2026-02-10 | Fixed extraction tracking in AddSourceDialog | command_id was discarded after upload-triggered extraction |
