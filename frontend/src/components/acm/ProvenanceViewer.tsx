'use client'

import { useCallback } from 'react'
import { AlertCircle, RefreshCw, X, FileText, MapPin, Building2, Hash } from 'lucide-react'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { PDFPageViewer } from './PDFPageViewer'
import type { PDFBbox } from './PDFPageViewer'
import { LineageTable } from './LineageTable'
import { useProvenance } from '@/lib/hooks/useProvenance'
import { cn } from '@/lib/utils'

interface ProvenanceViewerProps {
  sourceId: string
  recordId: string
  mode: 'panel' | 'page'
  onClose?: () => void
}

/**
 * Construct a PDF URL from the file path returned by the backend.
 *
 * If the path starts with "http", use it directly.
 * Otherwise proxy through the backend using the source file endpoint.
 */
function buildPdfUrl(sourceId: string, filePath: string | null): string | null {
  if (!filePath) return null
  if (filePath.startsWith('http://') || filePath.startsWith('https://')) {
    return filePath
  }
  // Proxy through backend: /api/sources/{sourceId}/file
  return `/api/sources/${encodeURIComponent(sourceId)}/file`
}

/** Inner content — shared between panel and page modes */
function ProvenanceContent({
  sourceId,
  recordId,
}: {
  sourceId: string
  recordId: string
}) {
  const { data, isLoading, isError, error, refetch } = useProvenance(recordId)

  const handleRetry = useCallback(() => {
    refetch()
  }, [refetch])

  if (isLoading) {
    return (
      <div className="space-y-4 p-4">
        <Skeleton className="h-6 w-48" />
        <Skeleton className="h-4 w-64" />
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-32 w-full" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 p-8 text-center">
        <AlertCircle className="h-10 w-10 text-destructive" />
        <div>
          <p className="font-medium">Failed to load provenance data</p>
          <p className="text-sm text-muted-foreground mt-1">
            {error instanceof Error ? error.message : 'An unexpected error occurred'}
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={handleRetry}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Retry
        </Button>
      </div>
    )
  }

  if (!data) return null

  const { record, table_section, raw_extractions, source_file_path, source_title } = data
  const pdfUrl = buildPdfUrl(sourceId, source_file_path)

  // Extract bbox from record.table_bbox if available (TableBoundingBox from generated types)
  // The ACMRecord type currently doesn't include table_bbox — access via unknown cast
  const tableBbox = (record as unknown as Record<string, unknown>)['table_bbox'] as PDFBbox | null | undefined
  const bbox: PDFBbox | null = tableBbox
    ? { x: tableBbox.x, y: tableBbox.y, width: tableBbox.width, height: tableBbox.height }
    : null

  const pageNumber = record.page_number ?? 1

  return (
    <div className="flex flex-col gap-6 p-4 overflow-y-auto">
      {/* Record identity card */}
      <div className="rounded-lg border bg-muted/20 p-3 space-y-2">
        {source_title && (
          <div className="flex items-center gap-2 text-sm">
            <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
            <span className="font-medium truncate">{source_title}</span>
          </div>
        )}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
          {record.building_name && (
            <span className="flex items-center gap-1.5 text-muted-foreground">
              <Building2 className="h-3.5 w-3.5 shrink-0" />
              {record.building_name}
            </span>
          )}
          {record.room_name && (
            <span className="flex items-center gap-1.5 text-muted-foreground">
              <MapPin className="h-3.5 w-3.5 shrink-0" />
              {record.room_name}
            </span>
          )}
          {pageNumber > 0 && (
            <Badge variant="secondary" className="text-xs">
              <Hash className="h-3 w-3 mr-0.5" />
              Page {pageNumber}
            </Badge>
          )}
        </div>
        <p className="text-sm font-medium">{record.product}</p>
        {record.material_description && (
          <p className="text-xs text-muted-foreground">{record.material_description}</p>
        )}
      </div>

      {/* PDF page viewer */}
      <div className="space-y-2">
        <h3 className="text-sm font-semibold">Source Document</h3>
        <PDFPageViewer
          pdfUrl={pdfUrl}
          pageNumber={pageNumber}
          bbox={bbox}
          className="w-full"
        />
      </div>

      {/* Extraction lineage */}
      <div className="space-y-2">
        <h3 className="text-sm font-semibold">Extraction Lineage</h3>
        {table_section && (
          <p className="text-xs text-muted-foreground">
            Table pages {table_section.page_start}–{table_section.page_end}
            {table_section.building_name && ` · ${table_section.building_name}`}
            {table_section.table_type && ` · ${table_section.table_type}`}
          </p>
        )}
        <LineageTable
          rawExtractions={raw_extractions}
          consensusTier={table_section?.consensus_tier}
          consensusScores={table_section?.consensus_scores ?? undefined}
        />
      </div>
    </div>
  )
}

/**
 * ProvenanceViewer — slide-over panel or full-page provenance display.
 *
 * - panel mode: renders inside a Radix Sheet (slide-over from right)
 * - page mode: full-page layout used by the /provenance/:recordId route
 *
 * Story: E33-S6 Provenance Viewer
 */
export function ProvenanceViewer({ sourceId, recordId, mode, onClose }: ProvenanceViewerProps) {
  if (mode === 'panel') {
    const isOpen = !!recordId

    return (
      <Sheet
        open={isOpen}
        onOpenChange={(open) => {
          if (!open && onClose) onClose()
        }}
      >
        <SheetContent
          side="right"
          className={cn('w-full sm:max-w-2xl overflow-y-auto p-0')}
          aria-describedby="provenance-description"
        >
          <SheetHeader className="px-4 py-3 border-b shrink-0">
            <SheetTitle>Record Provenance</SheetTitle>
            <SheetDescription id="provenance-description">
              Source document location and extraction lineage for this ACM record
            </SheetDescription>
          </SheetHeader>
          <ProvenanceContent sourceId={sourceId} recordId={recordId} />
        </SheetContent>
      </Sheet>
    )
  }

  // Page mode — full-page layout
  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Top bar */}
      <div className="flex items-center gap-3 px-4 py-2 border-b bg-background shrink-0">
        {onClose && (
          <Button variant="ghost" size="sm" onClick={onClose} aria-label="Close provenance viewer">
            <X className="h-4 w-4 mr-1" />
            Close
          </Button>
        )}
        <h1 className="text-lg font-semibold">Record Provenance</h1>
        <p className="text-sm text-muted-foreground">
          Source document location and extraction lineage
        </p>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto">
          <ProvenanceContent sourceId={sourceId} recordId={recordId} />
        </div>
      </div>
    </div>
  )
}
