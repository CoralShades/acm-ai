'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  FileText,
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Loader2,
  AlertCircle,
  X,
} from 'lucide-react'
import type { CellSelectionDetails } from './ACMGrid'

// Import react-pdf styles
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'

// Configure PDF.js worker - use bundled worker for reliability (no external CDN dependency)
pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url,
).toString()

// Zoom constraints as constants
const MIN_SCALE = 0.5
const MAX_SCALE = 2.5
const SCALE_STEP = 0.25

interface ACMCellViewerProps {
  /** Source ID - used for display in footer to help identify the source document */
  sourceId: string
  selection: CellSelectionDetails | null
  pdfUrl: string | null
  onClose: () => void
}

// Field display name mapping
const fieldDisplayNames: Record<string, string> = {
  building_id: 'Building ID',
  building_name: 'Building Name',
  room_id: 'Room ID',
  room_name: 'Room Name',
  product: 'Product',
  material_description: 'Material Description',
  risk_status: 'Risk Status',
  result: 'Result',
  friable: 'Friable',
  material_condition: 'Condition',
  page_number: 'Page Number',
}

/**
 * ACMCellViewer - PDF viewer modal for viewing cell source citations
 *
 * Features:
 * - PDF rendering with react-pdf
 * - Page navigation (prev/next)
 * - Zoom controls
 * - Auto-navigate to source page number
 * - Loading and error states
 */
export function ACMCellViewer({ sourceId, selection, pdfUrl, onClose }: ACMCellViewerProps) {
  const [numPages, setNumPages] = useState<number>(0)
  const [pageNumber, setPageNumber] = useState<number>(1)
  const [scale, setScale] = useState<number>(1.0)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  // Track current selection to detect changes and reset properly
  const prevSelectionRef = useRef<string | null>(null)

  // Reset state when selection changes - full cleanup to prevent stale state
  useEffect(() => {
    const selectionKey = selection ? `${selection.recordId}-${selection.field}` : null

    if (selection && selectionKey !== prevSelectionRef.current) {
      // New selection - reset all state
      setNumPages(0)
      setLoading(true)
      setError(null)
      setScale(1.0)
      // Set initial page from record's page_number
      const initialPage = selection.pageNumber && selection.pageNumber > 0 ? selection.pageNumber : 1
      setPageNumber(initialPage)
    }

    prevSelectionRef.current = selectionKey
  }, [selection])

  const onDocumentLoadSuccess = useCallback(({ numPages: pages }: { numPages: number }) => {
    setNumPages(pages)
    // Ensure page number is within bounds
    if (selection?.pageNumber && selection.pageNumber > 0) {
      setPageNumber(Math.min(selection.pageNumber, pages))
    }
    setLoading(false)
    setError(null)
  }, [selection?.pageNumber])

  const onDocumentLoadError = useCallback((err: Error) => {
    // Error is captured in state for user display - no console logging in production
    setError(err.message || 'Failed to load PDF')
    setLoading(false)
  }, [])

  const goToPrevPage = useCallback(() => {
    setPageNumber(prev => Math.max(1, prev - 1))
  }, [])

  const goToNextPage = useCallback(() => {
    setPageNumber(prev => Math.min(numPages, prev + 1))
  }, [numPages])

  const zoomIn = useCallback(() => {
    setScale(prev => Math.min(MAX_SCALE, prev + SCALE_STEP))
  }, [])

  const zoomOut = useCallback(() => {
    setScale(prev => Math.max(MIN_SCALE, prev - SCALE_STEP))
  }, [])

  const resetZoom = useCallback(() => {
    setScale(1.0)
  }, [])

  const goToSourcePage = useCallback(() => {
    if (selection?.pageNumber && selection.pageNumber > 0 && selection.pageNumber <= numPages) {
      setPageNumber(selection.pageNumber)
    }
  }, [selection?.pageNumber, numPages])

  if (!selection) return null

  const fieldName = fieldDisplayNames[selection.field] || selection.field
  const hasPageNumber = selection.pageNumber != null && selection.pageNumber > 0
  const hasPdf = !!pdfUrl

  return (
    <Dialog open={!!selection} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-5xl h-[90vh] flex flex-col p-0 gap-0">
        <DialogHeader className="px-6 py-4 border-b shrink-0">
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Source Citation
          </DialogTitle>
          <DialogDescription className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">{fieldName}</Badge>
            <span className="text-foreground font-medium">
              {String(selection.value ?? 'N/A')}
            </span>
            {hasPageNumber && (
              <>
                <span className="text-muted-foreground">|</span>
                <Badge variant="secondary">Page {selection.pageNumber}</Badge>
              </>
            )}
          </DialogDescription>
        </DialogHeader>

        {/* PDF Viewer Section */}
        {hasPdf ? (
          <>
            {/* Controls */}
            <div className="flex items-center justify-between px-4 py-2 border-b bg-muted/30 shrink-0">
              {/* Page Navigation */}
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={goToPrevPage}
                  disabled={pageNumber <= 1 || loading}
                  aria-label="Previous page"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm min-w-[100px] text-center">
                  Page {pageNumber} of {numPages || '...'}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={goToNextPage}
                  disabled={pageNumber >= numPages || loading}
                  aria-label="Next page"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
                {hasPageNumber && pageNumber !== selection.pageNumber && !loading && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={goToSourcePage}
                    className="ml-2 text-primary"
                    aria-label="Go to source page"
                  >
                    Go to Page {selection.pageNumber}
                  </Button>
                )}
              </div>

              {/* Zoom Controls */}
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={zoomOut}
                  disabled={scale <= MIN_SCALE || loading}
                  aria-label="Zoom out"
                >
                  <ZoomOut className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={resetZoom}
                  className="w-16 text-center"
                  disabled={loading || scale === 1.0}
                  aria-label="Reset zoom to 100%"
                >
                  {Math.round(scale * 100)}%
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={zoomIn}
                  disabled={scale >= MAX_SCALE || loading}
                  aria-label="Zoom in"
                >
                  <ZoomIn className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* PDF Document */}
            <div className="flex-1 overflow-auto flex justify-center p-4 bg-muted/20">
              {loading && (
                <div className="flex flex-col items-center justify-center gap-3 text-muted-foreground">
                  <Loader2 className="h-8 w-8 animate-spin" />
                  <span>Loading PDF...</span>
                </div>
              )}
              {error && (
                <div className="flex flex-col items-center justify-center gap-3 text-destructive">
                  <AlertCircle className="h-8 w-8" />
                  <span>Failed to load PDF</span>
                  <span className="text-sm text-muted-foreground">{error}</span>
                </div>
              )}
              <Document
                file={pdfUrl}
                onLoadSuccess={onDocumentLoadSuccess}
                onLoadError={onDocumentLoadError}
                loading=""
                error=""
                className={loading || error ? 'hidden' : ''}
              >
                <Page
                  pageNumber={pageNumber}
                  scale={scale}
                  renderTextLayer={true}
                  renderAnnotationLayer={true}
                  className="shadow-lg"
                />
              </Document>
            </div>
          </>
        ) : (
          /* No PDF Available */
          <div className="flex-1 flex flex-col items-center justify-center gap-4 p-8 text-center">
            <FileText className="h-16 w-16 text-muted-foreground" />
            <div>
              <p className="text-lg font-medium">PDF Not Available</p>
              <p className="text-sm text-muted-foreground mt-1">
                {hasPageNumber
                  ? `This record references page ${selection.pageNumber}, but no PDF is available for this source.`
                  : 'No PDF document is associated with this source.'}
              </p>
            </div>

            {/* Still show the cell info */}
            <div className="rounded-lg border p-4 space-y-2 max-w-md w-full mt-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Field</span>
                <Badge variant="outline">{fieldName}</Badge>
              </div>
              <div className="flex items-start justify-between gap-4">
                <span className="text-sm text-muted-foreground">Value</span>
                <span className="text-sm font-medium text-right max-w-[200px] break-words">
                  {String(selection.value ?? 'N/A')}
                </span>
              </div>
              {hasPageNumber && (
                <div className="flex items-center justify-between">
                  <span className="text-sm text-muted-foreground">Source Page</span>
                  <Badge variant="secondary">Page {selection.pageNumber}</Badge>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Footer with Close button */}
        <div className="flex justify-between items-center px-6 py-3 border-t bg-muted/30 shrink-0">
          <div className="text-xs text-muted-foreground">
            Record: {selection.recordId.slice(0, 20)}... | Source: {sourceId.slice(0, 20)}...
          </div>
          <Button variant="outline" onClick={onClose} aria-label="Close citation viewer">
            <X className="h-4 w-4 mr-2" />
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
