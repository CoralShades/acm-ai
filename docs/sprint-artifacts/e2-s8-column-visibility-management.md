# Story E2-S8: Column Visibility Management

**Epic:** E2 — AG Grid Spreadsheet Integration
**Priority:** P0
**Status:** ready-for-dev
**Change Proposal:** Sprint Change Proposal CP#4 (2026-02-04); enhanced 2026-02-08 (CP-3: AG Grid columns generated from field schema config API)

---

## User Story

**As a** compliance officer reviewing ACM register data,
**I want to** show and hide columns in the ACM spreadsheet and save my preferences,
**So that** I can focus on relevant fields without being overwhelmed by all 47 BAR columns.

---

## Background

E2-S7 (Building Tab Navigation) is complete. The ACM register now exposes all 47 BAR columns (delivered by PR #30 alongside E2-S12), but with many columns using `hide: true` as a partial workaround. This story replaces that workaround with a proper column visibility management system including preset views, a column picker UI, and localStorage persistence.

Note from YAML (2026-02-08 Course Correction CP-3): E2-S8 is enhanced to have AG Grid columns generated from the field schema config API (E1-S11 Generic Configurable Parser). The column picker should reflect the field config, not a hardcoded list.

**Dependency chain:**
```
E2-S7 (done) → E2-S8 (this story)
```

---

## Acceptance Criteria

- [ ] Column picker dropdown accessible from ACM spreadsheet toolbar (icon button, e.g., columns/sliders icon)
- [ ] Picker shows all available columns with toggle checkboxes (on/off)
- [ ] Individual column toggle applies immediately to AG Grid (no page reload)
- [ ] Preset views available and selectable from picker:
  - "Essential" — 12 core fields (see definition below)
  - "Full BAR" — all 47 columns visible
  - "Assessment Focus" — condition/action/risk assessment columns
  - "Removal Tracking" — quantity, removal date, removal fields
- [ ] Selecting a preset applies that column set immediately
- [ ] "Custom" label shown when user has manually toggled columns away from a preset
- [ ] Column visibility state persisted to localStorage under key `acm-column-visibility`
- [ ] On page load, localStorage state restored (if present) instead of default hidden columns
- [ ] "Reset to Default" option clears localStorage and reverts to "Essential" preset
- [ ] Column list in picker sourced from field schema config API (`GET /api/acm/field-config`) rather than hardcoded list
- [ ] Picker is keyboard accessible (arrow keys to navigate list, Space to toggle)
- [ ] No backend changes required — pure frontend implementation
- [ ] Existing `hide: true` flags on AG Grid column definitions removed once this feature is live

---

## Preset Column Definitions

### Essential (12 columns)
`building_id`, `room_id`, `item_no`, `product_description`, `friability`, `result`, `risk_status`, `condition`, `recommendation_action`, `location_description`, `sampled`, `area_sqm`

### Assessment Focus
`building_id`, `room_id`, `item_no`, `product_description`, `friability`, `result`, `risk_status`, `condition`, `disturbance_potential`, `accessibility`, `recommendation_action`, `reassessment_date`, `inspector_name`

### Removal Tracking
`building_id`, `room_id`, `item_no`, `product_description`, `quantity`, `unit_of_measure`, `removal_priority`, `removal_date`, `removal_contractor`, `removal_method`, `disposal_certificate_no`, `verification_date`

### Full BAR
All 47 BAR columns — `hide: false` on all column definitions.

---

## Technical Notes

### Zustand Store

```typescript
// frontend/src/stores/column-visibility-store.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type PresetName = 'essential' | 'full-bar' | 'assessment-focus' | 'removal-tracking' | 'custom'

interface ColumnVisibilityState {
  visibleColumns: string[]          // list of field keys that are visible
  activePreset: PresetName
  setVisibleColumns: (cols: string[]) => void
  applyPreset: (preset: PresetName) => void
  toggleColumn: (fieldKey: string) => void
  resetToDefault: () => void
}

export const PRESETS: Record<PresetName, string[]> = {
  'essential': ['building_id', 'room_id', 'item_no', 'product_description', 'friability',
                'result', 'risk_status', 'condition', 'recommendation_action',
                'location_description', 'sampled', 'area_sqm'],
  'full-bar': [],  // empty = show all
  'assessment-focus': ['building_id', 'room_id', 'item_no', 'product_description', 'friability',
                       'result', 'risk_status', 'condition', 'disturbance_potential',
                       'accessibility', 'recommendation_action', 'reassessment_date', 'inspector_name'],
  'removal-tracking': ['building_id', 'room_id', 'item_no', 'product_description', 'quantity',
                       'unit_of_measure', 'removal_priority', 'removal_date', 'removal_contractor',
                       'removal_method', 'disposal_certificate_no', 'verification_date'],
  'custom': [],    // user-defined, populated dynamically
}

export const useColumnVisibilityStore = create<ColumnVisibilityState>()(
  persist(
    (set, get) => ({
      visibleColumns: PRESETS['essential'],
      activePreset: 'essential',
      setVisibleColumns: (cols) => set({ visibleColumns: cols, activePreset: 'custom' }),
      applyPreset: (preset) => set({ visibleColumns: PRESETS[preset], activePreset: preset }),
      toggleColumn: (fieldKey) => {
        const current = get().visibleColumns
        const next = current.includes(fieldKey)
          ? current.filter(k => k !== fieldKey)
          : [...current, fieldKey]
        set({ visibleColumns: next, activePreset: 'custom' })
      },
      resetToDefault: () => set({ visibleColumns: PRESETS['essential'], activePreset: 'essential' }),
    }),
    { name: 'acm-column-visibility' }  // localStorage key
  )
)
```

### AG Grid Integration

In `ACMSpreadsheet.tsx`, read `visibleColumns` from the store and call AG Grid Column API on change:

```typescript
const { visibleColumns, activePreset } = useColumnVisibilityStore()
const gridRef = useRef<AgGridReact>(null)

useEffect(() => {
  const api = gridRef.current?.api
  if (!api) return
  const allColumns = api.getColumns() ?? []
  allColumns.forEach(col => {
    const fieldKey = col.getColId()
    const shouldShow = activePreset === 'full-bar' || visibleColumns.includes(fieldKey)
    api.setColumnVisible(fieldKey, shouldShow)
  })
}, [visibleColumns, activePreset])
```

Remove any existing `hide: true` from column definitions after this is live.

### Column Picker Component

```
frontend/src/components/acm/ColumnVisibilityPicker.tsx
```

Structure:
- Trigger: `<Button variant="outline" size="sm"><Columns2Icon /> Columns</Button>`
- Popover/dropdown content:
  - Preset selector row (4 preset buttons + "Custom" indicator)
  - Divider
  - Scrollable column list (max-height 320px, overflow-y auto)
    - Each row: `<Checkbox checked={isVisible} onCheckedChange={() => toggleColumn(key)} /> <label>{displayName}</label>`
  - Footer: "Reset to Default" text button

Column display names come from the field schema config API response (`GET /api/acm/field-config`) — use `field.display_name` rather than the raw field key. If the API is unavailable, fall back to a local mapping derived from the BAR column definitions.

### Toolbar Integration

The column picker button is added to the existing ACM spreadsheet toolbar alongside Search, Export, and Building Tabs. Check `frontend/src/components/acm/ACMSpreadsheet.tsx` for the toolbar section.

---

## Key File Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `frontend/src/stores/column-visibility-store.ts` | NEW | Zustand store with localStorage persistence |
| `frontend/src/components/acm/ColumnVisibilityPicker.tsx` | NEW | Dropdown column picker with presets |
| `frontend/src/components/acm/ACMSpreadsheet.tsx` | MODIFY | Wire store to AG Grid Column API, add picker to toolbar, remove `hide: true` flags |
| `frontend/src/app/(dashboard)/sources/[id]/acm/page.tsx` | MODIFY (if needed) | Ensure store is available in page scope |

---

## Dependencies

- **Requires:** E2-S7 (Building Tab Navigation — done)
- **Requires (soft):** E1-S11 (Generic Configurable Parser — done) provides `GET /api/acm/field-config` for dynamic column names. Falls back to hardcoded names if unavailable.
- **Blocks:** Nothing. E5-S4 (Field Mapping) benefits from this but does not depend on it.

---

## Estimated Effort

S (Small) — Pure frontend work. Zustand store with `persist` middleware handles localStorage automatically. AG Grid Column API (`setColumnVisible`) is well-documented. The main effort is the column picker component UI and wiring it to the store and grid.

---

## Dev Agent Record

> To be filled in by implementing agent.

- [ ] Build status: —
- [ ] Files verified: —
- [ ] Pages verified: —
- [ ] Notes: —
