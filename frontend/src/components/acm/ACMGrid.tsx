'use client'

import { useCallback, useMemo, useRef, useState } from 'react'
import { AgGridReact } from 'ag-grid-react'
import type { ColDef, GridReadyEvent, CellClickedEvent, GridApi } from 'ag-grid-community'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Edit2, Trash2 } from 'lucide-react'
import type { ACMRecord } from '@/lib/types/acm'

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule])

interface ACMGridProps {
  records: ACMRecord[]
  isLoading?: boolean
  onEdit: (record: ACMRecord) => void
  onDelete: (record: ACMRecord) => void
}

// Custom cell renderer for risk status
function RiskStatusRenderer({ value }: { value: string | null | undefined }) {
  if (!value) return null

  const variants: Record<string, string> = {
    High: 'bg-red-100 text-red-800 hover:bg-red-200',
    Medium: 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200',
    Low: 'bg-green-100 text-green-800 hover:bg-green-200',
  }

  return (
    <Badge variant="secondary" className={variants[value] || ''}>
      {value}
    </Badge>
  )
}

// Custom cell renderer for actions
function ActionsRenderer({
  data,
  onEdit,
  onDelete,
}: {
  data: ACMRecord
  onEdit: (record: ACMRecord) => void
  onDelete: (record: ACMRecord) => void
}) {
  return (
    <div className="flex gap-1">
      <Button
        variant="ghost"
        size="icon"
        className="h-7 w-7"
        onClick={(e) => {
          e.stopPropagation()
          onEdit(data)
        }}
      >
        <Edit2 className="h-4 w-4" />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        className="h-7 w-7 text-destructive hover:text-destructive"
        onClick={(e) => {
          e.stopPropagation()
          onDelete(data)
        }}
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  )
}

export function ACMGrid({ records, isLoading, onEdit, onDelete }: ACMGridProps) {
  const gridRef = useRef<AgGridReact<ACMRecord>>(null)
  const [gridApi, setGridApi] = useState<GridApi<ACMRecord> | null>(null)

  const onGridReady = useCallback((params: GridReadyEvent<ACMRecord>) => {
    setGridApi(params.api)
    params.api.sizeColumnsToFit()
  }, [])

  const columnDefs = useMemo<ColDef<ACMRecord>[]>(
    () => [
      {
        field: 'building_id',
        headerName: 'Building ID',
        width: 110,
        sortable: true,
        filter: true,
      },
      {
        field: 'building_name',
        headerName: 'Building',
        width: 150,
        sortable: true,
        filter: true,
      },
      {
        field: 'room_id',
        headerName: 'Room ID',
        width: 100,
        sortable: true,
        filter: true,
      },
      {
        field: 'room_name',
        headerName: 'Room',
        width: 130,
        sortable: true,
        filter: true,
      },
      {
        field: 'product',
        headerName: 'Product',
        width: 140,
        sortable: true,
        filter: true,
      },
      {
        field: 'material_description',
        headerName: 'Description',
        flex: 1,
        minWidth: 200,
        sortable: true,
        filter: true,
      },
      {
        field: 'risk_status',
        headerName: 'Risk',
        width: 100,
        sortable: true,
        filter: true,
        cellRenderer: RiskStatusRenderer,
      },
      {
        field: 'result',
        headerName: 'Result',
        width: 100,
        sortable: true,
        filter: true,
      },
      {
        field: 'friable',
        headerName: 'Friable',
        width: 100,
        sortable: true,
        filter: true,
      },
      {
        field: 'material_condition',
        headerName: 'Condition',
        width: 100,
        sortable: true,
        filter: true,
      },
      {
        field: 'page_number',
        headerName: 'Page',
        width: 70,
        sortable: true,
      },
      {
        headerName: 'Actions',
        width: 90,
        pinned: 'right',
        cellRenderer: (params: { data: ACMRecord }) =>
          params.data ? (
            <ActionsRenderer data={params.data} onEdit={onEdit} onDelete={onDelete} />
          ) : null,
        sortable: false,
        filter: false,
      },
    ],
    [onEdit, onDelete]
  )

  const defaultColDef = useMemo<ColDef>(
    () => ({
      resizable: true,
      suppressMenu: true,
    }),
    []
  )

  const onCellClicked = useCallback(
    (event: CellClickedEvent<ACMRecord>) => {
      if (event.colDef.headerName !== 'Actions' && event.data) {
        onEdit(event.data)
      }
    },
    [onEdit]
  )

  return (
    <div className="ag-theme-alpine h-[500px] w-full">
      <style jsx global>{`
        .ag-theme-alpine {
          --ag-header-background-color: hsl(var(--muted));
          --ag-odd-row-background-color: hsl(var(--muted) / 0.3);
          --ag-row-hover-color: hsl(var(--muted));
          --ag-border-color: hsl(var(--border));
          --ag-header-foreground-color: hsl(var(--foreground));
          --ag-foreground-color: hsl(var(--foreground));
          --ag-background-color: hsl(var(--background));
        }
        .dark .ag-theme-alpine {
          --ag-header-background-color: hsl(var(--muted));
          --ag-odd-row-background-color: hsl(var(--muted) / 0.3);
          --ag-row-hover-color: hsl(var(--muted));
        }
      `}</style>
      <AgGridReact<ACMRecord>
        ref={gridRef}
        rowData={records}
        columnDefs={columnDefs}
        defaultColDef={defaultColDef}
        onGridReady={onGridReady}
        onCellClicked={onCellClicked}
        loading={isLoading}
        animateRows={true}
        rowSelection="single"
        suppressRowClickSelection={true}
        pagination={true}
        paginationPageSize={50}
        paginationPageSizeSelector={[20, 50, 100]}
        domLayout="normal"
      />
    </div>
  )
}
