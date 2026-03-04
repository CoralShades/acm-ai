'use client'

import { use, useState, useEffect } from 'react'
import Link from 'next/link'
import { AppShell } from '@/components/layout/AppShell'
import { BuildingSidebar } from '@/components/acm/BuildingSidebar'
import { ItemGrid } from '@/components/acm/ItemGrid'
import { BulkOperationsBar } from '@/components/acm/BulkOperationsBar'
import { ExportDialog } from '@/components/acm/ExportDialog'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { useBuildingStore } from '@/lib/stores/buildingStore'
import { useBuildings } from '@/lib/hooks/useBuildings'
import { useValidationSummary, useBulkFix, useFieldSchema } from '@/lib/hooks/useACMItems'
import { useV3BuildingStream } from '@/lib/hooks/useV3BuildingStream'
import type { ACMRecord } from '@/lib/types/acm'
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
  const [exportOpen, setExportOpen] = useState(false)
  const [commandId, setCommandId] = useState<string | null>(null)
  const [selectedRecords, setSelectedRecords] = useState<ACMRecord[]>([])
  const { selectedBuildingId, setSelectedBuilding } = useBuildingStore()
  const { data: fieldSchema } = useFieldSchema()

  // Read commandId from sessionStorage to subscribe to the active extraction SSE stream
  useEffect(() => {
    const key = `acm-extraction-progress-${sourceId}`
    const stored = sessionStorage.getItem(key)
    setCommandId(stored)
  }, [sourceId])

  // Load buildings list for progress bar denominator
  const { data: buildingsData } = useBuildings(sourceId)
  const buildings = buildingsData?.buildings ?? []

  // Streaming progress
  const { isStreaming, completedCount, estimatedSecondsRemaining } = useV3BuildingStream({
    sourceId,
    operationId: commandId,
    totalBuildings: buildings.length,
  })

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

  // Clear record selection when the viewed building changes (E34-S2)
  useEffect(() => {
    setSelectedRecords([])
  }, [selectedBuildingId])

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

            {/* Export button — opens ExportDialog */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setExportOpen(true)}
              title="Export ACM register"
            >
              <Download className="h-4 w-4 mr-1" />
              Export
            </Button>
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

        {/* Bulk operations bar — visible when records are selected (E34-S2) */}
        {selectedRecords.length > 0 && (
          <BulkOperationsBar
            sourceId={sourceId}
            selectedRecords={selectedRecords}
            onClearSelection={() => setSelectedRecords([])}
            schema={fieldSchema ?? null}
          />
        )}

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
                onSelectionChanged={(recs) => setSelectedRecords(recs)}
              />
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                Select a building to view its ACM items
              </div>
            )}
          </div>
        </div>
      </div>

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
