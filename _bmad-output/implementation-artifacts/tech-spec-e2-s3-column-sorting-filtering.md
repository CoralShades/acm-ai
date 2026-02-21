# Tech Spec: E2-S3 - Implement Column Sorting and Filtering

> **Story:** E2-S3
> **Epic:** AG Grid Spreadsheet Integration
> **Status:** Done
> **Created:** 2025-12-08
> **Completed:** 2025-12-08

---

## Overview

Enable AG Grid's built-in sorting and filtering capabilities for the ACM spreadsheet, with appropriate filter types for each column.

---

## User Story

**As a** user
**I want** to sort and filter the ACM data
**So that** I can find specific records quickly

---

## Acceptance Criteria

- [x] Click column header to sort ascending/descending
- [x] Filter icon in header opens filter menu
- [x] Text filter for string columns
- [x] Dropdown filter for enum columns (Risk Status, Friable, Result)
- [x] Filter state persists during session

---

## Technical Design

### 1. Column Definitions with Filters

Update `ACMSpreadsheet.tsx` column definitions:

```tsx
const columnDefs: ColDef<ACMRecord>[] = [
  // Text filter for string columns
  {
    field: 'school_name',
    headerName: 'School',
    filter: 'agTextColumnFilter',
    filterParams: {
      filterOptions: ['contains', 'startsWith', 'equals'],
      defaultOption: 'contains',
    },
  },
  {
    field: 'building_id',
    headerName: 'Building ID',
    filter: 'agTextColumnFilter',
  },
  {
    field: 'building_name',
    headerName: 'Building Name',
    filter: 'agTextColumnFilter',
  },
  {
    field: 'room_id',
    headerName: 'Room ID',
    filter: 'agTextColumnFilter',
  },
  {
    field: 'product',
    headerName: 'Product',
    filter: 'agTextColumnFilter',
  },
  {
    field: 'material_description',
    headerName: 'Material',
    filter: 'agTextColumnFilter',
    flex: 2,
  },

  // Dropdown filter for enum columns
  {
    field: 'risk_status',
    headerName: 'Risk Status',
    filter: 'agSetColumnFilter',
    filterParams: {
      values: ['Low', 'Medium', 'High'],
    },
  },
  {
    field: 'friable',
    headerName: 'Friable',
    filter: 'agSetColumnFilter',
    filterParams: {
      values: ['Friable', 'Non Friable'],
    },
  },
  {
    field: 'result',
    headerName: 'Result',
    filter: 'agSetColumnFilter',
    filterParams: {
      values: ['Detected', 'Not Detected', 'Presumed'],
    },
  },
  {
    field: 'material_condition',
    headerName: 'Condition',
    filter: 'agSetColumnFilter',
    filterParams: {
      values: ['Good', 'Fair', 'Poor'],
    },
  },

  // Number filter
  {
    field: 'page_number',
    headerName: 'Page',
    filter: 'agNumberColumnFilter',
    width: 80,
  },
];
```

### 2. Default Column Configuration

```tsx
const defaultColDef = useMemo<ColDef>(() => ({
  sortable: true,
  resizable: true,
  filter: true,
  floatingFilter: true,  // Shows filter row below headers
  minWidth: 100,
}), []);
```

### 3. Filter State Persistence

Use React state to persist filter model during session:

```tsx
const [filterModel, setFilterModel] = useState<FilterModel | null>(null);

// Save filter state on change
const onFilterChanged = useCallback((event: FilterChangedEvent) => {
  const model = event.api.getFilterModel();
  setFilterModel(model);
  // Optionally save to sessionStorage
  sessionStorage.setItem('acm-filter-model', JSON.stringify(model));
}, []);

// Restore filter state on grid ready
const onGridReady = useCallback((event: GridReadyEvent) => {
  const saved = sessionStorage.getItem('acm-filter-model');
  if (saved) {
    event.api.setFilterModel(JSON.parse(saved));
  }
}, []);
```

### 4. Sort Indicators

AG Grid includes sort indicators by default. Customize if needed:

```css
/* Custom sort indicator styling */
.ag-theme-custom .ag-header-cell-sorted-asc .ag-sort-indicator-icon {
  color: hsl(var(--primary));
}

.ag-theme-custom .ag-header-cell-sorted-desc .ag-sort-indicator-icon {
  color: hsl(var(--primary));
}
```

### 5. Multi-Column Sort

Enable multi-column sorting with Shift+Click:

```tsx
<AgGridReact
  multiSortKey="shift"
  // ...other props
/>
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/components/acm/ACMSpreadsheet.tsx` | Add filter configs to columns |
| `frontend/src/app/globals.css` | Custom filter/sort styles |

---

## Dependencies

- E2-S1: AG Grid installed
- E2-S2: ACMSpreadsheet component created

---

## Testing

1. Click column header - verify sort toggles ASC/DESC/none
2. Click filter icon - verify filter menu opens
3. Apply text filter - verify rows filter correctly
4. Apply dropdown filter for Risk Status - verify filtering
5. Apply multiple filters - verify combined filtering
6. Refresh page - verify filters persist (session)
7. Test multi-column sort with Shift+Click

---

## Estimated Complexity

**Low** - Built-in AG Grid functionality, configuration only

---
