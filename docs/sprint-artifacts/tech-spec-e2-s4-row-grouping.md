# Tech Spec: E2-S4 - Implement Row Grouping

> **Story:** E2-S4
> **Epic:** AG Grid Spreadsheet Integration
> **Status:** Done
> **Created:** 2025-12-08
> **Completed:** 2025-12-18

---

## Overview

Implement hierarchical row grouping in the ACM spreadsheet to organize data by Building and Room, making it easier to navigate large datasets.

---

## User Story

**As a** user
**I want** to see ACM data grouped by Building and Room
**So that** I can navigate the hierarchy easily

---

## Acceptance Criteria

- [x] Building rows are collapsible groups
- [x] Room rows are nested within Building groups
- [x] ACM items shown as leaf rows
- [x] Group expand/collapse icons work
- [x] "Expand All" / "Collapse All" buttons available

## Implementation Notes (2025-12-18)

Row grouping was already implemented in ACMGrid.tsx with:
- `rowGroup: true` on building_id and room_id columns
- `groupDisplayType="groupRows"` for row-based grouping
- `groupDefaultExpanded={1}` to expand first level by default
- `autoGroupColumnDef` with Location header

Added Expand/Collapse All buttons:
- Added `onExpandAll` and `onCollapseAll` props to ACMToolbar
- Added ChevronDown/ChevronRight icon buttons
- Wired up via `useRef<ACMGridRef>` in ACMTab
- Buttons only shown when `showGroupingControls={hasRecords}`

---

## Technical Design

### 1. Column Definitions for Grouping

```tsx
const columnDefs: ColDef<ACMRecord>[] = [
  {
    field: 'building_id',
    headerName: 'Building',
    rowGroup: true,
    hide: true,  // Hide column, show in group
    valueFormatter: (params) => {
      if (params.data?.building_name) {
        return `${params.value} - ${params.data.building_name}`;
      }
      return params.value;
    },
  },
  {
    field: 'room_id',
    headerName: 'Room',
    rowGroup: true,
    hide: true,  // Hide column, show in group
    valueFormatter: (params) => {
      if (params.data?.room_name) {
        return `${params.value} - ${params.data.room_name}`;
      }
      return params.value || 'No Room';
    },
  },
  // Visible columns (leaf data)
  { field: 'product', headerName: 'Product' },
  { field: 'material_description', headerName: 'Material', flex: 2 },
  { field: 'extent', headerName: 'Extent' },
  { field: 'location', headerName: 'Location' },
  { field: 'friable', headerName: 'Friable' },
  { field: 'material_condition', headerName: 'Condition' },
  { field: 'risk_status', headerName: 'Risk' },
  { field: 'result', headerName: 'Result' },
];
```

### 2. Grid Configuration for Grouping

```tsx
<AgGridReact
  rowData={acmRecords}
  columnDefs={columnDefs}
  defaultColDef={defaultColDef}

  // Grouping configuration
  groupDisplayType="groupRows"  // Show groups as separate rows
  groupDefaultExpanded={1}      // Expand first level by default
  autoGroupColumnDef={{
    headerName: 'Location',
    minWidth: 300,
    cellRendererParams: {
      suppressCount: false,     // Show child count
      checkbox: false,
    },
  }}

  // Row height for groups
  getRowHeight={(params) => {
    if (params.node.group) {
      return 48;  // Taller for group rows
    }
    return 40;
  }}
/>
```

### 3. Expand/Collapse Controls

Add toolbar with expand/collapse buttons:

```tsx
export function ACMSpreadsheet({ sourceId }: Props) {
  const gridRef = useRef<AgGridReact>(null);

  const expandAll = () => {
    gridRef.current?.api.expandAll();
  };

  const collapseAll = () => {
    gridRef.current?.api.collapseAll();
  };

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-2 p-2 border-b">
        <Button variant="outline" size="sm" onClick={expandAll}>
          <ChevronDown className="w-4 h-4 mr-1" />
          Expand All
        </Button>
        <Button variant="outline" size="sm" onClick={collapseAll}>
          <ChevronRight className="w-4 h-4 mr-1" />
          Collapse All
        </Button>
      </div>

      {/* Grid */}
      <div className="ag-theme-custom flex-1">
        <AgGridReact ref={gridRef} ... />
      </div>
    </div>
  );
}
```

### 4. Group Row Styling

```css
/* Group row styling */
.ag-theme-custom .ag-row-group {
  background-color: hsl(var(--muted) / 0.5);
  font-weight: 600;
}

.ag-theme-custom .ag-row-group-expanded {
  border-bottom: 2px solid hsl(var(--border));
}

/* Indent nested groups */
.ag-theme-custom .ag-row-level-1 {
  padding-left: 24px;
}

.ag-theme-custom .ag-row-level-2 {
  padding-left: 48px;
}
```

### 5. Group Aggregation (Optional)

Show risk summary at group level:

```tsx
const columnDefs: ColDef<ACMRecord>[] = [
  // ... other columns
  {
    field: 'risk_status',
    headerName: 'Risk',
    aggFunc: (params) => {
      // Show highest risk in group
      const risks = params.values.filter(Boolean);
      if (risks.includes('High')) return 'High';
      if (risks.includes('Medium')) return 'Medium';
      if (risks.includes('Low')) return 'Low';
      return null;
    },
  },
];
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/components/acm/ACMSpreadsheet.tsx` | Add grouping config |
| `frontend/src/app/globals.css` | Group row styles |

---

## Dependencies

- E2-S2: ACMSpreadsheet component created

---

## Testing

1. Verify Building groups appear as collapsible rows
2. Verify Rooms appear nested within Buildings
3. Click expand/collapse icons - verify behavior
4. Click "Expand All" - verify all groups open
5. Click "Collapse All" - verify all groups close
6. Verify child count shows in group row
7. Test with data spanning multiple buildings/rooms

---

## Notes

- AG Grid Community supports basic row grouping
- Enterprise features (row grouping panel, drag to group) not available
- Consider adding building count to header

---

## Estimated Complexity

**Medium** - Requires proper data structure and AG Grid grouping config

---
