# E33-S6: Provenance Viewer

## Story

**ID**: E33-S6
**Title**: Provenance Viewer
**Sprint**: V3-6
**Story Points**: 3
**Risk**: MEDIUM
**Type**: Frontend + Minor Backend
**Dependencies**: E31-S4 (Raw Extraction Table + Storage), E33-S2 (Building Grid + Item Grid)

### Acceptance Criteria

- AC1: Slide-over panel triggered from "Source" button on any AG Grid row
- AC2: Top section: PDF page rendering with bbox overlay highlighting the source table
- AC3: Bottom section: extraction lineage table showing provider, backend, confidence, consensus tier, edit history
- AC4: Lazy-load pages: only render the page containing target bbox
- AC5: Cell-level provenance: click individual field to see per-field provider agreement
- AC6: Route: /source/:id/provenance/:recordId (also accessible as panel overlay)
- AC7: Responsive: works in slide-over panel and full-page modes

---

## Overview

The Provenance Viewer lets officers trace any extracted ACM record back to its source PDF location and see which providers extracted it, their confidence scores, and how consensus was reached. It combines PDF page rendering (via react-pdf) with extraction lineage data from the raw_extraction table.

---

## Technical Design

### Architecture

```
ProvenanceViewer.tsx (slide-over panel or full-page)
  ├── PDFPageViewer.tsx (react-pdf single-page render + bbox overlay)
  └── LineageTable.tsx (provider comparison table)
```

### Data Sources

1. **ACMRecord** — `page_number`, `table_bbox` (x, y, width, height, page), `parent_table_id`
2. **ACMTableSection** — `consensus_tier`, `consensus_scores` (per-provider confidence + agreement)
3. **RawExtraction** — per-provider raw data for the same page: `provider_id`, `extraction_backend`, `confidence`, `bbox`, `officer_edits`
4. **Source** — `asset.file_path` for PDF URL

### Data Flow

```
1. User clicks "Source" button on AG Grid row
2. Fetch record details (already in grid data)
3. Fetch parent ACMTableSection (via parent_table_id) → consensus data
4. Fetch RawExtractions for the record's page_number → per-provider data
5. Render PDF page at record.page_number with bbox overlay
6. Display lineage table below PDF
```

### PDF Rendering Strategy (AC2, AC4)

- Use `react-pdf` (already installed) with `<Page>` component
- Only render the single page containing the record (`record.page_number`)
- Overlay a semi-transparent rectangle at `table_bbox` coordinates
- PDF URL: construct from source file_path via `/api/sources/{id}/content` or similar
- If no PDF available, show "PDF not available" placeholder

### Backend: Provenance Data Endpoint

Add `GET /api/acm/provenance/{record_id}` that returns:
```json
{
  "record": { ACMRecord fields },
  "table_section": { consensus_tier, consensus_scores, page_start, page_end },
  "raw_extractions": [{ provider_id, extraction_backend, confidence, bbox, officer_edits }],
  "source": { id, title, file_path }
}
```

This aggregates data from multiple tables into a single response to avoid N+1 queries from the frontend.

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/components/acm/ProvenanceViewer.tsx` | Create | Slide-over panel with PDF viewer + lineage table |
| `frontend/src/components/acm/PDFPageViewer.tsx` | Create | Single-page PDF renderer with bbox overlay using react-pdf |
| `frontend/src/components/acm/LineageTable.tsx` | Create | Provider comparison table showing extraction lineage |
| `frontend/src/components/acm/ItemGrid.tsx` | Modify | Add "Source" button/column to trigger provenance viewer |
| `frontend/src/lib/hooks/useProvenance.ts` | Create | React Query hook for provenance data |
| `frontend/src/lib/api/acm.ts` | Modify | Add `getProvenance(recordId)` API method |
| `frontend/src/lib/types/acm.ts` | Modify | Add provenance-related types |
| `frontend/src/app/(dashboard)/source/[id]/provenance/[recordId]/page.tsx` | Create | Full-page provenance route (AC6) |
| `api/routers/acm.py` | Modify | Add GET /provenance/{record_id} endpoint |
| `api/models.py` | Modify | Add ProvenanceResponse model |

---

## Component Specifications

### ProvenanceViewer

```tsx
interface ProvenanceViewerProps {
  sourceId: string
  recordId: string
  mode: 'panel' | 'page'  // slide-over vs full-page
  onClose?: () => void     // Only for panel mode
}
```

- Panel mode: Radix Sheet (slide-over from right, 50% width)
- Page mode: full-page layout via Next.js route
- Fetches provenance data via `useProvenance(recordId)` hook
- Renders PDFPageViewer at top, LineageTable at bottom
- Shows record identity info: building, room, product, page number

### PDFPageViewer

```tsx
interface PDFPageViewerProps {
  pdfUrl: string | null
  pageNumber: number
  bbox?: { x: number; y: number; width: number; height: number } | null
}
```

- Uses `<Document>` and `<Page>` from `react-pdf`
- Renders single page (AC4 — lazy load)
- Overlays a highlighted rectangle at bbox coordinates
- Bbox overlay: absolute positioned div with semi-transparent yellow/orange background
- Handles missing PDF gracefully (placeholder message)
- The PDF dimensions need to be known to scale bbox coordinates (use `onLoadSuccess` callback)

### LineageTable

```tsx
interface LineageTableProps {
  rawExtractions: RawExtractionRecord[]
  consensusTier?: string | null
  consensusScores?: Record<string, number> | null
}
```

- Simple HTML table showing per-provider data
- Columns: Provider, Backend, Confidence, Bbox, Edit History
- Consensus tier badge at top (e.g., "Multi-Provider Agreement" in green)
- Per-provider confidence with color coding (>0.8 green, 0.5-0.8 yellow, <0.5 red)
- Officer edits count with expandable list

---

## Testing Strategy

- Build verification: `cd frontend && npm run build`
- Lint: `cd frontend && npm run lint`
- Manual testing: navigate to /source/:id, click Source button on a row

---

## Edge Cases

1. **No table_bbox**: Show PDF page without overlay, display "No bounding box data"
2. **No raw extractions**: Show "No extraction data available" in lineage table
3. **No PDF file**: Show placeholder instead of PDF viewer
4. **Single provider**: LineageTable shows one row, consensus_tier = "single_provider"
5. **No page_number**: Can't render PDF, show message

---

## Out of Scope

- Per-field provider agreement visualization (AC5) — implement as future enhancement showing field-level diff between providers. For now, show a simplified version: the lineage table shows provider-level data, and clicking a field name shows which providers extracted different values (if structured_json is available).
- PDF text selection / annotation
- Multi-page PDF navigation (only show the relevant page)
