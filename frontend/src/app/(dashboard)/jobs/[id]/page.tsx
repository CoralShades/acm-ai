'use client'

import { use, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { AppShell } from '@/components/layout/AppShell'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { JobDetailHeader } from '@/components/jobs/JobDetailHeader'
import { JobOverviewTab } from '@/components/jobs/JobOverviewTab'
import { BuildingReviewGrid } from '@/components/acm/BuildingReviewGrid'
import { ACMReviewGrid } from '@/components/acm/ACMReviewGrid'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'

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
  const [activeTab, setActiveTab] = useState('overview')

  const { data: source } = useQuery({
    queryKey: ['source', sourceId],
    queryFn: () => fetchSource(sourceId),
  })

  const { data: stats } = useQuery({
    queryKey: ['acm-stats', sourceId],
    queryFn: () => fetchAcmStats(sourceId),
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
    window.open(`/api/acm/export?source_id=${encodeURIComponent(sourceId)}`, '_blank')
  }, [sourceId])

  const handleExportExcel = useCallback(() => {
    window.open(`/api/acm/export/excel?source_id=${encodeURIComponent(sourceId)}`, '_blank')
  }, [sourceId])

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
          onReExtract={handleReExtract}
          onExportCsv={handleExportCsv}
          onExportExcel={handleExportExcel}
        />

        <Tabs
          value={activeTab}
          onValueChange={setActiveTab}
          className="flex-1 flex flex-col overflow-hidden"
        >
          <div className="px-4 pt-3 pb-0 flex-shrink-0">
            <TabsList>
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="buildings">Buildings</TabsTrigger>
              <TabsTrigger value="records">ACM Records</TabsTrigger>
              <TabsTrigger value="log">Extraction Log</TabsTrigger>
            </TabsList>
          </div>

          <div className="flex-1 overflow-auto">
            <TabsContent value="overview" className="p-4 m-0">
              <JobOverviewTab
                sourceId={sourceId}
                recordCount={stats?.total_records ?? 0}
                buildingCount={stats?.building_count ?? 0}
                reviewStatus={source?.review_status}
                createdAt={source?.created ?? null}
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
              <div className="text-muted-foreground text-sm">
                Extraction log for this job.
              </div>
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
