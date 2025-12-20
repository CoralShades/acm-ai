'use client'

import { useCallback, useMemo, useRef, useState, useImperativeHandle, forwardRef, useEffect } from 'react'
import { AgGridReact } from 'ag-grid-react'
import type { ColDef, GridReadyEvent, CellClickedEvent, GridApi, ModelUpdatedEvent } from 'ag-grid-community'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Edit2, Trash2 } from 'lucide-react'
import type { ACMRecord } from '@/lib/types/acm'

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule])

// Expose grid control methods via ref
export interface ACMGridRef {
  expandAll: () => void
  collapseAll: () => void
}

interface ACMGridProps {
  records: ACMRecord[]
  isLoading?: boolean
  onEdit: (record: ACMRecord) => void
  onDelete: (record: ACMRecord) => void
  enableGrouping?: boolean
  // Quick filter search functionality
  quickFilterText?: string
  // Callback to report visible row count changes
  onVisibleCountChange?: (count: number) => void
}

// Custom cell renderer for risk status with theme-aware colors
function RiskStatusRenderer({ value }: { value: string | null | undefined }) {
  if (!value) return null

  const variants: Record<string, string> = {
    High: 'bg-risk-high-bg text-risk-high-foreground',
    Medium: 'bg-risk-medium-bg text-risk-medium-foreground',
    Low: 'bg-risk-low-bg text-risk-low-foreground',
    Presumed: 'bg-risk-presumed-bg text-risk-presumed-foreground',
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

export const ACMGrid = forwardRef<ACMGridRef, ACMGridProps>(function ACMGrid(
  { records, isLoading, onEdit, onDelete, enableGrouping = true, quickFilterText, onVisibleCountChange },
  ref
) {
  const gridRef = useRef<AgGridReact<ACMRecord>>(null)
  const [gridApi, setGridApi] = useState<GridApi<ACMRecord> | null>(null)

  // Expose expand/collapse methods to parent via ref
  useImperativeHandle(ref, () => ({
    expandAll: () => {
      gridApi?.expandAll()
    },
    collapseAll: () => {
      gridApi?.collapseAll()
    },
  }), [gridApi])

  // Apply quick filter when search text changes
  useEffect(() => {
    if (gridApi) {
      gridApi.setGridOption('quickFilterText', quickFilterText || '')
    }
  }, [gridApi, quickFilterText])

  const onGridReady = useCallback((params: GridReadyEvent<ACMRecord>) => {
    setGridApi(params.api)
    params.api.sizeColumnsToFit()
  }, [])

  // Track visible row count changes for result count display
  // Count only data rows, not group header rows
  const onModelUpdated = useCallback((event: ModelUpdatedEvent<ACMRecord>) => {
    if (onVisibleCountChange && event.api) {
      let dataRowCount = 0
      event.api.forEachNodeAfterFilterAndSort((node) => {
        // Only count leaf nodes (actual data rows), not group rows
        if (!node.group) {
          dataRowCount++
        }
      })
      onVisibleCountChange(dataRowCount)
    }
  }, [onVisibleCountChange])

  const columnDefs = useMemo<ColDef<ACMRecord>[]>(
    () => [
      {
        field: 'building_id',
        headerName: 'Building ID',
        width: 110,
        sortable: true,
        filter: true,
        rowGroup: enableGrouping,
        hide: enableGrouping,
        valueFormatter: (params) => {
          if (params.data?.building_name) {
            return `${params.value} - ${params.data.building_name}`
          }
          return params.value || 'Unknown Building'
        },
      },
      {
        field: 'building_name',
        headerName: 'Building',
        width: 150,
        sortable: true,
        filter: true,
        hide: enableGrouping,
      },
      {
        field: 'room_id',
        headerName: 'Room ID',
        width: 100,
        sortable: true,
        filter: true,
        rowGroup: enableGrouping,
        hide: enableGrouping,
        valueFormatter: (params) => {
          if (params.data?.room_name) {
            return `${params.value} - ${params.data.room_name}`
          }
          return params.value || 'No Room'
        },
      },
      {
        field: 'room_name',
        headerName: 'Room',
        width: 130,
        sortable: true,
        filter: true,
        hide: enableGrouping,
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
    [onEdit, onDelete, enableGrouping]
  )

  const defaultColDef = useMemo<ColDef>(
    () => ({
      resizable: true,
      suppressMenu: true,
    }),
    []
  )

  // Auto group column definition for the grouped hierarchy
  const autoGroupColumnDef = useMemo(() => ({
    headerName: 'Location',
    minWidth: 280,
    cellRendererParams: {
      suppressCount: false,
    },
  }), [])

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
        /* Group row styling */
        .ag-theme-alpine .ag-row-group {
          background-color: hsl(var(--muted) / 0.7);
          font-weight: 600;
        }
        .ag-theme-alpine .ag-row-group-expanded {
          border-bottom: 2px solid hsl(var(--border));
        }
        /* Group row level indentation */
        .ag-theme-alpine .ag-row-level-1 .ag-group-value {
          padding-left: 8px;
        }
        .ag-theme-alpine .ag-row-level-2 .ag-group-value {
          padding-left: 16px;
        }
      `}</style>
      <AgGridReact<ACMRecord>
        ref={gridRef}
        rowData={records}
        columnDefs={columnDefs}
        defaultColDef={defaultColDef}
        onGridReady={onGridReady}
        onCellClicked={onCellClicked}
        onModelUpdated={onModelUpdated}
        loading={isLoading}
        animateRows={true}
        rowSelection="single"
        suppressRowClickSelection={true}
        pagination={true}
        paginationPageSize={50}
        paginationPageSizeSelector={[20, 50, 100]}
        domLayout="normal"
        // Row grouping configuration
        groupDisplayType={enableGrouping ? 'groupRows' : undefined}
        groupDefaultExpanded={1}
        autoGroupColumnDef={enableGrouping ? autoGroupColumnDef : undefined}
        suppressAggFuncInHeader={true}
      />
    </div>
  )
})
