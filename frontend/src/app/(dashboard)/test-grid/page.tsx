'use client';

import { DataGrid } from '@/components/ui/data-grid';
import { ColDef } from 'ag-grid-community';

const testData = [
  { id: 1, building: 'Admin Block', room: 'A101', product: 'Floor Tiles', risk: 'Low' },
  { id: 2, building: 'Admin Block', room: 'A102', product: 'Ceiling Tiles', risk: 'Medium' },
  { id: 3, building: 'Science Wing', room: 'S201', product: 'Pipe Lagging', risk: 'High' },
  { id: 4, building: 'Main Building', room: 'M101', product: 'Vinyl Flooring', risk: 'Low' },
  { id: 5, building: 'Gymnasium', room: 'G001', product: 'Insulation Board', risk: 'Medium' },
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
      <p className="text-muted-foreground mb-4">
        This page verifies that AG Grid is properly installed and configured.
      </p>
      <DataGrid
        rowData={testData}
        columnDefs={columns}
        height={400}
      />
    </div>
  );
}
