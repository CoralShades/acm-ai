'use client'

import { useState, useCallback } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import { Loader2, AlertCircle, FileText } from 'lucide-react'
import { cn } from '@/lib/utils'

// Import react-pdf styles
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'

// Use CDN worker — avoids webpack bundling the worker .mjs entirely
// (recommended by react-pdf docs, prevents eval-* devtool crash in Next.js dev)
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`

export interface PDFBbox {
  x: number
  y: number
  width: number
  height: number
}

interface PDFPageViewerProps {
  pdfUrl: string | null
  pageNumber: number
  bbox?: PDFBbox | null
  className?: string
}

/**
 * PDFPageViewer — renders a single PDF page with an optional bbox overlay.
 *
 * The bbox is in PDF coordinate space (origin bottom-left, y increases upward).
 * We convert it to screen coordinates when overlaying.
 *
 * Story: E33-S6 Provenance Viewer
 */
export function PDFPageViewer({ pdfUrl, pageNumber, bbox, className }: PDFPageViewerProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  // Rendered page dimensions (px) — needed to scale bbox coordinates
  const [pageDimensions, setPageDimensions] = useState<{
    width: number
    height: number
    originalWidth: number
    originalHeight: number
  } | null>(null)

  const onDocumentLoadSuccess = useCallback(() => {
    setLoading(false)
    setError(null)
  }, [])

  const onDocumentLoadError = useCallback((err: Error) => {
    setError(err.message || 'Failed to load PDF')
    setLoading(false)
  }, [])

  const onPageRenderSuccess = useCallback(
    (page: { width: number; height: number; originalWidth: number; originalHeight: number }) => {
      setPageDimensions({
        width: page.width,
        height: page.height,
        originalWidth: page.originalWidth,
        originalHeight: page.originalHeight,
      })
    },
    []
  )

  if (!pdfUrl) {
    return (
      <div
        className={cn(
          'flex flex-col items-center justify-center gap-3 p-8 rounded-lg border bg-muted/20 text-muted-foreground',
          className
        )}
      >
        <FileText className="h-10 w-10" />
        <p className="text-sm font-medium">No PDF available for this record</p>
      </div>
    )
  }

  // Compute bbox overlay position in rendered pixel space
  // PDF coordinate system: origin bottom-left, y increases upward
  // Screen coordinate system: origin top-left, y increases downward
  let overlayStyle: React.CSSProperties | null = null
  if (bbox && pageDimensions && pageDimensions.originalWidth > 0 && pageDimensions.originalHeight > 0) {
    const scaleX = pageDimensions.width / pageDimensions.originalWidth
    const scaleY = pageDimensions.height / pageDimensions.originalHeight

    // Convert PDF y (bottom-left origin) to CSS top (top-left origin)
    // PDF y=0 is the bottom of the page, CSS top=0 is the top
    const cssLeft = bbox.x * scaleX
    const cssTop = (pageDimensions.originalHeight - bbox.y - bbox.height) * scaleY
    const cssWidth = bbox.width * scaleX
    const cssHeight = bbox.height * scaleY

    overlayStyle = {
      position: 'absolute',
      left: `${cssLeft}px`,
      top: `${cssTop}px`,
      width: `${cssWidth}px`,
      height: `${cssHeight}px`,
      backgroundColor: 'rgba(20, 184, 166, 0.10)',
      border: '2.5px solid rgba(20, 184, 166, 0.75)',
      borderRadius: '3px',
      pointerEvents: 'none',
      boxShadow: '0 0 0 1px rgba(20, 184, 166, 0.15)',
    }
  }

  return (
    <div className={cn('flex flex-col items-center', className)}>
      {/* Loading state */}
      {loading && (
        <div className="flex flex-col items-center justify-center gap-3 py-12 text-muted-foreground">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="text-sm">Loading PDF page...</span>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="flex flex-col items-center justify-center gap-3 py-12 text-destructive">
          <AlertCircle className="h-8 w-8" />
          <span className="text-sm font-medium">Failed to load PDF</span>
          <span className="text-xs text-muted-foreground">{error}</span>
        </div>
      )}

      {/* PDF Document */}
      <div className={cn('overflow-auto w-full', loading || error ? 'hidden' : '')}>
        <Document
          file={pdfUrl}
          onLoadSuccess={onDocumentLoadSuccess}
          onLoadError={onDocumentLoadError}
          loading=""
          error=""
        >
          {/* Wrap Page in a relative container so overlay can be absolutely positioned */}
          <div className="relative inline-block">
            <Page
              pageNumber={pageNumber}
              renderTextLayer={false}
              renderAnnotationLayer={false}
              className="shadow-md"
              onRenderSuccess={onPageRenderSuccess}
            />
            {overlayStyle && <div style={overlayStyle} aria-hidden="true" />}
          </div>
        </Document>
      </div>

      {/* Bbox info when no bbox data */}
      {!bbox && !loading && !error && (
        <p className="text-xs text-muted-foreground mt-2">No bounding box data available</p>
      )}
    </div>
  )
}
