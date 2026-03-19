# Session: Fix upload 502 errors in BOTH Quick Upload AND Full Wizard, remove mode selection, wire live SSE extraction progress to both upload paths and job cards

## Skills to Load

/systematic-debugging — structured diagnosis before proposing fixes (REQUIRED: diagnose 502 before fixing)
/acm-observability — query Langfuse traces, inspect extraction state, verify worker logs
/planning-with-files — persistent task_plan.md, findings.md, progress.md in docs/sprint-artifacts/upload-sse-fix/
/verification-before-completion — browser-verify the full upload→extraction→review flow before claiming done
/sse-streaming — SSE implementation patterns, auto-reconnection, heartbeats

---

## Prerequisites

Before starting this session, verify:

- SurrealDB running: `docker ps | grep acm-ai-db`
- API running: `curl http://localhost:5055/health`
- Worker running: `uv run python run_worker.py --import-modules commands`
- Frontend running: `cd frontend && npm run dev` (port 8503)
- Branch: ACMV3
- Browser open: `http://localhost:8503/jobs` (verify page loads)
- Screenshot reference: `docs/UI-UX-issues/E1.png` (502 error on Quick Upload)

---

## Project Glossary

| Term | Definition |
|------|-----------|
| QuickUploadDialog | Lightweight single-step upload modal. File drop → immediate upload + extract. In `components/sources/QuickUploadDialog.tsx`. |
| UploadWizard | 3-step wizard: file → mode selection → confirm. In `components/acm/UploadWizard.tsx`. Mode selection (Step 2) is being REMOVED. |
| `ExtractionMode` | Type `'standard' \| 'ai_enhanced'`. Being removed — always AI. |
| `UploadPhase` | State machine: `'idle' \| 'uploading' \| 'extracting' \| 'done' \| 'error'`. In QuickUploadDialog. |
| `commandId` | UUID returned by `POST /acm/extract`. Stored in `sessionStorage['acm-extraction-${sourceId}']`. Used to connect SSE. |
| `extraction_progress` | SurrealDB table written by worker during extraction. Contains `PipelineRunState` (stages, percentages). Polled by SSE endpoint. |
| PipelineEventBus | In-memory asyncio pub/sub in `pipeline_event_bus.py`. Emits real-time events during extraction. |
| `useExtractionProgress` | React hook connecting to `GET /api/acm/extraction-progress/{commandId}/stream` SSE endpoint. Primary progress source. |
| `useExtractionStatus` | Polling fallback hook. Queries `/api/commands/jobs/{commandId}` every 3s via React Query. |
| ExtractionProgressPanel | UI component rendering stage pills + log lines. In `components/acm/ExtractionProgressPanel.tsx`. |
| `review_status` | Source field: null → 'extracting' → 'building_review' → 'acm_review' → 'published'. Controls job card state. |
| StageId | Enum: STRUCTURE, PREFLIGHT, ORCHESTRATOR, DOCLING_EXTRACTION, EXTRACT, VALIDATE, CORRECT, NO_ACCESS_RECOVERY, STORE. |
| `_write_terminal_status()` | Function in `acm_commands.py` that writes final status to `extraction_progress` table. |

---

## Current State

- Branch: ACMV3 at `bc97792d`
- **BOTH upload paths are broken**: Quick Upload dialog AND Full Wizard both produce errors
- SSE streaming is inconsistent — sometimes works on re-extraction, never on first upload
- Job cards show "Published" instead of "Extracting" during active extraction
- UploadWizard still has Step 2 mode selection (standard vs ai_enhanced) — should be removed
- 2 existing job cards visible in screenshot: `Clucth_Alexander_` (Published, 4 pgs) and another (Published, 19 pgs)
- Worker may not be running or may not be picking up commands (needs diagnosis)

### CRITICAL: Two Upload Paths — BOTH Must Be Fixed

| Path | Component | Route | Current Issues |
|------|-----------|-------|----------------|
| **Quick Upload** | `QuickUploadDialog.tsx` | Sidebar button → modal dialog | 502 error, no progress feedback |
| **Full Wizard** | `UploadWizard.tsx` | `/upload` page (3-step wizard) | Mode selection to remove, same 502/progress issues |

**Every fix in this session must be applied to BOTH paths.** They share the same backend endpoints but have different frontend flows. Do NOT fix one and forget the other.

### The 502 Error

From screenshot: "Request failed with status code 502" appears in red text in the QuickUploadDialog after selecting `Clutch_Broadmeadows_2.pdf` (1.7 MB) and clicking "Upload & Extract". The same error occurs when using the Full Wizard path.

**Possible causes:**
1. API not running / crashed during request
2. Next.js proxy timeout (`/api/*` → FastAPI backend at :5055)
3. Backend endpoint throws unhandled exception
4. Worker not running → extraction command fails
5. File too large for proxy buffer

---

## Key Files

**Frontend — Upload Flow (MODIFY):**
- `frontend/src/components/sources/QuickUploadDialog.tsx` — Quick Upload modal, 502 error display, upload phases
- `frontend/src/components/acm/UploadWizard.tsx` — 3-step wizard, remove Step 2 mode selection
- `frontend/src/app/(dashboard)/upload/page.tsx` — Upload wizard route
- `frontend/src/lib/hooks/use-create-dialogs.tsx` — Dialog context provider

**Frontend — SSE / Progress (MODIFY):**
- `frontend/src/lib/hooks/use-extraction-progress.ts` — Legacy SSE hook, sessionStorage, commandId
- `frontend/src/lib/hooks/use-extraction-status.ts` — Polling fallback hook
- `frontend/src/lib/hooks/useV3SSE.ts` — V3 event bus SSE hook
- `frontend/src/lib/hooks/useV3BuildingStream.ts` — Per-building SSE wrapper
- `frontend/src/lib/stores/streamingStore.ts` — Zustand streaming state
- `frontend/src/components/acm/ExtractionProgress.tsx` — Full-page extraction progress
- `frontend/src/components/acm/ExtractionProgressPanel.tsx` — Stage pills + log panel

**Frontend — Job Cards / Status (MODIFY):**
- `frontend/src/app/(dashboard)/jobs/page.tsx` — Jobs list, status counts, job cards (or inline table)
- `frontend/src/app/(dashboard)/jobs/[id]/page.tsx` — Job detail page
- `frontend/src/app/(dashboard)/extraction/[id]/page.tsx` — Extraction progress page

**Backend — Upload + Extract API (READ/MODIFY):**
- `api/routers/sources.py` — `POST /sources` file upload endpoint (~line 403)
- `api/routers/acm.py` — `POST /acm/extract` trigger (~line 289)
- `api/routers/extraction_events.py` — SSE endpoint for extraction progress

**Backend — Worker (READ/MODIFY):**
- `commands/acm_commands.py` — `acm_extract` command handler, `_write_terminal_status()`
- `open_notebook/extractors/pipeline_event_bus.py` — PipelineEventBus pub/sub
- `api/routers/v3_streaming.py` — V3 SSE streaming endpoints

**Frontend API Client (READ):**
- `frontend/src/lib/api/acm.ts` — `acmApi.extract()`, `acmApi.getJobStatus()`
- `frontend/src/lib/api/sources.ts` — `sourcesApi.create()`

**Types (MODIFY):**
- `frontend/src/lib/types/pipeline.ts` — PipelineRunState, StageId, StageStatus
- `frontend/src/lib/types/api.ts` — Source types with review_status

---

## Plan

Read `docs/sprint-artifacts/upload-sse-fix/task_plan.md` before starting. Update it as you work.

### Task Plan Reference
- task_plan.md: `D:/ailocal/acm-ai/docs/sprint-artifacts/upload-sse-fix/task_plan.md`
- findings.md: `D:/ailocal/acm-ai/docs/sprint-artifacts/upload-sse-fix/findings.md`
- progress.md: `D:/ailocal/acm-ai/docs/sprint-artifacts/upload-sse-fix/progress.md`

### Execution Strategy

**Phase 1 — Diagnosis (/systematic-debugging)**

DO NOT CHANGE CODE IN THIS PHASE. Only read and observe.

Step 1: Read the 4 core frontend files:
- QuickUploadDialog.tsx (upload flow, error handling, commandId storage)
- UploadWizard.tsx (3-step wizard, mode selection)
- use-extraction-progress.ts (SSE hook, sessionStorage keys)
- ExtractionProgress.tsx (progress UI rendering)

Step 2: Read the 3 core backend files:
- sources.py POST /sources (upload endpoint)
- acm.py POST /acm/extract (extraction trigger)
- acm_commands.py (worker command handler, extraction_progress writes)

Step 3: Browser test — open http://localhost:8503/jobs and attempt Quick Upload:
- Open browser devtools Network tab
- Click "Upload Document" sidebar button
- Select a PDF file
- Click "Upload & Extract"
- Capture: which request returns 502? What's the response body?
- Check: Is the API at :5055 responding? `curl http://localhost:5055/health`

Step 4: Check worker:
- Is the worker process running?
- Check worker logs: `tail -50` the worker output
- After upload attempt, does the worker receive the `acm_extract` command?

Step 5: Synthesize findings → document RC1-RC4 in findings.md

**Phase 2 — Remove Mode Selection**

Step 6: UploadWizard.tsx changes:
- Remove Step 2 (mode card selection UI, lines ~243-310)
- Remove `ExtractionMode` type and `selectedMode` state
- Collapse stepper from 3→2 steps: "Upload File" → "Confirm & Extract"
- Hardcode `mode: 'ai_enhanced'` in the `acmApi.extract()` call
- Update step labels and progress indicator

Step 7: QuickUploadDialog.tsx changes:
- Ensure no `mode` param is sent (or always `'ai_enhanced'`)
- This dialog was already single-step, just verify consistency
- Wire the SAME progress panel that UploadWizard uses (shared component)

Step 8: Backend verification:
- Check `ACMExtractRequest` model — is `mode` optional with a default?
- If not, add `mode: str = "ai_enhanced"` default to the Pydantic model

**Phase 3 — Fix 502 Upload Error**

Based on Phase 1 diagnosis. Common scenarios:

**If API is down:**
- Fix startup issue, ensure `run_api.py` runs cleanly
- Add health check before upload attempt in QuickUploadDialog

**If proxy timeout:**
- Check `next.config.ts` proxy configuration for `/api/*`
- Increase timeout or use streaming upload

**If backend exception:**
- Read traceback from API logs
- Fix the endpoint (likely in sources.py or acm.py)
- Add proper error response instead of 500/502

**If worker not running:**
- The 502 might be because `POST /acm/extract` tries to write to a queue that fails
- Ensure command dispatch is non-blocking and returns commandId immediately

**Phase 4 — Fix SSE Streaming / Live Progress**

Step 9: Ensure commandId flows correctly:
- QuickUploadDialog: after `acmApi.extract()` → stores `commandId` in sessionStorage
- Verify the key format: `acm-extraction-${sourceId}` and `acm-extraction-progress-${sourceId}`
- Verify ExtractionProgress page reads from sessionStorage on mount

Step 10: Wire progress into BOTH upload paths:

**QuickUploadDialog:**
- After upload succeeds and extraction is triggered, DON'T navigate away immediately
- Show inline ExtractionProgressPanel in the dialog
- Use `useExtractionProgress(commandId)` to stream live stages
- Show stages as animated pills: STRUCTURE → EXTRACT → VALIDATE → STORE
- Show current stage with spinner, completed stages with checkmark
- On completion, show "Done — X records" with link to review

**UploadWizard:**
- After Step 2 (Confirm & Extract), transition to a progress view (Step 3 replacement)
- Show the SAME ExtractionProgressPanel component (shared)
- Keep user on the wizard page until extraction completes or they dismiss
- On completion, navigate to job detail or offer "View Results" button

**BOTH paths must share the same progress component** to avoid divergent behavior.

Step 11: Ensure worker writes to `extraction_progress` table:
- Check `acm_commands.py` — does `PipelineLogger` write stage updates?
- Check `extraction_events.py` — does SSE endpoint poll `extraction_progress` correctly?
- Verify `_write_terminal_status()` is called on both success AND failure

Step 12: Verify PipelineEventBus emits events:
- Check if `pipeline_event_bus.py` events reach `v3_streaming.py` SSE endpoints
- Check if frontend subscribes to correct category/operationId

Step 13: Add worker log rendering:
- Parse worker log messages into user-friendly strings
- Show in a collapsible log panel below stage pills
- Examples: "Extracting building 1 of 3...", "Found 31 records", "Validating..."

**Phase 5 — Fix Job Card Status**

Step 14: Fix status transitions:
- On `POST /acm/extract` success: set `review_status = 'extracting'` immediately
- Do NOT set to 'review' until extraction_progress shows terminal status
- Add "extracting" visual state to job card (animated spinner/pulse)

Step 15: Job card live updates:
- On `/jobs` list page: if any job has `review_status = 'extracting'`, poll for updates
- Show progress percentage or current stage on the card
- When extraction completes, auto-update card to "In Review" without page refresh

Step 16: Prevent premature review access:
- If `review_status = 'extracting'`, disable "Review" button on job card
- Show "Extraction in progress..." message if user tries to navigate to review
- Auto-redirect to extraction progress page if extraction is still running

**Phase 6 — E2E Verification**

Step 17: Full browser test — BOTH PATHS:

**Path A: Quick Upload**
1. Open http://localhost:8503/jobs
2. Click "Upload Document" → Quick Upload dialog opens
3. Select a PDF (use Broadmeadows or any test PDF)
4. Click "Upload & Extract" → no 502 error
5. See live progress stages in dialog (STRUCTURE → EXTRACT → VALIDATE → STORE)
6. Dialog shows "Done — X records extracted" on completion
7. Navigate to Jobs list → job card shows "In Review" (not during extraction)
8. Click job → records are present (not empty)

**Path B: Full Wizard**
1. Open http://localhost:8503/upload (or click "Full wizard" link)
2. Step 1: Drop a different PDF
3. Step 2: Confirm & Extract (no mode selection step)
4. See live progress stages on page (STRUCTURE → EXTRACT → VALIDATE → STORE)
5. Page shows completion with link to review
6. Navigate to Jobs list → job card shows "In Review"
7. Click job → records are present

Step 18: Run all checks:
```bash
cd frontend && npm run build    # Frontend builds clean
uv run pytest tests/ -x         # Backend tests pass
uv run ruff check .             # Lint clean
```

---

## Agent Strategy

Strategy: SUBAGENT-DISPATCH
**All subagents should use `model: "sonnet"`.**

### Phase 1 Subagents (launch in parallel)

**Subagent 1: frontend-flow-auditor**
- Read QuickUploadDialog.tsx, UploadWizard.tsx, use-extraction-progress.ts, ExtractionProgress.tsx, ExtractionProgressPanel.tsx
- Trace: upload button click → API calls → commandId storage → SSE connection → UI rendering
- Identify: where does the flow break? Why no progress after upload?
- Return: structured findings with file:line references

**Subagent 2: backend-flow-auditor**
- Read sources.py (POST /sources), acm.py (POST /acm/extract), acm_commands.py, extraction_events.py
- Trace: file upload → command dispatch → worker pickup → extraction_progress writes → SSE endpoint
- Check: does `_write_terminal_status()` get called? Are stage updates written during extraction?
- Return: structured findings with file:line references

**Subagent 3: browser-tester** (after subagents 1-2)
- Use agent-browser or chrome-devtools MCP to:
  1. Navigate to http://localhost:8503/jobs
  2. Click Upload Document button
  3. Attempt file upload
  4. Capture network requests (especially the 502)
  5. Screenshot the error state
- Return: network request details, error response body, console errors

### Phase 2-5 (sequential after diagnosis)

Apply fixes based on subagent findings. Test after each phase.

---

## Context7 Directives

Run these at session start to load current library documentation:

1. resolve-library-id for "next.js" → query-docs for "API route proxy rewrite middleware timeout"
2. resolve-library-id for "react" → query-docs for "EventSource SSE useEffect cleanup"
3. resolve-library-id for "zustand" → query-docs for "store subscribe selector"

---

## Verification Checklist

All must pass before marking session complete:

- [ ] **No 502 error (Quick Upload)**: QuickUploadDialog uploads PDF without error
- [ ] **No 502 error (Full Wizard)**: UploadWizard uploads PDF without error
- [ ] **Mode selection removed**: UploadWizard is 2-step (file → confirm), no mode cards
- [ ] **Always AI extraction**: `mode: 'ai_enhanced'` hardcoded in BOTH upload paths
- [ ] **Live progress (Quick Upload)**: After upload, QuickUploadDialog shows stage pills streaming
- [ ] **Live progress (Full Wizard)**: After confirm, UploadWizard shows stage pills streaming
- [ ] **Stage animations**: Active stage has spinner/pulse, completed stages have checkmark
- [ ] **Worker log visible**: Collapsible log panel shows user-friendly extraction messages
- [ ] **Job card "Extracting"**: During extraction, job card shows extracting state with indicator
- [ ] **No premature review**: "Review" disabled/hidden until extraction completes
- [ ] **Auto-update cards**: Jobs list polls/subscribes and updates card status live
- [ ] **Records present on review**: After extraction completes, review page shows extracted records
- [ ] **commandId propagation**: sessionStorage correctly stores and retrieves commandId
- [ ] **SSE connects**: useExtractionProgress successfully opens EventSource, receives events
- [ ] **Terminal status written**: Worker writes success/failure to extraction_progress table
- [ ] `cd frontend && npm run build` — Frontend builds clean (0 errors)
- [ ] `uv run pytest tests/ -x` — Backend tests pass
- [ ] `uv run ruff check .` — Lint clean
- [ ] Browser E2E: full upload → extraction → review flow works end-to-end

---

## Files Summary

| Operation | Count | Files |
|-----------|-------|-------|
| READ | ~20 | All upload, SSE, progress, worker files |
| MODIFY | ~12 | QuickUploadDialog, UploadWizard, use-extraction-progress, ExtractionProgress, ExtractionProgressPanel, acm.py, sources.py, acm_commands.py, jobs pages, pipeline types |
| NEW | 0-1 | Possibly a useUploadProgress hook if needed |
| DELETE | 0 | — |

---

## Commit Template

```
fix(upload+sse): fix 502 upload error, wire live extraction progress, remove mode selection

- Remove extraction mode selection from UploadWizard (always AI extraction)
- Fix [ROOT CAUSE] causing 502 on Quick Upload
- Wire ExtractionProgressPanel into QuickUploadDialog for live stage streaming
- Fix job card status: show "Extracting" during active extraction
- Prevent premature review access until extraction completes
- Add worker log rendering in progress panel

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>
```

---

## Critical Rules

1. **DIAGNOSE FIRST** (/systematic-debugging) — read all code + browser test BEFORE changing anything
2. **502 is the top priority** — if upload doesn't work, nothing else matters
3. **BOTH PATHS** — every fix must apply to QuickUploadDialog AND UploadWizard. Test both. Never fix one and forget the other.
4. **Don't break existing extraction** — the LangGraph pipeline itself works fine, this is a frontend/API wiring issue
5. **SSE must degrade gracefully** — if SSE fails, polling fallback must work
6. **No blank loading screens** — every state transition must have visual feedback
7. **User can't enter review during extraction** — this causes confusion with empty records
8. **commandId is the critical link** — if it's lost between upload and SSE, progress breaks
9. **Shared progress component** — QuickUploadDialog and UploadWizard must use the same ExtractionProgressPanel
10. **Test with real PDF** — use Broadmeadows PDF for E2E verification (test BOTH upload paths)
11. **Present findings before fixing** — document RC1-RC4 in findings.md, present to user, then fix
12. **Screenshot evidence** — capture before/after screenshots for each fix, for BOTH paths
