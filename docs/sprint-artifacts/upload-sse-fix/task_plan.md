# Task Plan: Upload UX + SSE Streaming Fix (2026-03-17)

## Objective

Fix the broken upload → extraction → progress flow. Remove extraction mode selection (always AI). Fix 502 upload errors. Make SSE streaming work reliably with live progress feedback in the upload modal and job cards.

---

## Phase 1 — Diagnosis (READ ONLY, /systematic-debugging)

- [ ] **1.1** Read QuickUploadDialog.tsx — trace upload flow, identify 502 source
- [ ] **1.2** Read UploadWizard.tsx — understand 3-step wizard, mode selection
- [ ] **1.3** Read `POST /sources` endpoint (sources.py) — check file upload + command dispatch
- [ ] **1.4** Read `POST /acm/extract` endpoint (acm.py:289) — check extraction trigger
- [ ] **1.5** Read acm_commands.py — trace worker extraction command flow
- [ ] **1.6** Read extraction_events.py — trace legacy SSE endpoint
- [ ] **1.7** Read useExtractionProgress hook — trace SSE connection + sessionStorage
- [ ] **1.8** Read ExtractionProgress.tsx + ExtractionProgressPanel.tsx — trace UI rendering
- [ ] **1.9** Test upload flow in browser — capture network requests, identify exact 502 failure point
- [ ] **1.10** Check worker logs during upload — is extraction command received?
- [ ] **1.11** Document root causes in findings.md

## Phase 2 — Remove Extraction Mode Selection (BOTH PATHS)

- [ ] **2.1** UploadWizard.tsx: Remove Step 2 (mode card selection), collapse to 2-step wizard
- [ ] **2.2** UploadWizard.tsx: Hardcode `mode: 'ai_enhanced'` in extract call
- [ ] **2.3** QuickUploadDialog.tsx: Remove any mode parameter, always use AI extraction
- [ ] **2.4** Backend: Verify `acm_extract` command handles missing/default mode gracefully
- [ ] **2.5** Remove `ExtractionMode` type if no longer used
- [ ] **2.6** Verify BOTH paths send identical parameters to `POST /acm/extract`

## Phase 3 — Fix 502 Upload Error

- [ ] **3.1** Identify 502 root cause (API down? proxy timeout? endpoint error?)
- [ ] **3.2** Fix the backend endpoint causing 502
- [ ] **3.3** Add proper error handling in QuickUploadDialog — show user-friendly error message
- [ ] **3.4** Add retry logic or fallback in upload flow

## Phase 4 — Fix SSE Streaming / Live Progress (BOTH PATHS)

- [ ] **4.1** Fix commandId propagation: ensure BOTH QuickUploadDialog AND UploadWizard store correct ID in sessionStorage
- [ ] **4.2** Fix SSE connection: ensure useExtractionProgress connects to correct endpoint
- [ ] **4.3** Fix extraction_events.py: ensure `extraction_progress` table is written by worker
- [ ] **4.4** Fix PipelineEventBus: ensure events emitted during extraction
- [ ] **4.5** Wire ExtractionProgressPanel into QuickUploadDialog post-upload phase
- [ ] **4.6** Wire ExtractionProgressPanel into UploadWizard post-confirm phase (shared component)
- [ ] **4.7** Show live stage progress (STRUCTURE → PREFLIGHT → EXTRACT → VALIDATE → STORE)
- [ ] **4.8** Add worker log streaming to progress panel (minimal, user-friendly)
- [ ] **4.9** Verify BOTH paths use the SAME shared progress component (no divergent implementations)

## Phase 5 — Fix Job Card Status

- [ ] **5.1** Fix review_status: don't set to "review" until extraction actually completes
- [ ] **5.2** Add "extracting" status to job card with animated indicator
- [ ] **5.3** Show extraction stage on job card (e.g., "Extracting: Building 1 of 3")
- [ ] **5.4** Disable "Review" navigation until extraction is confirmed complete
- [ ] **5.5** Add auto-refresh/polling on jobs list page to update status

## Phase 6 — E2E Verification (BOTH PATHS)

- [ ] **6.1** Upload a PDF via Quick Upload → verify no 502, progress streams live
- [ ] **6.2** Upload a PDF via Full Wizard → verify 2-step flow, AI extraction only, progress streams
- [ ] **6.3** Verify BOTH paths produce identical extraction results
- [ ] **6.4** Verify job card shows "Extracting" with live progress during extraction
- [ ] **6.5** Verify job transitions to "In Review" only after extraction completes
- [ ] **6.6** Verify records are present when user enters review
- [ ] **6.7** `npm run build` — frontend builds clean
- [ ] **6.8** `uv run pytest tests/ -x` — backend tests pass
- [ ] **6.9** `uv run ruff check .` — lint clean
- [ ] **6.10** Take screenshots for both paths as evidence
