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
import { useValidationSummary, useBulkFix } from '@/lib/hooks/useACMItems'
import { acmApi } from '@/lib/api/acm'
import { ArrowLeft, Table2, Wrench, Download } from 'lucide-react'

/**
 * SourceACMViewContent — inner content for the two-panel ACM register view.
 *
 * Manages local quick-filter text and room-grouping toggle state.
 * Reads selected building from Zustand buildingStore.
 */
function SourceACMViewContent({ sourceId }: { sourceId: string }) {
  const [quickFilter, setQuickFilter] = useState('')
  const [enableGrouping, setEnableGrouping] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const { selectedBuildingId, setSelectedBuilding } = useBuildingStore()

  // Validation summary for Fix All + Export guard
  const { data: validationSummary } = useValidationSummary(sourceId)
  const bulkFix = useBulkFix()

  const totalErrors = (validationSummary?.buildings ?? []).reduce(
    (sum, b) => sum + b.error_count,
    0
  )

  // Reset selected building when navigating to a different source
  useEffect(() => {
    setSelectedBuilding(null)
  }, [sourceId, setSelectedBuilding])

  const handleExport = async () => {
    setIsExporting(true)
    try {
      const blob = await acmApi.exportExcel(sourceId)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `acm-register-${sourceId}.xlsx`
      a.click()
      URL.revokeObjectURL(url)
    } finally {
      setIsExporting(false)
    }
  }

  const handleBulkFix = () => {
    bulkFix.mutate({ sourceId })
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

            {/* Fix All button — only visible when there are validation errors */}
            {totalErrors > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleBulkFix}
                disabled={bulkFix.isPending}
                title={`Auto-fix ${totalErrors} validation issue${totalErrors !== 1 ? 's' : ''}`}
              >
                <Wrench className="h-4 w-4 mr-1" />
                {bulkFix.isPending ? 'Fixing…' : `Fix All (${totalErrors})`}
              </Button>
            )}

            {/* Export button — disabled when validation errors exist */}
            <Button
              variant="outline"
              size="sm"
              onClick={handleExport}
              disabled={isExporting || totalErrors > 0}
              title={
                totalErrors > 0
                  ? `Export disabled: ${totalErrors} validation error${totalErrors !== 1 ? 's' : ''} must be resolved first`
                  : 'Export ACM register as Excel'
              }
            >
              <Download className="h-4 w-4 mr-1" />
              {isExporting ? 'Exporting…' : 'Export'}
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
