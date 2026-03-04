'use client'

import { useMemo, useCallback, useState, useRef } from 'react'
import { AgGridReact } from 'ag-grid-react'
import type { ColDef, ModelUpdatedEvent, RowDoubleClickedEvent, ICellRendererParams, GridApi, GridReadyEvent } from 'ag-grid-community'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { useACMItems, useFieldSchema, useUpdateACMRecord } from '@/lib/hooks/useACMItems'
import type { ACMRecord } from '@/lib/types/acm'
import { fieldApiToRecordKey } from '@/lib/utils/acm-field-mapping'
import { DependentPicklistEditor } from './DependentPicklistEditor'
import type { DependentPicklistEditorParams } from './DependentPicklistEditor'
import { ValidationBadge } from './ValidationBadge'
import { RecordWizard } from './RecordWizard'
import { ProvenanceViewer } from './ProvenanceViewer'
import { Eye } from 'lucide-react'

// Register AG Grid modules (idempotent — safe to call multiple times)
ModuleRegistry.registerModules([AllCommunityModule])

interface ItemGridProps {
  sourceId: string
  buildingId: string
  quickFilterText: string
  enableGrouping: boolean
  onSelectionChanged?: (records: ACMRecord[]) => void
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

// fieldApiToRecordKey is now imported from @/lib/utils/acm-field-mapping (E33-S3)

export function ItemGrid({ sourceId, buildingId, quickFilterText, enableGrouping, onSelectionChanged }: ItemGridProps) {
  const { data: acmData, isLoading: isLoadingItems } = useACMItems(sourceId, buildingId)
  const { data: fieldSchema, isLoading: isLoadingSchema } = useFieldSchema()
  const [visibleCount, setVisibleCount] = useState<number | null>(null)

  // RecordWizard state
  const [wizardRecord, setWizardRecord] = useState<ACMRecord | null>(null)
  const [wizardOpen, setWizardOpen] = useState(false)
  const updateRecord = useUpdateACMRecord()

  // Provenance panel state (E33-S6)
  const [provenanceRecordId, setProvenanceRecordId] = useState<string | null>(null)

  // Grid API ref for programmatic selection access (E34-S2)
  const gridApiRef = useRef<GridApi<ACMRecord> | null>(null)

  const onGridReady = useCallback((event: GridReadyEvent<ACMRecord>) => {
    gridApiRef.current = event.api
  }, [])

  const onSelectionChangedCb = useCallback(() => {
    if (gridApiRef.current && onSelectionChanged) {
      onSelectionChanged(gridApiRef.current.getSelectedRows())
    }
  }, [onSelectionChanged])

  const records = acmData?.records ?? []
  const totalCount = acmData?.total ?? 0

  // Build column definitions from SF field schema.
  // Falls back to a minimal set of hardcoded columns when schema is unavailable.
  const columnDefs = useMemo<ColDef<ACMRecord>[]>(() => {
    // Checkbox selection column (E34-S2)
    const checkboxCol: ColDef<ACMRecord> = {
      colId: 'selection',
      checkboxSelection: true,
      headerCheckboxSelection: true,
      width: 40,
      minWidth: 40,
      maxWidth: 40,
      pinned: 'left' as const,
      sortable: false,
      filter: false,
      resizable: false,
      suppressMovable: true,
      headerName: '',
    }

    // Action column — "Source" button to open Provenance Viewer (E33-S6)
    const sourceActionCol: ColDef<ACMRecord> = {
      headerName: '',
      colId: 'provenance_action',
      width: 72,
      minWidth: 72,
      maxWidth: 72,
      sortable: false,
      filter: false,
      resizable: false,
      suppressMovable: true,
      pinned: 'right' as const,
      cellRenderer: (params: ICellRendererParams<ACMRecord>) => {
        if (!params.data?.id) return null
        return (
          <button
            type="button"
            title="View source provenance"
            aria-label="View source provenance"
            onClick={() => setProvenanceRecordId(params.data!.id)}
            className="inline-flex items-center justify-center rounded px-1.5 py-0.5 text-xs text-primary hover:bg-primary/10 transition-colors"
          >
            <Eye className="h-3.5 w-3.5 mr-0.5" />
            Source
          </button>
        )
      },
    }

    if (!fieldSchema) {
      // Fallback columns when schema hasn't loaded yet
      return [
        checkboxCol,
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
        sourceActionCol,
      ]
    }

    // Columns pinned left by record key (after normalisation)
    const pinnedLeft = new Set(['building_id', 'room_id', 'room_name'])
    const GROUP_FIELD = 'room_id'
    const RISK_FIELD = 'risk_status'

    const dataCols = fieldSchema.item_fields.fields.map((fieldDef): ColDef<ACMRecord> => {
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

      // Risk status colour renderer (takes priority over ValidationBadge)
      if (String(recordKey) === RISK_FIELD) {
        colDef.cellRenderer = RiskStatusRenderer
        colDef.width = 110
      } else {
        // Validation badge renderer on all other data columns
        colDef.cellRenderer = ValidationBadge
      }

      // Dependent picklist cell editor (AC1-AC3)
      if (fieldDef.is_dependent && fieldDef.controller_field && fieldSchema) {
        colDef.editable = true
        const capturedApiName = fieldDef.api_name
        const capturedSchema = fieldSchema
        colDef.cellEditorSelector = () => ({
          component: DependentPicklistEditor,
          // Extra params are merged into the ICellEditorParams supplied by AG Grid
          params: {
            mode: 'grid' as const,
            fieldApiName: capturedApiName,
            schema: capturedSchema,
          } as Partial<DependentPicklistEditorParams>,
        })
      }

      return colDef
    })

    return [checkboxCol, ...dataCols, sourceActionCol]
  }, [fieldSchema, enableGrouping, setProvenanceRecordId])

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

  const onRowDoubleClicked = useCallback((event: RowDoubleClickedEvent<ACMRecord>) => {
    if (event.data) {
      setWizardRecord(event.data)
      setWizardOpen(true)
    }
  }, [])

  const handleWizardSave = useCallback(
    (data: Parameters<typeof updateRecord.mutate>[0]['data']) => {
      if (!wizardRecord) return
      updateRecord.mutate(
        { recordId: wizardRecord.id, data },
        {
          onSuccess: () => {
            setWizardOpen(false)
            setWizardRecord(null)
          },
        }
      )
    },
    [wizardRecord, updateRecord]
  )

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
          rowSelection="multiple"
          onGridReady={onGridReady}
          onSelectionChanged={onSelectionChangedCb}
          pagination={true}
          paginationPageSize={100}
          paginationPageSizeSelector={[50, 100, 250]}
          quickFilterText={quickFilterText}
          domLayout="normal"
          alwaysShowHorizontalScroll={true}
          onModelUpdated={onModelUpdated}
          onRowDoubleClicked={onRowDoubleClicked}
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
        <span>Double-click row to edit</span>
      </div>

      {/* Record edit wizard */}
      <RecordWizard
        record={wizardRecord}
        open={wizardOpen}
        onOpenChange={(open) => {
          setWizardOpen(open)
          if (!open) setWizardRecord(null)
        }}
        onSave={handleWizardSave}
        schema={fieldSchema ?? null}
        isSaving={updateRecord.isPending}
      />

      {/* Provenance viewer panel (E33-S6) */}
      {provenanceRecordId && (
        <ProvenanceViewer
          sourceId={sourceId}
          recordId={provenanceRecordId}
          mode="panel"
          onClose={() => setProvenanceRecordId(null)}
        />
      )}
    </div>
  )
}
