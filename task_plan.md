# MCS11: Unify `/jobs/[id]` as Canonical Page with Full Feature Parity

**Status**: Phases 1-3 DONE | Phase 4 DEFERRED | Phase 5 partial (5.1 done, 5.2-5.3 remaining) | Phase 6 partial (6.1 done, 6.2-6.6 remaining) | Gap4 FK exposure DONE | Pipeline accuracy fixes DONE (2026-03-21)
**SP**: 13 | **Priority**: P0
**Date**: 2026-03-19
**Audit ref**: MCS10 gap analysis + visual audit of /jobs/[id] vs /source/[id]

## Problem Statement

Two parallel pages exist for viewing the same source data:
- **`/jobs/[id]`** — The primary user workflow page (6 tabs: Overview, Buildings, ACM Records, Content, Raw Tables, Log + Chat)
- **`/source/[id]`** — The secondary "ACM Register" page (2 tabs: Buildings, ACM Records)

Over ~20 commits, critical features were built on `/source/[id]` but never ported to `/jobs/[id]`:
- SSE live streaming (real-time extraction progress)
- Per-building status badges (Extracting → Validating → Saving → Complete)
- Bulk edit/validate operations
- Validation error display and "Fix All" button
- Quick text search in grid
- "Group by Room" toggle
- Building selection persistence (Zustand vs useState)

Users navigate via `/jobs` → job card → `/jobs/source:ID`. They never see the features on `/source/[id]`.

## Architecture Decision

**Strategy: Feature-port from `/source/[id]` → `/jobs/[id]`**
- Keep `/jobs/[id]` as the canonical page (it has more tabs, chat, export)
- Port SSE streaming, bulk ops, validation, and search features into the jobs page
- Keep `/source/[id]` as a lightweight ACM-focused view (linked from "ACM Register" button)
- Do NOT merge/redirect — both serve different purposes

## Completed Pre-work

- [x] **MCS10-Bug**: Buildings tab showing "No Rows To Show" — fixed with `useJobBuildings` fallback hook
- [x] **MCS10-Gap2**: Buildings query invalidation timing (moved to `ai.building_extracted`)
- [x] **MCS10-Gap3**: Items query invalidation deferred to `ai.save_complete`
- [x] **MCS10**: Per-building "Saving..." status badge added

---

## Phase 1: SSE Streaming on Jobs Page (SP 3)

**Goal**: Real-time extraction progress on `/jobs/[id]` — progress bar, building status, ETA

### Tasks
- [x] 1.1 Wire `useV3BuildingStream` into `/jobs/[id]` page
  - Read `operationId` from `sessionStorage` key `acm-extraction-progress-{sourceId}` (same as /source/[id])
  - Also fall back to `source.command_id` for extraction-in-progress detection
  - Pass `totalBuildings` from buildings count
- [x] 1.2 Add streaming progress bar to jobs page header
  - Show `{completedCount}/{totalBuildings} buildings · ~{eta}s remaining` below tab strip
  - Use same pattern as `/source/[id]` `SourceACMViewContent`
  - Conditional on `isStreaming` from `useV3BuildingStream`
- [x] 1.3 Add save progress indicator
  - Show "Saving records... {savedCount}/{totalToSave}" during save phase
  - Wire `isSaving`, `savedCount`, `totalToSave` from `useV3BuildingStream`
- [x] 1.4 Update `JobStatusPill` to show "Extracting" with animated indicator when SSE stream is active
  - Currently shows `review_status` from source data (may say "Review" during extraction)
  - Override with SSE-derived status when `isStreaming`
- [x] 1.5 Invalidate records query on `ai.save_complete` in the jobs page context
  - Currently the jobs page polls for records; SSE should trigger refetch

### Key Files
- `frontend/src/app/(dashboard)/jobs/[id]/page.tsx` — add hook, progress UI
- `frontend/src/lib/hooks/useV3BuildingStream.ts` — already exists
- `frontend/src/components/jobs/JobDetailHeader.tsx` — update status pill
- `frontend/src/components/jobs/JobStatusPill.tsx` — SSE override

---

## Phase 2: Bulk Operations on Jobs Page (SP 3)

**Goal**: Multi-row selection, bulk edit, bulk validate, SSE progress on ACM Records tab

### Tasks
- [x] 2.1 Add multi-row selection to ACM Records tab
  - ACMGrid already supports `selectedRecords` prop
  - Add `selectedRecords` state + selection tracking in jobs page
- [x] 2.2 Wire `BulkOperationsBar` component
  - Import from `frontend/src/components/acm/BulkOperationsBar.tsx`
  - Pass `selectedRecords`, `sourceId`, `onClearSelection`
  - Show above/below grid when selection > 0
- [x] 2.3 Wire bulk SSE progress
  - `BulkOperationsBar` already uses `useV3SSE` for `bulk` category
  - Ensure `operationId` propagation works
- [x] 2.4 Add "Fix All" button for validation errors
  - Use `useValidationSummary(sourceId)` to get error counts
  - Show "Fix All" button when `totalErrors > 0`
  - Wire `useBulkFix` mutation

### Key Files
- `frontend/src/app/(dashboard)/jobs/[id]/page.tsx` — add selection state, BulkOperationsBar
- `frontend/src/components/acm/BulkOperationsBar.tsx` — already exists
- `frontend/src/lib/hooks/useACMItems.ts` — validation summary, bulk fix hooks

---

## Phase 3: Search, Filter & Grid Enhancements (SP 2)

**Goal**: Quick text search, Group by Room toggle, building-filtered per-building loading

### Tasks
- [x] 3.1 Add quick text search to ACM Records tab
  - Add search `Input` above grid
  - Wire `quickFilterText` prop on ACMGrid
- [x] 3.2 Add "Group by Room" toggle
  - Wire `enableGrouping` prop on ACMGrid
  - Add toggle button in toolbar
- [ ] 3.3 Switch ACM Records data source from "all records" to per-building
  - Currently: `fetch('/api/acm/records?source_id=...&limit=500')` loads ALL records
  - Target: Use `useACMItems(sourceId, selectedBuildingId)` for per-building loading
  - Much more efficient for large sources
- [ ] 3.4 Upgrade building filter from dropdown to tab strip
  - Replace `BuildingTabFilter` with `BuildingTabStrip` pattern (scrollable horizontal tabs)
  - Show per-building record count and error badges
  - Use Zustand `useBuildingStore` for persistent selection

### Key Files
- `frontend/src/app/(dashboard)/jobs/[id]/page.tsx` — search state, grouping, filter upgrade
- `frontend/src/components/acm/BuildingTabFilter.tsx` — may deprecate
- `frontend/src/lib/stores/buildingStore.ts` — building selection persistence

---

## Phase 4: Job Card Status on /jobs List (SP 2)

**Goal**: Job cards show real-time extraction status with mini progress

### Tasks
- [ ] 4.1 Add extraction status detection to job cards
  - Check `source.review_status` for "extracting" state
  - Show "Extracting..." badge instead of "Review" when in progress
- [ ] 4.2 Add mini progress indicator on extracting job cards
  - Show `{buildingCount} buildings · {recordCount} records` when in progress
  - Optional: SSE connection per active extraction (cost: one EventSource per card)
  - Alternative: Use polling from `command_id` (cheaper)
- [ ] 4.3 Auto-refresh job list when extraction completes
  - Invalidate jobs query when navigating back from completed extraction

### Key Files
- `frontend/src/app/(dashboard)/jobs/page.tsx` — job list page
- Job card component (need to identify exact file)
- `frontend/src/lib/hooks/use-sources.ts` — source data with review_status

---

## Phase 5: Validation Error Display (SP 2)

**Goal**: Per-building validation error counts and visual indicators on jobs page

### Tasks
- [x] 5.1 Wire `useValidationSummary` into jobs page
  - Show per-building error counts in building filter tabs
- [ ] 5.2 Add error row highlighting in ACMGrid
  - Highlight rows with validation errors (already supported via `rowClassRules`)
- [ ] 5.3 Add validation summary card to Overview tab
  - Show total errors, auto-fixable count, "Fix All" button
  - Link to ACM Records tab filtered to error rows

### Key Files
- `frontend/src/app/(dashboard)/jobs/[id]/page.tsx`
- `frontend/src/components/jobs/JobOverviewTab.tsx`
- `frontend/src/lib/hooks/useACMItems.ts` — useValidationSummary

---

## Phase 6: Verification & Polish (SP 1)

### Tasks
- [x] 6.1 E2E smoke test — all 6 tabs render without errors
- [ ] 6.2 SSE streaming test — extraction progress appears in real time
- [ ] 6.3 Bulk operations test — select, edit, validate flows
- [ ] 6.4 Cross-page consistency — verify /source/[id] still works
- [ ] 6.5 Mobile responsive check — chat panel, building tabs
- [ ] 6.6 Screenshot evidence at each verification point

---

## Agent Strategy

| Phase | Agents | Model | Parallelizable |
|-------|--------|-------|----------------|
| 1 | `frontend-specialist` | opus | Yes (independent of 2-5) |
| 2 | `frontend-specialist` | opus | After Phase 1 (depends on grid wiring) |
| 3 | `frontend-specialist` | opus | After Phase 2 |
| 4 | `frontend-specialist` | sonnet | Independent |
| 5 | `frontend-specialist` | sonnet | After Phase 2 |
| 6 | `e2e-tester` | sonnet | After all phases |

**Parallel batch 1**: Phase 1 + Phase 4 (independent)
**Sequential**: Phase 2 → Phase 3 → Phase 5 → Phase 6

---

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| BuildingGrid expects V3 `BuildingRecord` type | `useJobBuildings` adapter already built (MCS10 fix) |
| Dual SSE connections (jobs + source page open simultaneously) | EventBus supports multiple subscribers per operation_id |
| Chat panel + bulk ops bar competing for space | Collapse chat when bulk bar active |
| `review_status` field not updating during extraction | Override with SSE-derived status client-side |
| Old pipeline extractions have no `building_record` entities | `useJobBuildings` fallback already handles this |
