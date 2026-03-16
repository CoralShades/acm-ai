'use client'

import { use, useState, useCallback, useEffect, useMemo, useRef } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { AppShell } from '@/components/layout/AppShell'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent } from '@/components/ui/sheet'
import { JobDetailHeader } from '@/components/jobs/JobDetailHeader'
import { JobOverviewTab } from '@/components/jobs/JobOverviewTab'
import { JobContentPanel } from '@/components/jobs/JobContentPanel'
import { JobCrudChatPanel } from '@/components/jobs/JobCrudChatPanel'
import { BuildingGrid } from '@/components/acm/BuildingGrid'
import {
  BuildingTabFilter,
  getRecordBuildingTabId,
} from '@/components/acm/BuildingTabFilter'
import { ACMGrid, type ACMGridRef } from '@/components/acm/ACMGrid'
import { ColumnVisibilityPicker } from '@/components/acm/ColumnVisibilityPicker'
import { ACMRecordDialog } from '@/components/acm/ACMRecordDialog'
import { ACMRecordDetailDialog } from '@/components/acm/ACMRecordDetailDialog'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { RawTableViewer } from '@/components/acm/RawTableViewer'
import { ExtractionProgressPanel } from '@/components/acm/ExtractionProgressPanel'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { useSource } from '@/lib/hooks/use-sources'
import { useBuildings } from '@/lib/hooks/useBuildings'
import { useFieldSchema } from '@/lib/hooks/useACMItems'
import { useACMStats, useDeleteACMRecord } from '@/lib/hooks/use-acm'
import { sourcesApi } from '@/lib/api/sources'
import { acmApi } from '@/lib/api/acm'
import type { ACMRecord } from '@/lib/types/acm'
import { cn } from '@/lib/utils'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ChevronLeft, ChevronRight, MessageSquare, Download } from 'lucide-react'

const KEY_FIELDS = ['room_name', 'product', 'result', 'friable', 'material_condition', 'sample_no', 'sample_result'] as const

/**
 * JobDetailPageContent — inner content for the job detail page.
 *
 * Displays a two-column layout:
 * - Left: Overview, Buildings, ACM Records, Content, Extraction Log tabs
 * - Right: Inline CRUD chat panel
 *
 * URL: /jobs/{source_id}
 * Story: E19-S7 Job Detail Page
 */
function JobDetailPageContent({ sourceId }: { sourceId: string }) {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedBuilding, setSelectedBuilding] = useState<string | null>(null)
  const [chatExpanded, setChatExpanded] = useState(false)
  const [mobileChatOpen, setMobileChatOpen] = useState(false)

  // ACM Records tab state (ACMGrid + dialogs)
  const gridRef = useRef<ACMGridRef>(null)
  const [editingRecord, setEditingRecord] = useState<ACMRecord | null>(null)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [deletingRecord, setDeletingRecord] = useState<ACMRecord | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [detailRecord, setDetailRecord] = useState<ACMRecord | null>(null)
  const [detailDialogOpen, setDetailDialogOpen] = useState(false)
  const deleteRecordMutation = useDeleteACMRecord()

  const { data: source } = useSource(sourceId)
  const { data: stats } = useACMStats(sourceId)
  const { data: buildingsData, isLoading: isLoadingBuildings } = useBuildings(sourceId)
  const buildings = useMemo(() => buildingsData?.buildings ?? [], [buildingsData])
  const { data: fieldSchema } = useFieldSchema()
  const { data: records = [], refetch: refetchRecords } = useQuery<ACMRecord[]>({
    queryKey: ['acm-records', sourceId],
    queryFn: () =>
      fetch(`/api/acm/records?source_id=${encodeURIComponent(sourceId)}&limit=500`)
        .then((response) => response.json())
        .then((data) => (Array.isArray(data) ? data : (data.records ?? []))),
    staleTime: 30_000,
  })

  const { data: extractionProgress } = useQuery({
    queryKey: ['extraction-progress', source?.command_id],
    queryFn: async () => {
      const commandId = source?.command_id
      if (!commandId) return null
      const res = await fetch(
        `/api/acm/extraction-progress/${encodeURIComponent(commandId)}`
      )
      if (!res.ok) return null
      return res.json()
    },
    enabled: !!source?.command_id,
    staleTime: 15_000,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'running') return 3000
      return false
    },
  })

  const handleReExtract = useCallback(async () => {
    await fetch('/api/acm/extract', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_id: sourceId, force: true }),
    })
    await fetch(`/api/sources/${encodeURIComponent(sourceId)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ review_status: 'extracting' }),
    })
    router.push(`/jobs/${sourceId}/extract`)
  }, [sourceId, router])

  const handleExportCsv = useCallback(() => {
    window.open(
      `/api/acm/export/csv?source_id=${encodeURIComponent(sourceId)}`,
      '_blank'
    )
  }, [sourceId])

  const handleExportExcel = useCallback(() => {
    window.open(
      `/api/acm/export/excel?source_id=${encodeURIComponent(sourceId)}`,
      '_blank'
    )
  }, [sourceId])

  const handleRename = useCallback(
    async (newTitle: string) => {
      await sourcesApi.update(sourceId, { title: newTitle })
      await queryClient.invalidateQueries({ queryKey: ['sources', sourceId] })
      await queryClient.invalidateQueries({ queryKey: ['sources'] })
    },
    [queryClient, sourceId]
  )

  const panelPhase: 'idle' | 'extracting' | 'completed' | 'failed' =
    extractionProgress?.status === 'running'
      ? 'extracting'
      : extractionProgress?.status === 'completed'
        ? 'completed'
        : extractionProgress?.status === 'failed'
          ? 'failed'
          : 'idle'

  // ACM Records tab handlers
  const handleEditRecord = useCallback((record: ACMRecord) => {
    setEditingRecord(record)
    setEditDialogOpen(true)
  }, [])

  const handleDeleteRecord = useCallback((record: ACMRecord) => {
    setDeletingRecord(record)
    setDeleteDialogOpen(true)
  }, [])

  const confirmDeleteRecord = useCallback(async () => {
    if (deletingRecord) {
      await deleteRecordMutation.mutateAsync({
        recordId: deletingRecord.id,
        sourceId,
      })
      setDeleteDialogOpen(false)
      setDeletingRecord(null)
      void refetchRecords()
    }
  }, [deletingRecord, deleteRecordMutation, sourceId, refetchRecords])

  const handleRowClick = useCallback((record: ACMRecord) => {
    setDetailRecord(record)
    setDetailDialogOpen(true)
  }, [])

  const handleEditFromDetail = useCallback((record: ACMRecord) => {
    setDetailDialogOpen(false)
    setDetailRecord(null)
    handleEditRecord(record)
  }, [handleEditRecord])

  useEffect(() => {
    setSelectedBuilding(null)
  }, [sourceId])

  useEffect(() => {
    if (!selectedBuilding) {
      return
    }

    const buildingExists = records.some(
      (record) => getRecordBuildingTabId(record) === selectedBuilding
    )
    if (!buildingExists) {
      setSelectedBuilding(null)
    }
  }, [records, selectedBuilding])

  // Filter records by selected building for the ACM Records tab
  const filteredRecords = useMemo(() => {
    if (!selectedBuilding) return records
    return records.filter(
      (record) => getRecordBuildingTabId(record) === selectedBuilding
    )
  }, [records, selectedBuilding])

  // Compute missing fields % and extraction quality score from actual record data

  const missingFieldsPercent = useMemo<number | null>(() => {
    if (records.length === 0) return null
    let emptyCount = 0
    for (const record of records) {
      for (const field of KEY_FIELDS) {
        const value = record[field]
        if (value === null || value === undefined || value === '') {
          emptyCount++
        }
      }
    }
    const pct = (emptyCount / (records.length * KEY_FIELDS.length)) * 100
    return Math.round(pct * 10) / 10
  }, [records])

  const extractionQualityScore = useMemo<number | null>(() => {
    if (records.length === 0) return null
    let score = 100
    for (const record of records) {
      if (!record.sample_no) score -= 2
      if (!record.room_name) score -= 3
      // Check for "Unknown" in key text fields
      const textFields = [record.product, record.result, record.friable, record.material_condition, record.room_name] as const
      for (const val of textFields) {
        if (typeof val === 'string' && val.toLowerCase() === 'unknown') {
          score -= 1
        }
      }
    }
    return Math.max(0, Math.min(100, score))
  }, [records])

  return (
    <AppShell>
      <div className="flex h-full w-full min-h-0 flex-col">
        <div className="flex-shrink-0 px-6 pb-4 pt-6">
          <JobDetailHeader
            sourceId={sourceId}
            title={source?.title ?? null}
            reviewStatus={source?.review_status}
            createdAt={source?.created ?? null}
            recordCount={stats?.total_records}
            buildingCount={stats?.building_count}
            onRename={handleRename}
            onReExtract={handleReExtract}
            onExportCsv={handleExportCsv}
            onExportExcel={handleExportExcel}
          />
        </div>

        <div className="flex min-h-0 flex-1 px-6 pb-6">
          <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl border bg-card shadow-sm">
            <Tabs
              value={activeTab}
              onValueChange={setActiveTab}
              className="flex h-full min-h-0 flex-col"
            >
              <div className="flex-shrink-0 border-b p-2 flex items-center gap-2">
                <TabsList className="flex-1 justify-start overflow-x-auto">
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="buildings">Buildings</TabsTrigger>
                  <TabsTrigger value="records">ACM Records</TabsTrigger>
                  <TabsTrigger value="content">Content</TabsTrigger>
                </TabsList>
              </div>

              <div className="min-h-0 flex-1 overflow-hidden">
                <TabsContent
                  value="overview"
                  className="m-0 h-full overflow-auto p-4 sm:p-6"
                >
                  <JobOverviewTab
                    sourceId={sourceId}
                    recordCount={stats?.total_records ?? 0}
                    buildingCount={stats?.building_count ?? 0}
                    reviewStatus={source?.review_status}
                    missingFieldsPercent={missingFieldsPercent}
                    extractionQualityScore={extractionQualityScore}
                    onReExtract={handleReExtract}
                  />
                </TabsContent>

                <TabsContent
                  value="buildings"
                  className="m-0 h-full overflow-auto p-4 sm:p-6"
                >
                  <Card className="rounded-xl shadow-sm">
                    <CardContent className="p-4 sm:p-6">
                      <BuildingGrid
                        buildings={buildings}
                        isLoading={isLoadingBuildings}
                        sourceId={sourceId}
                        schema={fieldSchema ?? null}
                      />
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent
                  value="records"
                  className="m-0 h-full overflow-auto p-4 sm:p-6"
                >
                  <Card className="rounded-xl shadow-sm">
                    <CardContent className="space-y-4 p-4 sm:p-6">
                      <div className="flex items-center justify-between">
                        <BuildingTabFilter
                          records={records}
                          selectedBuilding={selectedBuilding}
                          onBuildingChange={setSelectedBuilding}
                        />
                        {/* Column visibility picker */}
                        <ColumnVisibilityPicker
                          gridApi={gridRef.current?.getGridApi() ?? null}
                          onResetColumns={() => gridRef.current?.resetColumns()}
                        />
                        {/* Per-building + complete export */}
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="outline" size="sm">
                              <Download className="h-4 w-4 mr-1" />
                              Export
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end" className="w-56">
                            {selectedBuilding && (
                              <>
                                <DropdownMenuItem
                                  onClick={async () => {
                                    const buildingRecord = buildings.find(
                                      (b) => b.id === selectedBuilding || b.internal_id === selectedBuilding
                                    )
                                    const label = buildingRecord?.building_name ?? 'building'
                                    const buildingIds = buildingRecord ? [buildingRecord.id] : [selectedBuilding]
                                    const blob = await acmApi.exportSfExcel(sourceId, buildingIds)
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
                            <DropdownMenuItem onClick={handleExportExcel}>
                              <Download className="h-4 w-4 mr-2" />
                              Export All (Excel)
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={handleExportCsv}>
                              <Download className="h-4 w-4 mr-2" />
                              Export All (CSV)
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                      <ACMGrid
                        ref={gridRef}
                        records={filteredRecords}
                        onEdit={handleEditRecord}
                        onDelete={handleDeleteRecord}
                        onRowClick={handleRowClick}
                        sourceId={sourceId}
                      />
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="content" className="m-0 h-full p-4 sm:p-6">
                  <JobContentPanel sourceId={sourceId} />
                </TabsContent>

                <TabsContent
                  value="raw-tables"
                  className="m-0 h-full overflow-auto p-4 sm:p-6"
                >
                  <Card className="rounded-xl shadow-sm">
                    <CardContent className="p-4 sm:p-6">
                      <RawTableViewer sourceId={sourceId} />
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent
                  value="log"
                  className="m-0 h-full overflow-auto p-4 sm:p-6"
                >
                  <Card className="rounded-xl shadow-sm">
                    <CardContent className="p-4 sm:p-6">
                      {source?.command_id ? (
                        <ExtractionProgressPanel
                          phase={panelPhase}
                          pipelineState={extractionProgress?.state ?? null}
                          logEntries={extractionProgress?.log_entries ?? []}
                          recordsCreated={extractionProgress?.state?.total_records}
                          errorMessage={
                            extractionProgress?.state?.error ??
                            (extractionProgress?.status === 'failed'
                              ? 'Extraction failed'
                              : undefined)
                          }
                          onDismiss={() => {}}
                        />
                      ) : (
                        <div className="text-sm text-muted-foreground">
                          No extraction log available yet for this job.
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>
              </div>
            </Tabs>
          </div>

          <div
            className={cn(
              'ml-4 hidden min-h-0 rounded-xl border bg-card shadow-sm transition-[width] duration-200 lg:flex lg:flex-col',
              chatExpanded ? 'w-[380px]' : 'w-14'
            )}
          >
            <div
              className={cn(
                'flex items-center border-b py-2',
                chatExpanded ? 'justify-between px-3' : 'justify-center px-2'
              )}
            >
              {chatExpanded && (
                <div className="flex items-center gap-2 text-sm font-medium">
                  <MessageSquare className="h-4 w-4" />
                  CRUD Chat
                </div>
              )}
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={() => setChatExpanded((prev) => !prev)}
                aria-label={chatExpanded ? 'Collapse chat panel' : 'Expand chat panel'}
              >
                {chatExpanded ? (
                  <ChevronRight className="h-4 w-4" />
                ) : (
                  <ChevronLeft className="h-4 w-4" />
                )}
              </Button>
            </div>
            {chatExpanded && (
              <div className="min-h-0 flex-1">
                <JobCrudChatPanel sourceId={sourceId} className="h-full" />
              </div>
            )}
          </div>
        </div>

        <Button
          type="button"
          size="icon"
          className="fixed bottom-6 right-6 z-40 h-12 w-12 rounded-full shadow-lg lg:hidden"
          aria-label="Open CRUD chat"
          onClick={() => setMobileChatOpen(true)}
        >
          <MessageSquare className="h-5 w-5" />
        </Button>

        <Sheet open={mobileChatOpen} onOpenChange={setMobileChatOpen}>
          <SheetContent side="right" className="w-full p-0 sm:max-w-md">
            <div className="flex h-full min-h-0 flex-col pt-10">
              <div className="border-b px-4 py-3">
                <h2 className="text-sm font-semibold">CRUD Chat</h2>
                <p className="mt-1 text-xs text-muted-foreground">
                  Create, update, and delete ACM records with explicit confirmation.
                </p>
              </div>
              <div className="min-h-0 flex-1">
                <JobCrudChatPanel sourceId={sourceId} className="h-full" />
              </div>
            </div>
          </SheetContent>
        </Sheet>

        {/* ACM Records tab dialogs */}
        <ACMRecordDialog
          open={editDialogOpen}
          onOpenChange={setEditDialogOpen}
          sourceId={sourceId}
          record={editingRecord}
          mode="edit"
        />

        <ACMRecordDetailDialog
          open={detailDialogOpen}
          onOpenChange={setDetailDialogOpen}
          record={detailRecord}
          onEdit={handleEditFromDetail}
        />

        <ConfirmDialog
          open={deleteDialogOpen}
          onOpenChange={setDeleteDialogOpen}
          title="Delete ACM Record"
          description="Are you sure you want to delete this ACM record? This action cannot be undone."
          confirmText="Delete"
          confirmVariant="destructive"
          onConfirm={confirmDeleteRecord}
          isLoading={deleteRecordMutation.isPending}
        />
      </div>
    </AppShell>
  )
}

/**
 * JobDetailPage — Next.js 15 page component with async params.
 *
 * URL: /jobs/[id]
 * Story: E19-S7 Job Detail Page
 */
export default function JobDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id: sourceId } = use(params)

  return (
    <ErrorBoundary
      fallback={(props) => (
        <PageErrorFallback
          {...props}
          pageName="Job Detail"
          reloadUrl="/jobs"
        />
      )}
    >
      <JobDetailPageContent sourceId={decodeURIComponent(sourceId)} />
    </ErrorBoundary>
  )
}
