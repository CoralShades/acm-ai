'use client'

import { useMemo, useCallback, useState } from 'react'
import { AgGridReact } from 'ag-grid-react'
import type { ColDef, ModelUpdatedEvent } from 'ag-grid-community'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { useACMItems, useFieldSchema } from '@/lib/hooks/useACMItems'
import type { ACMRecord } from '@/lib/types/acm'

// Register AG Grid modules (idempotent — safe to call multiple times)
ModuleRegistry.registerModules([AllCommunityModule])

interface ItemGridProps {
  sourceId: string
  buildingId: string
  quickFilterText: string
  enableGrouping: boolean
}

// Custom cell renderer for risk status badges
function RiskStatusRenderer({ value }: { value: string | null | undefined }) {
  if (!value) return <span className="text-muted-foreground">-</span>

  const colorMap: Record<string, string> = {
    Low: 'text-green-600 bg-green-50 dark:bg-green-950/30',
    Medium: 'text-yellow-600 bg-yellow-50 dark:bg-yellow-950/30',
    High: 'text-red-600 bg-red-50 dark:bg-red-950/30',
  }
  const classes = colorMap[value] ?? 'text-muted-foreground'

  return (
    <span className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium ${classes}`}>
      {value}
    </span>
  )
}

/**
 * Maps a SF api_name to the corresponding ACMRecord property key.
 *
 * The SF taxonomy (E32-S4) may use names like "Building_Code__c" or "Risk_Status__c".
 * The ACMRecord interface uses snake_case backend names (building_id, risk_status, etc.).
 * This normalizer converts common SF __c suffixed names to their backend equivalents.
 * Fields that already exist verbatim on ACMRecord pass through unchanged.
 */
function fieldApiToRecordKey(apiName: string): string {
  // Strip Salesforce __c suffix and lowercase
  const stripped = apiName.replace(/__c$/i, '').toLowerCase()

  // Explicit overrides for known mapping differences
  const overrides: Record<string, string> = {
    building_code: 'building_id',
    acm_name: 'product',
    acm_description: 'material_description',
    condition: 'material_condition',
    friability: 'friable',
    risk: 'risk_status',
    internal_external: 'area_type',
  }

  return overrides[stripped] ?? stripped
}

export function ItemGrid({ sourceId, buildingId, quickFilterText, enableGrouping }: ItemGridProps) {
  const { data: acmData, isLoading: isLoadingItems } = useACMItems(sourceId, buildingId)
  const { data: fieldSchema, isLoading: isLoadingSchema } = useFieldSchema()
  const [visibleCount, setVisibleCount] = useState<number | null>(null)

  const records = acmData?.records ?? []
  const totalCount = acmData?.total ?? 0

  // Build column definitions from SF field schema.
  // Falls back to a minimal set of hardcoded columns when schema is unavailable.
  const columnDefs = useMemo<ColDef<ACMRecord>[]>(() => {
    if (!fieldSchema) {
      // Fallback columns when schema hasn't loaded yet
      return [
        { field: 'building_id', headerName: 'Building', pinned: 'left' as const, width: 160, sortable: true, filter: true, resizable: true },
        {
          field: 'room_id', headerName: 'Room ID', pinned: enableGrouping ? undefined : ('left' as const),
          width: 160, sortable: true, filter: true, resizable: true,
          rowGroup: enableGrouping, hide: enableGrouping,
        },
        { field: 'room_name', headerName: 'Room Name', width: 180, sortable: true, filter: true, resizable: true },
        { field: 'product', headerName: 'ACM Product', flex: 1, minWidth: 200, sortable: true, filter: true, resizable: true },
        { field: 'result', headerName: 'Result', width: 130, sortable: true, filter: true, resizable: true },
        { field: 'risk_status', headerName: 'Risk Status', width: 110, sortable: true, filter: true, resizable: true, cellRenderer: RiskStatusRenderer },
        { field: 'friable', headerName: 'Friability', width: 110, sortable: true, filter: true, resizable: true },
        { field: 'material_condition', headerName: 'Condition', width: 120, sortable: true, filter: true, resizable: true },
      ]
    }

    // Columns pinned left by record key (after normalisation)
    const pinnedLeft = new Set(['building_id', 'room_id', 'room_name'])
    const GROUP_FIELD = 'room_id'
    const RISK_FIELD = 'risk_status'

    return fieldSchema.item_fields.fields.map((fieldDef): ColDef<ACMRecord> => {
      const recordKey = fieldApiToRecordKey(fieldDef.api_name) as keyof ACMRecord
      const isGroupField = String(recordKey) === GROUP_FIELD
      const colDef: ColDef<ACMRecord> = {
        field: recordKey,
        headerName: fieldDef.label,
        sortable: true,
        filter: true,
        resizable: true,
        ...(pinnedLeft.has(String(recordKey)) && !isGroupField && { pinned: 'left' as const, width: 160 }),
        // Grouping: mark room_id as the row-group column when grouping is active
        ...(isGroupField && enableGrouping && { rowGroup: true, hide: true }),
        ...(isGroupField && !enableGrouping && { pinned: 'left' as const, width: 160 }),
      }

      // Risk status colour renderer
      if (String(recordKey) === RISK_FIELD) {
        colDef.cellRenderer = RiskStatusRenderer
        colDef.width = 110
      }

      return colDef
    })
  }, [fieldSchema, enableGrouping])

  const defaultColDef = useMemo<ColDef>(
    () => ({
      resizable: true,
      suppressMenu: true,
    }),
    []
  )

  const autoGroupColumnDef = useMemo(
    () => ({
      headerName: 'Room / Area',
      minWidth: 260,
    }),
    []
  )

  const onModelUpdated = useCallback((event: ModelUpdatedEvent<ACMRecord>) => {
    if (event.api) {
      let count = 0
      event.api.forEachNodeAfterFilterAndSort((node) => {
        if (!node.group) count++
      })
      setVisibleCount(count)
    }
  }, [])

  const isLoading = isLoadingItems || isLoadingSchema

  return (
    <div className="flex flex-col h-full">
      {/* Record count bar */}
      <div className="flex items-center gap-2 mb-2 text-xs text-muted-foreground shrink-0">
        {visibleCount !== null && visibleCount !== totalCount ? (
          <span>Showing {visibleCount} of {totalCount} records</span>
        ) : (
          <span>{totalCount} record{totalCount !== 1 ? 's' : ''}</span>
        )}
      </div>

      {/* AG Grid wrapper — must have explicit height for domLayout="normal" */}
      <div
        className="ag-theme-alpine flex-1 min-h-0 w-full overflow-hidden"
        style={{ height: '100%' }}
        role="region"
        aria-label="ACM Items Data Grid — use arrow keys to navigate"
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
          .ag-theme-alpine .ag-row-group {
            background-color: hsl(var(--muted) / 0.7);
            font-weight: 600;
          }
          .ag-theme-alpine .ag-row-group-expanded {
            border-bottom: 2px solid hsl(var(--border));
          }
        `}</style>
        <AgGridReact<ACMRecord>
          rowData={records}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          loading={isLoading}
          animateRows={true}
          rowSelection="single"
          suppressRowClickSelection={true}
          pagination={true}
          paginationPageSize={100}
          paginationPageSizeSelector={[50, 100, 250]}
          quickFilterText={quickFilterText}
          domLayout="normal"
          alwaysShowHorizontalScroll={true}
          onModelUpdated={onModelUpdated}
          // Row grouping configuration (toggled by parent toolbar)
          {...(enableGrouping
            ? {
                groupDisplayType: 'groupRows' as const,
                groupDefaultExpanded: 1,
                autoGroupColumnDef,
                suppressAggFuncInHeader: true,
              }
            : {})}
          // Use legacy theming for ag-theme-alpine CSS compatibility
          theme="legacy"
        />
      </div>

      {/* Keyboard hints */}
      <div className="text-xs text-muted-foreground mt-2 flex items-center gap-4 shrink-0">
        <span>Arrow keys to navigate</span>
        <span>Space to expand/collapse groups</span>
      </div>
    </div>
  )
}
