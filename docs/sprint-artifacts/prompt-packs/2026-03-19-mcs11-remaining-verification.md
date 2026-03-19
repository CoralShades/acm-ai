# MCS11-Verification: Full E2E Verification (Phases 6.2-6.6)
# Generated from MCS11 task_plan.md audit — 2026-03-19

**SP: 2 | Priority: P1 | Dependencies: ALL prior MCS11 packs + MCS12 + MCS13**
**Audit ref: MCS11 task_plan.md — Phase 6 verification tasks 6.2-6.6 incomplete**
**Completion gate: This is the final sign-off for MCS11. Do not mark MCS11 Done until this passes.**

## Skills to Load

/e2e-test — browser-based end-to-end verification
/agent-browser — DOM snapshots, screenshots, eval
/acm-observability — trace extraction events, verify SSE event flow
/verification-before-completion — complete checklist before any Done marking
/systematic-debugging — if anything fails, root-cause before moving on

---

## Problem Statement

MCS11 unified `/jobs/[id]` as the canonical ACM workflow page. Phases 1-3.2 and 5.1 are done. The remaining phases (3.3, 3.4, 5.2, 5.3 — implemented in `2026-03-19-mcs11-remaining-frontend-phases.md`) and the building/room ID fix (`2026-03-19-mcs11-remaining-building-room-id-audit-fix.md`) all need end-to-end verification.

Phase 6 tasks remaining:
- **6.2** SSE streaming test — extraction progress appears in real time on `/jobs/[id]`
- **6.3** Bulk operations test — select, bulk edit, bulk validate flows
- **6.4** Cross-page consistency — `/source/[id]` still works after all changes
- **6.5** Mobile responsive check — chat panel, building tabs
- **6.6** Screenshot evidence at each verification point

This pack is a verification-only execution — no new code. Any failures found must be triaged and fixed with targeted commits before re-running verification.

---

## Key Pages to Verify

| URL | Tab / Feature | Verification Goal |
|-----|--------------|-------------------|
| `/jobs` | Job list | Cards show status, extraction in-progress badge works |
| `/jobs/{sourceId}` | Overview tab | Validation summary card, source metadata |
| `/jobs/{sourceId}` | Buildings tab | BuildingGrid renders, all buildings listed |
| `/jobs/{sourceId}` | ACM Records tab | Per-building data loading, tab strip, error rows |
| `/jobs/{sourceId}` | Content tab | Source content renders |
| `/jobs/{sourceId}` | Raw Tables tab | Raw extraction tables render |
| `/jobs/{sourceId}` | Log tab | Extraction log shows |
| `/source/{sourceId}` | All tabs | Still functional, not broken by jobs page changes |

---

## Key Files to Reference (for diagnostics only)

- `frontend/src/app/(dashboard)/jobs/[id]/page.tsx` — full jobs page
- `frontend/src/components/acm/ACMGrid.tsx` — for rowClassRules debug
- `frontend/src/lib/hooks/useACMItems.ts` — per-building query
- `frontend/src/lib/hooks/useBuildings.ts` — buildings query
- `open_notebook/graphs/acm_extraction.py` — SSE event emission (Phase 6.2)
- `api/routers/v3_streaming.py` — SSE endpoints
- `open_notebook/extractors/pipeline_event_bus.py` — event types

---

## Verification Plan

### 6.2 SSE Streaming Test

**Setup**: Use a PDF that hasn't been extracted yet, or re-extract an existing source.

- [ ] 6.2.1 Navigate to `/jobs/{sourceId}` with an unextracted or re-extractable source
- [ ] 6.2.2 Trigger extraction (upload or re-extract button)
- [ ] 6.2.3 Verify within 3 seconds: `JobStatusPill` changes to "Extracting" with animated indicator
- [ ] 6.2.4 Verify progress bar appears below tab strip: `{N}/{total} buildings · ~{eta}s remaining`
- [ ] 6.2.5 Verify per-building status badges update in Buildings tab as each building extracts
- [ ] 6.2.6 Verify save progress indicator: `Saving records... {saved}/{total}` during save phase
- [ ] 6.2.7 Verify ACM Records tab auto-refreshes after `ai.save_complete` event
- [ ] 6.2.8 Verify status returns to normal (not "Extracting") after completion
- [ ] 6.2.9 Screenshot at: start, mid-extraction, post-completion → save to `docs/sprint-artifacts/e36/`

**SSE Event Verification (using acm-observability):**
```bash
# Check SSE endpoint delivers events during extraction
curl -N http://localhost:5055/api/v3/stream/ai/{operationId}
# Should see: ai.building_started, ai.building_extracted, ai.save_complete
```

### 6.3 Bulk Operations Test

- [ ] 6.3.1 Navigate to `/jobs/{sourceId}` → ACM Records tab with records loaded
- [ ] 6.3.2 Select multiple rows using AG Grid checkboxes
- [ ] 6.3.3 Verify `BulkOperationsBar` appears with selection count: `{N} records selected`
- [ ] 6.3.4 Test bulk edit: change a picklist field (e.g., Friability) on selected rows
  - Verify API call fires to `/api/acm/bulk-edit`
  - Verify grid refreshes with updated values
- [ ] 6.3.5 Test bulk validate: click "Validate" button
  - Verify validation runs (progress or status change)
  - Verify grid highlights any newly found errors
- [ ] 6.3.6 Test "Fix All" button on Overview tab (from validation summary card)
  - Verify bulk fix API call fires
  - Verify error count decreases after fix
- [ ] 6.3.7 Screenshot bulk ops bar, selection state, post-fix state

### 6.4 Cross-Page Consistency

- [ ] 6.4.1 Navigate to `/source/{sourceId}` (the secondary ACM register view)
  - Must render without errors
  - Buildings tab must show buildings
  - ACM Records tab must show records
- [ ] 6.4.2 Verify both pages show identical data for the same source:
  - Building count matches between `/jobs/[id]` Buildings tab and `/source/[id]` Buildings tab
  - Record count matches between pages
- [ ] 6.4.3 Verify `/source/[id]` `BuildingTabStrip` still works (not broken by jobs page changes)
- [ ] 6.4.4 Verify navigation: `/jobs` → job card → `/jobs/{sourceId}` works
- [ ] 6.4.5 Verify "ACM Register" button on jobs page navigates to `/source/{sourceId}`

### 6.5 Mobile Responsive Check

- [ ] 6.5.1 Resize browser to 375px width (iPhone SE) using agent-browser
  ```bash
  agent-browser eval 'window.innerWidth'
  # Use browser devtools or resize
  ```
- [ ] 6.5.2 Verify `/jobs/{sourceId}` renders without horizontal scroll on:
  - Overview tab
  - Buildings tab
  - ACM Records tab (grid may scroll — that is acceptable)
- [ ] 6.5.3 Verify chat panel collapses or hides gracefully at mobile width
- [ ] 6.5.4 Verify building tab strip scrolls horizontally (overflow-x-auto) rather than wrapping
- [ ] 6.5.5 Screenshot at 375px for each tab

### 6.6 Screenshot Evidence Collection

For each verification point, save screenshots to `docs/sprint-artifacts/e36/mcs11-verification/`:

- [ ] 6.6.1 `01-jobs-page.png` — jobs list with status badges
- [ ] 6.6.2 `02-overview-tab.png` — overview tab with validation summary card
- [ ] 6.6.3 `03-buildings-tab.png` — buildings grid with all buildings
- [ ] 6.6.4 `04-acm-records-tab-building-a.png` — records tab with building A selected
- [ ] 6.6.5 `05-acm-records-tab-building-b.png` — records tab with building B selected (data changes)
- [ ] 6.6.6 `06-tab-strip-error-badges.png` — tab strip with error count badges
- [ ] 6.6.7 `07-error-row-highlight.png` — red rows in ACMGrid
- [ ] 6.6.8 `08-sse-streaming-active.png` — extraction progress bar in real time
- [ ] 6.6.9 `09-bulk-ops-bar.png` — bulk operations bar with selection
- [ ] 6.6.10 `10-source-page-cross-check.png` — /source/[id] working correctly
- [ ] 6.6.11 `11-mobile-375px.png` — mobile responsive state

---

## Failure Triage Protocol

If any check fails:

1. Screenshot the failure state: `agent-browser screenshot failure-{phase}.png`
2. Check console errors: `agent-browser eval 'JSON.stringify(window.__consoleErrors || [])'`
3. Check network requests: `agent-browser eval 'JSON.stringify(performance.getEntriesByType("resource").filter(r => r.duration === 0).map(r => r.name))'`
4. Check API logs: review FastAPI server output for 4xx/5xx responses
5. Check SSE connection: `curl -N http://localhost:5055/api/v3/stream/ai/{opId}`
6. Fix the issue with a targeted commit BEFORE continuing verification
7. Re-run only the failed check (not the full suite)
8. **Maximum 2 fix-retry cycles per check** — if still failing after 2 cycles, flag as BLOCKED

---

## Agent Strategy

| Agent | Role | Model | Tasks |
|-------|------|-------|-------|
| `browser-tester` | SSE, bulk ops, cross-page browser tests | sonnet | 6.2, 6.3, 6.4 |
| `mobile-screenshotter` | Mobile responsive + screenshot collection | sonnet | 6.5, 6.6 |

**Sequential**: 6.2 → 6.3 → 6.4 → 6.5 → 6.6 (each phase builds evidence for the next)

---

## Verification Checklist

### SSE Streaming (6.2)
- [ ] JobStatusPill shows "Extracting" during active extraction
- [ ] Progress bar shows `{N}/{total} buildings` during extraction
- [ ] Per-building status badges update in real time
- [ ] ACM Records grid auto-refreshes after extraction completes
- [ ] Status returns to normal after completion

### Bulk Operations (6.3)
- [ ] Multi-row selection shows BulkOperationsBar
- [ ] Bulk edit updates records and grid refreshes
- [ ] Bulk validate runs and highlights errors
- [ ] "Fix All" reduces error count

### Cross-Page Consistency (6.4)
- [ ] `/source/[id]` renders without errors
- [ ] Building count matches between `/jobs/[id]` and `/source/[id]`
- [ ] Record count matches between pages
- [ ] Navigation flows work end-to-end

### Mobile Responsive (6.5)
- [ ] No horizontal overflow on Overview/Buildings tabs at 375px
- [ ] Building tab strip scrolls horizontally
- [ ] Chat panel collapses gracefully

### Evidence (6.6)
- [ ] All 11 screenshots saved to `docs/sprint-artifacts/e36/mcs11-verification/`
- [ ] No screenshot shows an error overlay or blank page

---

## Build Verification (Run Before Starting Browser Tests)

```bash
# Frontend must build cleanly
cd /home/demi/gitrepo/acm-ai/frontend && npm run build

# Backend lint must pass
cd /home/demi/gitrepo/acm-ai && uv run ruff check .

# Backend tests must pass
cd /home/demi/gitrepo/acm-ai && uv run pytest tests/ -x
```

All three must pass before starting browser verification. If build fails, fix it first.

---

## Commit Template

```
test(verification): MCS11 E2E verification complete — phases 6.2-6.6

- SSE streaming verified: extraction progress, building status, auto-refresh
- Bulk operations verified: select, edit, validate, fix-all flows
- Cross-page consistency verified: /jobs/[id] and /source/[id] consistent
- Mobile responsive verified at 375px: no overflow, tab strip scrolls
- Screenshot evidence collected: docs/sprint-artifacts/e36/mcs11-verification/
- MCS11 Phase 6 verification COMPLETE

Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

---

## Execution Order

This is the **final gate** for MCS11. Do not run this until all of the following are confirmed done:

1. **MCS11 Building/Room ID Fix** (`2026-03-19-mcs11-remaining-building-room-id-audit-fix.md`) — DONE
2. **MCS11-Gap4 FK Fix** (`2026-03-19-mcs11-building-record-id-fk-fix.md`) — DONE
3. **MCS11 Frontend Phases** (`2026-03-19-mcs11-remaining-frontend-phases.md`) — DONE
4. **MCS12** (`2026-03-19-mcs12-extraction-events-dead-endpoint.md`) — DONE (SSE events needed for 6.2)
5. **MCS13** (`2026-03-19-mcs13-schema-inference-documentmeta-fix.md`) — DONE (schema inference needed for multi-format test in 6.4)

**Full recommended sequence:**

1. MCS11 Building/Room ID Fix (backend, foundational)
2. MCS12 (SSE events, backend, independent — can run in parallel with item 1)
3. MCS13 (DocumentMeta fix, backend, independent — can run in parallel with items 1-2)
4. MCS11 Frontend Phases (depends on items 1 + MCS11-Gap4 FK fix)
5. **This pack — MCS11 Verification** (final, depends on all above)
