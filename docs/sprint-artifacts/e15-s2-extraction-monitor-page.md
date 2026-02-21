# Story E15-S2: Dedicated Extraction Monitor Page

**Epic:** E15 — Extraction Monitor & Live Logging UI
**Priority:** P0
**Status:** done
**Change Proposal:** SCP-20260220 (2026-02-20)
**Blocked by:** E15-S1

---

## User Story

**As a** system administrator,
**I want** a single page showing all active and historical extractions with full log detail,
**So that** I can monitor system health, debug failures, and manage the extraction queue from one place.

---

## Background

With E15-S1 delivering the inline log panel in the Document Library, E15-S2 creates a dedicated full-page monitor for power users. It reuses the same components built in E15-S1 and provides a broader operational view.

---

## Acceptance Criteria

- [ ] New route: `/extraction-monitor` — accessible in sidebar under CONFIGURE section
- [ ] Navigation entry added: CONFIGURE > "Extraction Monitor"
- [ ] Two tabs: **Active** and **History**

### Active Tab
- [ ] Lists all in-progress extractions, auto-refreshed every 3s
- [ ] Each card shows: document name, file type, started_at, elapsed time (live counter)
- [ ] Each card has expandable `ExtractionProgressPanel` with live SSE
- [ ] Empty state when no active extractions: "No extractions currently running"

### History Tab
- [ ] Lists past extractions (paginated, 20 per page)
- [ ] Each row: document name, status badge, start time, duration, record count extracted
- [ ] Status filter: All / Completed / Failed / Partial
- [ ] Date range filter: Today / Last 7 days / Last 30 days / Custom
- [ ] Expandable log terminal per row (loads from REST endpoint, lazy)
- [ ] Retry button for failed/partial extractions

### General
- [ ] Page title: "Extraction Monitor"
- [ ] Loading skeleton while fetching
- [ ] Error state if API unreachable
- [ ] Keyboard accessible throughout

---

## Technical Notes

### API Endpoint Needed
A new list endpoint for extraction history:
```
GET /api/acm/extraction-progress?status=completed&limit=20&offset=0
```
Queries `extraction_progress` SurrealDB table, supports filtering/pagination.

Or reuse the sources list with extraction metadata joined.

### Component Reuse
Reuse the `ExtractionProgressPanel` component from E15-S1 for both the active and history views.

---

## Key Files to Create/Modify

| File | Change |
|------|--------|
| `frontend/src/app/(dashboard)/extraction-monitor/page.tsx` | New page |
| `frontend/src/components/extraction/ExtractionMonitorPage.tsx` | New component |
| `frontend/src/components/extraction/ExtractionHistoryList.tsx` | New history list |
| `frontend/src/lib/api/extractionApi.ts` | New API client for history endpoint |
| `api/routers/extraction_events.py` | Add `GET /extraction-progress` list endpoint |
| `frontend/src/components/layout/Sidebar.tsx` | Add nav item |

---

## Dependencies

- **Requires:** E15-S1 (for components), E1-S21 (done ✓)
- **Blocks:** nothing

---

## Estimated Effort

M (Medium) — New page + new API list endpoint. Component reuse from E15-S1 reduces effort.

## Dev Agent Record
- **Completed:** 2026-02-22
- **Commit:** a7bc02f
- **Build Status:** PASS
- **Implementation:** Ralph sprint batch implementation
