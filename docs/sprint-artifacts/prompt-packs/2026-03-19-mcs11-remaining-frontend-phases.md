# MCS11-Frontend: Remaining Frontend Phases (3.3, 3.4, 5.2, 5.3)
# Generated from MCS11 task_plan.md audit — 2026-03-19

**SP: 5 | Priority: P1 | Dependencies: MCS11-Gap4 (FK fix), MCS11 Building/Room ID fix**
**Audit ref: MCS11 task_plan.md — phases 3.3, 3.4, 5.2, 5.3 marked incomplete**
**Blocks: MCS11 Verification (6.2-6.6)**

## Skills to Load

/frontend-design — React Query, Zustand patterns
/e2e-test — browser verification
/agent-browser — screenshot and DOM snapshot
/ui-ux-pro-max — grid enhancements, error highlighting
/uncodixfy — no placeholder UI, real data only
/verification-before-completion — verify all tabs and hooks before marking done

---

## Problem Statement

MCS11 unified `/jobs/[id]` as the canonical page. Phases 1, 2, 3.1, 3.2, 5.1 are complete. Four tasks remain:

### Phase 3.3: Per-Building Data Loading (Efficiency Fix)
Currently the ACM Records tab loads ALL records for the source via:
```
fetch('/api/acm/records?source_id=...&limit=500')
```
This ignores the selected building — all 500+ records load regardless of which building tab is selected. The hook `useACMItems(sourceId, buildingId)` already exists and filters by `building_record_id`. It just needs to replace the all-records query in the jobs page.

**Impact**: Large sources (500+ records) are slow and the building tab selection has no filtering effect on the data displayed.

### Phase 3.4: Building Tab Strip Upgrade
The current building filter is a dropdown or basic `BuildingTabFilter`. The target is a scrollable horizontal tab strip (`BuildingTabStrip` pattern from `/source/[id]`) that shows:
- Per-building record count badge
- Per-building error badge (from `useValidationSummary`)
- Persistent selection via Zustand `useBuildingStore`

### Phase 5.2: Error Row Highlighting in ACMGrid
`ACMGrid` already supports `rowClassRules` for highlighting. The validation summary provides per-record error counts. Records with validation errors need a visual highlight (red/amber row background) in the grid so users can see which rows need attention without scrolling through all records.

### Phase 5.3: Validation Summary Card on Overview Tab
The Overview tab needs a "Validation Summary" card showing:
- Total records count
- Total errors count
- Auto-fixable count
- "Fix All" button (wires `useBulkFix` mutation)
- Link to ACM Records tab filtered to error rows

---

## Key Files

**Read (understand current state):**
- `frontend/src/app/(dashboard)/jobs/[id]/page.tsx` — full jobs page, understand current ACM Records tab wiring
- `frontend/src/components/acm/ACMGrid.tsx` — `rowClassRules` prop, `quickFilterText`, `enableGrouping`
- `frontend/src/components/acm/BuildingGrid.tsx` — building grid component
- `frontend/src/lib/hooks/useACMItems.ts` — `useACMItems(sourceId, buildingId)`, `useValidationSummary`
- `frontend/src/lib/hooks/useBuildings.ts` — buildings hook
- `frontend/src/lib/stores/buildingStore.ts` — Zustand building selection store
- `frontend/src/components/jobs/JobOverviewTab.tsx` — Overview tab (where validation card goes)
- `frontend/src/components/acm/BulkOperationsBar.tsx` — bulk ops, `useBulkFix` reference

**Modify:**
- `frontend/src/app/(dashboard)/jobs/[id]/page.tsx` — Phase 3.3 (switch ACM data source), Phase 3.4 (tab strip)
- `frontend/src/components/acm/ACMGrid.tsx` — Phase 5.2 (error row highlighting via rowClassRules)
- `frontend/src/components/jobs/JobOverviewTab.tsx` — Phase 5.3 (validation summary card)

**Reference (do not modify):**
- `frontend/src/app/(dashboard)/source/[id]/page.tsx` — source page has BuildingTabStrip pattern to copy
- `frontend/src/components/acm/BulkOperationsBar.tsx` — bulk fix hook pattern

---

## Plan

### Phase 3.3: Switch ACM Records Data Source to Per-Building

- [ ] 3.3.1 Locate the current ACM Records tab data fetch in `jobs/[id]/page.tsx`
  - Find where it calls the all-records API (not using `buildingId` filter)
  - Identify the selected building state variable
- [ ] 3.3.2 Replace all-records fetch with `useACMItems(sourceId, selectedBuildingId)` hook
  - `useACMItems` already exists in `frontend/src/lib/hooks/useACMItems.ts`
  - When `selectedBuildingId` is null (no building selected), show empty state or all-records fallback
  - Pass `isExtracting` option when SSE stream is active
- [ ] 3.3.3 Update ACMGrid to receive `data` from the per-building hook result
- [ ] 3.3.4 Show loading skeleton when building is selected but data not yet loaded
- [ ] 3.3.5 Verify: selecting building A → grid shows only building A records; selecting building B → grid shows only building B records

### Phase 3.4: Building Tab Strip Upgrade

- [ ] 3.4.1 Read the `BuildingTabStrip` or equivalent component from `/source/[id]` page
  - Look for scrollable horizontal tabs with count badges
  - If it exists as a standalone component, import it; if not, build it from the pattern
- [ ] 3.4.2 In `jobs/[id]/page.tsx`, replace current building filter (dropdown or basic filter) with tab strip:
  - Each tab: building name + record count badge + error count badge (if errors > 0)
  - Active tab highlighted
  - Scrollable when many buildings (overflow-x-auto)
- [ ] 3.4.3 Wire tab selection to Zustand `useBuildingStore`:
  - Read `selectedBuildingId` from store
  - On tab click: call store's `setSelectedBuilding(buildingId)`
  - Persist across re-renders and tab switches
- [ ] 3.4.4 Wire record counts from `useBuildings(sourceId)` — use `record_count` field on `BuildingRecord`
- [ ] 3.4.5 Wire error counts from `useValidationSummary(sourceId)` — per-building error counts
- [ ] 3.4.6 Verify: switching tabs updates both tab highlight AND grid data (3.3 + 3.4 combined)

### Phase 5.2: Error Row Highlighting in ACMGrid

- [ ] 5.2.1 Read `ACMGrid.tsx` — find `rowClassRules` prop handling
- [ ] 5.2.2 Add a `hasValidationErrors` row class rule:
  - Apply `'bg-red-50 dark:bg-red-950/20'` (or similar) when record has validation errors
  - Determine error detection: check if record has a `validation_errors` field, or use `validation_status !== 'valid'`
  - Check the `ACMRecord` type in `frontend/src/lib/types/acm.ts` to see available fields
- [ ] 5.2.3 Pass validation error data into ACMGrid:
  - Either via `rowData` augmentation (add error flag to each row object)
  - Or via the `rowClassRules` callback receiving the row data node
- [ ] 5.2.4 Add legend: small note below or above grid: "Red rows have validation errors"
- [ ] 5.2.5 Verify: upload a source with known validation errors, see red rows in grid

### Phase 5.3: Validation Summary Card on Overview Tab

- [ ] 5.3.1 Read `JobOverviewTab.tsx` — find where to add the card (after existing stats cards)
- [ ] 5.3.2 Create validation summary card using `useValidationSummary(sourceId)`:
  - Show: Total Records | Total Errors | Auto-fixable | Manual Review needed
  - Show "Fix All" button using `useBulkFix` mutation (import from `BulkOperationsBar` or `useACMItems`)
  - Show "View Errors" link that navigates to ACM Records tab (use tab state or router)
- [ ] 5.3.3 Hide card when no errors (or show "No validation errors" success state)
- [ ] 5.3.4 Apply /ui-ux-pro-max — use appropriate color coding (green for clean, amber for warnings, red for errors)
- [ ] 5.3.5 Apply /uncodixfy — do not show placeholder text; hide card entirely if validation summary is loading or no errors
- [ ] 5.3.6 Verify: card appears on Overview tab, "Fix All" triggers bulk fix, "View Errors" navigates to ACM Records tab

---

## Agent Strategy

| Agent | Role | Model | Tasks |
|-------|------|-------|-------|
| `frontend-data` | Per-building data loading + tab strip | sonnet | Phase 3.3, 3.4 |
| `frontend-ui` | Error highlighting + validation card | sonnet | Phase 5.2, 5.3 |
| `verifier` | Browser verification of all phases | sonnet | Final verification |

**Parallel batch**: Phase 3.3+3.4 (data layer) can start in parallel with Phase 5.2+5.3 (UI layer), since they touch different components. Merge and verify together at end.

**Sequential within each agent**: 3.3 before 3.4 (tab strip depends on per-building data being wired); 5.2 before 5.3 (error data pattern established in grid first).

---

## Verification Checklist

- [ ] ACM Records tab loads only the selected building's records (not all 500)
- [ ] Switching building tabs changes grid data (not just visual tab state)
- [ ] Building tab strip shows record count badge per building
- [ ] Building tab strip shows error count badge when building has validation errors
- [ ] Building selection persists across tab switches (Zustand store)
- [ ] ACMGrid rows with validation errors have visual highlight (red/amber background)
- [ ] Validation summary card appears on Overview tab
- [ ] "Fix All" button triggers bulk fix and grid refreshes
- [ ] "View Errors" link navigates to ACM Records tab
- [ ] `npm run build` passes with no TypeScript errors
- [ ] `npm run lint` passes
- [ ] Browser: open `/jobs/{sourceId}`, click Buildings tab, select a building, click ACM Records tab — records match selected building

---

## Browser Verification Steps

After implementation:
```bash
agent-browser open http://localhost:8502/jobs/{sourceId}
agent-browser wait --load networkidle
agent-browser screenshot phase33-start.png --annotate

# Click ACM Records tab
agent-browser snapshot -i
# Click building tab strip — second building
# Verify grid changes

agent-browser screenshot phase34-tab-strip.png --annotate
agent-browser eval 'document.querySelectorAll("[data-nextjs-dialog]").length === 0 ? "OK" : "ERROR"'
agent-browser close
```

---

## Commit Template

```
feat(jobs-page): per-building ACM data loading, tab strip, error highlighting, validation card

- Phase 3.3: ACM Records tab now loads per-building (useACMItems + buildingId)
- Phase 3.4: Building tab strip with record count + error count badges
- Phase 5.2: Error row highlighting in ACMGrid (red rows for validation errors)
- Phase 5.3: Validation summary card on Overview tab with Fix All button
- Zustand buildingStore persists tab selection across route changes
- MCS11 frontend phases 3.3, 3.4, 5.2, 5.3

Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```

---

## Execution Order

**Prerequisites (must be done first):**
- MCS11-Gap4 FK fix (building_record_id not NULL) — `useACMItems` hook queries by `building_record_id`
- MCS11 Building/Room ID fix (`2026-03-19-mcs11-remaining-building-room-id-audit-fix.md`) — building_code values must be stable codes not names

**Recommended full sequence:**

1. **MCS11 Building/Room ID Fix** — backend, foundational
2. **MCS12** (SSE events) — backend, independent, parallel with item 1
3. **MCS13** (DocumentMeta fix) — backend, independent, parallel with items 1-2
4. **This pack (MCS11 Frontend Phases)** — depends on items 1 + MCS11-Gap4 FK fix
5. **MCS11 Verification** (`2026-03-19-mcs11-remaining-verification.md`) — final, depends on all above
