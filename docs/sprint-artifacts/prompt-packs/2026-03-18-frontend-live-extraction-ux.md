# Session: Fix frontend/backend sync — live extraction UX with SSE streaming, job lifecycle controls, and real-time record display

## Skills to Load

/planning-with-files — persistent markdown plan for session continuity
/sse-streaming — SSE implementation patterns and resilience
/systematic-debugging — structured diagnosis of SSE/UI breakage
/e2e-test — self-healing E2E test workflows
/find-bugs — systematic bug discovery across frontend
/react-best-practices — React and Next.js performance optimization
/dogfood — E2E exploration with real data
/verification-before-completion — verify work before claiming done

---

## Prerequisites

Before starting this session, verify:

- SurrealDB running: `docker ps | grep acm-ai-db`
- API running: `curl http://localhost:5055/health`
- Worker running: check for `run_worker.py` process
- Frontend running: `curl http://localhost:8503`
- Branch: `git checkout ACMV3`
- Test PDF available for triggering extractions
- Browser DevTools or agent-browser available for UI verification
- Read audit findings: `docs/sprint-artifacts/pipeline-audit-2026-03-18/findings.md` (F4: Frontend/Backend Desync)

---

## Project Glossary

| Term | Definition |
|------|-----------|
| PipelineEventBus | Pub/sub bus emitting structured events during extraction. Categories: `extraction`, `ai`, `bulk` |
| SSE (Server-Sent Events) | One-way server→client streaming. Endpoint: `/api/v3/stream/{category}/{id}` |
| useV3SSE | React hook subscribing to SSE streaming endpoint. Zustand store: `streamingStore` |
| ExtractionProgressPanel | UI component showing stage-by-stage extraction progress. Subscribes to PipelineEventBus |
| StageId | Enum (9 values): STRUCTURE, PREFLIGHT, ORCHESTRATOR, DOCLING_EXTRACTION, EXTRACT, VALIDATE, CORRECT, NO_ACCESS_RECOVERY, STORE |
| AG Grid | Enterprise React data grid for ItemGrid and BuildingGrid. Supports dynamic columns from SF schema API |
| CopilotKit | AI copilot framework with `useCopilotReadable`/`useCopilotAction` hooks. AG-UI protocol streaming |
| BUG-4 | AG-UI adapter crash on `execute_write_node` AIMessage — blocks HITL chat flow |
| Upload Wizard | Multi-step wizard component for PDF upload. Needs processing state animation |
| Job lifecycle | (GAP) No cancel/restart API. Users can start duplicate extractions |
| Zustand store | Client-side state: `buildingStore`, `streamingStore`, `notebookStore` |
| Skill | Markdown instruction set for Claude Code activated via `/skill-name` |
| Plan mode | Session reads/writes `task_plan.md` to prevent scope creep |

---

## Current State

- SSE infrastructure exists but UI components are disconnected/broken
- No `POST /api/jobs/{id}/cancel` or restart endpoint
- No duplicate extraction guard — user can upload same doc while processing
- ExtractionProgressPanel shows stages but not live extracted records
- SSE terminal event (E35-S5) implemented backend but frontend doesn't consume `complete` event properly
- Upload wizard has no processing state animation (spinner/skeleton)
- CopilotKit/AG-UI adapter crash (BUG-4) blocks HITL chat flow
- ExtractionLogPanel exists but reliability is inconsistent
- Frontend has 17 loading.tsx skeletons (bug-frontend-nav-performance fix) but extraction-specific loading states are missing

---

## Key Files

**Read (reference):**
- `open_notebook/extractors/pipeline_event_bus.py` — PipelineEventBus implementation
- `api/routers/v3_streaming.py` — SSE streaming endpoints
- `frontend/src/lib/hooks/useV3SSE.ts` — SSE React hook
- `frontend/src/lib/stores/streamingStore.ts` — Zustand SSE store
- `frontend/src/lib/types/pipeline.ts` — StageId, StageStatus types
- `frontend/src/lib/types/v3-streaming.ts` — V3EventEnvelope type
- `frontend/src/components/acm/ExtractionProgressPanel.tsx` — stage progress UI
- `frontend/src/components/acm/UploadWizard.tsx` — upload wizard
- `frontend/src/components/jobs/` — job components directory
- `frontend/src/app/(dashboard)/jobs/page.tsx` — jobs listing page
- `frontend/src/app/(dashboard)/jobs/[id]/page.tsx` — job detail page
- `api/routers/agui_chat.py` — AG-UI chat endpoint (BUG-4 location)

**Modify:**
- `frontend/src/lib/hooks/useV3SSE.ts` — fix SSE `complete` event handling
- `frontend/src/lib/stores/streamingStore.ts` — add job lifecycle state
- `frontend/src/components/acm/ExtractionProgressPanel.tsx` — add live record display
- `frontend/src/components/acm/UploadWizard.tsx` — add processing state animation
- `frontend/src/app/(dashboard)/jobs/page.tsx` — add pending/processing indicators, duplicate guard
- `frontend/src/app/(dashboard)/jobs/[id]/page.tsx` — add stop/restart controls
- `api/routers/acm.py` — add job lifecycle endpoints (cancel, restart)

**Create:**
- `frontend/src/components/jobs/ExtractionLiveView.tsx` — ChatGPT-style live extraction display
- `frontend/src/components/jobs/JobControls.tsx` — stop/restart/status controls
- `api/routers/job_lifecycle.py` — job lifecycle API (cancel, restart, status)

---

## Plan

### Phase 1: SSE + Progress Fix

1. **Debug SSE connection** — Verify SSE endpoint works, check EventSource connection in browser DevTools
2. **Fix `complete` event handling** — Ensure frontend consumes SSE terminal event and transitions to completed state
3. **Fix ExtractionProgressPanel** — Verify all 9 stages render with correct transitions
4. **Add processing state to Upload Wizard** — Spinner/skeleton while extraction runs

### Phase 2: Job Lifecycle Controls

5. **Backend: job lifecycle API** — `POST /api/jobs/{id}/cancel`, `POST /api/jobs/{id}/restart`
   - Cancel: set command status to `cancelled`, emit SSE cancel event
   - Restart: create new command, reset extraction state
   - Guard: check if extraction is already running before allowing new one
6. **Frontend: duplicate guard** — Disable "Process" button when extraction is pending/running
7. **Frontend: stop/restart controls** — Add buttons to job detail page header
8. **Frontend: job status indicators** — Show pending/running/completed/failed badges on job cards

### Phase 3: Live Record Streaming Display

9. **Design ExtractionLiveView** — ChatGPT-style scrolling feed showing:
   - Current stage + progress bar
   - Each extracted record appearing in real-time (from SSE events)
   - Extracted record count vs expected (from building inventory)
   - Errors/warnings as they occur
   - Collapsible sections for each building being processed
10. **Wire to SSE** — Subscribe to `extraction` + `ai` event categories
11. **Integrate into job detail page** — Tab or panel alongside existing grid

### Phase 4: BUG-4 Fix (AG-UI HITL)

12. **Diagnose BUG-4** — AG-UI adapter crashes on `execute_write_node` AIMessage
13. **Fix adapter** — Handle AIMessage type in AG-UI event encoder
14. **Verify HITL flow** — Full write-approve-execute cycle in CRUD chat

### Task Plan Reference
- task_plan.md: `docs/sprint-artifacts/pipeline-audit-2026-03-18/task_plan.md`
- findings.md: `docs/sprint-artifacts/pipeline-audit-2026-03-18/findings.md`
- progress.md: `docs/sprint-artifacts/pipeline-audit-2026-03-18/progress.md`

---

## Agent Strategy

Strategy: SUBAGENT-DISPATCH
Use the Task tool to dispatch independent work items.

Subagents:
- sse-debugger: Debug SSE endpoint + frontend connection, fix complete event handling, fix ExtractionProgressPanel (Phase 1)
- backend-lifecycle: Create job lifecycle API endpoints — cancel, restart, duplicate guard (Phase 2 backend)
- frontend-ux: Add processing states, stop/restart controls, job status indicators (Phase 2 frontend — after backend-lifecycle)
- live-view-builder: Design and build ExtractionLiveView component with SSE wiring (Phase 3 — after Phase 1)
- bug4-fixer: Diagnose and fix AG-UI adapter BUG-4 (Phase 4 — independent)

Parallel dispatch: sse-debugger, backend-lifecycle, bug4-fixer
Sequential: frontend-ux (after backend-lifecycle), live-view-builder (after sse-debugger)

---

## Context7 Directives

Run these at session start to load current library documentation:

1. resolve-library-id for "react" → query-docs for "useEffect EventSource SSE streaming cleanup"
2. resolve-library-id for "zustand" → query-docs for "store subscribe middleware persist"
3. resolve-library-id for "next.js" → query-docs for "server-sent events streaming API routes app router"
4. resolve-library-id for "ag-grid-react" → query-docs for "row data update transaction dynamic refresh"

---

## Verification Checklist

Run these in order before marking the session complete. All must pass.

- [ ] `cd frontend && npm run build` — Frontend build (0 errors)
- [ ] `cd frontend && npm run lint` — Frontend lint (0 errors)
- [ ] `uv run ruff check .` — Backend lint (0 errors)
- [ ] `uv run pytest tests/ -x` — Backend tests (all pass)
- [ ] SSE test: start extraction, verify EventSource connects and receives stage events in browser DevTools
- [ ] SSE complete: verify extraction completion triggers UI state transition (progress → results)
- [ ] Upload wizard: verify processing animation shows during extraction
- [ ] Duplicate guard: verify "Process" button disabled when extraction is running
- [ ] Job controls: verify cancel button stops extraction, restart creates new command
- [ ] Live view: verify records appear in ExtractionLiveView as they're extracted
- [ ] BUG-4: verify HITL dialog renders in CRUD chat write flow (if tackled)
- [ ] Screenshot evidence saved to `docs/sprint-artifacts/pipeline-audit-2026-03-18/`

---

## Files Summary

| Operation | Count | Files |
|-----------|-------|-------|
| READ | 12 | pipeline_event_bus.py, v3_streaming.py, useV3SSE.ts, streamingStore.ts, pipeline.ts, v3-streaming.ts, ExtractionProgressPanel.tsx, UploadWizard.tsx, jobs/*.tsx, agui_chat.py |
| MODIFY | 7 | useV3SSE.ts, streamingStore.ts, ExtractionProgressPanel.tsx, UploadWizard.tsx, jobs/page.tsx, jobs/[id]/page.tsx, acm.py |
| NEW | 3 | ExtractionLiveView.tsx, JobControls.tsx, job_lifecycle.py |

---

## Commit Template

```
feat(ux): live extraction UX — SSE streaming fix, job lifecycle controls, real-time record display

- Fix SSE complete event handling and ExtractionProgressPanel transitions
- Add job lifecycle API (cancel, restart, duplicate guard)
- Add ExtractionLiveView component with ChatGPT-style record streaming
- Add processing state animation to Upload Wizard
- Fix BUG-4: AG-UI adapter AIMessage handling

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
```
