'use client'

import { useCallback, useMemo, useRef, useState, useEffect } from 'react'
import { AgGridReact } from 'ag-grid-react'
import type {
  ColDef,
  GridReadyEvent,
  GridApi,
  ColumnResizedEvent,
  ColumnVisibleEvent,
  RowClickedEvent,
} from 'ag-grid-community'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { Button } from '@/components/ui/button'
import { Eye } from 'lucide-react'
import { BuildingViewDialog } from '@/components/acm/BuildingViewDialog'
import type { BuildingRecord } from '@/lib/types/building'
import type { SFFieldSchemaConfig } from '@/lib/types/sf-schema'

// Register AG Grid modules
ModuleRegistry.registerModules([AllCommunityModule])

const COLUMN_STATE_KEY = 'building-grid-column-state'

/**
 * Default visible column field keys (16 fields).
 * These are shown by default; all other BuildingRecord fields are hidden
 * but togglable via AG Grid column menu.
 */
const DEFAULT_VISIBLE_FIELDS = new Set([
  'building_name',
  'building_address',
  'suburb',
  'postcode',
  'state',
  'building_type',
  'building_category',
  'building_construction',
  'building_year',
  'number_of_levels',
  'owned_or_leased',
  'frequency_of_use',
  'record_count',
])

// Fields to exclude from the grid entirely (system/internal fields)
const EXCLUDED_FIELDS = new Set([
  'id',
  'internal_id',
  'source_id',
  'created',
  'updated',
])

interface BuildingGridProps {
  buildings: BuildingRecord[]
  isLoading?: boolean
  sourceId: string
  quickFilterText?: string
  schema: SFFieldSchemaConfig | null
}

/** Humanize a snake_case field name into a readable label. */
function humanize(key: string): string {
  return key
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

/** Map field keys to explicit header names for the default visible columns. */
const HEADER_NAME_MAP: Record<string, string> = {
  building_name: 'Asset Name',
  building_address: 'Street Address',
  suburb: 'Suburb',
  postcode: 'Postcode',
  state: 'State',
  building_type: 'Asset Type',
  building_category: 'Asset Category',
  building_construction: 'Construction Type',
  building_year: 'Year Built',
  number_of_levels: 'Number of Levels',
  owned_or_leased: 'Owned or Leased',
  frequency_of_use: 'Frequency of Use',
  record_count: 'Records',
}

/**
 * BuildingGrid -- AG Grid for displaying building records.
 * Default 13 visible columns + actions; all other fields hidden but togglable.
 */
export function BuildingGrid({
  buildings,
  isLoading,
  sourceId,
  quickFilterText,
  schema,
}: BuildingGridProps) {
  const gridRef = useRef<AgGridReact<BuildingRecord>>(null)
  const [gridApi, setGridApi] = useState<GridApi<BuildingRecord> | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedBuilding, setSelectedBuilding] = useState<BuildingRecord | null>(null)

  const handleViewBuilding = useCallback((building: BuildingRecord) => {
    setSelectedBuilding(building)
    setDialogOpen(true)
  }, [])

  // Apply quick filter when search text changes
  useEffect(() => {
    if (gridApi) {
      gridApi.setGridOption('quickFilterText', quickFilterText || '')
    }
  }, [gridApi, quickFilterText])

  // Build column definitions from BuildingRecord fields
  const columnDefs = useMemo<ColDef<BuildingRecord>[]>(() => {
    // Get all field keys from BuildingRecord by examining the first building
    // or use a static list of known fields
    const allFieldKeys = Object.keys(
      buildings[0] ?? {}
    ).filter((key) => !EXCLUDED_FIELDS.has(key))

    // If no buildings, use a known field list
    const fieldKeys =
      allFieldKeys.length > 0
        ? allFieldKeys
        : [
            'building_code',
            'building_name',
            'building_address',
            'suburb',
            'postcode',
            'state',
            'building_type',
            'building_category',
            'building_construction',
            'building_year',
            'number_of_levels',
            'owned_or_leased',
            'frequency_of_use',
            'record_count',
            'building_address_lga',
            'building_address_region',
            'roof_type',
            'est_building_size_m2',
            'daily_duration',
            'level_of_activity',
            'public_access',
            'mobile_plant',
            'asbestos_register_available',
            'audit_report_available',
            'date_of_audit_report',
            'no_identified_acms',
            'no_identified_acms_note',
            'site_name',
            'school_uid',
            'building_unique_id',
            'external_id',
            'building_out_of_scope',
            'building_out_of_scope_comments',
            'demolished_status',
            'demolition_date',
            'demolition_type',
            'demolition_comments',
            'additional_comments',
            'within_your_portfolio',
            'psb_district_region',
            'country',
            'gps_coordinates',
            'capital_works_project_details',
            'possible_capital_works_project',
          ]

    const cols: ColDef<BuildingRecord>[] = fieldKeys.map((key) => {
      const isDefault = DEFAULT_VISIBLE_FIELDS.has(key)
      const headerName = HEADER_NAME_MAP[key] ?? humanize(key)
      const col: ColDef<BuildingRecord> = {
        field: key as keyof BuildingRecord,
        headerName,
        sortable: true,
        filter: true,
        hide: !isDefault,
      }

      // Special widths
      if (key === 'record_count') {
        col.width = 90
      } else if (key === 'building_name' || key === 'building_address') {
        col.minWidth = 180
        col.flex = key === 'building_name' ? 1 : undefined
      } else {
        col.width = 140
      }

      return col
    })

    // Actions column (pinned right)
    cols.push({
      headerName: 'Actions',
      width: 70,
      pinned: 'right',
      cellRenderer: (params: { data: BuildingRecord }) =>
        params.data ? (
          <div className="flex items-center justify-center h-full">
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={(e) => {
                e.stopPropagation()
                handleViewBuilding(params.data)
              }}
              aria-label="View building details"
            >
              <Eye className="h-4 w-4" />
            </Button>
          </div>
        ) : null,
      sortable: false,
      filter: false,
    })

    return cols
  }, [buildings, handleViewBuilding])

  const defaultColDef = useMemo<ColDef>(
    () => ({
      resizable: true,
      suppressMenu: true,
    }),
    []
  )

  // Restore saved column state from localStorage on grid ready
  const onGridReady = useCallback((params: GridReadyEvent<BuildingRecord>) => {
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

  // Save column state to localStorage when column visibility changes
  const onColumnVisible = useCallback((event: ColumnVisibleEvent) => {
    if (event.source === 'api' || event.source === 'toolPanelUi') {
      const state = event.api.getColumnState()
      localStorage.setItem(COLUMN_STATE_KEY, JSON.stringify(state))
    }
  }, [])

  // Row click opens the BuildingViewDialog
  const onRowClicked = useCallback(
    (event: RowClickedEvent<BuildingRecord>) => {
      if (event.data) {
        handleViewBuilding(event.data)
      }
    },
    [handleViewBuilding]
  )

  return (
    <>
      <div
        className="ag-theme-alpine h-full w-full"
        role="region"
        aria-label="Buildings Data Grid - Click a row to view building details"
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
          /* Clickable row cursor */
          .ag-theme-alpine .ag-row {
            cursor: pointer;
          }
        `}</style>
        <AgGridReact<BuildingRecord>
          ref={gridRef}
          rowData={buildings}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          onGridReady={onGridReady}
          onRowClicked={onRowClicked}
          onColumnResized={onColumnResized}
          onColumnVisible={onColumnVisible}
          loading={isLoading}
          animateRows={true}
          pagination={true}
          paginationPageSize={50}
          paginationPageSizeSelector={[20, 50, 100]}
          domLayout="normal"
          alwaysShowHorizontalScroll={true}
          tooltipShowDelay={300}
          theme="legacy"
        />
      </div>

      {/* Building view/edit dialog */}
      <BuildingViewDialog
        building={selectedBuilding}
        open={dialogOpen}
        onOpenChange={(open) => {
          setDialogOpen(open)
          if (!open) setSelectedBuilding(null)
        }}
        sourceId={sourceId}
        schema={schema}
      />
    </>
  )
}
