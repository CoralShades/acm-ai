# Upload UX + SSE Streaming Fix — Findings

## Symptoms (from user report + screenshot)

1. **502 error** on Quick Upload dialog when uploading `Clutch_Broadmeadows_2.pdf` (1.7 MB)
2. **No progress feedback** after upload — user sees loading screen with no extraction stages
3. **Job shows as "review"** immediately — user thinks extraction is done, finds empty records
4. **SSE streaming sometimes appears** when opening review or triggering re-extraction (inconsistent)
5. **Extraction mode selection** still present in wizard — should always use AI

## Architecture Overview

```
QuickUploadDialog → POST /sources (upload) → POST /acm/extract (trigger)
                                                    ↓
                                    Worker picks up `acm_extract` command
                                                    ↓
                                    PipelineEventBus emits events
                                    extraction_progress table updated
                                                    ↓
Frontend SSE:                       GET /api/acm/extraction-progress/{cmd}/stream
  useExtractionProgress ←───── EventSource ←── extraction_events.py
  useExtractionStatus ←──── React Query polling ←── /api/commands/jobs/{cmd}
```

## Root Causes

### RC1: 502 Error Source
- **Likely cause**: The `getApiUrl()` config resolution (`frontend/src/lib/config.ts:22`) may resolve to wrong URL after RunPod infra changes (commit `31b0aa33`). OR transient API crash during file processing. API and SurrealDB are both healthy when checked.
- **Contributing factor**: No retry logic or health check before upload attempt
- **Status**: Backend is healthy. Improved error handling added. Will monitor.

### RC2: Missing Progress Feedback
- **Files**: `QuickUploadDialog.tsx:127-128`, `UploadWizard.tsx:164`
- **Cause**: Both upload paths immediately navigate away after triggering extraction — QuickUploadDialog shows "done" with "View Progress" link, UploadWizard navigates to `/extraction/${sourceId}`. Neither shows inline progress in the dialog/wizard itself.
- **Fix**: Wire `ExtractionProgressPanel` into both components, show progress inline.

### RC3: Premature "Review" Status
- **Files**: Job status is set by frontend navigation, not backend. `review_status` is set when user clicks into review pages.
- **Cause**: The QuickUploadDialog shows "Extraction started!" with green checkmark immediately when the command is submitted, making user think extraction is done. User navigates to job → sees no records.
- **Fix**: Replace the "done" success state with live progress panel showing actual extraction stages.

### RC4: Inconsistent SSE Connection
- **File**: `use-extraction-progress.ts:82-94`
- **Cause**: SSE connects only when `phase === 'extracting'` AND `commandId` is set. If user navigates before both are set, SSE never connects. The hook has a 3-second timeout before falling back to polling.
- **Status**: SSE infrastructure is sound. The issue is that users navigate away before SSE can connect.

## Fixes Applied

### Fix 1: Default mode to 'ai_enhanced' (BOTH paths)
- `api/models.py:530` — `ACMExtractRequest.mode` default changed from `'standard'` to `'ai_enhanced'`
- `frontend/src/lib/api/acm.ts:85` — Frontend default changed from `'standard'` to `'ai_enhanced'`

### Fix 2: Remove mode selection from UploadWizard
- `frontend/src/components/acm/UploadWizard.tsx` — Complete rewrite:
  - Collapsed from 3 steps to 2 steps: "Upload PDF" → "Confirm & Extract"
  - Removed `ExtractionMode` type, `selectedMode` state, Step 2 mode card UI
  - Added inline `ExtractionProgressPanel` after extraction starts (replaces navigation to `/extraction/[id]`)
  - Added "View Results" / "Back to Jobs" buttons after completion

### Fix 3: Wire inline progress into QuickUploadDialog
- `frontend/src/components/sources/QuickUploadDialog.tsx` — Complete rewrite:
  - Replaced "done" success state with live `ExtractionProgressPanel`
  - Dialog widens from `sm:max-w-md` to `sm:max-w-lg` when progress is shown
  - Title changes to "Extraction Progress" during extraction
  - Added "View Results" / "Upload Another" buttons after completion
  - Prevents closing dialog during extraction
  - Removed "(mode selection)" from "Full wizard" link text
