'use client'

import { useCallback, useMemo, useRef, useState, useImperativeHandle, forwardRef, useEffect } from 'react'
import { AgGridReact } from 'ag-grid-react'
import type { ColDef, GridReadyEvent, CellClickedEvent, CellKeyDownEvent, GridApi, ModelUpdatedEvent, ColumnResizedEvent, RowClassParams } from 'ag-grid-community'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { Button } from '@/components/ui/button'
import { Edit2, Trash2 } from 'lucide-react'
import type { ACMRecord } from '@/lib/types/acm'

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule])

const COLUMN_STATE_KEY = 'acm-grid-column-state'

// Expose grid control methods via ref
export interface ACMGridRef {
  expandAll: () => void
  collapseAll: () => void
  resetColumns: () => void
}

// Cell selection details for citation viewer
export interface CellSelectionDetails {
  recordId: string
  field: string
  value: unknown
  pageNumber?: number | null
  record: ACMRecord
}

// Extended record type for preview rows from AG-UI streaming
type ACMGridRecord = ACMRecord & { _is_preview?: boolean }

interface ACMGridProps {
  records: ACMRecord[]
  previewRecords?: ACMRecord[]
  isLoading?: boolean
  onEdit: (record: ACMRecord) => void
  onDelete: (record: ACMRecord) => void
  enableGrouping?: boolean
  // Quick filter search functionality
  quickFilterText?: string
  // Callback to report visible row count changes
  onVisibleCountChange?: (count: number) => void
  // Callback when a cell is selected for citation viewing
  onCellSelect?: (details: CellSelectionDetails) => void
  // Callback when a row is clicked to show record details
  onRowClick?: (record: ACMRecord) => void
  // ID of the currently selected/highlighted record
  selectedRecordId?: string | null
}

// Custom cell renderer for boolean labelled field
function LabelledRenderer({ value }: { value: boolean | null | undefined }) {
  if (value === null || value === undefined) return <span className="text-muted-foreground">-</span>
  return <span>{value ? 'YES' : 'NO'}</span>
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
        aria-label="Edit ACM record"
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
        aria-label="Delete ACM record"
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  )
}

export const ACMGrid = forwardRef<ACMGridRef, ACMGridProps>(function ACMGrid(
  { records, previewRecords, isLoading, onEdit, onDelete, enableGrouping = false, quickFilterText, onVisibleCountChange, onCellSelect, onRowClick, selectedRecordId },
  ref
) {
  const gridRef = useRef<AgGridReact<ACMGridRecord>>(null)
  const [gridApi, setGridApi] = useState<GridApi<ACMGridRecord> | null>(null)

  // Merge saved records with preview (streaming) records
  const mergedRows = useMemo<ACMGridRecord[]>(() => {
    if (!previewRecords || previewRecords.length === 0) return records
    const previewRows: ACMGridRecord[] = previewRecords.map((r, i) => ({
      ...r,
      id: r.id || `_preview_${i}`,
      _is_preview: true,
    }))
    return [...records, ...previewRows]
  }, [records, previewRecords])

  // Expose expand/collapse/resetColumns methods to parent via ref
  useImperativeHandle(ref, () => ({
    expandAll: () => {
      gridApi?.expandAll()
    },
    collapseAll: () => {
      gridApi?.collapseAll()
    },
    resetColumns: () => {
      if (gridApi) {
        localStorage.removeItem(COLUMN_STATE_KEY)
        gridApi.resetColumnState()
      }
    },
  }), [gridApi])

  // Apply quick filter when search text changes
  useEffect(() => {
    if (gridApi) {
      gridApi.setGridOption('quickFilterText', quickFilterText || '')
    }
  }, [gridApi, quickFilterText])

  // Restore saved column state from localStorage on grid ready
  const onGridReady = useCallback((params: GridReadyEvent<ACMRecord>) => {
    setGridApi(params.api)
    const savedState = localStorage.getItem(COLUMN_STATE_KEY)
    if (savedState) {
      try {
        params.api.applyColumnState({ state: JSON.parse(savedState), applyOrder: true })
      } catch {
        localStorage.removeItem(COLUMN_STATE_KEY)
      }
    }
  }, [])

  // Save column state to localStorage when user finishes resizing
  const onColumnResized = useCallback((event: ColumnResizedEvent) => {
    if (event.finished && event.source === 'uiColumnResized') {
      const state = event.api.getColumnState()
      localStorage.setItem(COLUMN_STATE_KEY, JSON.stringify(state))
    }
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

  // Redraw rows when selected record changes to update highlighting
  useEffect(() => {
    if (gridApi) {
      gridApi.redrawRows()
    }
  }, [gridApi, selectedRecordId])

  // Apply highlight class to selected row and preview styling
  const getRowClass = useCallback(
    (params: RowClassParams<ACMGridRecord>) => {
      const classes: string[] = []
      if ((params.data as ACMGridRecord)?._is_preview) {
        classes.push('acm-row-preview')
      }
      if (params.data?.id && params.data.id === selectedRecordId) {
        classes.push('acm-row-selected')
      }
      return classes.length > 0 ? classes.join(' ') : undefined
    },
    [selectedRecordId]
  )

  const columnDefs = useMemo<ColDef<ACMRecord>[]>(
    () => [
      {
        field: 'building_id',
        headerName: 'Building Code',
        headerTooltip: 'Building code identifier',
        width: 120,
        sortable: true,
        filter: true,
        ...(enableGrouping && { rowGroup: true }),
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
        headerName: 'Building Name',
        width: 180,
        sortable: true,
        filter: true,
        hide: enableGrouping,
      },
      {
        field: 'room_id',
        headerName: 'Room ID',
        headerTooltip: 'Room identifier and name',
        width: 100,
        sortable: true,
        filter: true,
        ...(enableGrouping && { rowGroup: true }),
        hide: true, // Hidden by default — accessible via detail view
        valueFormatter: (params) => {
          if (params.data?.room_name) {
            return `${params.value} - ${params.data.room_name}`
          }
          return params.value || 'No Room'
        },
      },
      {
        field: 'room_name',
        headerName: 'Room Name',
        width: 160,
        sortable: true,
        filter: true,
        hide: enableGrouping,
      },
      {
        field: 'product',
        headerName: 'ACM Name',
        headerTooltip: 'Asbestos containing material name',
        width: 160,
        sortable: true,
        filter: true,
      },
      {
        field: 'acm_product_type',
        headerName: 'ACM Product Type',
        headerTooltip: 'AI-classified product type (falls back to raw description)',
        flex: 1,
        minWidth: 250,
        sortable: true,
        filter: true,
        valueGetter: (params) => {
          return params.data?.acm_product_type || params.data?.material_description || ''
        },
      },
      {
        field: 'result',
        headerName: 'Result',
        width: 130,
        sortable: true,
        filter: true,
      },
      {
        field: 'friable',
        headerName: 'Friability',
        width: 100,
        sortable: true,
        filter: true,
      },
      {
        field: 'material_condition',
        headerName: 'Condition',
        width: 110,
        sortable: true,
        filter: true,
        hide: true, // Hidden by default — accessible via detail view
      },
      {
        field: 'area_type',
        headerName: 'Internal/External',
        width: 130,
        sortable: true,
        filter: true,
      },
      {
        field: 'hygienist_recommendations',
        headerName: 'Hygienist Recommendations',
        width: 200,
        sortable: true,
        filter: true,
      },
      {
        field: 'page_number',
        headerName: 'Page',
        width: 70,
        sortable: true,
      },
      // BAR Compliance Fields
      {
        headerName: 'BAR Compliance',
        children: [
          {
            field: 'sample_no',
            headerName: 'Sample No',
            headerTooltip: 'Sample identification number',
            width: 120,
            sortable: true,
            filter: true,
          },
          {
            field: 'sample_result',
            headerName: 'Sample Result',
            headerTooltip: 'Laboratory sample result',
            width: 130,
            sortable: true,
            filter: true,
          },
          {
            field: 'quantity',
            headerName: 'Quantity',
            headerTooltip: 'Quantity of ACM present',
            width: 100,
            sortable: true,
            filter: true,
          },
          {
            field: 'floor_level',
            headerName: 'Floor Level',
            headerTooltip: 'Floor or level location',
            width: 110,
            sortable: true,
            filter: true,
          },
          {
            field: 'acm_labelled',
            headerName: 'Labelled',
            headerTooltip: 'Whether ACM is labelled',
            width: 90,
            sortable: true,
            filter: true,
            hide: true,
            cellRenderer: LabelledRenderer,
          },
          {
            field: 'identifying_company',
            headerName: 'Identifying Company',
            headerTooltip: 'Company that identified the ACM',
            width: 180,
            sortable: true,
            filter: true,
            hide: true,
          },
          {
            field: 'acm_product_group',
            headerName: 'Product Group',
            headerTooltip: 'ACM product group classification',
            width: 150,
            sortable: true,
            filter: true,
            hide: true,
          },
        ],
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
      // Skip if clicking on Actions column or group row
      if (event.colDef.headerName === 'Actions' || event.node.group || !event.data) {
        return
      }

      const field = event.colDef?.field
      if (!field) return

      // Guard: Skip if record has no ID (unsaved records)
      const recordId = event.data.id
      if (!recordId) return

      // Row click opens detail dialog if handler is provided
      if (onRowClick) {
        onRowClick(event.data)
      } else if (onCellSelect) {
        // Fallback: use cell selection for citation viewing
        onCellSelect({
          recordId,
          field: field,
          value: event.value,
          pageNumber: event.data.page_number,
          record: event.data,
        })
      } else {
        // Final fallback to edit behavior
        onEdit(event.data)
      }
    },
    [onEdit, onCellSelect, onRowClick]
  )

  // Keyboard navigation: Enter, Space, E, Delete key handlers
  const onCellKeyDown = useCallback(
    (event: CellKeyDownEvent<ACMRecord>) => {
      const keyboardEvent = event.event as KeyboardEvent
      const key = keyboardEvent?.key

      if (!key || !event.data) return

      // Enter key: Open detail dialog or fallback to citation/edit
      if (key === 'Enter' && !event.node.group) {
        const field = event.colDef?.field
        const recordId = event.data.id
        if (field && event.colDef?.headerName !== 'Actions' && recordId) {
          if (onRowClick) {
            onRowClick(event.data)
          } else if (onCellSelect) {
            onCellSelect({
              recordId,
              field: field,
              value: event.value,
              pageNumber: event.data.page_number,
              record: event.data,
            })
          } else {
            onEdit(event.data)
          }
        }
      }

      // Space key: Expand/collapse group row
      if (key === ' ' && event.node.group) {
        keyboardEvent.preventDefault()
        event.node.setExpanded(!event.node.expanded)
      }

      // E key: Edit record (when not in group row)
      if (key === 'e' && !event.node.group && event.data.id) {
        keyboardEvent.preventDefault()
        onEdit(event.data)
      }

      // Delete key: Delete record (when not in group row)
      if (key === 'Delete' && !event.node.group && event.data.id) {
        keyboardEvent.preventDefault()
        onDelete(event.data)
      }
    },
    [onEdit, onDelete, onCellSelect, onRowClick]
  )

  return (
    <div
      className="ag-theme-alpine h-[calc(100vh-200px)] min-h-[500px] w-full"
      role="region"
      aria-label="ACM Records Data Grid - Use arrow keys to navigate, Enter to view details"
    >
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
        /* Clickable row cursor */
        .ag-theme-alpine .ag-row:not(.ag-row-group) {
          cursor: pointer;
        }
        /* Selected row highlight for detail panel */
        .ag-theme-alpine .acm-row-selected {
          background-color: hsl(var(--primary) / 0.12) !important;
          border-left: 3px solid hsl(var(--primary)) !important;
        }
        .dark .ag-theme-alpine .acm-row-selected {
          background-color: hsl(var(--primary) / 0.2) !important;
        }
        /* Preview/streaming row styling (E17-S2) */
        .ag-theme-alpine .acm-row-preview {
          font-style: italic;
          opacity: 0.75;
          border-left: 3px solid hsl(var(--primary) / 0.5) !important;
          animation: acm-preview-pulse 2s ease-in-out infinite;
        }
        @keyframes acm-preview-pulse {
          0%, 100% { border-left-color: hsl(var(--primary) / 0.3); }
          50% { border-left-color: hsl(var(--primary)); }
        }
      `}</style>
      <AgGridReact<ACMGridRecord>
        ref={gridRef}
        rowData={mergedRows}
        columnDefs={columnDefs}
        defaultColDef={defaultColDef}
        onGridReady={onGridReady}
        onCellClicked={onCellClicked}
        onCellKeyDown={onCellKeyDown}
        onModelUpdated={onModelUpdated}
        onColumnResized={onColumnResized}
        getRowClass={getRowClass}
        loading={isLoading}
        animateRows={true}
        rowSelection="single"
        suppressRowClickSelection={true}
        pagination={true}
        paginationPageSize={50}
        paginationPageSizeSelector={[20, 50, 100]}
        domLayout="normal"
        alwaysShowHorizontalScroll={true}
        tooltipShowDelay={300}
        // Row grouping configuration (enterprise-only, conditionally applied)
        {...(enableGrouping ? {
          groupDisplayType: 'groupRows' as const,
          groupDefaultExpanded: 1,
          autoGroupColumnDef: autoGroupColumnDef,
          suppressAggFuncInHeader: true,
        } : {})}
        // Use legacy theming for v32 CSS compatibility (ag-theme-alpine)
        theme="legacy"
      />
      <div className="text-xs text-muted-foreground mt-2 flex items-center gap-4">
        <span>Arrow keys to navigate</span>
        <span>Enter to view</span>
        <span>E to edit</span>
        <span>Space to expand/collapse</span>
        <span>? for all shortcuts</span>
      </div>
    </div>
  )
})
