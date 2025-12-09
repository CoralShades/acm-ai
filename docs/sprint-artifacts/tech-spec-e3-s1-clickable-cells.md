# Tech Spec: E3-S1 - Make Cells Clickable

> **Story:** E3-S1
> **Epic:** Cell Citations & PDF Viewer
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Make ACM spreadsheet cells clickable so users can click on any cell to view its source citation in the PDF viewer.

---

## User Story

**As a** user
**I want** to click a cell to see its source
**So that** I can verify the extracted data

---

## Acceptance Criteria

- [ ] All cells have click handler
- [ ] Click event includes record ID and field name
- [ ] Visual feedback on hover (cursor change)
- [ ] Click opens citation modal

---

## Technical Design

### 1. Cell Click Handler

In `ACMSpreadsheet.tsx`:

```tsx
import { CellClickedEvent } from 'ag-grid-community';

export function ACMSpreadsheet({ sourceId }: Props) {
  const [selectedCell, setSelectedCell] = useState<{
    recordId: string;
    field: string;
    value: any;
    pageNumber?: number;
  } | null>(null);

  const onCellClicked = useCallback((event: CellClickedEvent<ACMRecord>) => {
    // Skip if clicking on group row or no data
    if (event.node.group || !event.data) return;

    // Get field and record info
    const field = event.colDef?.field;
    if (!field) return;

    setSelectedCell({
      recordId: event.data.id!,
      field: field,
      value: event.value,
      pageNumber: event.data.page_number,
    });
  }, []);

  return (
    <>
      <div className="ag-theme-custom flex-1">
        <AgGridReact
          onCellClicked={onCellClicked}
          // ... other props
        />
      </div>

      {/* Citation Modal */}
      {selectedCell && (
        <ACMCellViewer
          sourceId={sourceId}
          recordId={selectedCell.recordId}
          field={selectedCell.field}
          value={selectedCell.value}
          pageNumber={selectedCell.pageNumber}
          onClose={() => setSelectedCell(null)}
        />
      )}
    </>
  );
}
```

### 2. Cursor Styling

Add CSS for clickable cells:

```css
/* Clickable cells */
.ag-theme-custom .ag-cell {
  cursor: pointer;
}

.ag-theme-custom .ag-cell:hover {
  background-color: hsl(var(--accent) / 0.3);
}

/* Visual indicator for clickable cells */
.ag-theme-custom .ag-cell::after {
  content: '';
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background-color: hsl(var(--primary) / 0.3);
  opacity: 0;
  transition: opacity 0.2s;
}

.ag-theme-custom .ag-cell:hover::after {
  opacity: 1;
}
```

### 3. Cell Renderer with Click Indicator

Optional: Create a cell renderer that shows a citation icon:

```tsx
import { ExternalLink } from 'lucide-react';

export function CitableCellRenderer(props: ICellRendererParams) {
  const hasPageNumber = props.data?.page_number != null;

  return (
    <div className="flex items-center justify-between w-full group">
      <span className="truncate">{props.value}</span>
      {hasPageNumber && (
        <ExternalLink
          className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity"
        />
      )}
    </div>
  );
}
```

### 4. Keyboard Navigation

Support Enter key to activate cell:

```tsx
const onCellKeyDown = useCallback((event: CellKeyDownEvent<ACMRecord>) => {
  if (event.event?.key === 'Enter' && event.data) {
    const field = event.colDef?.field;
    if (field) {
      setSelectedCell({
        recordId: event.data.id!,
        field: field,
        value: event.value,
        pageNumber: event.data.page_number,
      });
    }
  }
}, []);

<AgGridReact
  onCellKeyDown={onCellKeyDown}
  // ... other props
/>
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/components/acm/ACMSpreadsheet.tsx` | Add cell click handler |
| `frontend/src/components/acm/CitableCellRenderer.tsx` | New (optional) |
| `frontend/src/app/globals.css` | Clickable cell styles |

---

## Dependencies

- E2-S2: ACMSpreadsheet component created

---

## Testing

1. Click on any cell - verify modal opens
2. Verify correct record ID passed to modal
3. Verify correct field name passed to modal
4. Hover over cell - verify cursor changes
5. Test keyboard Enter key on focused cell
6. Verify group rows are not clickable
7. Verify page number passed when available

---

## Estimated Complexity

**Low** - AG Grid onCellClicked event handling

---
