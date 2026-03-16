'use client'

import { use, useState, useEffect, useRef, useMemo } from 'react'
import Link from 'next/link'
import { useQueryClient } from '@tanstack/react-query'
import { AppShell } from '@/components/layout/AppShell'
import { ACMGrid, type ACMGridRef } from '@/components/acm/ACMGrid'
import { ACMRecordDialog } from '@/components/acm/ACMRecordDialog'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { BulkOperationsBar } from '@/components/acm/BulkOperationsBar'
import { ExportDialog } from '@/components/acm/ExportDialog'
import { BuildingGrid } from '@/components/acm/BuildingGrid'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useBuildingStore } from '@/lib/stores/buildingStore'
import { useBuildings } from '@/lib/hooks/useBuildings'
import { useACMItems, useValidationSummary, useBulkFix, useFieldSchema, ACM_ITEMS_QUERY_KEYS } from '@/lib/hooks/useACMItems'
import { useDeleteACMRecord } from '@/lib/hooks/use-acm'
import { useV3BuildingStream } from '@/lib/hooks/useV3BuildingStream'
import type { ACMRecord } from '@/lib/types/acm'
import type { BuildingRecord } from '@/lib/types/building'
import type { BuildingStreamStatus } from '@/lib/stores/buildingStore'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ArrowLeft, Table2, Wrench, Download, Building2, ExternalLink, ChevronLeft, ChevronRight, Search } from 'lucide-react'
import { acmApi } from '@/lib/api/acm'
import { cn } from '@/lib/utils'

/** Scrollable horizontal building tab strip. */
function BuildingTabStrip({
  buildings,
  isLoading,
  selectedBuildingId,
  onSelect,
  sourceId,
  validationSummary,
}: {
  buildings: BuildingRecord[]
  isLoading: boolean
  selectedBuildingId: string | null
  onSelect: (id: string | null) => void
  sourceId: string
  validationSummary: { buildings: Array<{ building_id: string; error_count: number }> } | null | undefined
}) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const { buildingStatus } = useBuildingStore()

  const errorMap = new Map<string, number>(
    (validationSummary?.buildings ?? []).map((b) => [b.building_id, b.error_count])
  )

  const scroll = (dir: 'left' | 'right') => {
    scrollRef.current?.scrollBy({ left: dir === 'left' ? -200 : 200, behavior: 'smooth' })
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 border-b shrink-0 bg-muted/20">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-9 w-36 rounded-md" />
        ))}
      </div>
    )
  }

  if (buildings.length === 0) return null

  const streamBadge = (status: BuildingStreamStatus | undefined) => {
    if (!status) return null
    const classes: Record<BuildingStreamStatus, string> = {
      extracting: 'bg-blue-500',
      validating: 'bg-yellow-500',
      complete: 'bg-green-500',
      error: 'bg-red-500',
    }
    return <span className={cn('inline-block h-2 w-2 rounded-full shrink-0', classes[status])} />
  }

  return (
    <div className="flex items-center border-b shrink-0 bg-muted/20">
      <button
        type="button"
        onClick={() => scroll('left')}
        className="shrink-0 px-1.5 py-2 text-muted-foreground hover:text-foreground"
        aria-label="Scroll tabs left"
      >
        <ChevronLeft className="h-4 w-4" />
      </button>
      <div
        ref={scrollRef}
        className="flex-1 flex items-center gap-1 overflow-x-auto scrollbar-none py-1.5"
        style={{ scrollbarWidth: 'none' }}
      >
        {buildings.map((b) => {
          const isSelected = b.id === selectedBuildingId
          const errorCount = errorMap.get(b.id) ?? 0
          const status = buildingStatus.get(b.internal_id)
          return (
            <button
              key={b.id}
              type="button"
              onClick={() => onSelect(b.id)}
              className={cn(
                'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm whitespace-nowrap transition-colors shrink-0',
                isSelected
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'hover:bg-muted text-muted-foreground hover:text-foreground'
              )}
            >
              {streamBadge(status)}
              <span className="font-medium truncate max-w-40">
                {b.building_name ?? b.building_code ?? b.internal_id}
              </span>
              <span className={cn(
                'text-xs tabular-nums',
                isSelected ? 'text-primary-foreground/70' : 'text-muted-foreground'
              )}>
                {b.record_count}
              </span>
              {errorCount > 0 && (
                <span className="text-xs bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-400 px-1 py-0.5 rounded-full leading-none">
                  {errorCount}
                </span>
              )}
              <Link
                href={`/source/${sourceId}/building/${encodeURIComponent(b.id)}`}
                onClick={(e) => e.stopPropagation()}
                title="Edit building details"
                className={cn(
                  'p-0.5 rounded transition-colors',
                  isSelected
                    ? 'text-primary-foreground/60 hover:text-primary-foreground'
                    : 'text-muted-foreground/40 hover:text-foreground'
                )}
              >
                <ExternalLink className="h-3 w-3" />
              </Link>
            </button>
          )
        })}
      </div>
      <button
        type="button"
        onClick={() => scroll('right')}
        className="shrink-0 px-1.5 py-2 text-muted-foreground hover:text-foreground"
        aria-label="Scroll tabs right"
      >
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  )
}

/**
 * SourceACMViewContent -- ACM register view with two-tab layout:
 *   Tab 1: Buildings grid (all buildings for this source)
 *   Tab 2: ACM Records (building tab strip + item grid)
 */
function SourceACMViewContent({ sourceId }: { sourceId: string }) {
  const [activeTab, setActiveTab] = useState('buildings')
  const [quickFilter, setQuickFilter] = useState('')
  const [buildingQuickFilter, setBuildingQuickFilter] = useState('')
  const [enableGrouping, setEnableGrouping] = useState(false)
  const [exportOpen, setExportOpen] = useState(false)
  const [commandId, setCommandId] = useState<string | null>(null)
  const [selectedRecords, setSelectedRecords] = useState<ACMRecord[]>([])
  const [editingRecord, setEditingRecord] = useState<ACMRecord | null>(null)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [deletingRecord, setDeletingRecord] = useState<ACMRecord | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const gridRef = useRef<ACMGridRef>(null)
  const queryClient = useQueryClient()
  const { selectedBuildingId, setSelectedBuilding } = useBuildingStore()
  const { data: fieldSchema } = useFieldSchema()
  const deleteRecord = useDeleteACMRecord()

  // Fetch ACM items for the selected building
  const { data: itemsData, isLoading: isLoadingItems } = useACMItems(sourceId, selectedBuildingId)
  const items = useMemo(() => itemsData?.records ?? [], [itemsData])

  // Read commandId from sessionStorage to subscribe to the active extraction SSE stream
  useEffect(() => {
    const key = `acm-extraction-progress-${sourceId}`
    const stored = sessionStorage.getItem(key)
    setCommandId(stored)
  }, [sourceId])

  // Load buildings list for progress bar denominator
  const { data: buildingsData, isLoading: isLoadingBuildings } = useBuildings(sourceId)
  const buildings = useMemo(() => buildingsData?.buildings ?? [], [buildingsData])

  // Streaming progress
  const { isStreaming, completedCount, estimatedSecondsRemaining } = useV3BuildingStream({
    sourceId,
    operationId: commandId,
    totalBuildings: buildings.length,
  })

  // Validation summary for Fix All + Export guard (skip when no buildings)
  const { data: validationSummary } = useValidationSummary(sourceId)
  const bulkFix = useBulkFix()

  const totalErrors = (validationSummary?.buildings ?? []).reduce(
    (sum, b) => sum + b.error_count,
    0
  )

  // Auto-select first building when data loads, or reset when source changes
  useEffect(() => {
    if (buildings.length > 0 && !selectedBuildingId) {
      setSelectedBuilding(buildings[0].id)
    }
  }, [buildings, selectedBuildingId, setSelectedBuilding])

  // Reset selected building when navigating to a different source
  useEffect(() => {
    setSelectedBuilding(null)
  }, [sourceId, setSelectedBuilding])

  // Clear record selection when the viewed building changes (E34-S2)
  useEffect(() => {
    setSelectedRecords([])
  }, [selectedBuildingId])

  const handleBulkFix = () => {
    bulkFix.mutate({ sourceId })
  }

  const handleEdit = (record: ACMRecord) => {
    setEditingRecord(record)
    setEditDialogOpen(true)
  }

  const handleDelete = (record: ACMRecord) => {
    setDeletingRecord(record)
    setDeleteDialogOpen(true)
  }

  const confirmDelete = async () => {
    if (deletingRecord) {
      await deleteRecord.mutateAsync({
        recordId: deletingRecord.id,
        sourceId,
      })
      // Also invalidate the items query used by this page
      queryClient.invalidateQueries({
        queryKey: ACM_ITEMS_QUERY_KEYS.byBuilding(sourceId, selectedBuildingId),
      })
      setDeleteDialogOpen(false)
      setDeletingRecord(null)
    }
  }

  return (
    <AppShell>
      <div className="flex flex-col h-full overflow-hidden">
        {/* Top bar */}
        <div className="flex items-center gap-3 px-4 py-2 border-b bg-background shrink-0">
          <Button variant="ghost" size="sm" asChild>
            <Link href={`/jobs/${sourceId}`}>
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back to Job
            </Link>
          </Button>
          <h1 className="text-lg font-semibold truncate">ACM Register</h1>
          <div className="ml-auto flex items-center gap-2">
            <Button variant="outline" size="sm" asChild>
              <Link href={`/source/${sourceId}/raw`}>
                <Table2 className="h-4 w-4 mr-1" />
                Review Raw Tables
              </Link>
            </Button>

            {/* Export dropdown -- per-building + complete export */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm" title="Export ACM register">
                  <Download className="h-4 w-4 mr-1" />
                  Export
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                {selectedBuildingId && (
                  <>
                    <DropdownMenuItem
                      onClick={async () => {
                        const building = buildings.find((b) => b.id === selectedBuildingId)
                        const label = building?.building_name ?? 'building'
                        const blob = await acmApi.exportSfExcel(sourceId, [selectedBuildingId])
                        const url = URL.createObjectURL(blob)
                        const a = document.createElement('a')
                        a.href = url
                        a.download = `acm-${label.replace(/\s+/g, '-')}.xlsx`
                        a.click()
                        URL.revokeObjectURL(url)
                      }}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Export Current Building
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                  </>
                )}
                <DropdownMenuItem onClick={() => setExportOpen(true)}>
                  <Download className="h-4 w-4 mr-2" />
                  Export All (Options...)
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Streaming progress bar */}
        {isStreaming && (
          <div className="w-full px-4 py-1 bg-muted/50 border-b shrink-0">
            <div className="flex items-center gap-3">
              <div className="flex-1 h-1.5 rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full bg-primary transition-all duration-500"
                  style={{ width: `${Math.round((completedCount / Math.max(1, buildings.length)) * 100)}%` }}
                />
              </div>
              <span className="text-xs text-muted-foreground shrink-0">
                {completedCount}/{buildings.length} buildings
                {estimatedSecondsRemaining !== null && ` · ~${estimatedSecondsRemaining}s remaining`}
              </span>
            </div>
          </div>
        )}

        {/* Two-tab layout: Buildings | ACM Records */}
        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="flex-1 flex flex-col overflow-hidden min-h-0"
        >
          <div className="flex items-center gap-3 px-4 py-2 border-b shrink-0">
            <TabsList>
              <TabsTrigger value="buildings">
                <Building2 className="h-4 w-4 mr-1.5" />
                Buildings
                {buildings.length > 0 && (
                  <span className="ml-1.5 text-xs tabular-nums text-muted-foreground">
                    ({buildings.length})
                  </span>
                )}
              </TabsTrigger>
              <TabsTrigger value="acm-records">
                <Table2 className="h-4 w-4 mr-1.5" />
                ACM Records
              </TabsTrigger>
            </TabsList>

            {/* Buildings tab toolbar */}
            {activeTab === 'buildings' && (
              <div className="ml-auto flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search buildings..."
                    value={buildingQuickFilter}
                    onChange={(e) => setBuildingQuickFilter(e.target.value)}
                    className="w-60 pl-9"
                  />
                </div>
              </div>
            )}

            {/* ACM Records tab toolbar */}
            {activeTab === 'acm-records' && (
              <div className="ml-auto flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search records..."
                    value={quickFilter}
                    onChange={(e) => setQuickFilter(e.target.value)}
                    className="w-60 pl-9"
                  />
                </div>
                <Button
                  variant={enableGrouping ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setEnableGrouping((v) => !v)}
                >
                  Group by Room
                </Button>

                {/* Fix All button -- only visible when there are validation errors */}
                {totalErrors > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleBulkFix}
                    disabled={bulkFix.isPending}
                    title={`Auto-fix ${totalErrors} validation issue${totalErrors !== 1 ? 's' : ''}`}
                  >
                    <Wrench className="h-4 w-4 mr-1" />
                    {bulkFix.isPending ? 'Fixing...' : `Fix All (${totalErrors})`}
                  </Button>
                )}
              </div>
            )}
          </div>

          {/* Buildings tab content */}
          <TabsContent value="buildings" className="flex-1 overflow-hidden min-h-0 p-4">
            {isLoadingBuildings ? (
              <div className="flex items-center justify-center h-full">
                <div className="space-y-3 w-full max-w-lg">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-10 w-full rounded-md" />
                  ))}
                </div>
              </div>
            ) : buildings.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full gap-3">
                <Building2 className="h-10 w-10 text-muted-foreground/40" />
                <p className="text-sm text-muted-foreground font-medium">
                  No buildings extracted yet
                </p>
                <Button variant="outline" size="sm" asChild>
                  <Link href={`/jobs/${sourceId}/extract`}>Go to Extraction</Link>
                </Button>
              </div>
            ) : (
              <BuildingGrid
                buildings={buildings}
                isLoading={isLoadingBuildings}
                sourceId={sourceId}
                quickFilterText={buildingQuickFilter}
                schema={fieldSchema ?? null}
              />
            )}
          </TabsContent>

          {/* ACM Records tab content */}
          <TabsContent value="acm-records" className="flex-1 flex flex-col overflow-hidden min-h-0">
            {/* Bulk operations bar -- visible when records are selected (E34-S2) */}
            {selectedRecords.length > 0 && (
              <BulkOperationsBar
                sourceId={sourceId}
                selectedRecords={selectedRecords}
                onClearSelection={() => setSelectedRecords([])}
                schema={fieldSchema ?? null}
              />
            )}

            {/* Building tabs */}
            <BuildingTabStrip
              buildings={buildings}
              isLoading={!buildingsData}
              selectedBuildingId={selectedBuildingId}
              onSelect={setSelectedBuilding}
              sourceId={sourceId}
              validationSummary={validationSummary}
            />

            {/* Full-width item grid */}
            <div className="flex-1 overflow-hidden p-4 min-h-0">
              {selectedBuildingId ? (
                <ACMGrid
                  ref={gridRef}
                  records={items}
                  isLoading={isLoadingItems}
                  sourceId={sourceId}
                  onEdit={handleEdit}
                  onDelete={handleDelete}
                  enableGrouping={enableGrouping}
                  quickFilterText={quickFilter}
                />
              ) : (
                <div className="flex flex-col items-center justify-center h-full gap-3">
                  <Building2 className="h-10 w-10 text-muted-foreground/40" />
                  <p className="text-sm text-muted-foreground font-medium">
                    {buildings.length > 0
                      ? 'Select a building tab above to view its ACM items'
                      : 'No buildings extracted yet'}
                  </p>
                  {buildings.length === 0 && (
                    <Button variant="outline" size="sm" asChild>
                      <Link href={`/jobs/${sourceId}/extract`}>Go to Extraction</Link>
                    </Button>
                  )}
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Edit record dialog */}
      <ACMRecordDialog
        open={editDialogOpen}
        onOpenChange={(open) => {
          setEditDialogOpen(open)
          if (!open) setEditingRecord(null)
        }}
        sourceId={sourceId}
        record={editingRecord}
        mode="edit"
      />

      {/* Delete confirmation dialog */}
      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete ACM Record"
        description="Are you sure you want to delete this ACM record? This action cannot be undone."
        confirmText="Delete"
        confirmVariant="destructive"
        onConfirm={confirmDelete}
        isLoading={deleteRecord.isPending}
      />

      {/* Export dialog */}
      <ExportDialog
        sourceId={sourceId}
        open={exportOpen}
        onOpenChange={setExportOpen}
        totalErrors={totalErrors}
      />
    </AppShell>
  )
}

/**
 * SourceACMPage -- Next.js 15 page component with async params.
 *
 * URL: /source/[id]
 * Story: E33-S2 Building Grid + Item Grid (Two-View)
 */
export default function SourceACMPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id: sourceId } = use(params)

  return (
    <ErrorBoundary
      fallback={(props) => (
        <PageErrorFallback {...props} pageName="Source ACM View" reloadUrl="/jobs" />
      )}
    >
      <SourceACMViewContent sourceId={decodeURIComponent(sourceId)} />
    </ErrorBoundary>
  )
}
