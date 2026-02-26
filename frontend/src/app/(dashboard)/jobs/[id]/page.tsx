'use client'

import { use, useState, useCallback, useEffect } from 'react'
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
import { BuildingReviewGrid } from '@/components/acm/BuildingReviewGrid'
import {
  BuildingTabFilter,
  getRecordBuildingTabId,
} from '@/components/acm/BuildingTabFilter'
import { ACMReviewGrid } from '@/components/acm/ACMReviewGrid'
import { ExtractionProgressPanel } from '@/components/acm/ExtractionProgressPanel'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { useSource } from '@/lib/hooks/use-sources'
import { useACMStats } from '@/lib/hooks/use-acm'
import { sourcesApi } from '@/lib/api/sources'
import type { ACMRecord } from '@/lib/types/acm'
import { cn } from '@/lib/utils'
import { ChevronLeft, ChevronRight, MessageSquare } from 'lucide-react'

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
  const [chatExpanded, setChatExpanded] = useState(true)
  const [mobileChatOpen, setMobileChatOpen] = useState(false)

  const { data: source } = useSource(sourceId)
  const { data: stats } = useACMStats(sourceId)
  const { data: records = [] } = useQuery<ACMRecord[]>({
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
              <div className="flex-shrink-0 border-b p-2">
                <TabsList className="w-full justify-start overflow-x-auto">
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="buildings">Buildings</TabsTrigger>
                  <TabsTrigger value="records">ACM Records</TabsTrigger>
                  <TabsTrigger value="content">Content</TabsTrigger>
                  <TabsTrigger value="log">Extraction Log</TabsTrigger>
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
                    missingFieldsPercent={null}
                    extractionQualityScore={null}
                    onReExtract={handleReExtract}
                  />
                </TabsContent>

                <TabsContent
                  value="buildings"
                  className="m-0 h-full overflow-auto p-4 sm:p-6"
                >
                  <Card className="rounded-xl shadow-sm">
                    <CardContent className="p-4 sm:p-6">
                      <BuildingReviewGrid sourceId={sourceId} />
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent
                  value="records"
                  className="m-0 h-full overflow-auto p-4 sm:p-6"
                >
                  <Card className="rounded-xl shadow-sm">
                    <CardContent className="space-y-4 p-4 sm:p-6">
                      <BuildingTabFilter
                        records={records}
                        selectedBuilding={selectedBuilding}
                        onBuildingChange={setSelectedBuilding}
                      />
                      <ACMReviewGrid
                        sourceId={sourceId}
                        buildingId={selectedBuilding}
                      />
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="content" className="m-0 h-full p-4 sm:p-6">
                  <JobContentPanel sourceId={sourceId} />
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
