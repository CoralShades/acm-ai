# Tech Spec: E14-S7 - Merge Sources and Documents into Unified View

> **Story:** E14-S7
> **Epic:** E14 - UX & Enterprise Readiness
> **Status:** Ready for Dev
> **Created:** 2026-02-08

---

## Overview

This story merges the separate `/sources` and `/documents` pages into a single unified `/documents` route. Users currently face confusion with two overlapping pages that both display uploaded files. The unified view will combine the best features of both pages: the powerful search/sort/bulk actions from the sources page with the Library/Processing tab structure from the documents page.

The `/sources` route will redirect to `/documents` via middleware, but the deep link route `/sources/[id]` (source detail page) will remain unchanged to preserve existing navigation patterns.

---

## User Story

**As a** user
**I want** a single Documents page instead of separate Sources and Documents views
**So that** I have one place to find all my uploaded files

---

## Acceptance Criteria

- [ ] `/sources` redirects to `/documents` via middleware (preserving query params)
- [ ] `/sources/[id]` continues to work (source detail page remains unchanged)
- [ ] Unified `/documents` page has Library and Processing tabs (from current documents page)
- [ ] Library tab includes grid/table/list view toggle (from current sources page)
- [ ] All document filters available (search, type, status, sort) in Library tab
- [ ] Bulk actions preserved (select multiple, delete selected)
- [ ] Infinite scroll for large source lists (from current sources page)
- [ ] Keyboard navigation works in list view (from current sources page)
- [ ] Empty state with "Upload Document" CTA
- [ ] Sidebar navigation updated to show single "Documents" entry

---

## Technical Design

### 1. Unified Documents Page Architecture

The new `/documents/page.tsx` will combine:

**From current documents page:**
- Library/Processing tab structure using Radix `<Tabs>`
- `DocumentLibrary` component (enhance with new features)
- `ProcessingStatus` component (unchanged)

**From current sources page:**
- Infinite scroll with pagination (`offset`, `limit`, `hasMore` logic)
- Keyboard navigation (Arrow Up/Down, Enter, Home, End)
- Search with deferred value for performance
- Sort by created/updated with asc/desc toggle
- Bulk selection and bulk delete
- Grid/List/Table view toggle with localStorage persistence

### 2. Component Strategy

#### 2.1 Enhanced DocumentLibrary Component

The existing `DocumentLibrary` component at `/components/documents/DocumentLibrary.tsx` already has:
- ✅ Grid/List view toggle (via `ViewToggle`)
- ✅ Search filter with deferred value
- ✅ Type filter (upload vs URL)
- ✅ Status filter (completed, processing, failed, pending)
- ✅ Sort by (name, date, records)
- ✅ Bulk selection and `BulkActions` component
- ✅ Empty state with Upload CTA

**Missing features to add from sources page:**
- ❌ **Table view** (currently only grid and list, but list uses `DocumentList` which is cards, not a table)
- ❌ **Infinite scroll** (currently loads all sources at once via `useSources()` hook)
- ❌ **Keyboard navigation** for list view (Arrow keys, Enter, Home, End)

**Recommendation:** Keep `DocumentLibrary` as the base, but enhance it:
1. Add a third view option: `'table'` alongside `'grid'` and `'list'`
2. When view is `'table'`, render `SourcesTableView` component (which has keyboard nav built-in)
3. Add infinite scroll logic similar to sources page (refs: `offsetRef`, `hasMoreRef`, `loadingMoreRef`)
4. Create a new API hook `useSourcesPaginated()` that supports offset-based pagination

#### 2.2 Reusable Components from Sources Page

These components from `/components/sources/` can be reused in the documents page:

| Component | Purpose | Reuse Strategy |
|-----------|---------|----------------|
| `SourcesTableView.tsx` | Table layout with keyboard nav | Import directly; rename in JSX as `<DocumentTable>` |
| `SourcesGridView.tsx` | Bento grid layout | Already similar to `DocumentGrid`; prefer existing `DocumentGrid` |
| `SourceCard.tsx` | Individual grid card | Consolidate with `DocumentCard` (very similar) |

**Action:** For table view, import and reuse `SourcesTableView` directly. It already has keyboard navigation, sort headers, and select-all logic.

### 3. Middleware Redirect

**File:** `frontend/src/middleware.ts`

**Current code:**
```typescript
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Redirect root to notebooks
  if (pathname === '/') {
    return NextResponse.redirect(new URL('/notebooks', request.url))
  }

  return NextResponse.next()
}
```

**Updated code:**
```typescript
export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl

  // Redirect root to notebooks (will change in E14-S1 to dashboard)
  if (pathname === '/') {
    return NextResponse.redirect(new URL('/notebooks', request.url))
  }

  // Redirect /sources to /documents (preserve query params)
  if (pathname === '/sources') {
    return NextResponse.redirect(new URL(`/documents${search}`, request.url))
  }

  return NextResponse.next()
}
```

**Key points:**
- Only redirect `/sources` (exact match)
- Preserve query params via `search` (e.g., `/sources?action=upload` → `/documents?action=upload`)
- Do NOT redirect `/sources/[id]` routes (they will continue to work as source detail pages)

### 4. View Toggle Strategy

**Current state:**
- **Sources page:** Uses `useLocalStorage('sources-view', 'list')` with options `'grid' | 'list'`
- **Documents page:** Uses `useLocalStorage('doc-library-view', 'grid')` with options `'grid' | 'list'`

**Target state:**
- **Unified documents page:** Use `useLocalStorage('documents-view', 'grid')` with options `'grid' | 'list' | 'table'`

**Implementation:**
```typescript
const [view, setView] = useLocalStorage<'grid' | 'list' | 'table'>('documents-view', 'grid')
```

Update `ViewToggle` component to support three options:
```typescript
// components/documents/ViewToggle.tsx
export function ViewToggle({
  view,
  onChange
}: {
  view: 'grid' | 'list' | 'table'
  onChange: (view: 'grid' | 'list' | 'table') => void
}) {
  return (
    <div className="flex items-center border rounded-lg p-1">
      <Button
        variant={view === 'grid' ? 'secondary' : 'ghost'}
        size="sm"
        onClick={() => onChange('grid')}
        className="px-2"
      >
        <LayoutGrid className="w-4 h-4" />
      </Button>
      <Button
        variant={view === 'list' ? 'secondary' : 'ghost'}
        size="sm"
        onClick={() => onChange('list')}
        className="px-2"
      >
        <List className="w-4 h-4" />
      </Button>
      <Button
        variant={view === 'table' ? 'secondary' : 'ghost'}
        size="sm"
        onClick={() => onChange('table')}
        className="px-2"
      >
        <Table className="w-4 h-4" />
      </Button>
    </div>
  )
}
```

### 5. Filter Consolidation

The `DocumentFilters` component already supports all necessary filters:
- ✅ Search (text input with clear button)
- ✅ Type (upload vs URL)
- ✅ Status (completed, processing, failed, pending)
- ✅ Sort (name, date, records with asc/desc)

**No changes needed** to filter logic. Filters apply to all views (grid, list, table).

### 6. Bulk Actions Preservation

The `BulkActions` component already exists and supports:
- ✅ Display selected count
- ✅ Clear selection button
- ✅ Bulk delete with confirmation dialog
- ✅ Partial failure handling (toast warnings)

**No changes needed** to bulk actions logic.

### 7. Infinite Scroll Implementation

**Current state:**
- Sources page: Implements infinite scroll with `offsetRef`, `hasMoreRef`, `loadingMoreRef`
- Documents page: Loads all sources via `useSources()` hook (no pagination)

**Target state:** Add pagination to documents page.

**New hook:** `useSourcesPaginated`
```typescript
// lib/hooks/use-sources-paginated.ts
export function useSourcesPaginated({
  limit = 30,
  sortBy = 'updated',
  sortOrder = 'desc',
}: {
  limit?: number
  sortBy?: 'created' | 'updated'
  sortOrder?: 'asc' | 'desc'
}) {
  const [sources, setSources] = useState<SourceListResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const offsetRef = useRef(0)
  const hasMoreRef = useRef(true)
  const loadingMoreRef = useRef(false)

  const fetchMore = useCallback(async (reset = false) => {
    if (!reset && (loadingMoreRef.current || !hasMoreRef.current)) return

    if (reset) {
      setLoading(true)
      offsetRef.current = 0
      setSources([])
      hasMoreRef.current = true
    } else {
      loadingMoreRef.current = true
      setLoadingMore(true)
    }

    const data = await sourcesApi.list({
      limit,
      offset: offsetRef.current,
      sort_by: sortBy,
      sort_order: sortOrder,
    })

    if (reset) {
      setSources(data)
    } else {
      setSources(prev => [...prev, ...data])
    }

    hasMoreRef.current = data.length === limit
    offsetRef.current += data.length
    setLoading(false)
    setLoadingMore(false)
    loadingMoreRef.current = false
  }, [limit, sortBy, sortOrder])

  useEffect(() => {
    fetchMore(true)
  }, [fetchMore])

  return { sources, loading, loadingMore, fetchMore, hasMore: hasMoreRef.current }
}
```

Update `DocumentLibrary` to use this hook instead of `useSources()`.

### 8. Keyboard Navigation

**Current state:**
- Sources page table view: Full keyboard nav (Arrow Up/Down, Enter, Home, End)
- Documents page: No keyboard nav

**Target state:** Preserve keyboard nav when table view is selected.

**Implementation:** The `SourcesTableView` component already handles keyboard nav internally. When the user selects "table" view, the component will automatically enable keyboard shortcuts.

### 9. Navigation Sidebar Update

**This change is NOT part of E14-S7.** It belongs to E14-S2 (Navigation Redesign).

However, for reference, the change will be:
```typescript
// In AppSidebar.tsx navigation array (future story)
{
  title: 'Workspace',
  items: [
    { name: 'Dashboard', href: '/', icon: LayoutDashboard },
    { name: 'Documents', href: '/documents', icon: Library }, // ← merged from Sources + Documents
    { name: 'ACM Register', href: '/acm', icon: FileWarning },
    { name: 'Search', href: '/search', icon: Search },
  ],
}
```

---

## File Changes

| File | Change Type | Description |
|------|-------------|-------------|
| `frontend/src/app/(dashboard)/documents/page.tsx` | **Modify** | Keep Library/Processing tabs; no structural change |
| `frontend/src/components/documents/DocumentLibrary.tsx` | **Modify** | Add table view option, infinite scroll, and keyboard nav support |
| `frontend/src/components/documents/ViewToggle.tsx` | **Modify** | Add third option: `'table'` |
| `frontend/src/lib/hooks/use-sources-paginated.ts` | **Create** | New hook for paginated source fetching |
| `frontend/src/middleware.ts` | **Modify** | Add `/sources` → `/documents` redirect |
| `frontend/src/app/(dashboard)/sources/page.tsx` | **No Change** | Keep for now (middleware redirects); can deprecate later |
| `frontend/src/app/(dashboard)/sources/[id]/page.tsx` | **No Change** | Source detail page remains at same route |

---

## Implementation Details

### Step 1: Create Paginated Hook

**File:** `frontend/src/lib/hooks/use-sources-paginated.ts`

```typescript
'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { sourcesApi } from '@/lib/api/sources'
import { SourceListResponse } from '@/lib/types/api'

interface UseSourcesPaginatedParams {
  limit?: number
  sortBy?: 'created' | 'updated'
  sortOrder?: 'asc' | 'desc'
}

export function useSourcesPaginated({
  limit = 30,
  sortBy = 'updated',
  sortOrder = 'desc',
}: UseSourcesPaginatedParams = {}) {
  const [sources, setSources] = useState<SourceListResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const offsetRef = useRef(0)
  const hasMoreRef = useRef(true)
  const loadingMoreRef = useRef(false)

  const fetchMore = useCallback(
    async (reset = false) => {
      if (!reset && (loadingMoreRef.current || !hasMoreRef.current)) {
        return
      }

      if (reset) {
        setLoading(true)
        offsetRef.current = 0
        setSources([])
        hasMoreRef.current = true
      } else {
        loadingMoreRef.current = true
        setLoadingMore(true)
      }

      try {
        const data = await sourcesApi.list({
          limit,
          offset: offsetRef.current,
          sort_by: sortBy,
          sort_order: sortOrder,
        })

        if (reset) {
          setSources(data)
        } else {
          setSources((prev) => [...prev, ...data])
        }

        hasMoreRef.current = data.length === limit
        offsetRef.current += data.length
      } catch (error) {
        console.error('Failed to fetch sources:', error)
      } finally {
        setLoading(false)
        setLoadingMore(false)
        loadingMoreRef.current = false
      }
    },
    [limit, sortBy, sortOrder]
  )

  useEffect(() => {
    fetchMore(true)
  }, [fetchMore])

  return {
    sources,
    loading,
    loadingMore,
    fetchMore,
    hasMore: hasMoreRef.current,
  }
}
```

### Step 2: Update ViewToggle Component

**File:** `frontend/src/components/documents/ViewToggle.tsx`

```typescript
'use client'

import { LayoutGrid, List, Table } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ViewToggleProps {
  view: 'grid' | 'list' | 'table'
  onChange: (view: 'grid' | 'list' | 'table') => void
}

export function ViewToggle({ view, onChange }: ViewToggleProps) {
  return (
    <div className="flex items-center border rounded-lg p-1">
      <Button
        variant={view === 'grid' ? 'secondary' : 'ghost'}
        size="sm"
        onClick={() => onChange('grid')}
        className="px-2"
        aria-label="Grid view"
      >
        <LayoutGrid className="w-4 h-4" />
      </Button>
      <Button
        variant={view === 'list' ? 'secondary' : 'ghost'}
        size="sm"
        onClick={() => onChange('list')}
        className="px-2"
        aria-label="List view"
      >
        <List className="w-4 h-4" />
      </Button>
      <Button
        variant={view === 'table' ? 'secondary' : 'ghost'}
        size="sm"
        onClick={() => onChange('table')}
        className="px-2"
        aria-label="Table view"
      >
        <Table className="w-4 h-4" />
      </Button>
    </div>
  )
}
```

### Step 3: Enhance DocumentLibrary Component

**File:** `frontend/src/components/documents/DocumentLibrary.tsx`

**Key changes:**
1. Replace `useSources()` with `useSourcesPaginated()`
2. Add `'table'` to view type union
3. Add infinite scroll listener
4. Add table view rendering (import `SourcesTableView`)
5. Add keyboard navigation state for table view

**Code pattern:**
```typescript
'use client'

import { useState, useMemo, useDeferredValue, useCallback, useRef, useEffect } from 'react'
import { useSourcesPaginated } from '@/lib/hooks/use-sources-paginated'
import { useLocalStorage } from '@/lib/hooks/use-local-storage'
import { DocumentGrid } from './DocumentGrid'
import { DocumentList } from './DocumentList'
import { SourcesTableView } from '@/components/sources/SourcesTableView'
import { DocumentFilters, type DocumentFiltersState } from './DocumentFilters'
import { ViewToggle } from './ViewToggle'
import { BulkActions } from './BulkActions'
// ... other imports

export function DocumentLibrary() {
  const [view, setView] = useLocalStorage<'grid' | 'list' | 'table'>('documents-view', 'grid')
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [selectedIndex, setSelectedIndex] = useState(0) // For keyboard nav in table view
  const [filters, setFilters] = useState<DocumentFiltersState>({
    search: '',
    type: null,
    status: null,
    sortBy: 'date',
    sortOrder: 'desc',
  })
  const deferredSearch = useDeferredValue(filters.search)
  const scrollContainerRef = useRef<HTMLDivElement>(null)

  // Use paginated hook
  const {
    sources,
    loading,
    loadingMore,
    fetchMore,
    hasMore
  } = useSourcesPaginated({
    limit: 30,
    sortBy: filters.sortBy === 'date' ? 'created' : 'updated',
    sortOrder: filters.sortOrder,
  })

  // Filter sources client-side
  const filteredDocuments = useMemo(() => {
    let filtered = [...sources]

    // Search
    if (deferredSearch) {
      const searchLower = deferredSearch.toLowerCase()
      filtered = filtered.filter(
        (s) =>
          s.title?.toLowerCase().includes(searchLower) ||
          s.asset?.url?.toLowerCase().includes(searchLower)
      )
    }

    // Type filter
    if (filters.type) {
      filtered = filtered.filter((s) => {
        if (filters.type === 'upload') return s.asset?.file_path
        if (filters.type === 'url') return s.asset?.url && !s.asset?.file_path
        return true
      })
    }

    // Status filter
    if (filters.status) {
      filtered = filtered.filter((s) => {
        const status = s.status || (s.embedded ? 'completed' : 'pending')
        return status === filters.status
      })
    }

    return filtered
  }, [sources, deferredSearch, filters.type, filters.status])

  // Infinite scroll
  useEffect(() => {
    const scrollContainer = scrollContainerRef.current
    if (!scrollContainer || !hasMore || loadingMore) return

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = scrollContainer
      const distanceFromBottom = scrollHeight - scrollTop - clientHeight

      if (distanceFromBottom < 200 && hasMore) {
        fetchMore(false)
      }
    }

    scrollContainer.addEventListener('scroll', handleScroll)
    handleScroll() // Check on mount

    return () => scrollContainer.removeEventListener('scroll', handleScroll)
  }, [fetchMore, hasMore, loadingMore])

  // ... selection handlers, loading states, empty states ...

  return (
    <div className="flex flex-col flex-1 space-y-4">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-4 flex-shrink-0">
        <DocumentFilters filters={filters} onChange={setFilters} />
        <div className="flex-1" />
        <ViewToggle view={view} onChange={setView} />
      </div>

      {/* Bulk Actions */}
      {selectedIds.size > 0 && (
        <BulkActions
          selectedCount={selectedIds.size}
          selectedIds={Array.from(selectedIds)}
          onClearSelection={() => setSelectedIds(new Set())}
          onActionComplete={() => {
            setSelectedIds(new Set())
            fetchMore(true) // Refresh
          }}
        />
      )}

      {/* Document Display */}
      <div ref={scrollContainerRef} className="flex-1 overflow-auto">
        {filteredDocuments.length === 0 ? (
          <EmptyState />
        ) : view === 'grid' ? (
          <DocumentGrid
            documents={filteredDocuments}
            selectedIds={selectedIds}
            onSelect={handleSelectOne}
            onSelectAll={handleSelectAll}
            onRefetch={() => fetchMore(true)}
          />
        ) : view === 'list' ? (
          <DocumentList
            documents={filteredDocuments}
            selectedIds={selectedIds}
            onSelect={handleSelectOne}
            onSelectAll={handleSelectAll}
            onRefetch={() => fetchMore(true)}
          />
        ) : (
          <div className="rounded-md border">
            <SourcesTableView
              sources={filteredDocuments}
              selectedIds={selectedIds}
              onToggleSelection={handleSelectOne}
              onDeleteSource={(source) => {
                // Show confirm dialog, then delete
              }}
              sortBy="created"
              sortOrder={filters.sortOrder}
              onToggleSort={(field) => {
                // Update filters.sortBy and filters.sortOrder
              }}
              selectedIndex={selectedIndex}
              onSelectIndex={setSelectedIndex}
              loadingMore={loadingMore}
            />
          </div>
        )}
      </div>
    </div>
  )
}
```

### Step 4: Update Middleware

**File:** `frontend/src/middleware.ts`

```typescript
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl

  // Redirect root to notebooks (will change in E14-S1 to dashboard)
  if (pathname === '/') {
    return NextResponse.redirect(new URL('/notebooks', request.url))
  }

  // Redirect /sources to /documents (preserve query params)
  if (pathname === '/sources') {
    return NextResponse.redirect(new URL(`/documents${search}`, request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico|brand).*)',
  ],
}
```

---

## Dependencies

- **Epic 14 Stories:**
  - No dependencies within Epic 14
  - This story can be implemented independently

- **Existing Code:**
  - `sourcesApi.list()` - REST API client for paginated source fetching
  - `SourcesTableView` component - Reused for table view
  - `DocumentGrid`, `DocumentList`, `BulkActions` - Existing components

- **No Database Changes:** All data fetched via existing `sources` API endpoint

---

## Testing Strategy

### 1. Unit Tests
- `useSourcesPaginated` hook: Test pagination logic, reset, and hasMore flag
- `ViewToggle` component: Test three-way toggle (grid/list/table)
- Middleware: Test `/sources` redirect preserves query params

### 2. Integration Tests
- **Library tab with table view:**
  - Verify infinite scroll triggers `fetchMore()`
  - Verify keyboard navigation (Arrow keys, Enter)
  - Verify sort headers update URL params

- **Bulk actions:**
  - Select multiple documents → verify count badge
  - Delete selected → verify confirmation dialog
  - Partial failure → verify warning toast

- **Filters:**
  - Apply search filter → verify filtered results
  - Apply type filter (upload vs URL) → verify results
  - Apply status filter → verify results
  - Change sort → verify order changes

### 3. E2E Tests (Playwright)
```typescript
test('E14-S7: /sources redirects to /documents', async ({ page }) => {
  await page.goto('/sources')
  await expect(page).toHaveURL('/documents')
})

test('E14-S7: /sources/[id] does NOT redirect', async ({ page }) => {
  await page.goto('/sources/source:123')
  await expect(page).toHaveURL('/sources/source:123')
})

test('E14-S7: table view has keyboard navigation', async ({ page }) => {
  await page.goto('/documents')
  await page.click('button[aria-label="Table view"]')
  await page.keyboard.press('ArrowDown')
  await page.keyboard.press('ArrowDown')
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/\/sources\/source:/)
})

test('E14-S7: bulk delete works in library tab', async ({ page }) => {
  await page.goto('/documents')
  await page.click('input[type="checkbox"]') // Select first
  await page.click('button:has-text("Delete")')
  await page.click('button:has-text("Delete")') // Confirm
  await expect(page.locator('text="deleted successfully"')).toBeVisible()
})
```

### 4. Manual Testing Checklist
- [ ] Visit `/sources` → redirects to `/documents`
- [ ] Visit `/sources?action=upload` → redirects to `/documents?action=upload`
- [ ] Visit `/sources/source:123` → stays at `/sources/source:123` (no redirect)
- [ ] Library tab: Switch between grid/list/table views
- [ ] Table view: Use Arrow keys to navigate, Enter to open
- [ ] Scroll to bottom → more sources load automatically
- [ ] Select multiple sources → bulk actions appear
- [ ] Delete selected sources → confirmation dialog → success toast
- [ ] Apply search filter → results update
- [ ] Apply type filter → results update
- [ ] Apply status filter → results update
- [ ] Change sort order → results reorder
- [ ] Empty state shows when no sources exist

---

## Estimated Complexity

**Story Points:** 5

**Breakdown:**
- Create `useSourcesPaginated` hook: 1 point
- Update `ViewToggle` to support table: 0.5 points
- Enhance `DocumentLibrary` with table view and infinite scroll: 2 points
- Add keyboard navigation state management: 1 point
- Update middleware redirect: 0.5 points
- Testing (unit + integration + E2E): 1 point

**Risk Factors:**
- **Medium risk:** Infinite scroll performance with large datasets (100+ sources)
- **Low risk:** Keyboard navigation conflicts with browser shortcuts
- **Low risk:** Middleware redirect edge cases (deep links, external referrers)

**Mitigation:**
- Use deferred values and `useMemo` for filtering to prevent re-renders
- Test keyboard shortcuts in different browsers (Chrome, Firefox, Safari)
- Test middleware redirects with various query param combinations

---

## Notes

- **Source detail pages (`/sources/[id]`) are NOT affected** - they remain at their current route to avoid breaking existing links/bookmarks
- **Navigation sidebar update** (removing "Sources" link) is handled in E14-S2, not this story
- **Empty state CTA** already exists in `DocumentLibrary` - no changes needed
- **Processing tab** remains unchanged - it only displays background job status
- **LocalStorage migration:** Users who have `sources-view` or `doc-library-view` persisted will default to grid view on first visit to unified page (acceptable behavior)
