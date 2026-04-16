'use client'

import { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import {
  Loader2,
  AlertCircle,
  FileText,
  ZoomIn,
  ZoomOut,
  ChevronLeft,
  ChevronRight,
  Search,
  X,
  ArrowUp,
  ArrowDown,
  Crosshair,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { useAuthStore } from '@/lib/stores/auth-store'

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

const MIN_SCALE = 0.5
const MAX_SCALE = 3.0
const SCALE_STEP = 0.25

interface PDFPageViewerProps {
  pdfUrl: string | null
  pageNumber: number
  bbox?: PDFBbox | null
  className?: string
}

/**
 * PDFPageViewer — renders a PDF page with zoom, scroll, search, and bbox overlay.
 *
 * Features:
 * - Zoom in/out with keyboard shortcuts (Ctrl +/-)
 * - Page navigation (prev/next)
 * - In-page text search with match highlighting
 * - Bbox overlay with auto-scroll and pulse animation
 * - Scrollable canvas
 *
 * Story: E33-S6 Provenance Viewer (enhanced)
 */
export function PDFPageViewer({ pdfUrl, pageNumber: initialPage, bbox, className }: PDFPageViewerProps) {
  // Auth token for authenticated PDF fetches (pdfjs doesn't send auth headers by default)
  const token = useAuthStore((state) => state.token)

  // Build the pdfjs file object — include Authorization header when a token is present.
  // react-pdf accepts { url, httpHeaders } as an alternative to a bare URL string.
  const pdfFile = useMemo(() => {
    if (!pdfUrl) return null
    if (!token || token === 'not-required') return pdfUrl
    return { url: pdfUrl, httpHeaders: { Authorization: `Bearer ${token}` } }
  }, [pdfUrl, token])

  // Document state
  const [numPages, setNumPages] = useState(0)
  const [pageNumber, setPageNumber] = useState(initialPage)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Zoom state
  const [scale, setScale] = useState(1.0)
  const prevScaleRef = useRef(1.0)

  // Space+drag panning state
  const [isPanning, setIsPanning] = useState(false)
  const [isPanningActive, setIsPanningActive] = useState(false)
  const panStartRef = useRef({ x: 0, y: 0, scrollLeft: 0, scrollTop: 0 })

  // Page dimensions for bbox overlay
  const [pageDimensions, setPageDimensions] = useState<{
    width: number
    height: number
    originalWidth: number
    originalHeight: number
  } | null>(null)

  // Search state
  const [searchOpen, setSearchOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchMatches, setSearchMatches] = useState<HTMLElement[]>([])
  const [currentMatchIndex, setCurrentMatchIndex] = useState(-1)

  // Refs
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const pageContainerRef = useRef<HTMLDivElement>(null)
  const bboxOverlayRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)
  const rootRef = useRef<HTMLDivElement>(null)

  // Sync pageNumber when prop changes
  useEffect(() => {
    setPageNumber(initialPage)
  }, [initialPage])

  // Document load handlers
  const onDocumentLoadSuccess = useCallback(
    ({ numPages: pages }: { numPages: number }) => {
      setNumPages(pages)
      setLoading(false)
      setError(null)
    },
    []
  )

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

  // Auto-scroll to bbox after page renders
  useEffect(() => {
    if (!bbox || !pageDimensions || !bboxOverlayRef.current) return

    const timer = setTimeout(() => {
      bboxOverlayRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'center',
        inline: 'center',
      })
    }, 350)

    return () => clearTimeout(timer)
  }, [bbox, pageDimensions, pageNumber])

  // Page navigation
  const goToPrevPage = useCallback(() => setPageNumber((p) => Math.max(1, p - 1)), [])
  const goToNextPage = useCallback(() => setPageNumber((p) => Math.min(numPages, p + 1)), [numPages])
  const goToSourcePage = useCallback(() => setPageNumber(initialPage), [initialPage])

  // Zoom
  const zoomIn = useCallback(() => setScale((s) => Math.min(MAX_SCALE, s + SCALE_STEP)), [])
  const zoomOut = useCallback(() => setScale((s) => Math.max(MIN_SCALE, s - SCALE_STEP)), [])
  const resetZoom = useCallback(() => setScale(1.0), [])

  // Scroll to bbox highlight
  const scrollToBbox = useCallback(() => {
    bboxOverlayRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'center',
      inline: 'center',
    })
  }, [])

  // Search: find and highlight matching text spans in the text layer
  const performSearch = useCallback((query: string) => {
    // Clear previous highlights
    pageContainerRef.current
      ?.querySelectorAll('.pdf-search-highlight')
      .forEach((el) => {
        el.classList.remove('pdf-search-highlight', 'pdf-search-highlight-active')
      })

    if (!query.trim() || !pageContainerRef.current) {
      setSearchMatches([])
      setCurrentMatchIndex(-1)
      return
    }

    const matches: HTMLElement[] = []
    const spans = pageContainerRef.current.querySelectorAll(
      '.react-pdf__Page__textContent span'
    )
    const lowerQuery = query.toLowerCase()

    spans.forEach((span) => {
      const text = span.textContent?.toLowerCase() || ''
      if (text.includes(lowerQuery)) {
        ;(span as HTMLElement).classList.add('pdf-search-highlight')
        matches.push(span as HTMLElement)
      }
    })

    setSearchMatches(matches)
    if (matches.length > 0) {
      setCurrentMatchIndex(0)
      matches[0].classList.add('pdf-search-highlight-active')
      matches[0].scrollIntoView({ behavior: 'smooth', block: 'center' })
    } else {
      setCurrentMatchIndex(-1)
    }
  }, [])

  const goToNextMatch = useCallback(() => {
    if (searchMatches.length === 0) return
    const prev = searchMatches[currentMatchIndex]
    if (prev) prev.classList.remove('pdf-search-highlight-active')

    const nextIdx = (currentMatchIndex + 1) % searchMatches.length
    setCurrentMatchIndex(nextIdx)
    searchMatches[nextIdx].classList.add('pdf-search-highlight-active')
    searchMatches[nextIdx].scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [searchMatches, currentMatchIndex])

  const goToPrevMatch = useCallback(() => {
    if (searchMatches.length === 0) return
    const prev = searchMatches[currentMatchIndex]
    if (prev) prev.classList.remove('pdf-search-highlight-active')

    const nextIdx = (currentMatchIndex - 1 + searchMatches.length) % searchMatches.length
    setCurrentMatchIndex(nextIdx)
    searchMatches[nextIdx].classList.add('pdf-search-highlight-active')
    searchMatches[nextIdx].scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [searchMatches, currentMatchIndex])

  const clearSearch = useCallback(() => {
    setSearchQuery('')
    setSearchMatches([])
    setCurrentMatchIndex(-1)
    pageContainerRef.current
      ?.querySelectorAll('.pdf-search-highlight')
      .forEach((el) => {
        el.classList.remove('pdf-search-highlight', 'pdf-search-highlight-active')
      })
  }, [])

  const toggleSearch = useCallback(() => {
    setSearchOpen((prev) => {
      if (!prev) {
        // Opening — focus the input after render
        setTimeout(() => searchInputRef.current?.focus(), 100)
      } else {
        // Closing — clear search state
        clearSearch()
      }
      return !prev
    })
  }, [clearSearch])

  // Debounced search on query change
  useEffect(() => {
    const timer = setTimeout(() => performSearch(searchQuery), 200)
    return () => clearTimeout(timer)
  }, [searchQuery, performSearch, pageNumber])

  // Keyboard shortcuts (scoped to this component)
  useEffect(() => {
    const root = rootRef.current
    if (!root) return

    const handler = (e: KeyboardEvent) => {
      // Ctrl+F / Cmd+F — toggle search
      if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
        e.preventDefault()
        e.stopPropagation()
        toggleSearch()
        return
      }
      // Escape — close search
      if (e.key === 'Escape' && searchOpen) {
        e.preventDefault()
        toggleSearch()
        return
      }
      // Ctrl + / Ctrl - — zoom
      if ((e.ctrlKey || e.metaKey) && (e.key === '=' || e.key === '+')) {
        e.preventDefault()
        zoomIn()
        return
      }
      if ((e.ctrlKey || e.metaKey) && e.key === '-') {
        e.preventDefault()
        zoomOut()
        return
      }
      // Ctrl+0 — reset zoom
      if ((e.ctrlKey || e.metaKey) && e.key === '0') {
        e.preventDefault()
        resetZoom()
      }
    }

    root.addEventListener('keydown', handler)
    return () => root.removeEventListener('keydown', handler)
  }, [searchOpen, toggleSearch, zoomIn, zoomOut, resetZoom])

  // Space key for panning mode (Photoshop-style space+drag)
  useEffect(() => {
    const root = rootRef.current
    if (!root) return

    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't activate panning if focused on search input
      if (e.key === ' ' && !(e.target instanceof HTMLInputElement)) {
        e.preventDefault()
        setIsPanning(true)
      }
    }
    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.key === ' ') {
        setIsPanning(false)
        setIsPanningActive(false)
      }
    }

    root.addEventListener('keydown', handleKeyDown)
    root.addEventListener('keyup', handleKeyUp)
    return () => {
      root.removeEventListener('keydown', handleKeyDown)
      root.removeEventListener('keyup', handleKeyUp)
    }
  }, [])

  // Preserve scroll center when zoom changes
  useEffect(() => {
    const container = scrollContainerRef.current
    if (!container || prevScaleRef.current === scale) return

    const prevScale = prevScaleRef.current
    prevScaleRef.current = scale

    // Calculate viewport center point relative to content
    const centerX = (container.scrollLeft + container.clientWidth / 2) / prevScale
    const centerY = (container.scrollTop + container.clientHeight / 2) / prevScale

    requestAnimationFrame(() => {
      container.scrollLeft = centerX * scale - container.clientWidth / 2
      container.scrollTop = centerY * scale - container.clientHeight / 2
    })
  }, [scale])

  // Mouse handlers for space+drag panning
  const handlePanMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (!isPanning) return
      e.preventDefault()
      setIsPanningActive(true)
      const container = scrollContainerRef.current
      if (container) {
        panStartRef.current = {
          x: e.clientX,
          y: e.clientY,
          scrollLeft: container.scrollLeft,
          scrollTop: container.scrollTop,
        }
      }
    },
    [isPanning]
  )

  const handlePanMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!isPanningActive) return
      e.preventDefault()
      const container = scrollContainerRef.current
      if (!container) return
      const dx = e.clientX - panStartRef.current.x
      const dy = e.clientY - panStartRef.current.y
      container.scrollLeft = panStartRef.current.scrollLeft - dx
      container.scrollTop = panStartRef.current.scrollTop - dy
    },
    [isPanningActive]
  )

  const handlePanMouseUp = useCallback(() => {
    setIsPanningActive(false)
  }, [])

  // ─── Render ─────────────────────────────────────────

  if (!pdfFile) {
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
      backgroundColor: 'rgba(20, 184, 166, 0.12)',
      border: '2.5px solid rgba(20, 184, 166, 0.80)',
      borderRadius: '3px',
      pointerEvents: 'none',
      boxShadow: '0 0 8px 2px rgba(20, 184, 166, 0.25)',
      zIndex: 10,
    }
  }

  const isSourcePage = pageNumber === initialPage

  return (
    <div
      ref={rootRef}
      tabIndex={-1}
      className={cn('flex flex-col rounded-lg border bg-background focus:outline-none', className)}
    >
      {/* ─── Toolbar ─── */}
      <div className="flex flex-wrap items-center gap-2 px-3 py-2 border-b bg-muted/30 shrink-0">
        {/* Page Navigation */}
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={goToPrevPage}
            disabled={pageNumber <= 1 || loading}
            aria-label="Previous page"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="text-xs min-w-[80px] text-center tabular-nums">
            {pageNumber} / {numPages || '...'}
          </span>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={goToNextPage}
            disabled={pageNumber >= numPages || loading}
            aria-label="Next page"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
          {!isSourcePage && numPages > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs text-primary"
              onClick={goToSourcePage}
              aria-label={`Go to source page ${initialPage}`}
            >
              Page {initialPage}
            </Button>
          )}
        </div>

        <div className="h-4 w-px bg-border" aria-hidden="true" />

        {/* Zoom Controls */}
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={zoomOut}
            disabled={scale <= MIN_SCALE || loading}
            aria-label="Zoom out"
          >
            <ZoomOut className="h-3.5 w-3.5" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 w-12 text-xs tabular-nums"
            onClick={resetZoom}
            disabled={loading || scale === 1.0}
            aria-label="Reset zoom"
          >
            {Math.round(scale * 100)}%
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={zoomIn}
            disabled={scale >= MAX_SCALE || loading}
            aria-label="Zoom in"
          >
            <ZoomIn className="h-3.5 w-3.5" />
          </Button>
        </div>

        <div className="h-4 w-px bg-border" aria-hidden="true" />

        {/* Search toggle + bbox scroll */}
        <div className="flex items-center gap-1">
          <Button
            variant={searchOpen ? 'secondary' : 'ghost'}
            size="icon"
            className="h-7 w-7"
            onClick={toggleSearch}
            disabled={loading}
            aria-label="Toggle search"
          >
            <Search className="h-3.5 w-3.5" />
          </Button>
          {bbox && (
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={scrollToBbox}
              disabled={loading}
              title="Scroll to highlighted record"
              aria-label="Scroll to highlighted record"
            >
              <Crosshair className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      </div>

      {/* ─── Search Bar ─── */}
      {searchOpen && (
        <div className="flex items-center gap-2 px-3 py-1.5 border-b bg-muted/20">
          <Search className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
          <Input
            ref={searchInputRef}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search in page..."
            className="h-7 text-xs flex-1"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.shiftKey ? goToPrevMatch() : goToNextMatch()
              }
            }}
          />
          {searchMatches.length > 0 && (
            <span className="text-xs text-muted-foreground whitespace-nowrap tabular-nums">
              {currentMatchIndex + 1}/{searchMatches.length}
            </span>
          )}
          {searchQuery && searchMatches.length === 0 && (
            <span className="text-xs text-destructive whitespace-nowrap">No matches</span>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={goToPrevMatch}
            disabled={searchMatches.length === 0}
            aria-label="Previous match"
          >
            <ArrowUp className="h-3 w-3" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={goToNextMatch}
            disabled={searchMatches.length === 0}
            aria-label="Next match"
          >
            <ArrowDown className="h-3 w-3" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={toggleSearch}
            aria-label="Close search"
          >
            <X className="h-3 w-3" />
          </Button>
        </div>
      )}

      {/* ─── Loading ─── */}
      {loading && (
        <div className="flex flex-col items-center justify-center gap-3 py-12 text-muted-foreground">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="text-sm">Loading PDF...</span>
        </div>
      )}

      {/* ─── Error ─── */}
      {error && (
        <div className="flex flex-col items-center justify-center gap-3 py-12 text-destructive">
          <AlertCircle className="h-8 w-8" />
          <span className="text-sm font-medium">Failed to load PDF</span>
          <span className="text-xs text-muted-foreground">{error}</span>
        </div>
      )}

      {/* ─── PDF Canvas (scrollable) ─── */}
      <div
        ref={scrollContainerRef}
        className={cn(
          'overflow-auto p-4 bg-muted/10',
          loading || error ? 'hidden' : '',
          isPanning && !isPanningActive && 'cursor-grab',
          isPanningActive && 'cursor-grabbing select-none'
        )}
        style={{ maxHeight: '65vh' }}
        onMouseDown={handlePanMouseDown}
        onMouseMove={handlePanMouseMove}
        onMouseUp={handlePanMouseUp}
        onMouseLeave={handlePanMouseUp}
      >
        {/* Centering wrapper: margin auto centers when content < container,
            left-aligns when content overflows so scrollbar reaches both edges */}
        <div style={{ width: 'fit-content', margin: '0 auto' }}>
          <Document
            file={pdfFile}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={onDocumentLoadError}
            loading=""
            error=""
          >
            <div ref={pageContainerRef} className="relative inline-block">
              <Page
                pageNumber={pageNumber}
                scale={scale}
                renderTextLayer={true}
                renderAnnotationLayer={true}
                className="shadow-md"
                onRenderSuccess={onPageRenderSuccess}
              />
              {overlayStyle && (
                <div
                  ref={bboxOverlayRef}
                  className="pdf-bbox-highlight"
                  style={overlayStyle}
                  aria-hidden="true"
                />
              )}
            </div>
          </Document>
        </div>
      </div>

      {/* ─── Status Bar ─── */}
      {!loading && !error && (
        <div className="flex items-center justify-between px-3 py-1 border-t bg-muted/20 text-xs text-muted-foreground">
          <span>{bbox ? 'Record location highlighted' : 'No bounding box data'}</span>
          <span className="tabular-nums">
            {Math.round(scale * 100)}% | Page {pageNumber}
          </span>
        </div>
      )}
    </div>
  )
}
