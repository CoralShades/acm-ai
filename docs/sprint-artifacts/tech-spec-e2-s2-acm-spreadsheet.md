# Tech-Spec: E2-S2 ACMSpreadsheet Component

**Created:** 2025-12-07
**Status:** Ready for Development
**Epic:** E2 - AG Grid Spreadsheet Integration
**Story:** S2 - Create ACMSpreadsheet Component

---

## Overview

### Problem Statement

Users need to view ACM (Asbestos Containing Material) records in an interactive spreadsheet format that supports sorting, filtering, and hierarchical grouping by Building/Room. The AG Grid library has been installed (E2-S1), but there's no component to display ACM data.

### Solution

Create an `ACMSpreadsheet` React component that:
- Uses AG Grid to display ACM records in a spreadsheet
- Fetches data from `/api/acm/records` using React Query
- Groups rows by Building and Room hierarchy
- Supports sorting, filtering, and searching
- Shows loading/empty/error states
- Makes cells clickable for citation viewing (E3-S1)

### Scope

**In Scope:**
- ACMSpreadsheet component with AG Grid
- API client for ACM endpoints
- React Query hook for data fetching
- Column definitions matching ACM schema
- Loading, empty, and error states

**Out of Scope:**
- Row grouping (E2-S4)
- Risk color coding (E2-S5)
- Search bar (E2-S6)
- Cell click modal (E3-S1, E3-S2)

---

## Context for Development

### Codebase Patterns

#### 1. API Client Pattern
Location: `frontend/src/lib/api/`

```typescript
import apiClient from './client'

export const myApi = {
  list: async (params) => {
    const response = await apiClient.get<ResponseType>('/endpoint', { params })
    return response.data
  },
}
```

#### 2. React Query Pattern
Used throughout the app for data fetching:

```typescript
import { useQuery } from '@tanstack/react-query'

const { data, isLoading, error } = useQuery({
  queryKey: ['myData', id],
  queryFn: () => myApi.get(id),
})
```

#### 3. Component Pattern
From existing components:

```typescript
'use client'

import { useState } from 'react'

interface Props {
  sourceId: string
}

export function MyComponent({ sourceId }: Props) {
  // Component logic
}
```

### Files to Reference

| File | Purpose |
|------|---------|
| `frontend/src/lib/api/sources.ts` | API client pattern |
| `frontend/src/components/source/SourceDetailContent.tsx` | Component pattern |
| `frontend/src/lib/types/api.ts` | Type definitions |
| `docs/acm-ai/04-architecture.md` | AG Grid column config |

### Dependencies After E2-S1

After completing E2-S1 (Install AG Grid), these should exist:
- `ag-grid-react` and `ag-grid-community` in package.json
- AG Grid CSS imported in globals.css

---

## Implementation Plan

### Tasks

- [ ] **Task 1: Create ACM types in `frontend/src/lib/types/acm.ts`**
  - ACMRecord interface
  - ACMRecordListResponse interface
  - ACMStats interface

- [ ] **Task 2: Create ACM API client in `frontend/src/lib/api/acm.ts`**
  - list() - fetch records with filters
  - get() - fetch single record
  - extract() - trigger extraction
  - export() - download CSV
  - stats() - get statistics

- [ ] **Task 3: Create ACMSpreadsheet component**
  - Location: `frontend/src/components/acm/ACMSpreadsheet.tsx`
  - Use AG Grid with column definitions
  - Fetch data via React Query
  - Handle loading/error/empty states

- [ ] **Task 4: Define column configuration**
  - All ACM fields as columns
  - Appropriate widths
  - Sortable and filterable

- [ ] **Task 5: Create ACMSpreadsheet index export**
  - `frontend/src/components/acm/index.ts`

- [ ] **Task 6: Test in source detail view**
  - Temporarily render in source page
  - Verify data loads correctly

### Acceptance Criteria

- [ ] **AC1**: Component renders AG Grid with ACM columns
  - Given: ACMSpreadsheet with sourceId prop
  - When: Component mounts
  - Then: AG Grid renders with defined columns

- [ ] **AC2**: Fetches data from API on source selection
  - Given: sourceId is provided
  - When: Component mounts
  - Then: Calls `/api/acm/records?source_id=xxx`

- [ ] **AC3**: Shows loading state during fetch
  - Given: Data is being fetched
  - When: isLoading is true
  - Then: Loading spinner displayed

- [ ] **AC4**: Shows empty state when no ACM data
  - Given: API returns empty records
  - When: Data loads
  - Then: Empty state message shown

- [ ] **AC5**: Shows error state on API failure
  - Given: API call fails
  - When: Error occurs
  - Then: Error message displayed

---

## Code Specification

### File: `frontend/src/lib/types/acm.ts`

```typescript
/**
 * ACM (Asbestos Containing Material) Types
 */

export interface ACMRecord {
  id: string
  source_id: string
  school_name: string
  school_code?: string
  building_id: string
  building_name?: string
  building_year?: number
  building_construction?: string
  room_id?: string
  room_name?: string
  room_area?: number
  area_type?: 'Interior' | 'Exterior' | 'Grounds'
  product: string
  material_description: string
  extent?: string
  location?: string
  friable?: 'Friable' | 'Non Friable'
  material_condition?: string
  risk_status?: 'Low' | 'Medium' | 'High'
  result: string
  page_number?: number
  extraction_confidence?: number
  created?: string
  updated?: string
}

export interface ACMRecordListResponse {
  records: ACMRecord[]
  total: number
  page: number
  pages: number
  limit: number
}

export interface ACMExtractRequest {
  source_id: string
}

export interface ACMExtractResponse {
  command_id: string
  status: string
  message: string
}

export interface ACMStats {
  total_records: number
  high_risk_count: number
  medium_risk_count: number
  low_risk_count: number
  building_count: number
  room_count: number
  source_id?: string
}
```

### File: `frontend/src/lib/api/acm.ts`

```typescript
/**
 * ACM API Client
 */

import apiClient from './client'
import type {
  ACMRecord,
  ACMRecordListResponse,
  ACMExtractRequest,
  ACMExtractResponse,
  ACMStats
} from '@/lib/types/acm'

export interface ACMListParams {
  source_id: string
  building_id?: string
  room_id?: string
  risk_status?: 'Low' | 'Medium' | 'High'
  search?: string
  page?: number
  limit?: number
}

export const acmApi = {
  /**
   * List ACM records with filtering and pagination
   */
  list: async (params: ACMListParams): Promise<ACMRecordListResponse> => {
    const response = await apiClient.get<ACMRecordListResponse>('/acm/records', { params })
    return response.data
  },

  /**
   * Get a single ACM record by ID
   */
  get: async (id: string): Promise<ACMRecord> => {
    const response = await apiClient.get<ACMRecord>(`/acm/records/${id}`)
    return response.data
  },

  /**
   * Trigger ACM extraction for a source
   */
  extract: async (data: ACMExtractRequest): Promise<ACMExtractResponse> => {
    const response = await apiClient.post<ACMExtractResponse>('/acm/extract', data)
    return response.data
  },

  /**
   * Get export URL for downloading CSV
   */
  getExportUrl: (source_id: string, format: 'csv' | 'json' = 'csv'): string => {
    return `${apiClient.defaults.baseURL}/acm/export?source_id=${encodeURIComponent(source_id)}&format=${format}`
  },

  /**
   * Get ACM statistics
   */
  stats: async (source_id?: string): Promise<ACMStats> => {
    const params = source_id ? { source_id } : undefined
    const response = await apiClient.get<ACMStats>('/acm/stats', { params })
    return response.data
  },
}

export default acmApi
```

### File: `frontend/src/components/acm/ACMSpreadsheet.tsx`

```typescript
'use client'

import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AgGridReact } from 'ag-grid-react'
import type { ColDef, GridReadyEvent, CellClickedEvent } from 'ag-grid-community'

import { acmApi } from '@/lib/api/acm'
import type { ACMRecord } from '@/lib/types/acm'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle, FileSpreadsheet } from 'lucide-react'

// Import AG Grid styles (should also be in globals.css)
import 'ag-grid-community/styles/ag-grid.css'
import 'ag-grid-community/styles/ag-theme-alpine.css'

interface ACMSpreadsheetProps {
  sourceId: string
  onCellClick?: (record: ACMRecord, field: string) => void
}

export function ACMSpreadsheet({ sourceId, onCellClick }: ACMSpreadsheetProps) {
  // Fetch ACM records
  const {
    data,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['acm-records', sourceId],
    queryFn: () => acmApi.list({ source_id: sourceId, limit: 500 }),
    enabled: !!sourceId,
  })

  // Column definitions
  const columnDefs = useMemo<ColDef<ACMRecord>[]>(() => [
    {
      field: 'building_name',
      headerName: 'Building',
      width: 150,
      filter: 'agTextColumnFilter',
      sortable: true,
    },
    {
      field: 'room_name',
      headerName: 'Room',
      width: 150,
      filter: 'agTextColumnFilter',
      sortable: true,
    },
    {
      field: 'product',
      headerName: 'Product',
      width: 150,
      filter: 'agTextColumnFilter',
      sortable: true,
    },
    {
      field: 'material_description',
      headerName: 'Material',
      width: 200,
      filter: 'agTextColumnFilter',
      sortable: true,
    },
    {
      field: 'extent',
      headerName: 'Extent',
      width: 100,
      sortable: true,
    },
    {
      field: 'location',
      headerName: 'Location',
      width: 120,
      filter: 'agTextColumnFilter',
      sortable: true,
    },
    {
      field: 'friable',
      headerName: 'Friable',
      width: 100,
      filter: 'agSetColumnFilter',
      sortable: true,
    },
    {
      field: 'material_condition',
      headerName: 'Condition',
      width: 120,
      filter: 'agSetColumnFilter',
      sortable: true,
    },
    {
      field: 'risk_status',
      headerName: 'Risk',
      width: 90,
      filter: 'agSetColumnFilter',
      sortable: true,
      // Cell renderer will be added in E2-S5
    },
    {
      field: 'result',
      headerName: 'Result',
      width: 150,
      filter: 'agSetColumnFilter',
      sortable: true,
    },
  ], [])

  // Default column properties
  const defaultColDef = useMemo<ColDef>(() => ({
    resizable: true,
    cellClass: 'cursor-pointer',
  }), [])

  // Handle cell click
  const handleCellClicked = (event: CellClickedEvent<ACMRecord>) => {
    if (event.data && event.colDef.field && onCellClick) {
      onCellClick(event.data, event.colDef.field)
    }
  }

  // Handle grid ready
  const handleGridReady = (event: GridReadyEvent) => {
    // Auto-size columns to fit content
    event.api.sizeColumnsToFit()
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner />
        <span className="ml-2 text-muted-foreground">Loading ACM records...</span>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load ACM records: {error instanceof Error ? error.message : 'Unknown error'}
        </AlertDescription>
      </Alert>
    )
  }

  // Empty state
  if (!data?.records || data.records.length === 0) {
    return (
      <EmptyState
        icon={<FileSpreadsheet className="h-12 w-12 text-muted-foreground" />}
        title="No ACM Records"
        description="No asbestos register data has been extracted from this document yet."
      />
    )
  }

  return (
    <div className="h-full w-full">
      {/* Stats bar */}
      <div className="flex items-center gap-4 px-2 py-1 text-sm text-muted-foreground border-b">
        <span>{data.total} records</span>
        <span>|</span>
        <span>Page {data.page} of {data.pages}</span>
      </div>

      {/* AG Grid */}
      <div className="ag-theme-alpine h-[calc(100%-32px)] w-full">
        <AgGridReact<ACMRecord>
          rowData={data.records}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          onGridReady={handleGridReady}
          onCellClicked={handleCellClicked}
          animateRows={true}
          enableCellTextSelection={true}
          suppressRowClickSelection={true}
          rowSelection="single"
        />
      </div>
    </div>
  )
}

export default ACMSpreadsheet
```

### File: `frontend/src/components/acm/index.ts`

```typescript
export { ACMSpreadsheet } from './ACMSpreadsheet'
export type { } from './ACMSpreadsheet'
```

---

## Additional Context

### Dependencies

| Dependency | Type | Notes |
|------------|------|-------|
| E2-S1 (AG Grid Install) | Story | Must be complete |
| E1-S4 (ACM API) | Story | Must be complete |
| ag-grid-react | npm | AG Grid React wrapper |
| ag-grid-community | npm | AG Grid core |
| @tanstack/react-query | npm | Already installed |

### AG Grid Setup (E2-S1 prerequisite)

After E2-S1, these should exist:

```json
// package.json
{
  "dependencies": {
    "ag-grid-react": "^31.x",
    "ag-grid-community": "^31.x"
  }
}
```

```css
/* globals.css */
@import 'ag-grid-community/styles/ag-grid.css';
@import 'ag-grid-community/styles/ag-theme-alpine.css';
```

### Testing Strategy

1. **Component Tests**: Render with mock data
2. **Integration Tests**: Full flow with real API
3. **Visual Tests**: Check layout, responsiveness

### Future Enhancements (Later Stories)

- E2-S3: Sorting/Filtering (mostly built-in, enhance)
- E2-S4: Row Grouping by Building/Room
- E2-S5: Risk Status Color Coding
- E2-S6: Quick Search Bar

---

## Next Stories After This

| Story | Description | Depends On |
|-------|-------------|------------|
| E2-S3 | Column Sorting and Filtering | This story |
| E2-S4 | Row Grouping | This story |
| E3-S1 | Make Cells Clickable | This story |

---

*Tech-Spec generated by create-tech-spec workflow*
