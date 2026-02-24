'use client'

import { use, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { AppShell } from '@/components/layout/AppShell'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { JobDetailHeader } from '@/components/jobs/JobDetailHeader'
import { JobOverviewTab } from '@/components/jobs/JobOverviewTab'
import { BuildingReviewGrid } from '@/components/acm/BuildingReviewGrid'
import { ACMReviewGrid } from '@/components/acm/ACMReviewGrid'
import { ExtractionProgressPanel } from '@/components/acm/ExtractionProgressPanel'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { MessageSquare } from 'lucide-react'

/**
 * Fetch source details from the API.
 */
async function fetchSource(sourceId: string) {
  const res = await fetch(`/api/sources/${encodeURIComponent(sourceId)}`)
  if (!res.ok) throw new Error(`Failed to fetch source: ${res.statusText}`)
  return res.json()
}

/**
 * Fetch ACM stats for record and building counts.
 */
async function fetchAcmStats(sourceId: string) {
  const res = await fetch(`/api/acm/stats?source_id=${encodeURIComponent(sourceId)}`)
  if (!res.ok) throw new Error(`Failed to fetch ACM stats: ${res.statusText}`)
  return res.json()
}

/**
 * JobDetailPageContent — inner content for the job detail page.
 *
 * Displays a 4-tab view: Overview, Buildings, ACM Records, and Extraction Log.
 *
 * URL: /jobs/{source_id}
 * Story: E19-S7 Job Detail Page
 */
function JobDetailPageContent({ sourceId }: { sourceId: string }) {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('overview')

  const { data: source } = useQuery({
    queryKey: ['source', sourceId],
    queryFn: () => fetchSource(sourceId),
  })

  const { data: stats } = useQuery({
    queryKey: ['acm-stats', sourceId],
    queryFn: () => fetchAcmStats(sourceId),
  })

  const { data: extractionProgress } = useQuery({
    queryKey: ['extraction-progress', source?.command_id],
    queryFn: async () => {
      const commandId = source?.command_id
      if (!commandId) return null
      const res = await fetch(`/api/acm/extraction-progress/${encodeURIComponent(commandId)}`)
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
    window.open(`/api/acm/export/csv?source_id=${encodeURIComponent(sourceId)}`, '_blank')
  }, [sourceId])

  const handleExportExcel = useCallback(() => {
    window.open(`/api/acm/export/excel?source_id=${encodeURIComponent(sourceId)}`, '_blank')
  }, [sourceId])

  const handleRename = useCallback(
    async (newTitle: string) => {
      await fetch(`/api/sources/${encodeURIComponent(sourceId)}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: newTitle }),
      })
      await queryClient.invalidateQueries({ queryKey: ['source', sourceId] })
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

  return (
    <AppShell>
      <div className="flex flex-col h-full overflow-hidden">
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

        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="flex-1 flex flex-col overflow-hidden"
        >
          <div className="px-4 pt-3 pb-0 flex-shrink-0 flex items-center gap-4">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="buildings">Buildings</TabsTrigger>
              <TabsTrigger value="records">ACM Records</TabsTrigger>
              <TabsTrigger value="log">Extraction Log</TabsTrigger>
            </TabsList>
            <Link
              href={`/jobs/${sourceId}/chat`}
              className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors ml-2"
            >
              <MessageSquare className="h-4 w-4" />
              CRUD Chat
            </Link>
          </div>

          <div className="flex-1 overflow-auto">
            <TabsContent value="overview" className="p-4 m-0">
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

            <TabsContent value="buildings" className="p-4 m-0 h-full">
              <BuildingReviewGrid sourceId={sourceId} />
            </TabsContent>

            <TabsContent value="records" className="p-4 m-0 h-full">
              <ACMReviewGrid sourceId={sourceId} />
            </TabsContent>

            <TabsContent value="log" className="p-4 m-0">
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
                <div className="text-muted-foreground text-sm">
                  No extraction log available yet for this job.
                </div>
              )}
            </TabsContent>
          </div>
        </Tabs>
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
