# Story 2.8: Column Visibility Management

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **user**,
I want to **show/hide columns and save my preferences**,
so that **I can focus on relevant data without clutter from 47+ columns**.

## Acceptance Criteria

1. Column visibility panel accessible from ACM toolbar (popover or sidebar)
2. Toggle individual columns on/off with immediate grid update
3. Preset views available and selectable:
   - "Essential" (7 key columns: building_name, room_name, product, friable, material_condition, risk_status, sample_result)
   - "Full BAR" (all 47 columns visible)
   - "Assessment Focus" (building_name, room_name, product, material_condition, disturbance_potential, risk_status, hygienist_recommendations)
   - "Removal Tracking" (building_name, room_name, product, assumed_removed, date_of_removal, quantity_removed, removal_notification_no)
4. Save custom column views with user-defined name
5. Apply saved view to current spreadsheet instantly
6. Default view per user preference (persisted)
7. Column visibility persists in localStorage across sessions
8. Column groups displayed in visibility panel matching AG Grid column groups (Organization, Building, Location, ACM Details, Assessment, Documentation, Removal)

## Tasks / Subtasks

- [ ] Task 1: Create ColumnVisibility component (AC: #1, #2, #8)
  - [ ] 1.1 Create `frontend/src/components/acm/ColumnVisibility.tsx`
  - [ ] 1.2 Build popover UI with checkbox list grouped by column groups
  - [ ] 1.3 Wire toggle to AG Grid `applyColumnState()` API
  - [ ] 1.4 Add "Columns" button to ACMToolbar.tsx
- [ ] Task 2: Implement preset views (AC: #3)
  - [ ] 2.1 Define COLUMN_PRESETS constant (from Architecture 6.1)
  - [ ] 2.2 Add preset selector dropdown/buttons in ColumnVisibility
  - [ ] 2.3 Apply preset by showing only preset columns, hiding all others
- [ ] Task 3: Custom view save/load (AC: #4, #5)
  - [ ] 3.1 Add "Save Current View" button with name input
  - [ ] 3.2 Store saved views in localStorage key `acm-column-views`
  - [ ] 3.3 List saved views with apply/delete actions
- [ ] Task 4: Persistence and defaults (AC: #6, #7)
  - [ ] 4.1 Persist active column state to localStorage key `acm-column-visibility`
  - [ ] 4.2 Restore column state on grid ready
  - [ ] 4.3 Store default view preference in localStorage key `acm-default-view`
  - [ ] 4.4 Apply default view on initial load when no saved state exists
- [ ] Task 5: Expand column definitions to match Architecture spec (AC: #8)
  - [ ] 5.1 Update ACMGrid.tsx column definitions from 13 to full 47+ BAR columns
  - [ ] 5.2 Organize into 7 column groups per Architecture Section 6.1
  - [ ] 5.3 Set appropriate `hide: true` defaults for non-essential columns
  - [ ] 5.4 Add proper `headerName`, `width`, `filter` config per column
- [ ] Task 6: Integration and testing (AC: all)
  - [ ] 6.1 Integrate ColumnVisibility into ACMTab/ACMToolbar
  - [ ] 6.2 Verify all presets show/hide correct columns
  - [ ] 6.3 Verify persistence across page reloads
  - [ ] 6.4 Test with building grouping enabled/disabled

## Dev Notes

### Critical Context

**AG Grid Version:** v35.0.0 (Community Edition) - `ag-grid-react` and `ag-grid-community`

**Current State:** ACMGrid.tsx currently defines only **13 columns** but Architecture Section 6.1 specifies **47+ columns in 7 groups**. This story MUST expand column definitions to the full set AND add visibility management.

**Architecture Reference:** Section 6.1 defines `COLUMN_PRESETS` and `columnGroupDefs` with all 7 groups. Use this as the authoritative column specification.
[Source: _bmad-output/project-planning-artifacts/acm-ai/04-architecture.md#Section 6.1]

### AG Grid Column API (v35)

Use these AG Grid API methods for column visibility:

```typescript
// Get current column state (includes visibility)
const state = gridApi.getColumnState();

// Apply column visibility changes
gridApi.applyColumnState({
  state: [
    { colId: 'department', hide: true },
    { colId: 'building_name', hide: false },
  ],
  defaultState: { hide: true } // Hide all not explicitly set
});

// Show/hide single column
gridApi.setColumnsVisible(['department', 'agency'], false);
gridApi.setColumnsVisible(['building_name', 'room_name'], true);
```

### Existing Patterns to Follow

**GridApi access pattern** (ACMGrid.tsx):
```typescript
const [gridApi, setGridApi] = useState<GridApi<ACMRecord> | null>(null);
const onGridReady = useCallback((params: GridReadyEvent<ACMRecord>) => {
  setGridApi(params.api);
  params.api.sizeColumnsToFit();
}, []);
```
The gridApi is currently stored in ACMGrid and exposed via `useImperativeHandle`. The ColumnVisibility component needs access to the gridApi - pass it as a prop or lift the api ref to ACMTab.

**localStorage persistence** - Use existing `useLocalStorage` hook at:
`frontend/src/lib/hooks/use-local-storage.ts`
```typescript
const [value, setValue] = useLocalStorage('acm-column-visibility', defaultState);
```

**Session storage pattern** - Building filter already uses:
`frontend/src/lib/hooks/use-session-storage.ts`

**Zustand store pattern** (if needed for complex state) - See:
`frontend/src/lib/stores/notebook-columns-store.ts` for persist pattern.

**Toolbar UI pattern** - ACMToolbar already has DropdownMenu for export:
```tsx
<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant="outline" size="sm">
      <Columns3 className="h-4 w-4 mr-1" /> Columns
    </Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent>
    {/* Column toggles here */}
  </DropdownMenuContent>
</DropdownMenu>
```

### Column Preset Definitions (from Architecture 6.1)

```typescript
const COLUMN_PRESETS: Record<string, string[] | null> = {
  essential: ['building_name', 'room_name', 'product', 'friable', 'material_condition', 'risk_status', 'sample_result'],
  full_bar: null, // null = show ALL columns
  assessment_focus: ['building_name', 'room_name', 'product', 'material_condition', 'disturbance_potential', 'risk_status', 'hygienist_recommendations'],
  removal_tracking: ['building_name', 'room_name', 'product', 'assumed_removed', 'date_of_removal', 'quantity_removed', 'removal_notification_no'],
};
```

### Column Groups (Architecture 6.1 - 7 groups)

| Group | Fields | Default Visible |
|-------|--------|----------------|
| Organization | department, agency, sub_agency, site_name | Hidden |
| Building | building_name, building_type, building_address, suburb, postcode, owned_or_leased, building_unique_id, frequency_of_use, public_access, date_of_inspection, building_year, building_size_m2, number_of_levels, building_construction, roof_type | building_name only |
| Location | area_type, level, room_name, room_area, location | All visible |
| ACM Details | product, material_description, friable, acm_product_group, acm_product_type, nata_sample_number, sample_result, hygiene_company | Most visible, product_group/type hidden |
| Assessment | material_condition, disturbance_potential, extent, risk_status | All visible |
| Documentation | labelled, label_details, hygienist_recommendations, additional_comments, photo_reference | All hidden |
| Removal | psb_acm_id, assumed_removed, date_of_removal, quantity_removed, removal_notification_no, epa_certificate_no, removal_comments | All hidden |

### UI Components Available (DO NOT create new ones)

Reuse existing components from `frontend/src/components/ui/`:
- `popover.tsx` - Use for column visibility panel
- `checkbox.tsx` - Use for column toggles
- `button.tsx` - Use for preset buttons and save
- `dropdown-menu.tsx` - Alternative to popover, already used in toolbar
- `scroll-area.tsx` - For scrollable column list (47+ items)
- `input.tsx` - For custom view name input
- `separator.tsx` - Between preset section and column list

### File Changes Required

| File | Action | Purpose |
|------|--------|---------|
| `frontend/src/components/acm/ColumnVisibility.tsx` | CREATE | Column visibility panel component |
| `frontend/src/components/acm/ACMGrid.tsx` | MODIFY | Expand to 47+ column definitions with groups; expose gridApi for column state |
| `frontend/src/components/acm/ACMToolbar.tsx` | MODIFY | Add "Columns" button that opens ColumnVisibility |
| `frontend/src/components/acm/ACMTab.tsx` | MODIFY | Pass gridApi to toolbar; handle column state persistence on grid ready |

### Anti-Patterns to Avoid

- **DO NOT** use AG Grid Enterprise features (sideBar, tool panels) - Community edition only
- **DO NOT** create a Zustand store unless needed - `useLocalStorage` hook is simpler and sufficient
- **DO NOT** modify the ACMRecord TypeScript type - column defs map to existing fields
- **DO NOT** add backend endpoints - this is purely frontend localStorage-based
- **DO NOT** duplicate column definitions - define once and derive presets from the master list
- **DO NOT** break existing grid functionality (sorting, filtering, grouping, cell click, quick filter, pagination, risk badges)

### Dependencies

- **Depends on:** E2-S7 (Building Tab Navigation) - DONE
- **No blockers:** All dependencies satisfied
- **Blocks:** Nothing

### Project Structure Notes

- All ACM components live in `frontend/src/components/acm/`
- Hooks in `frontend/src/lib/hooks/`
- Types in `frontend/src/lib/types/acm.ts` (ACMRecord interface exists)
- AG Grid config in `frontend/src/lib/ag-grid-config.ts`
- Theme CSS in `frontend/src/app/globals.css` (ag-theme-alpine with legacy mode)

### References

- [Architecture Section 6.1: AG Grid Configuration](../_bmad-output/project-planning-artifacts/acm-ai/04-architecture.md#6.1)
- [Epics: E2-S8 Column Visibility Management](../_bmad-output/project-planning-artifacts/acm-ai/05-epics-and-stories.md#E2-S8)
- [Sprint Change Proposal CP#4](../_bmad-output/sprint-change-proposal-20260204.md)
- [ACMGrid.tsx](frontend/src/components/acm/ACMGrid.tsx) - Current 13-column implementation
- [ACMToolbar.tsx](frontend/src/components/acm/ACMToolbar.tsx) - Toolbar with export dropdown pattern
- [ACMTab.tsx](frontend/src/components/acm/ACMTab.tsx) - Container component
- [use-local-storage.ts](frontend/src/lib/hooks/use-local-storage.ts) - Persistence hook
- [notebook-columns-store.ts](frontend/src/lib/stores/notebook-columns-store.ts) - Zustand persist pattern

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
