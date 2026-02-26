'use client'

import { useCallback, useMemo, useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AgGridReact } from 'ag-grid-react'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import type { ColDef, CellValueChangedEvent } from 'ag-grid-community'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { Plus, RefreshCw, Search } from 'lucide-react'

// Register AG Grid modules (safe to call multiple times)
ModuleRegistry.registerModules([AllCommunityModule])

/**
 * BuildingRecord — shape returned by GET /api/acm/jobs/{sourceId}/buildings
 */
export interface BuildingRecord {
  building_id: string
  building_name?: string | null
  building_type?: string | null
  building_address?: string | null
  suburb?: string | null
  postcode?: string | null
  department?: string | null
  agency?: string | null
  sub_agency?: string | null
  site_name?: string | null
  building_unique_id?: string | null
  owned_or_leased?: string | null
  frequency_of_use?: string | null
  public_access?: string | null
  date_of_inspection?: string | null
  building_year?: number | null
  building_size_m2?: number | null
  number_of_levels?: number | null
  building_construction?: string | null
  roof_type?: string | null
  additional_comments?: string | null
  building_out_of_scope?: boolean | null
  // Local-only flag for optimistic removes
  _removed?: boolean
}

interface BuildingReviewGridProps {
  sourceId: string
  onDataChanged?: () => void
}

type ScopeFilter = 'all' | 'in_scope' | 'out_of_scope'

/**
 * Fetch buildings from the API.
 */
async function fetchBuildings(sourceId: string): Promise<BuildingRecord[]> {
  const res = await fetch(`/api/acm/jobs/${encodeURIComponent(sourceId)}/buildings`)
  if (!res.ok) {
    throw new Error(`Failed to fetch buildings: ${res.statusText}`)
  }
  // Accept both array responses and {buildings: [...]} shaped responses
  const data = await res.json()
  return Array.isArray(data) ? data : (data.buildings ?? [])
}

/**
 * Save a building via PUT /api/acm/jobs/{sourceId}/buildings/{building_id}
 */
async function saveBuilding(
  sourceId: string,
  buildingId: string,
  payload: Partial<BuildingRecord>
): Promise<void> {
  const res = await fetch(
    `/api/acm/jobs/${encodeURIComponent(sourceId)}/buildings/${encodeURIComponent(buildingId)}`,
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
  onMarkOutOfScope,
  onRemove,
}: {
  data: BuildingRecord
  onMarkOutOfScope: (buildingId: string) => void
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
          onMarkOutOfScope(data.building_id)
        }}
        title="Mark building as out of scope"
      >
        Out of Scope
      </Button>
      <Button
        variant="ghost"
        size="sm"
        className="h-6 px-2 text-xs text-destructive hover:text-destructive"
        onClick={(e) => {
          e.stopPropagation()
          onRemove(data.building_id)
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
  const queryClient = useQueryClient()
  const [searchText, setSearchText] = useState('')
  const [scopeFilter, setScopeFilter] = useState<ScopeFilter>('all')

  // Local state for rows — starts from query data, allows optimistic adds/removes
  const [localRows, setLocalRows] = useState<BuildingRecord[] | null>(null)

  const {
    data: fetchedBuildings,
    isLoading,
    error,
    refetch,
  } = useQuery<BuildingRecord[]>({
    queryKey: ['buildings', sourceId],
    queryFn: () => fetchBuildings(sourceId),
    staleTime: 30_000,
  })

  // Sync fetched data into localRows on first load (or when cache is refreshed)
  const prevFetchedRef = useRef<BuildingRecord[] | null>(null)
  if (fetchedBuildings && fetchedBuildings !== prevFetchedRef.current) {
    prevFetchedRef.current = fetchedBuildings
    setLocalRows(fetchedBuildings)
  }

  const baseRows = (localRows ?? fetchedBuildings ?? []).filter((row) => !row._removed)
  const displayRows = baseRows.filter((row) => {
    if (scopeFilter === 'in_scope' && row.building_out_of_scope) {
      return false
    }
    if (scopeFilter === 'out_of_scope' && !row.building_out_of_scope) {
      return false
    }

    const normalizedSearch = searchText.trim().toLowerCase()
    if (!normalizedSearch) return true

    return [
      row.building_id,
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
    mutationFn: ({ buildingId, payload }: { buildingId: string; payload: Partial<BuildingRecord> }) =>
      saveBuilding(sourceId, buildingId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['buildings', sourceId] })
      onDataChanged?.()
    },
  })

  // Mutation for marking a building out of scope
  const markOutOfScopeMutation = useMutation({
    mutationFn: (buildingId: string) =>
      saveBuilding(sourceId, buildingId, { building_out_of_scope: true }),
    onSuccess: (_data, buildingId) => {
      setLocalRows((prev) =>
        prev
          ? prev.map((r) =>
              r.building_id === buildingId ? { ...r, building_out_of_scope: true } : r
            )
          : prev
      )
      queryClient.invalidateQueries({ queryKey: ['buildings', sourceId] })
      onDataChanged?.()
    },
  })

  const handleMarkOutOfScope = useCallback(
    (buildingId: string) => {
      markOutOfScopeMutation.mutate(buildingId)
    },
    [markOutOfScopeMutation]
  )

  const handleRemove = useCallback((buildingId: string) => {
    // Optimistic local remove — no backend call needed for this story
    setLocalRows((prev) =>
      prev ? prev.map((r) => (r.building_id === buildingId ? { ...r, _removed: true } : r)) : prev
    )
    onDataChanged?.()
  }, [onDataChanged])

  const handleAddBuilding = useCallback(() => {
    const newRow: BuildingRecord = {
      building_id: `new_building_${Date.now()}`,
      building_name: '',
    }
    setLocalRows((prev) => [...(prev ?? []), newRow])
  }, [])

  const handleRefresh = useCallback(() => {
    void refetch()
  }, [refetch])

  const onCellValueChanged = useCallback(
    (event: CellValueChangedEvent<BuildingRecord>) => {
      if (!event.data) return
      const { building_id } = event.data
      const field = event.colDef.field as keyof BuildingRecord
      if (!field || !building_id) return

      // Update local state immediately
      setLocalRows((prev) =>
        prev
          ? prev.map((r) => (r.building_id === building_id ? { ...r, [field]: event.newValue } : r))
          : prev
      )

      // Debounce the save by 500ms
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
      saveTimerRef.current = setTimeout(() => {
        // Skip auto-save for newly added rows (they have no real backend record yet)
        if (building_id.startsWith('new_building_')) return
        saveMutation.mutate({ buildingId: building_id, payload: { [field]: event.newValue } })
      }, 500)
    },
    [saveMutation]
  )

  const columnDefs = useMemo<ColDef<BuildingRecord>[]>(
    () => [
      { field: 'building_id', headerName: 'Building ID', width: 130, editable: false, pinned: 'left' },
      { field: 'building_name', headerName: 'Building Name', width: 160, editable: true },
      { field: 'building_type', headerName: 'Building Type', width: 140, editable: true },
      { field: 'building_address', headerName: 'Address', width: 200, editable: true },
      { field: 'suburb', headerName: 'Suburb', width: 130, editable: true },
      { field: 'postcode', headerName: 'Postcode', width: 100, editable: true },
      { field: 'department', headerName: 'Department', width: 130, editable: true },
      { field: 'agency', headerName: 'Agency', width: 130, editable: true },
      { field: 'sub_agency', headerName: 'PSB District/Region', width: 170, editable: true },
      { field: 'site_name', headerName: 'Site Name', width: 150, editable: true },
      { field: 'building_unique_id', headerName: 'Building Unique ID', width: 160, editable: true },
      { field: 'owned_or_leased', headerName: 'Owned/Leased', width: 130, editable: true },
      { field: 'frequency_of_use', headerName: 'Frequency of Use', width: 160, editable: true },
      { field: 'public_access', headerName: 'Public Access', width: 120, editable: true },
      { field: 'date_of_inspection', headerName: 'Date of Inspection', width: 160, editable: true },
      { field: 'building_year', headerName: 'Building Year', width: 130, editable: true, type: 'numericColumn' },
      { field: 'building_size_m2', headerName: 'Size (m\u00b2)', width: 110, editable: true, type: 'numericColumn' },
      { field: 'number_of_levels', headerName: 'No. Levels', width: 110, editable: true, type: 'numericColumn' },
      { field: 'building_construction', headerName: 'Construction', width: 140, editable: true },
      { field: 'roof_type', headerName: 'Roof Type', width: 130, editable: true },
      { field: 'additional_comments', headerName: 'Comments', flex: 1, minWidth: 180, editable: true },
      {
        headerName: 'Actions',
        width: 200,
        pinned: 'right',
        editable: false,
        sortable: false,
        filter: false,
        cellRenderer: (params: { data: BuildingRecord }) =>
          params.data ? (
            <ActionsRenderer
              data={params.data}
              onMarkOutOfScope={handleMarkOutOfScope}
              onRemove={handleRemove}
            />
          ) : null,
      },
    ],
    [handleMarkOutOfScope, handleRemove]
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

          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant={scopeFilter === 'all' ? 'default' : 'outline'}
              size="sm"
              className={cn(
                'rounded-full',
                scopeFilter === 'all' &&
                  'bg-[color:var(--vaea-teal-500)] text-white hover:bg-[color:var(--vaea-teal-700)]'
              )}
              onClick={() => setScopeFilter('all')}
            >
              All
            </Button>
            <Button
              variant={scopeFilter === 'in_scope' ? 'default' : 'outline'}
              size="sm"
              className={cn(
                'rounded-full',
                scopeFilter === 'in_scope' &&
                  'bg-[color:var(--vaea-teal-500)] text-white hover:bg-[color:var(--vaea-teal-700)]'
              )}
              onClick={() => setScopeFilter('in_scope')}
            >
              In Scope
            </Button>
            <Button
              variant={scopeFilter === 'out_of_scope' ? 'default' : 'outline'}
              size="sm"
              className={cn(
                'rounded-full',
                scopeFilter === 'out_of_scope' &&
                  'bg-[color:var(--vaea-teal-500)] text-white hover:bg-[color:var(--vaea-teal-700)]'
              )}
              onClick={() => setScopeFilter('out_of_scope')}
            >
              Out of Scope
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
        <AgGridReact<BuildingRecord>
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
