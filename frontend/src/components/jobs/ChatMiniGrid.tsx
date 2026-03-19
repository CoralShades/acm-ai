'use client'

import React, { useMemo, useCallback, useRef, useState } from 'react'
import { AgGridReact } from 'ag-grid-react'
import type { ColDef, SelectionChangedEvent } from 'ag-grid-community'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { Edit2, Eye } from 'lucide-react'

// Register AG Grid modules (idempotent — safe to call multiple times)
ModuleRegistry.registerModules([AllCommunityModule])

// Fields excluded from auto-derived columns
const EXCLUDED_KEYS = new Set([
  'id',
  'source_id',
  'embedding',
  'embedding_text',
  'embedding_model',
  'embedded_at',
  'enriched_text',
])

interface ChatMiniGridProps {
  data: Record<string, unknown>[]
  onEditRecord?: (recordId: string, row: Record<string, unknown>) => void
  onViewRecord?: (recordId: string, row: Record<string, unknown>) => void
  enableCheckbox?: boolean
  onSelectionChange?: (selectedRows: Record<string, unknown>[]) => void
  onBulkAction?: (selectedIds: string[]) => void
  height?: number
}

/**
 * Compact AG Grid for rendering query results inside chat bubbles.
 * Auto-derives column definitions from the first data row's keys.
 */
export function ChatMiniGrid({
  data,
  onEditRecord,
  onViewRecord,
  enableCheckbox = false,
  onSelectionChange,
  onBulkAction,
  height = 280,
}: ChatMiniGridProps) {
  const gridRef = useRef<AgGridReact<Record<string, unknown>>>(null)
  const [selectedRows, setSelectedRows] = useState<Record<string, unknown>[]>([])

  const columnDefs = useMemo<ColDef<Record<string, unknown>>[]>(() => {
    if (data.length === 0) return []

    const keys = Object.keys(data[0]).filter((k) => !EXCLUDED_KEYS.has(k))

    const dataCols: ColDef<Record<string, unknown>>[] = keys.map((key) => ({
      field: key,
      headerName: key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
      flex: 1,
      minWidth: 90,
      sortable: true,
      filter: false,
      resizable: true,
      valueFormatter: (params) => {
        const val = params.value
        if (val === null || val === undefined) return '—'
        if (typeof val === 'boolean') return val ? 'Yes' : 'No'
        if (typeof val === 'object') return JSON.stringify(val)
        return String(val)
      },
    }))

    // Prepend checkbox selection column when in multi-select mode
    if (enableCheckbox) {
      return [
        {
          checkboxSelection: true,
          headerCheckboxSelection: true,
          width: 40,
          minWidth: 40,
          maxWidth: 40,
          pinned: 'left' as const,
          sortable: false,
          filter: false,
          resizable: false,
          suppressSizeToFit: true,
        },
        ...dataCols,
      ]
    }

    return dataCols
  }, [data, enableCheckbox])

  const defaultColDef = useMemo<ColDef>(
    () => ({
      resizable: true,
      sortable: true,
    }),
    []
  )

  const onSelectionChanged = useCallback(
    (event: SelectionChangedEvent) => {
      const rows = event.api.getSelectedRows() as Record<string, unknown>[]
      setSelectedRows(rows)
      onSelectionChange?.(rows)
    },
    [onSelectionChange]
  )

  const handleEdit = useCallback(() => {
    if (selectedRows.length !== 1) return
    const row = selectedRows[0]
    const id = row.id as string
    if (id && onEditRecord) {
      onEditRecord(id, row)
    }
  }, [selectedRows, onEditRecord])

  const handleView = useCallback(() => {
    if (selectedRows.length !== 1) return
    const row = selectedRows[0]
    const id = row.id as string
    if (id && onViewRecord) {
      onViewRecord(id, row)
    }
  }, [selectedRows, onViewRecord])

  const handleBulkAction = useCallback(() => {
    if (selectedRows.length === 0) return
    const ids = selectedRows
      .map((r) => r.id as string)
      .filter(Boolean)
    onBulkAction?.(ids)
  }, [selectedRows, onBulkAction])

  if (data.length === 0) {
    return (
      <div className="border rounded-lg p-3 my-2 text-sm bg-background text-muted-foreground">
        No data to display.
      </div>
    )
  }

  const hasSingleSelection = !enableCheckbox && selectedRows.length === 1
  const hasCheckboxSelection = enableCheckbox && selectedRows.length > 0

  return (
    <div className="border rounded-lg my-2 bg-background overflow-hidden text-sm">
      {/* AG Grid */}
      <div
        className="ag-theme-quartz"
        style={{ height }}
      >
        <style>{`
          .ag-theme-quartz {
            --ag-font-size: 12px;
            --ag-row-height: 28px;
            --ag-header-height: 30px;
            --ag-header-background-color: hsl(var(--muted));
            --ag-header-foreground-color: hsl(var(--muted-foreground));
            --ag-background-color: hsl(var(--background));
            --ag-foreground-color: hsl(var(--foreground));
            --ag-border-color: hsl(var(--border));
            --ag-row-hover-color: hsl(var(--muted) / 0.5);
            --ag-odd-row-background-color: hsl(var(--muted) / 0.2);
            --ag-cell-horizontal-padding: 8px;
          }
        `}</style>
        <AgGridReact<Record<string, unknown>>
          ref={gridRef}
          rowData={data}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          onSelectionChanged={onSelectionChanged}
          rowSelection={enableCheckbox ? 'multiple' : 'single'}
          suppressRowClickSelection={false}
          domLayout="normal"
          suppressMovableColumns={true}
          suppressColumnVirtualisation={false}
          animateRows={false}
          theme="legacy"
        />
      </div>

      {/* Action bar */}
      {(onEditRecord || onViewRecord || (enableCheckbox && onBulkAction)) && (
        <div className="flex items-center gap-2 px-3 py-2 border-t bg-muted/30">
          {!enableCheckbox && (
            <>
              {onEditRecord && (
                <button
                  type="button"
                  disabled={!hasSingleSelection}
                  onClick={handleEdit}
                  className="inline-flex items-center gap-1 px-2.5 py-1 text-xs border rounded-md transition-colors cursor-pointer hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <Edit2 className="h-3 w-3" />
                  Edit Record
                </button>
              )}
              {onViewRecord && (
                <button
                  type="button"
                  disabled={!hasSingleSelection}
                  onClick={handleView}
                  className="inline-flex items-center gap-1 px-2.5 py-1 text-xs border rounded-md transition-colors cursor-pointer hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  <Eye className="h-3 w-3" />
                  View Detail
                </button>
              )}
              {!hasSingleSelection && (
                <span className="text-xs text-muted-foreground ml-1">
                  Select a row to enable actions
                </span>
              )}
            </>
          )}

          {enableCheckbox && onBulkAction && (
            <>
              <button
                type="button"
                disabled={!hasCheckboxSelection}
                onClick={handleBulkAction}
                className="inline-flex items-center gap-1 px-2.5 py-1 text-xs bg-foreground text-background rounded-md transition-opacity cursor-pointer hover:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Apply to {selectedRows.length > 0 ? selectedRows.length : 0} selected
              </button>
              {!hasCheckboxSelection && (
                <span className="text-xs text-muted-foreground ml-1">
                  Select rows to apply bulk action
                </span>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
