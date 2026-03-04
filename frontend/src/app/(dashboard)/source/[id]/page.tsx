'use client'

import { use, useState, useEffect } from 'react'
import Link from 'next/link'
import { AppShell } from '@/components/layout/AppShell'
import { BuildingSidebar } from '@/components/acm/BuildingSidebar'
import { ItemGrid } from '@/components/acm/ItemGrid'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { useBuildingStore } from '@/lib/stores/buildingStore'
import { ArrowLeft, Table2 } from 'lucide-react'

/**
 * SourceACMViewContent — inner content for the two-panel ACM register view.
 *
 * Manages local quick-filter text and room-grouping toggle state.
 * Reads selected building from Zustand buildingStore.
 */
function SourceACMViewContent({ sourceId }: { sourceId: string }) {
  const [quickFilter, setQuickFilter] = useState('')
  const [enableGrouping, setEnableGrouping] = useState(false)
  const { selectedBuildingId, setSelectedBuilding } = useBuildingStore()

  // Reset selected building when navigating to a different source
  useEffect(() => {
    setSelectedBuilding(null)
  }, [sourceId, setSelectedBuilding])

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
            <Input
              placeholder="Search records..."
              value={quickFilter}
              onChange={(e) => setQuickFilter(e.target.value)}
              className="w-60"
            />
            <Button
              variant={enableGrouping ? 'default' : 'outline'}
              size="sm"
              onClick={() => setEnableGrouping((v) => !v)}
            >
              Group by Room
            </Button>
          </div>
        </div>

        {/* Two-panel body */}
        <div className="flex flex-1 overflow-hidden min-h-0">
          <BuildingSidebar sourceId={sourceId} />
          <div className="flex-1 overflow-hidden p-4 min-h-0">
            {selectedBuildingId ? (
              <ItemGrid
                sourceId={sourceId}
                buildingId={selectedBuildingId}
                quickFilterText={quickFilter}
                enableGrouping={enableGrouping}
              />
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                Select a building to view its ACM items
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  )
}

/**
 * SourceACMPage — Next.js 15 page component with async params.
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
        <PageErrorFallback {...props} pageName="Source ACM View" reloadUrl="/sources" />
      )}
    >
      <SourceACMViewContent sourceId={decodeURIComponent(sourceId)} />
    </ErrorBoundary>
  )
}
