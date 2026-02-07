'use client'

import { useState, useMemo, useDeferredValue, useCallback } from 'react'
import { useSources } from '@/lib/hooks/use-sources'
import { useLocalStorage } from '@/lib/hooks/use-local-storage'
import { DocumentGrid } from './DocumentGrid'
import { DocumentList } from './DocumentList'
import { DocumentFilters, type DocumentFiltersState } from './DocumentFilters'
import { ViewToggle } from './ViewToggle'
import { BulkActions } from './BulkActions'
import { EmptyState } from '@/components/common/EmptyState'
import { Skeleton } from '@/components/ui/skeleton'
import { FileText, Upload } from 'lucide-react'
import { Button } from '@/components/ui/button'
import Link from 'next/link'

export function DocumentLibrary() {
  const { data: sources, isLoading, refetch } = useSources()
  const [view, setView] = useLocalStorage<'grid' | 'list'>('doc-library-view', 'grid')
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [filters, setFilters] = useState<DocumentFiltersState>({
    search: '',
    type: null,
    status: null,
    sortBy: 'date',
    sortOrder: 'desc',
  })
  const deferredSearch = useDeferredValue(filters.search)

  const filteredDocuments = useMemo(() => {
    if (!sources) return []

    let filtered = [...sources]

    // Search filter
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

    // Sorting
    filtered.sort((a, b) => {
      const order = filters.sortOrder === 'asc' ? 1 : -1
      switch (filters.sortBy) {
        case 'name':
          return (a.title || '').localeCompare(b.title || '') * order
        case 'date':
          return (new Date(a.created).getTime() - new Date(b.created).getTime()) * order
        case 'records':
          return ((a.insights_count || 0) - (b.insights_count || 0)) * order
        default:
          return 0
      }
    })

    return filtered
  }, [sources, deferredSearch, filters.type, filters.status, filters.sortBy, filters.sortOrder])

  const handleSelectAll = useCallback(() => {
    if (selectedIds.size === filteredDocuments.length) {
      setSelectedIds(new Set())
    } else {
      setSelectedIds(new Set(filteredDocuments.map((d) => d.id)))
    }
  }, [selectedIds.size, filteredDocuments])

  const handleSelectOne = useCallback((id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }, [])

  if (isLoading) {
    return <DocumentLibrarySkeleton />
  }

  if (!sources || sources.length === 0) {
    return (
      <EmptyState
        icon={FileText}
        title="No Documents Yet"
        description="Upload your first SAMP document to start extracting ACM register data."
        action={
          <Button asChild>
            <Link href="/sources?action=upload">
              <Upload className="w-4 h-4 mr-2" />
              Upload Document
            </Link>
          </Button>
        }
      />
    )
  }

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
            refetch()
          }}
        />
      )}

      {/* Document Display */}
      <div className="flex-1 overflow-auto">
        {filteredDocuments.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-xl font-semibold mb-2">No documents found</h2>
            <p className="text-muted-foreground">Try adjusting your filters</p>
          </div>
        ) : view === 'grid' ? (
          <DocumentGrid
            documents={filteredDocuments}
            selectedIds={selectedIds}
            onSelect={handleSelectOne}
            onSelectAll={handleSelectAll}
            onRefetch={refetch}
          />
        ) : (
          <DocumentList
            documents={filteredDocuments}
            selectedIds={selectedIds}
            onSelect={handleSelectOne}
            onSelectAll={handleSelectAll}
            onRefetch={refetch}
          />
        )}
      </div>
    </div>
  )
}

function DocumentLibrarySkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-10 w-36" />
        <Skeleton className="h-10 w-36" />
        <div className="flex-1" />
        <Skeleton className="h-10 w-20" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="rounded-lg border p-4 space-y-3">
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <div className="flex gap-2">
              <Skeleton className="h-6 w-16" />
              <Skeleton className="h-6 w-20" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
