'use client'

import { useCallback, useMemo, useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AgGridReact } from 'ag-grid-react'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import type {
  ColDef,
  CellValueChangedEvent,
  SelectionChangedEvent,
} from 'ag-grid-community'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { Plus, RefreshCw, Search, Trash2 } from 'lucide-react'
import type { ACMRecord } from '@/lib/types/acm'
import { RecordMergeModal } from './RecordMergeModal'
import { UNASSIGNED_TAB_ID } from './BuildingTabs'

// Register AG Grid modules (safe to call multiple times)
ModuleRegistry.registerModules([AllCommunityModule])

/**
 * ACMReviewRecord — extends ACMRecord with additional fields returned by the
 * backend that are not yet included in the shared ACMRecord type.
 */
interface ACMReviewRecord extends ACMRecord {
  no_access?: boolean | null
  smf_present?: string | null
  additional_comments?: string | null
  acm_label_details?: string | null
  psb_acm_id?: string | null
  assumed_removed?: string | null
  date_of_removal?: string | null
  quantity_removed?: string | null
  epa_certificate_no?: string | null
  removal_notification_no?: string | null
  // Local-only flag for optimistic removes
  _removed?: boolean
}

interface ACMReviewGridProps {
  sourceId: string
  buildingId?: string | null
  onDataChanged?: () => void
}

type RecordFilter = 'all' | 'attention'

/**
 * Fetch ACM records from the API, optionally filtered by building.
 */
async function fetchRecords(
  sourceId: string,
  buildingId?: string | null
): Promise<ACMReviewRecord[]> {
  const url = new URL('/api/acm/records', window.location.origin)
  url.searchParams.set('source_id', sourceId)
  url.searchParams.set('limit', '500')
  if (buildingId && buildingId !== UNASSIGNED_TAB_ID) {
    url.searchParams.set('building_id', buildingId)
  }
  const res = await fetch(url.toString())
  if (!res.ok) {
    throw new Error(`Failed to fetch records: ${res.statusText}`)
  }
  const data = await res.json()
  return Array.isArray(data) ? data : (data.records ?? [])
}

/**
 * Save a record via PUT /api/acm/records/{id}
 */
async function saveRecord(
  recordId: string,
  payload: Partial<ACMReviewRecord>
): Promise<void> {
  const res = await fetch(`/api/acm/records/${encodeURIComponent(recordId)}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    throw new Error(`Failed to save record: ${res.statusText}`)
  }
}

/**
 * Delete a record via DELETE /api/acm/records/{id}
 */
async function deleteRecord(recordId: string): Promise<void> {
  const res = await fetch(`/api/acm/records/${encodeURIComponent(recordId)}`, {
    method: 'DELETE',
  })
  if (!res.ok) {
    throw new Error(`Failed to delete record: ${res.statusText}`)
  }
}

/**
 * Create a new ACM record via POST /api/acm/records
 */
async function createRecord(
  sourceId: string,
  buildingId: string
): Promise<ACMReviewRecord> {
  const res = await fetch('/api/acm/records', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      source_id: sourceId,
      building_id: buildingId,
      school_name: '',
      product: 'New Record',
      material_description: '',
      result: '',
    }),
  })
  if (!res.ok) {
    throw new Error(`Failed to create record: ${res.statusText}`)
  }
  return res.json()
}

/**
 * DeleteRenderer — Delete button rendered in the Actions column.
 */
function DeleteRenderer({
  data,
  onDelete,
}: {
  data: ACMReviewRecord
  onDelete: (record: ACMReviewRecord) => void
}) {
  return (
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
  )
}

/**
 * ACMReviewGrid — AG Grid component for reviewing and editing ACM records
 * during Step 2 of the wizard. Supports inline cell editing with debounced save,
 * record creation, and deletion.
 *
 * Story: E19-S6 ACM Schema Mapping Wizard — Step 2 (Frontend)
 */
export function ACMReviewGrid({
  sourceId,
  buildingId,
  onDataChanged,
}: ACMReviewGridProps) {
  const queryClient = useQueryClient()
  const [searchText, setSearchText] = useState('')
  const [recordFilter, setRecordFilter] = useState<RecordFilter>('all')

  // Local state for rows — supports optimistic adds/removes
  const [localRows, setLocalRows] = useState<ACMReviewRecord[] | null>(null)
  const [selectedRows, setSelectedRows] = useState<ACMReviewRecord[]>([])
  const [mergeOpen, setMergeOpen] = useState(false)
  const gridRef = useRef<AgGridReact<ACMReviewRecord> | null>(null)

  const {
    data: fetchedRecords,
    isLoading,
    error,
    refetch,
  } = useQuery<ACMReviewRecord[]>({
    queryKey: ['acm-review-records', sourceId, buildingId ?? 'all'],
    queryFn: () => fetchRecords(sourceId, buildingId),
    staleTime: 30_000,
  })

  // Sync fetched data into localRows on first load or when cache refreshes
  const prevFetchedRef = useRef<ACMReviewRecord[] | null>(null)
  if (fetchedRecords && fetchedRecords !== prevFetchedRef.current) {
    prevFetchedRef.current = fetchedRecords
    setLocalRows(fetchedRecords)
  }

  const baseRows = (localRows ?? fetchedRecords ?? [])
    .filter((r) => !r._removed)
    .filter((r) => {
      if (buildingId !== UNASSIGNED_TAB_ID) return true
      const bid = r.building_id?.trim().toLowerCase()
      return !bid || bid === 'unknown'
    })

  const displayRows = baseRows.filter((row) => {
    const requiresAttention =
      !!row.no_access || row.sample_result?.toLowerCase() === 'not sampled'

    if (recordFilter === 'attention' && !requiresAttention) {
      return false
    }

    const normalizedSearch = searchText.trim().toLowerCase()
    if (!normalizedSearch) return true

    return [
      row.building_id,
      row.room_name,
      row.location,
      row.product,
      row.sample_no,
      row.sample_result,
      row.material_condition,
    ]
      .map((value) => String(value ?? '').toLowerCase())
      .some((value) => value.includes(normalizedSearch))
  })

  // Debounce ref for cell-edit saves
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Mutation for saving record fields
  const saveMutation = useMutation({
    mutationFn: ({
      recordId,
      payload,
    }: {
      recordId: string
      payload: Partial<ACMReviewRecord>
    }) => saveRecord(recordId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['acm-review-records', sourceId],
      })
      onDataChanged?.()
    },
  })

  // Mutation for deleting a record
  const deleteMutation = useMutation({
    mutationFn: (recordId: string) => deleteRecord(recordId),
    onSuccess: (_data, recordId) => {
      setLocalRows((prev) =>
        prev
          ? prev.map((r) => (r.id === recordId ? { ...r, _removed: true } : r))
          : prev
      )
      queryClient.invalidateQueries({
        queryKey: ['acm-review-records', sourceId],
      })
      onDataChanged?.()
    },
  })

  // Mutation for creating a new record
  const createMutation = useMutation({
    mutationFn: () =>
      createRecord(
        sourceId,
        !buildingId || buildingId === UNASSIGNED_TAB_ID
          ? 'Unassigned'
          : buildingId
      ),
    onSuccess: (newRecord) => {
      setLocalRows((prev) => [...(prev ?? []), newRecord])
      queryClient.invalidateQueries({
        queryKey: ['acm-review-records', sourceId],
      })
      onDataChanged?.()
    },
  })

  const handleDelete = useCallback(
    (record: ACMReviewRecord) => {
      if (!record.id) return
      deleteMutation.mutate(record.id)
    },
    [deleteMutation]
  )

  const handleAddRecord = useCallback(() => {
    createMutation.mutate()
  }, [createMutation])

  const handleRefresh = useCallback(() => {
    void refetch()
  }, [refetch])

  const handleSelectionChanged = useCallback(
    (event: SelectionChangedEvent<ACMReviewRecord>) => {
      setSelectedRows(event.api.getSelectedRows())
    },
    []
  )

  const handleMergeSelected = useCallback(() => {
    if (selectedRows.length !== 2) return
    setMergeOpen(true)
  }, [selectedRows])

  const handleMerge = useCallback(
    async (keepId: string, deleteId: string) => {
      const rows = localRows ?? fetchedRecords ?? []
      const keepRecord = rows.find((r) => r.id === keepId)
      const deleteRecordRow = rows.find((r) => r.id === deleteId)
      if (!keepRecord || !deleteRecordRow) return

      const mergedPayload: Partial<ACMReviewRecord> = {}
      const fieldsToMerge: Array<keyof ACMReviewRecord> = [
        'location',
        'material_description',
        'sample_no',
        'sample_result',
        'material_condition',
        'disturbance_potential',
        'quantity',
        'hygienist_recommendations',
        'additional_comments',
        'acm_label_details',
        'psb_acm_id',
        'assumed_removed',
        'date_of_removal',
        'quantity_removed',
        'epa_certificate_no',
        'removal_notification_no',
      ]

      fieldsToMerge.forEach((field) => {
        const keepValue = keepRecord[field]
        const deleteValue = deleteRecordRow[field]
        const keepEmpty =
          keepValue === null ||
          keepValue === undefined ||
          (typeof keepValue === 'string' && keepValue.trim() === '')
        if (keepEmpty && deleteValue !== null && deleteValue !== undefined) {
          ;(mergedPayload as Record<string, unknown>)[field] = deleteValue
        }
      })

      if (Object.keys(mergedPayload).length > 0) {
        await saveMutation.mutateAsync({
          recordId: keepId,
          payload: mergedPayload,
        })
      }

      await deleteMutation.mutateAsync(deleteId)
      setMergeOpen(false)
      setSelectedRows([])
      gridRef.current?.api?.deselectAll()
    },
    [deleteMutation, fetchedRecords, localRows, saveMutation]
  )

  const onCellValueChanged = useCallback(
    (event: CellValueChangedEvent<ACMReviewRecord>) => {
      if (!event.data) return
      const { id: recordId } = event.data
      const field = event.colDef.field as keyof ACMReviewRecord
      if (!field || !recordId) return

      // Update local state immediately for responsive editing
      setLocalRows((prev) =>
        prev
          ? prev.map((r) =>
              r.id === recordId ? { ...r, [field]: event.newValue } : r
            )
          : prev
      )

      // Debounce the save by 500ms
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
      saveTimerRef.current = setTimeout(() => {
        saveMutation.mutate({
          recordId,
          payload: { [field]: event.newValue },
        })
      }, 500)
    },
    [saveMutation]
  )

  const columnDefs = useMemo<ColDef<ACMReviewRecord>[]>(
    () => [
      {
        field: 'building_id',
        headerName: 'Building',
        width: 120,
        editable: false,
        pinned: 'left',
        sortable: true,
        filter: true,
      },
      {
        field: 'room_name',
        headerName: 'Room/Area',
        width: 160,
        editable: true,
        sortable: true,
        filter: true,
      },
      {
        field: 'location',
        headerName: 'Location',
        width: 160,
        editable: true,
        sortable: true,
        filter: true,
      },
      {
        field: 'product',
        headerName: 'ACM Name',
        width: 160,
        editable: true,
        sortable: true,
        filter: true,
      },
      {
        field: 'friable',
        headerName: 'Friable',
        width: 130,
        editable: true,
        sortable: true,
        filter: true,
        cellEditor: 'agSelectCellEditor',
        cellEditorParams: { values: ['Friable', 'Non-friable'] },
      },
      {
        field: 'acm_product_group',
        headerName: 'Product Group',
        width: 150,
        editable: true,
        sortable: true,
        filter: true,
      },
      {
        field: 'acm_product_type',
        headerName: 'Product Type',
        width: 160,
        editable: true,
        sortable: true,
        filter: true,
      },
      {
        field: 'no_access',
        headerName: 'No Access',
        width: 110,
        editable: true,
        sortable: true,
        filter: true,
        cellEditor: 'agCheckboxCellEditor',
        cellRenderer: (params: { value: boolean | null | undefined }) => (
          <input
            type="checkbox"
            checked={!!params.value}
            onChange={() => {}}
            readOnly
            className="cursor-default"
          />
        ),
      },
      {
        field: 'sample_no',
        headerName: 'Sample No.',
        width: 120,
        editable: true,
        sortable: true,
        filter: true,
      },
      {
        field: 'sample_result',
        headerName: 'Sample Result',
        width: 140,
        editable: true,
        sortable: true,
        filter: true,
      },
      {
        field: 'material_condition',
        headerName: 'Condition',
        width: 130,
        editable: true,
        sortable: true,
        filter: true,
        cellEditor: 'agSelectCellEditor',
        cellEditorParams: { values: ['Good', 'Fair', 'Poor', 'Damaged'] },
      },
      {
        field: 'disturbance_potential',
        headerName: 'Disturbance',
        width: 130,
        editable: true,
        sortable: true,
        filter: true,
        cellEditor: 'agSelectCellEditor',
        cellEditorParams: { values: ['Low', 'Medium', 'High'] },
      },
      {
        field: 'quantity',
        headerName: 'Quantity',
        width: 100,
        editable: true,
        sortable: true,
        filter: true,
      },
      {
        field: 'acm_labelled',
        headerName: 'ACM Labelled',
        width: 120,
        editable: true,
        sortable: true,
        filter: true,
        cellEditor: 'agCheckboxCellEditor',
        cellRenderer: (params: { value: boolean | null | undefined }) => (
          <input
            type="checkbox"
            checked={!!params.value}
            onChange={() => {}}
            readOnly
            className="cursor-default"
          />
        ),
      },
      {
        field: 'acm_label_details',
        headerName: 'Label Details',
        width: 180,
        editable: true,
        sortable: true,
        filter: true,
      },
      {
        field: 'identifying_company',
        headerName: 'Identifying Company',
        width: 180,
        editable: true,
        sortable: true,
        filter: true,
      },
      {
        field: 'psb_acm_id',
        headerName: 'PSB ACM ID',
        width: 140,
        editable: true,
        sortable: true,
        filter: true,
      },
      {
        field: 'assumed_removed',
        headerName: 'Removal Status',
        width: 150,
        editable: true,
        sortable: true,
        filter: true,
      },
      {
        field: 'date_of_removal',
        headerName: 'Date Of Removal',
        width: 150,
        editable: true,
        sortable: true,
        filter: true,
      },
      {
        field: 'quantity_removed',
        headerName: 'Quantity Removed',
        width: 150,
        editable: true,
        sortable: true,
        filter: true,
      },
      {
        field: 'epa_certificate_no',
        headerName: 'EPA Certificate No',
        width: 170,
        editable: true,
        sortable: true,
        filter: true,
      },
      {
        field: 'removal_notification_no',
        headerName: 'Removal Notification No',
        width: 190,
        editable: true,
        sortable: true,
        filter: true,
      },
      {
        field: 'hygienist_recommendations',
        headerName: 'Hygienist Recommendations',
        width: 240,
        editable: true,
        sortable: true,
        filter: true,
      },
      {
        field: 'area_type',
        headerName: 'Int/Ext',
        width: 100,
        editable: true,
        sortable: true,
        filter: true,
      },
      {
        field: 'floor_level',
        headerName: 'Level',
        width: 90,
        editable: true,
        sortable: true,
        filter: true,
      },
      {
        field: 'smf_present',
        headerName: 'SMF Present',
        width: 120,
        editable: true,
        sortable: true,
        filter: true,
        cellEditor: 'agSelectCellEditor',
        cellEditorParams: { values: ['Yes', 'No', 'Unknown'] },
      },
      {
        field: 'additional_comments',
        headerName: 'Additional Comments',
        flex: 1,
        minWidth: 180,
        editable: true,
        sortable: true,
        filter: true,
      },
      {
        headerName: 'Actions',
        width: 80,
        pinned: 'right',
        editable: false,
        sortable: false,
        filter: false,
        cellRenderer: (params: { data: ACMReviewRecord }) =>
          params.data ? (
            <DeleteRenderer data={params.data} onDelete={handleDelete} />
          ) : null,
      },
    ],
    [handleDelete]
  )

  const defaultColDef = useMemo<ColDef>(
    () => ({
      resizable: true,
      suppressMenu: true,
    }),
    []
  )

  if (isLoading && !localRows) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-muted-foreground">
        Loading records...
      </div>
    )
  }

  if (error && !localRows) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-destructive">
        Failed to load records. Please try refreshing.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Toolbar */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative min-w-[240px] flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={searchText}
              onChange={(event) => setSearchText(event.target.value)}
              placeholder="Search records"
              className="pl-9"
            />
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant={recordFilter === 'all' ? 'default' : 'outline'}
              size="sm"
              className={cn(
                'rounded-full',
                recordFilter === 'all' &&
                  'bg-[color:var(--vaea-teal-500)] text-white hover:bg-[color:var(--vaea-teal-700)]'
              )}
              onClick={() => setRecordFilter('all')}
            >
              All
            </Button>
            <Button
              variant={recordFilter === 'attention' ? 'default' : 'outline'}
              size="sm"
              className={cn(
                'rounded-full',
                recordFilter === 'attention' &&
                  'bg-[color:var(--vaea-teal-500)] text-white hover:bg-[color:var(--vaea-teal-700)]'
              )}
              onClick={() => setRecordFilter('attention')}
            >
              Needs Attention
            </Button>
          </div>

          <div className="ml-auto flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleRefresh}>
              <RefreshCw className="mr-1.5 h-4 w-4" />
              Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleMergeSelected}
              disabled={selectedRows.length !== 2}
              className="flex items-center gap-1.5"
            >
              Merge Duplicate
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleAddRecord}
              disabled={createMutation.isPending}
              className="flex items-center gap-1.5"
            >
              <Plus className="h-4 w-4" />
              Add Record
            </Button>
          </div>
        </div>

        <div className="text-sm text-muted-foreground">
          Showing {displayRows.length} of {baseRows.length} record
          {baseRows.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* AG Grid */}
      <div
        className="ag-theme-alpine w-full"
        style={{ height: '600px' }}
        role="region"
        aria-label="ACM Records Review Data Grid"
      >
        <style jsx global>{`
          .ag-theme-alpine {
            --ag-row-height: 40px;
            --ag-header-height: 44px;
            --ag-font-size: 14px;
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
          .ag-theme-alpine .acm-review-row-warning {
            background-color: rgb(255 251 235) !important;
          }
          .dark .ag-theme-alpine .acm-review-row-warning {
            background-color: rgb(120 80 20 / 0.25) !important;
          }
        `}</style>
        <AgGridReact<ACMReviewRecord>
          ref={gridRef}
          rowData={displayRows}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          onCellValueChanged={onCellValueChanged}
          rowSelection="multiple"
          rowMultiSelectWithClick={true}
          onSelectionChanged={handleSelectionChanged}
          animateRows={true}
          pagination={true}
          paginationPageSize={50}
          paginationPageSizeSelector={[20, 50, 100]}
          domLayout="normal"
          alwaysShowHorizontalScroll={true}
          stopEditingWhenCellsLoseFocus={true}
          rowClassRules={{
            'acm-review-row-warning': (params) =>
              !!(
                params.data?.no_access ||
                params.data?.sample_result === 'Not Sampled'
              ),
          }}
          // Use legacy theming for ag-theme-alpine CSS compatibility
          theme="legacy"
          overlayNoRowsTemplate='<span class="text-muted-foreground text-sm">No records found. Click "+ Add Record" to add one.</span>'
        />
      </div>

      <RecordMergeModal
        open={mergeOpen}
        onClose={() => setMergeOpen(false)}
        record1={selectedRows[0] ?? null}
        record2={selectedRows[1] ?? null}
        onMerge={handleMerge}
      />
    </div>
  )
}
