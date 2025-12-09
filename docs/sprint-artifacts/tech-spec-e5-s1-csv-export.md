# Tech Spec: E5-S1 - Implement CSV Export

> **Story:** E5-S1
> **Epic:** Export Functionality
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Add CSV export functionality to the ACM spreadsheet, allowing users to download the currently visible/filtered data.

---

## User Story

**As a** user
**I want** to download ACM data as CSV
**So that** I can use it in other tools

---

## Acceptance Criteria

- [ ] Export button in spreadsheet toolbar
- [ ] Exports currently filtered/visible data
- [ ] File named with source name and date
- [ ] All columns included with proper headers
- [ ] UTF-8 encoding for special characters

---

## Technical Design

### 1. Export Button in Toolbar

Add to `ACMSpreadsheet.tsx`:

```tsx
import { Download } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function ACMSpreadsheet({ sourceId, sourceName }: Props) {
  const gridRef = useRef<AgGridReact>(null);

  const exportToCsv = useCallback(() => {
    if (!gridRef.current?.api) return;

    const timestamp = new Date().toISOString().split('T')[0];
    const fileName = `${sourceName || 'acm-data'}-${timestamp}.csv`;

    gridRef.current.api.exportDataAsCsv({
      fileName,
      columnSeparator: ',',
      suppressQuotes: false,
      // Only export visible columns
      columnKeys: gridRef.current.api
        .getAllDisplayedColumns()
        .map(col => col.getColId()),
    });
  }, [sourceName]);

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-2 p-3 border-b">
        {/* Search and other controls... */}

        <div className="ml-auto">
          <Button variant="outline" size="sm" onClick={exportToCsv}>
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Grid */}
      <div className="ag-theme-custom flex-1">
        <AgGridReact ref={gridRef} ... />
      </div>
    </div>
  );
}
```

### 2. Custom CSV Export Options

For more control over the export:

```tsx
const exportToCsv = useCallback(() => {
  if (!gridRef.current?.api) return;

  const timestamp = new Date().toISOString().split('T')[0];
  const fileName = `${sourceName || 'acm-data'}-${timestamp}.csv`;

  gridRef.current.api.exportDataAsCsv({
    fileName,
    columnSeparator: ',',
    suppressQuotes: false,

    // Custom header names
    processCellCallback: (params) => {
      // Format dates
      if (params.column.getColId() === 'created_at') {
        return new Date(params.value).toLocaleDateString();
      }
      return params.value;
    },

    // Skip internal columns
    shouldRowBeSkipped: (params) => {
      return params.node.group; // Skip group rows
    },

    // Custom headers
    processHeaderCallback: (params) => {
      const headerMap: Record<string, string> = {
        'school_name': 'School Name',
        'building_id': 'Building ID',
        'building_name': 'Building Name',
        'room_id': 'Room ID',
        'product': 'Product/Material',
        'material_description': 'Description',
        'friable': 'Friable',
        'material_condition': 'Condition',
        'risk_status': 'Risk Status',
        'result': 'Result',
        'page_number': 'Source Page',
      };
      return headerMap[params.column.getColId()] || params.column.getColId();
    },
  });
}, [sourceName]);
```

### 3. Alternative: Backend Export

If client-side export has issues, use backend:

```python
# api/routers/acm.py
from fastapi.responses import StreamingResponse
import csv
import io

@router.get("/acm/export/csv")
async def export_acm_csv(
    source_id: str,
    building_id: Optional[str] = None,
    risk_status: Optional[str] = None,
):
    """Export ACM records as CSV."""
    records = await ACMRecord.get_by_source(source_id)

    # Apply filters
    if building_id:
        records = [r for r in records if r.building_id == building_id]
    if risk_status:
        records = [r for r in records if r.risk_status == risk_status]

    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Headers
    headers = [
        'School Name', 'Building ID', 'Building Name', 'Room ID',
        'Product', 'Material Description', 'Extent', 'Location',
        'Friable', 'Condition', 'Risk Status', 'Result', 'Page'
    ]
    writer.writerow(headers)

    # Data rows
    for r in records:
        writer.writerow([
            r.school_name, r.building_id, r.building_name, r.room_id,
            r.product, r.material_description, r.extent, r.location,
            r.friable, r.material_condition, r.risk_status, r.result,
            r.page_number
        ])

    output.seek(0)

    # Get source name for filename
    source = await Source.get(source_id)
    filename = f"{source.title or 'acm-data'}-{date.today()}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

Frontend call:

```tsx
const exportViaBackend = async () => {
  const url = `/api/acm/export/csv?source_id=${sourceId}`;
  window.location.href = url;
};
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/components/acm/ACMSpreadsheet.tsx` | Add export button |
| `api/routers/acm.py` | Add CSV export endpoint (optional) |

---

## Dependencies

- E2-S2: ACMSpreadsheet component created

---

## Testing

1. Click Export CSV button
2. Verify file downloads with correct name
3. Open CSV in Excel - verify UTF-8 encoding
4. Verify all columns have proper headers
5. Apply filter, export - verify only filtered rows exported
6. Verify group rows not included in export

---

## Estimated Complexity

**Low** - Uses AG Grid built-in export or simple backend endpoint

---
