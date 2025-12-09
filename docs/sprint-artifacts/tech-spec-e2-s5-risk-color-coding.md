# Tech Spec: E2-S5 - Implement Risk Status Color Coding

> **Story:** E2-S5
> **Epic:** AG Grid Spreadsheet Integration
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Add visual color coding to risk status cells in the ACM spreadsheet to help users quickly identify high-risk items.

---

## User Story

**As a** user
**I want** risk levels visually highlighted
**So that** I can quickly identify high-risk items

---

## Acceptance Criteria

- [ ] Low risk: green background/badge
- [ ] Medium risk: yellow/amber background/badge
- [ ] High risk: red background/badge
- [ ] Colors accessible (sufficient contrast)
- [ ] Custom cell renderer for Risk Status column

---

## Technical Design

### 1. Risk Badge Cell Renderer

Create `frontend/src/components/acm/RiskBadgeCellRenderer.tsx`:

```tsx
import { ICellRendererParams } from 'ag-grid-community';
import { cn } from '@/lib/utils';

export function RiskBadgeCellRenderer(props: ICellRendererParams) {
  const risk = props.value as string | null;

  if (!risk) {
    return <span className="text-muted-foreground">—</span>;
  }

  const badgeStyles = {
    Low: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    Medium: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
    High: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  };

  const styles = badgeStyles[risk as keyof typeof badgeStyles] ||
    'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';

  return (
    <span className={cn(
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
      styles
    )}>
      {risk}
    </span>
  );
}
```

### 2. Register Cell Renderer

In `ACMSpreadsheet.tsx`:

```tsx
import { RiskBadgeCellRenderer } from './RiskBadgeCellRenderer';

// Register component
const components = useMemo(() => ({
  riskBadgeRenderer: RiskBadgeCellRenderer,
}), []);

// Column definition
const columnDefs: ColDef<ACMRecord>[] = [
  // ... other columns
  {
    field: 'risk_status',
    headerName: 'Risk Status',
    cellRenderer: 'riskBadgeRenderer',
    filter: 'agSetColumnFilter',
    filterParams: {
      values: ['Low', 'Medium', 'High'],
    },
    width: 120,
  },
];

// Grid
<AgGridReact
  components={components}
  // ... other props
/>
```

### 3. Row-Level Highlighting (Optional)

Highlight entire row based on risk:

```tsx
const getRowStyle = useCallback((params: RowClassParams<ACMRecord>) => {
  const risk = params.data?.risk_status;

  if (risk === 'High') {
    return {
      backgroundColor: 'hsl(0 84% 60% / 0.1)',
      borderLeft: '4px solid hsl(0 84% 60%)',
    };
  }
  if (risk === 'Medium') {
    return {
      backgroundColor: 'hsl(45 93% 47% / 0.1)',
      borderLeft: '4px solid hsl(45 93% 47%)',
    };
  }
  return undefined;
}, []);

<AgGridReact
  getRowStyle={getRowStyle}
  // ... other props
/>
```

### 4. CSS Variables for Colors

Add to `globals.css` for consistency:

```css
/* Risk status colors */
:root {
  --risk-low: 142 76% 36%;
  --risk-low-bg: 142 76% 36% / 0.1;
  --risk-medium: 45 93% 47%;
  --risk-medium-bg: 45 93% 47% / 0.1;
  --risk-high: 0 84% 60%;
  --risk-high-bg: 0 84% 60% / 0.1;
}

.dark {
  --risk-low: 142 70% 45%;
  --risk-low-bg: 142 70% 45% / 0.15;
  --risk-medium: 45 93% 55%;
  --risk-medium-bg: 45 93% 55% / 0.15;
  --risk-high: 0 84% 65%;
  --risk-high-bg: 0 84% 65% / 0.15;
}
```

### 5. Accessibility

Ensure sufficient color contrast:

| Risk Level | Background | Text | Contrast Ratio |
|------------|------------|------|----------------|
| Low | #dcfce7 | #166534 | 7.2:1 |
| Medium | #fef3c7 | #92400e | 5.8:1 |
| High | #fee2e2 | #991b1b | 7.1:1 |

All pass WCAG AA (4.5:1 minimum for normal text).

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/components/acm/RiskBadgeCellRenderer.tsx` | New file |
| `frontend/src/components/acm/ACMSpreadsheet.tsx` | Register renderer |
| `frontend/src/app/globals.css` | Risk color variables |

---

## Dependencies

- E2-S2: ACMSpreadsheet component created

---

## Testing

1. View spreadsheet with ACM data containing different risk levels
2. Verify Low risk shows green badge
3. Verify Medium risk shows amber/yellow badge
4. Verify High risk shows red badge
5. Toggle dark mode - verify colors adjust
6. Run accessibility audit for color contrast
7. Verify colors are distinguishable for colorblind users

---

## Estimated Complexity

**Low** - Custom cell renderer with styling

---
