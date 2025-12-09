# Tech Spec: E5-S2 - Implement Excel Export

> **Story:** E5-S2
> **Epic:** Export Functionality
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Add Excel (.xlsx) export functionality with formatting, including auto-sized columns, formatted headers, and optional risk status color coding.

---

## User Story

**As a** user
**I want** to download ACM data as Excel
**So that** I get formatted spreadsheet

---

## Acceptance Criteria

- [ ] Export as .xlsx option
- [ ] Column widths auto-sized
- [ ] Header row formatted
- [ ] Risk status cells color-coded (if possible)

---

## Technical Design

### 1. Backend Excel Export with openpyxl

Install dependency:
```bash
uv add openpyxl
```

Create export endpoint in `api/routers/acm.py`:

```python
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import io

# Risk status colors
RISK_COLORS = {
    'Low': 'C6EFCE',      # Green
    'Medium': 'FFEB9C',   # Yellow
    'High': 'FFC7CE',     # Red
}

@router.get("/acm/export/excel")
async def export_acm_excel(source_id: str):
    """Export ACM records as formatted Excel file."""
    records = await ACMRecord.get_by_source(source_id)
    source = await Source.get(source_id)

    # Create workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "ACM Register"

    # Define columns
    columns = [
        ('School Name', 'school_name', 25),
        ('Building ID', 'building_id', 12),
        ('Building Name', 'building_name', 20),
        ('Room ID', 'room_id', 10),
        ('Product', 'product', 20),
        ('Material Description', 'material_description', 35),
        ('Extent', 'extent', 15),
        ('Location', 'location', 20),
        ('Friable', 'friable', 12),
        ('Condition', 'material_condition', 12),
        ('Risk Status', 'risk_status', 12),
        ('Result', 'result', 15),
        ('Page', 'page_number', 8),
    ]

    # Header styles
    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
    header_alignment = Alignment(horizontal='center', vertical='center')
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Write headers
    for col_idx, (header, _, width) in enumerate(columns, 1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    # Write data rows
    for row_idx, record in enumerate(records, 2):
        for col_idx, (_, field, _) in enumerate(columns, 1):
            value = getattr(record, field, None)
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.border = thin_border

            # Color code risk status
            if field == 'risk_status' and value in RISK_COLORS:
                cell.fill = PatternFill(
                    start_color=RISK_COLORS[value],
                    end_color=RISK_COLORS[value],
                    fill_type='solid'
                )

    # Freeze header row
    ws.freeze_panes = 'A2'

    # Auto-filter
    ws.auto_filter.ref = ws.dimensions

    # Save to bytes
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"{source.title or 'acm-data'}-{date.today()}.xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

### 2. Frontend Export Button

Add Excel option to toolbar:

```tsx
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Download, FileSpreadsheet, FileText } from 'lucide-react';

export function ExportDropdown({ sourceId, sourceName }: Props) {
  const exportCsv = () => {
    // AG Grid export
    gridRef.current?.api.exportDataAsCsv({ ... });
  };

  const exportExcel = () => {
    // Backend export
    window.location.href = `/api/acm/export/excel?source_id=${sourceId}`;
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm">
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuItem onClick={exportCsv}>
          <FileText className="w-4 h-4 mr-2" />
          Export as CSV
        </DropdownMenuItem>
        <DropdownMenuItem onClick={exportExcel}>
          <FileSpreadsheet className="w-4 h-4 mr-2" />
          Export as Excel
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

### 3. Include Summary Sheet (Optional)

Add a summary sheet to the Excel file:

```python
# Create summary sheet
ws_summary = wb.create_sheet("Summary", 0)

# Risk distribution
risk_counts = {}
for r in records:
    risk = r.risk_status or 'Unknown'
    risk_counts[risk] = risk_counts.get(risk, 0) + 1

ws_summary['A1'] = 'Risk Status Summary'
ws_summary['A1'].font = Font(bold=True, size=14)

row = 3
for risk, count in sorted(risk_counts.items()):
    ws_summary.cell(row=row, column=1, value=risk)
    ws_summary.cell(row=row, column=2, value=count)
    row += 1

# Building distribution
ws_summary.cell(row=row + 1, column=1, value='Building Summary')
ws_summary.cell(row=row + 1, column=1).font = Font(bold=True, size=14)

building_counts = {}
for r in records:
    building_counts[r.building_id] = building_counts.get(r.building_id, 0) + 1

row += 3
for building, count in sorted(building_counts.items()):
    ws_summary.cell(row=row, column=1, value=building)
    ws_summary.cell(row=row, column=2, value=count)
    row += 1
```

---

## File Changes

| File | Change |
|------|--------|
| `pyproject.toml` | Add openpyxl dependency |
| `api/routers/acm.py` | Add Excel export endpoint |
| `frontend/src/components/acm/ACMSpreadsheet.tsx` | Add export dropdown |

---

## Dependencies

- E5-S1: CSV export (shared UI components)

---

## Testing

1. Click Export → Excel
2. Verify .xlsx file downloads
3. Open in Excel - verify formatting
4. Check header row is bold with background color
5. Verify risk status cells are color-coded
6. Verify column widths are reasonable
7. Check auto-filter is enabled
8. Verify frozen header row

---

## Notes

- openpyxl is pure Python, no external dependencies
- Consider adding export progress for large datasets
- May defer detailed formatting to post-MVP

---

## Estimated Complexity

**Medium** - Requires backend implementation with openpyxl

---
