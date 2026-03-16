'use client'

import { useCallback, useMemo, useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AgGridReact } from 'ag-grid-react'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import type { ColDef, CellValueChangedEvent } from 'ag-grid-community'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useRouter } from 'next/navigation'
import { Eye, Plus, RefreshCw, Search } from 'lucide-react'
import type { BuildingRecord, BuildingRecordUpdateRequest } from '@/lib/types/building'

// Register AG Grid modules (safe to call multiple times)
ModuleRegistry.registerModules([AllCommunityModule])

/**
 * Extended BuildingRecord with local-only UI flags.
 * The canonical BuildingRecord is imported from @/lib/types/building.
 */
type BuildingRowData = BuildingRecord & {
  /** Local-only flag for optimistic removes — not sent to API */
  _removed?: boolean
}

interface BuildingReviewGridProps {
  sourceId: string
  onDataChanged?: () => void
}


/**
 * Fetch buildings from the V3 API.
 * GET /api/acm/buildings?source_id={sourceId} → { buildings: BuildingRecord[], total: number }
 */
async function fetchBuildings(sourceId: string): Promise<BuildingRecord[]> {
  const res = await fetch(`/api/acm/buildings?source_id=${encodeURIComponent(sourceId)}`)
  if (!res.ok) {
    throw new Error(`Failed to fetch buildings: ${res.statusText}`)
  }
  const data = await res.json()
  return data.buildings ?? []
}

/**
 * Save a building via PUT /api/acm/buildings/{building_id}
 */
async function saveBuilding(
  buildingId: string,
  payload: BuildingRecordUpdateRequest
): Promise<void> {
  const res = await fetch(
    `/api/acm/buildings/${encodeURIComponent(buildingId)}`,
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }
  )
  if (!res.ok) {
    throw new Error(`Failed to save building: ${res.statusText}`)
  }
}

/**
 * ActionsRenderer — per-row action buttons for mark-out-of-scope and remove.
 */
function ActionsRenderer({
  data,
  onView,
  onRemove,
}: {
  data: BuildingRowData
  onView: () => void
  onRemove: (buildingId: string) => void
}) {
  return (
    <div className="flex items-center gap-1 h-full">
      <Button
        variant="outline"
        size="sm"
        className="h-6 px-2 text-xs"
        onClick={(e) => {
          e.stopPropagation()
          onView()
        }}
        title="View building ACM records"
      >
        <Eye className="h-3 w-3 mr-1" />
        View
      </Button>
      <Button
        variant="ghost"
        size="sm"
        className="h-6 px-2 text-xs text-destructive hover:text-destructive"
        onClick={(e) => {
          e.stopPropagation()
          onRemove(data.id)
        }}
        title="Remove building row"
      >
        Remove
      </Button>
    </div>
  )
}

/**
 * BuildingReviewGrid — AG Grid component for reviewing and editing building records
 * before proceeding to ACM record review.
 *
 * Story: E19-S5 Building Review Wizard Step 1
 */
export function BuildingReviewGrid({ sourceId, onDataChanged }: BuildingReviewGridProps) {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [searchText, setSearchText] = useState('')

  // Local state for rows — starts from query data, allows optimistic adds/removes
  const [localRows, setLocalRows] = useState<BuildingRowData[] | null>(null)

  const {
    data: fetchedBuildings,
    isLoading,
    error,
    refetch,
  } = useQuery<BuildingRecord[]>({
    queryKey: ['buildings', 'v3', sourceId],
    queryFn: () => fetchBuildings(sourceId),
    staleTime: 30_000,
  })

  // Sync fetched data into localRows on first load (or when cache is refreshed)
  const prevFetchedRef = useRef<BuildingRecord[] | null>(null)
  if (fetchedBuildings && fetchedBuildings !== prevFetchedRef.current) {
    prevFetchedRef.current = fetchedBuildings
    setLocalRows(fetchedBuildings)
  }

  const rows: BuildingRowData[] = localRows ?? fetchedBuildings ?? []
  const baseRows = rows.filter((row) => !row._removed)
  const displayRows = baseRows.filter((row) => {
    const normalizedSearch = searchText.trim().toLowerCase()
    if (!normalizedSearch) return true

    return [
      row.id,
      row.internal_id,
      row.building_name,
      row.building_type,
      row.building_address,
      row.suburb,
      row.postcode,
    ]
      .map((value) => String(value ?? '').toLowerCase())
      .some((value) => value.includes(normalizedSearch))
  })

  // Debounce ref for cell-edit saves
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Mutation for saving building fields
  const saveMutation = useMutation({
    mutationFn: ({ buildingId, payload }: { buildingId: string; payload: BuildingRecordUpdateRequest }) =>
      saveBuilding(buildingId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['buildings', 'v3', sourceId] })
      onDataChanged?.()
    },
  })

  // Mutation for marking a building out of scope
  const markOutOfScopeMutation = useMutation({
    mutationFn: (buildingId: string) =>
      saveBuilding(buildingId, { building_out_of_scope: true }),
    onSuccess: (_data, buildingId) => {
      setLocalRows((prev) =>
        prev
          ? prev.map((r) =>
              r.id === buildingId ? { ...r, building_out_of_scope: true } : r
            )
          : prev
      )
      queryClient.invalidateQueries({ queryKey: ['buildings', 'v3', sourceId] })
      onDataChanged?.()
    },
  })

  const handleMarkOutOfScope = useCallback(
    (buildingId: string) => {
      markOutOfScopeMutation.mutate(buildingId)
    },
    [markOutOfScopeMutation]
  )

  const handleView = useCallback(
    // Navigate to the ACM Register page for this source
    () => router.push(`/source/${encodeURIComponent(sourceId)}`),
    [router, sourceId]
  )

  const handleRemove = useCallback((buildingId: string) => {
    // Optimistic local remove — no backend call needed for this story
    setLocalRows((prev) =>
      prev ? prev.map((r) => (r.id === buildingId ? { ...r, _removed: true } : r)) : prev
    )
    onDataChanged?.()
  }, [onDataChanged])

  const handleAddBuilding = useCallback(() => {
    const newRow: BuildingRowData = {
      id: `new_building_${Date.now()}`,
      internal_id: '',
      source_id: sourceId,
      building_code: null,
      building_name: '',
      building_year: null,
      building_construction: null,
      building_address: null,
      suburb: null,
      postcode: null,
      building_type: null,
      building_category: null,
      building_sub_category: null,
      building_risk_rating: null,
      building_address_lga: null,
      building_address_region: null,
      roof_type: null,
      number_of_levels: null,
      est_building_size_m2: null,
      frequency_of_use: null,
      daily_duration: null,
      level_of_activity: null,
      public_access: null,
      mobile_plant: null,
      owned_or_leased: null,
      asbestos_register_available: null,
      audit_report_available: null,
      date_of_audit_report: null,
      no_identified_acms: null,
      no_identified_acms_note: null,
      site_name: null,
      school_uid: null,
      building_unique_id: null,
      external_id: null,
      building_out_of_scope: null,
      building_out_of_scope_comments: null,
      demolished_status: null,
      demolition_date: null,
      demolition_type: null,
      demolition_comments: null,
      additional_comments: null,
      within_your_portfolio: null,
      psb_district_region: null,
      state: null,
      country: null,
      gps_coordinates: null,
      capital_works_project_details: null,
      possible_capital_works_project: null,
      record_count: 0,
      created: null,
      updated: null,
    }
    setLocalRows((prev) => [...(prev ?? []), newRow])
  }, [sourceId])

  const handleRefresh = useCallback(() => {
    void refetch()
  }, [refetch])

  const onCellValueChanged = useCallback(
    (event: CellValueChangedEvent<BuildingRowData>) => {
      if (!event.data) return
      const { id: rowId } = event.data
      const field = event.colDef.field as keyof BuildingRowData
      if (!field || !rowId) return

      // Update local state immediately
      setLocalRows((prev) =>
        prev
          ? prev.map((r) => (r.id === rowId ? { ...r, [field]: event.newValue } : r))
          : prev
      )

      // Debounce the save by 500ms
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
      saveTimerRef.current = setTimeout(() => {
        // Skip auto-save for newly added rows (they have no real backend record yet)
        if (rowId.startsWith('new_building_')) return
        saveMutation.mutate({
          buildingId: rowId,
          payload: { [field]: event.newValue } as BuildingRecordUpdateRequest,
        })
      }, 500)
    },
    [saveMutation]
  )

  const columnDefs = useMemo<ColDef<BuildingRowData>[]>(
    () => [
      { field: 'internal_id', headerName: 'Building ID', width: 130, editable: false, pinned: 'left' },
      { field: 'building_name', headerName: 'Building Name', width: 160, editable: true },
      { field: 'building_type', headerName: 'Building Type', width: 140, editable: true },
      { field: 'building_address', headerName: 'Address', width: 200, editable: true },
      { field: 'suburb', headerName: 'Suburb', width: 130, editable: true },
      { field: 'postcode', headerName: 'Postcode', width: 100, editable: true },
      // NOTE: 'department' and 'agency' do not exist in canonical BuildingRecord.
      // Using 'within_your_portfolio' and 'psb_district_region' as closest equivalents.
      { field: 'within_your_portfolio', headerName: 'Department/Portfolio', width: 160, editable: true },
      { field: 'psb_district_region', headerName: 'PSB District/Region', width: 170, editable: true },
      { field: 'site_name', headerName: 'Site Name', width: 150, editable: true },
      { field: 'building_unique_id', headerName: 'Building Unique ID', width: 160, editable: true },
      { field: 'owned_or_leased', headerName: 'Owned/Leased', width: 130, editable: true },
      { field: 'frequency_of_use', headerName: 'Frequency of Use', width: 160, editable: true },
      { field: 'public_access', headerName: 'Public Access', width: 120, editable: true },
      // NOTE: 'date_of_inspection' does not exist in canonical BuildingRecord.
      // Using 'date_of_audit_report' as the closest equivalent.
      { field: 'date_of_audit_report', headerName: 'Date of Audit Report', width: 160, editable: true },
      { field: 'building_year', headerName: 'Building Year', width: 130, editable: true },
      { field: 'est_building_size_m2', headerName: 'Size (m\u00b2)', width: 110, editable: true, type: 'numericColumn' },
      { field: 'number_of_levels', headerName: 'No. Levels', width: 110, editable: true, type: 'numericColumn' },
      { field: 'building_construction', headerName: 'Construction', width: 140, editable: true },
      { field: 'roof_type', headerName: 'Roof Type', width: 130, editable: true },
      { field: 'additional_comments', headerName: 'Comments', flex: 1, minWidth: 180, editable: true },
      {
        headerName: 'Actions',
        width: 260,
        pinned: 'right',
        editable: false,
        sortable: false,
        filter: false,
        cellRenderer: (params: { data: BuildingRowData }) =>
          params.data ? (
            <ActionsRenderer
              data={params.data}
              onView={handleView}
              onRemove={handleRemove}
            />
          ) : null,
      },
    ],
    [handleView, handleRemove]
  )

  const defaultColDef = useMemo<ColDef>(
    () => ({
      resizable: true,
      sortable: true,
      filter: true,
      suppressMenu: true,
    }),
    []
  )

  if (isLoading && !localRows) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-muted-foreground">
        Loading buildings...
      </div>
    )
  }

  if (error && !localRows) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-destructive">
        Failed to load buildings. Please try refreshing.
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
              placeholder="Search buildings"
              className="pl-9"
            />
          </div>

          <div className="ml-auto flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleRefresh}>
              <RefreshCw className="mr-1.5 h-4 w-4" />
              Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleAddBuilding}
              className="flex items-center gap-1.5"
            >
              <Plus className="h-4 w-4" />
              Add Building
            </Button>
          </div>
        </div>

        <div className="text-sm text-muted-foreground">
          Showing {displayRows.length} of {baseRows.length} building
          {baseRows.length !== 1 ? 's' : ''}
        </div>

        {/* Completion summary */}
        {baseRows.length > 0 && (() => {
          const missingAddress = baseRows.filter((r) => !r.building_address).length
          const missingName = baseRows.filter((r) => !r.building_name || r.building_name === 'Unknown').length
          const totalMissing = missingAddress + missingName
          if (totalMissing === 0) return null
          return (
            <div className="flex items-center gap-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs dark:border-amber-800 dark:bg-amber-950/30">
              <span className="font-medium text-amber-700 dark:text-amber-300">Details needed:</span>
              {missingName > 0 && <span className="text-amber-600 dark:text-amber-400">{missingName} missing name{missingName !== 1 ? 's' : ''}</span>}
              {missingAddress > 0 && <span className="text-amber-600 dark:text-amber-400">{missingAddress} missing address{missingAddress !== 1 ? 'es' : ''}</span>}
            </div>
          )
        })()}
      </div>

      {/* AG Grid */}
      <div
        className="ag-theme-alpine w-full"
        style={{ height: '520px' }}
        role="region"
        aria-label="Building Review Data Grid"
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
        `}</style>
        <AgGridReact<BuildingRowData>
          rowData={displayRows}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          onCellValueChanged={onCellValueChanged}
          animateRows={true}
          pagination={true}
          paginationPageSize={50}
          paginationPageSizeSelector={[20, 50, 100]}
          domLayout="normal"
          alwaysShowHorizontalScroll={true}
          stopEditingWhenCellsLoseFocus={true}
          // Use legacy theming for ag-theme-alpine CSS compatibility
          theme="legacy"
          overlayNoRowsTemplate='<span class="text-muted-foreground text-sm">No buildings found. Click "+ Add Building" to add one.</span>'
        />
      </div>
    </div>
  )
}
