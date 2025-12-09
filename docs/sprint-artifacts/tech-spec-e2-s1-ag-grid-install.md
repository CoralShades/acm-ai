# Tech Spec: E2-S1 - Install and Configure AG Grid

> **Story:** E2-S1
> **Epic:** AG Grid Spreadsheet Integration
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Install AG Grid React library and configure it for use in the ACM-AI frontend, including theme customization to match the existing application design.

---

## User Story

**As a** developer
**I want** AG Grid installed in the frontend
**So that** I can build the spreadsheet component

---

## Acceptance Criteria

- [ ] `ag-grid-react` and `ag-grid-community` installed
- [ ] AG Grid CSS imported and themed to match app
- [ ] License configured (Community edition)
- [ ] Basic grid renders in test page

---

## Technical Design

### 1. Package Installation

```bash
cd frontend
npm install ag-grid-react ag-grid-community
```

### 2. AG Grid Module Registration

Create `frontend/src/lib/ag-grid-config.ts`:

```typescript
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community';

// Register all Community modules
ModuleRegistry.registerModules([AllCommunityModule]);

// Export flag to ensure registration happens once
export const AG_GRID_INITIALIZED = true;
```

### 3. Theme Configuration

Add to `frontend/src/app/globals.css`:

```css
/* AG Grid Theme Customization */
.ag-theme-custom {
  --ag-background-color: hsl(var(--background));
  --ag-foreground-color: hsl(var(--foreground));
  --ag-header-background-color: hsl(var(--muted));
  --ag-header-foreground-color: hsl(var(--foreground));
  --ag-odd-row-background-color: hsl(var(--background));
  --ag-row-hover-color: hsl(var(--accent));
  --ag-selected-row-background-color: hsl(var(--primary) / 0.1);
  --ag-border-color: hsl(var(--border));
  --ag-cell-horizontal-border: 1px solid hsl(var(--border));
  --ag-font-family: inherit;
  --ag-font-size: 14px;
  --ag-row-height: 40px;
  --ag-header-height: 44px;
}

/* Dark mode support */
.dark .ag-theme-custom {
  --ag-background-color: hsl(var(--background));
  --ag-foreground-color: hsl(var(--foreground));
  --ag-header-background-color: hsl(var(--muted));
  --ag-odd-row-background-color: hsl(var(--card));
}
```

### 4. Basic Grid Wrapper Component

Create `frontend/src/components/ui/data-grid.tsx`:

```tsx
'use client';

import { AgGridReact, AgGridReactProps } from 'ag-grid-react';
import { useRef, useMemo } from 'react';
import { cn } from '@/lib/utils';

// Ensure AG Grid is initialized
import '@/lib/ag-grid-config';

interface DataGridProps<T> extends AgGridReactProps<T> {
  className?: string;
  height?: string | number;
}

export function DataGrid<T>({
  className,
  height = 400,
  ...props
}: DataGridProps<T>) {
  const gridRef = useRef<AgGridReact<T>>(null);

  const defaultColDef = useMemo(() => ({
    sortable: true,
    resizable: true,
    filter: true,
  }), []);

  return (
    <div
      className={cn('ag-theme-custom w-full', className)}
      style={{ height }}
    >
      <AgGridReact<T>
        ref={gridRef}
        defaultColDef={defaultColDef}
        animateRows={true}
        {...props}
      />
    </div>
  );
}
```

### 5. Test Page

Create `frontend/src/app/(dashboard)/test-grid/page.tsx`:

```tsx
'use client';

import { DataGrid } from '@/components/ui/data-grid';
import { ColDef } from 'ag-grid-community';

const testData = [
  { id: 1, building: 'Admin Block', room: 'A101', product: 'Floor Tiles', risk: 'Low' },
  { id: 2, building: 'Admin Block', room: 'A102', product: 'Ceiling Tiles', risk: 'Medium' },
  { id: 3, building: 'Science Wing', room: 'S201', product: 'Pipe Lagging', risk: 'High' },
];

const columns: ColDef[] = [
  { field: 'building', headerName: 'Building' },
  { field: 'room', headerName: 'Room' },
  { field: 'product', headerName: 'Product' },
  { field: 'risk', headerName: 'Risk Status' },
];

export default function TestGridPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">AG Grid Test</h1>
      <DataGrid
        rowData={testData}
        columnDefs={columns}
        height={400}
      />
    </div>
  );
}
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/package.json` | Add AG Grid dependencies |
| `frontend/src/lib/ag-grid-config.ts` | New - module registration |
| `frontend/src/app/globals.css` | Add AG Grid theme styles |
| `frontend/src/components/ui/data-grid.tsx` | New - wrapper component |
| `frontend/src/app/(dashboard)/test-grid/page.tsx` | New - test page |

---

## Dependencies

None - this is the first story in Epic 2

---

## Testing

1. Run `npm install` and verify no errors
2. Navigate to `/test-grid` page
3. Verify grid renders with sample data
4. Check styling matches app theme
5. Test dark mode toggle
6. Verify sorting works on columns
7. Check responsive behavior

---

## Notes

- Using Community Edition (MIT license)
- AG Grid v32+ uses modular imports
- Theme uses CSS variables for consistency with shadcn/ui

---

## Estimated Complexity

**Low** - Standard package installation and configuration

---
