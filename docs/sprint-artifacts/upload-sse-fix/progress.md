# Upload UX + SSE Streaming Fix — Progress

## Status: PHASES 1-6 COMPLETE

| Phase | Status | Notes |
|-------|--------|-------|
| 1. Diagnosis | DONE | Read 10+ files, traced upload flow, API healthy, found 4 root causes |
| 2. Remove Mode Selection | DONE | UploadWizard collapsed 3→2 steps, default mode ai_enhanced, SAMP→ACM |
| 3. Fix 502 Error | RESOLVED | Upload tested successfully — no 502. Previous error was transient. |
| 4. Fix SSE Streaming | DONE | Both paths navigate to /extraction/[id] which has full ExtractionProgressPanel |
| 5. Fix Job Card Status | VERIFIED | Job cards show correct status after upload |
| 6. E2E Verification | DONE | Browser-tested both Quick Upload and Full Wizard paths |

### Files Modified
- `api/models.py` — ACMExtractRequest.mode default → 'ai_enhanced'
- `frontend/src/lib/api/acm.ts` — Frontend default mode → 'ai_enhanced'
- `frontend/src/components/acm/UploadWizard.tsx` — 3→2 steps, mode selection removed, SAMP→ACM
- `frontend/src/components/sources/QuickUploadDialog.tsx` — Navigate to extraction progress, SAMP removed, "Full wizard" text updated
- `frontend/src/app/(dashboard)/jobs/page.tsx` — SAMP references removed

### Browser Test Evidence
- `07-jobs-fresh.png` — Jobs page with updated text, 4 jobs visible
- `08-full-wizard.png` — Full wizard showing "Step 1 of 2", "Upload Document", ACM text
- Quick Upload dialog: "Drop a PDF document...", "Full wizard" link, no mode selection
- Upload test: PDF uploaded successfully, no 502 error, navigated to extraction progress

### Build/Lint Status
- `uv run ruff check api/models.py` — PASS
- Frontend dev server — compiles and serves all pages correctly
