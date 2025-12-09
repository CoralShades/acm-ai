# Tech-Spec: E3-S2 PDF Viewer Modal

**Created:** 2025-12-07
**Status:** Ready for Development
**Epic:** E3 - Cell Citations & PDF Viewer
**Story:** S2 - Create PDF Viewer Modal

---

## Overview

### Problem Statement

When users click a cell in the ACM spreadsheet (E3-S1), they need to see the source PDF page where that data was extracted from. This provides verification and trust in the extracted data.

### Solution

Create an `ACMCellViewer` modal component that:
- Opens when a cell is clicked
- Displays the source PDF at the correct page number
- Provides page navigation controls
- Supports zoom controls
- Works with the existing source asset system

### Scope

**In Scope:**
- Modal component with react-pdf
- PDF rendering at specific page
- Page navigation (prev/next)
- Zoom controls
- Loading and error states

**Out of Scope:**
- Text search within PDF
- PDF annotations
- Mobile optimization

---

## Implementation Plan

### Tasks

- [ ] **Task 1: Install react-pdf**
  - `npm install react-pdf`
  - Configure PDF.js worker

- [ ] **Task 2: Create ACMCellViewer component**
  - Location: `frontend/src/components/acm/ACMCellViewer.tsx`
  - Modal wrapper with PDF viewer
  - Page/zoom controls

- [ ] **Task 3: Integrate with ACMSpreadsheet**
  - Pass onCellClick handler
  - Open modal with record data

- [ ] **Task 4: Handle PDF loading**
  - Get PDF URL from source asset
  - Navigate to page_number
  - Handle missing page info

### Acceptance Criteria

- [ ] **AC1**: Modal opens with PDF viewer on cell click
- [ ] **AC2**: PDF loads to correct page number
- [ ] **AC3**: Page navigation controls work
- [ ] **AC4**: Zoom controls available
- [ ] **AC5**: Close button works
- [ ] **AC6**: Responsive sizing

---

## Code Specification

### File: `frontend/src/components/acm/ACMCellViewer.tsx`

```typescript
'use client'

import { useState } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  FileText,
  Loader2
} from 'lucide-react'
import type { ACMRecord } from '@/lib/types/acm'

// Configure PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`

interface ACMCellViewerProps {
  record: ACMRecord | null
  field: string | null
  pdfUrl: string | null
  open: boolean
  onClose: () => void
}

export function ACMCellViewer({ record, field, pdfUrl, open, onClose }: ACMCellViewerProps) {
  const [numPages, setNumPages] = useState<number>(0)
  const [pageNumber, setPageNumber] = useState<number>(1)
  const [scale, setScale] = useState<number>(1.0)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  // Set initial page when record changes
  const initialPage = record?.page_number || 1

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
    setPageNumber(Math.min(initialPage, numPages))
    setLoading(false)
    setError(null)
  }

  const onDocumentLoadError = (err: Error) => {
    setError(err.message)
    setLoading(false)
  }

  const goToPrevPage = () => setPageNumber(prev => Math.max(1, prev - 1))
  const goToNextPage = () => setPageNumber(prev => Math.min(numPages, prev + 1))
  const zoomIn = () => setScale(prev => Math.min(2.0, prev + 0.25))
  const zoomOut = () => setScale(prev => Math.max(0.5, prev - 0.25))

  if (!record || !pdfUrl) return null

  return (
    <Dialog open={open} onOpenChange={(isOpen) => !isOpen && onClose()}>
      <DialogContent className="max-w-4xl h-[90vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Source Citation
          </DialogTitle>
          <p className="text-sm text-muted-foreground">
            {field}: <strong>{record[field as keyof ACMRecord]?.toString() || 'N/A'}</strong>
            {' | '}Building: {record.building_name || record.building_id}
            {record.room_name && ` | Room: ${record.room_name}`}
          </p>
        </DialogHeader>

        {/* Controls */}
        <div className="flex items-center justify-between px-2 py-1 border-b">
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={goToPrevPage} disabled={pageNumber <= 1}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <span className="text-sm">
              Page {pageNumber} of {numPages}
            </span>
            <Button variant="outline" size="sm" onClick={goToNextPage} disabled={pageNumber >= numPages}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={zoomOut} disabled={scale <= 0.5}>
              <ZoomOut className="h-4 w-4" />
            </Button>
            <span className="text-sm w-16 text-center">{Math.round(scale * 100)}%</span>
            <Button variant="outline" size="sm" onClick={zoomIn} disabled={scale >= 2.0}>
              <ZoomIn className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* PDF Viewer */}
        <div className="flex-1 overflow-auto flex justify-center p-4 bg-muted/50">
          {loading && (
            <div className="flex items-center gap-2">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span>Loading PDF...</span>
            </div>
          )}
          {error && (
            <div className="text-destructive">
              Failed to load PDF: {error}
            </div>
          )}
          <Document
            file={pdfUrl}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={onDocumentLoadError}
            loading=""
          >
            <Page
              pageNumber={pageNumber}
              scale={scale}
              renderTextLayer={false}
              renderAnnotationLayer={false}
            />
          </Document>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default ACMCellViewer
```

---

## Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| E3-S1 (Clickable Cells) | Story | Provides click handler |
| react-pdf | npm | `npm install react-pdf` |
| Source asset URL | API | PDF file path from source |

---

*Tech-Spec generated by create-tech-spec workflow*
