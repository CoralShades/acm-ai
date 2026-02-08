'use client'

import { useState, useMemo, useDeferredValue, useCallback, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useSourcesPaginated } from '@/lib/hooks/use-sources-paginated'
import { useLocalStorage } from '@/lib/hooks/use-local-storage'
import { DocumentGrid } from './DocumentGrid'
import { DocumentList } from './DocumentList'
import { SourcesTableView } from '@/components/sources/SourcesTableView'
import { DocumentFilters, type DocumentFiltersState } from './DocumentFilters'
import { ViewToggle } from './ViewToggle'
import { BulkActions } from './BulkActions'
import { EmptyState } from '@/components/common/EmptyState'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { DocumentsSkeleton } from '@/components/skeletons/DocumentsSkeleton'
import { FileText, Upload } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { toast } from 'sonner'
import { sourcesApi } from '@/lib/api/sources'
import type { SourceListResponse } from '@/lib/types/api'
import Link from 'next/link'

export function DocumentLibrary() {
  const router = useRouter()
  const [view, setView] = useLocalStorage<'grid' | 'list' | 'table'>('documents-view', 'grid')
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [selectedIndex, setSelectedIndex] = useState(0)
  const [tableSortBy, setTableSortBy] = useState<'created' | 'updated'>('updated')
  const [tableSortOrder, setTableSortOrder] = useState<'asc' | 'desc'>('desc')
  const [filters, setFilters] = useState<DocumentFiltersState>({
    search: '',
    type: null,
    status: null,
    sortBy: 'date',
    sortOrder: 'desc',
  })
  const deferredSearch = useDeferredValue(filters.search)
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const [deleteDialog, setDeleteDialog] = useState<{
    open: boolean
    source: SourceListResponse | null
  }>({ open: false, source: null })

  // Use paginated hook - use table sort params when in table view, otherwise use filter sort
  const {
    sources,
    loading,
    loadingMore,
    fetchMore,
  } = useSourcesPaginated({
    limit: 30,
    sortBy: view === 'table' ? tableSortBy : (filters.sortBy === 'date' ? 'created' : 'updated'),
    sortOrder: view === 'table' ? tableSortOrder : filters.sortOrder,
  })

  // Client-side filtering (search, type, status)
  const filteredDocuments = useMemo(() => {
    let filtered = [...sources]

    if (deferredSearch) {
      const searchLower = deferredSearch.toLowerCase()
      filtered = filtered.filter(
        (s) =>
          s.title?.toLowerCase().includes(searchLower) ||
          s.asset?.url?.toLowerCase().includes(searchLower)
      )
    }

    if (filters.type) {
      filtered = filtered.filter((s) => {
        if (filters.type === 'upload') return s.asset?.file_path
        if (filters.type === 'url') return s.asset?.url && !s.asset?.file_path
        return true
      })
    }

    if (filters.status) {
      filtered = filtered.filter((s) => {
        const status = s.status || (s.embedded ? 'completed' : 'pending')
        return status === filters.status
      })
    }

    // Client-side sorting for grid/list views (table sorts server-side)
    if (view !== 'table') {
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
    }

    return filtered
  }, [sources, deferredSearch, filters.type, filters.status, filters.sortBy, filters.sortOrder, view])

  // Selection handlers
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

  // Table sort toggle
  const handleToggleSort = useCallback((field: 'created' | 'updated') => {
    if (tableSortBy === field) {
      setTableSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'))
    } else {
      setTableSortBy(field)
      setTableSortOrder('desc')
    }
  }, [tableSortBy])

  // Delete from table view
  const handleDeleteSource = useCallback((source: SourceListResponse) => {
    setDeleteDialog({ open: true, source })
  }, [])

  const handleDeleteConfirm = useCallback(async () => {
    if (!deleteDialog.source) return
    try {
      await sourcesApi.delete(deleteDialog.source.id)
      toast.success('Document deleted successfully')
      setDeleteDialog({ open: false, source: null })
      fetchMore(true) // Refresh the list
    } catch {
      toast.error('Failed to delete document')
    }
  }, [deleteDialog.source, fetchMore])

  // Scroll to selected row for keyboard nav
  const scrollToSelectedRow = useCallback((index: number) => {
    const scrollContainer = scrollContainerRef.current
    if (!scrollContainer) return
    const rows = scrollContainer.querySelectorAll('tbody tr')
    const selectedRow = rows[index] as HTMLElement
    if (!selectedRow) return
    const containerRect = scrollContainer.getBoundingClientRect()
    const rowRect = selectedRow.getBoundingClientRect()
    if (rowRect.top < containerRect.top) {
      selectedRow.scrollIntoView({ behavior: 'smooth', block: 'start' })
    } else if (rowRect.bottom > containerRect.bottom) {
      selectedRow.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }, [])

  // Keyboard navigation for table view
  useEffect(() => {
    if (view !== 'table' || filteredDocuments.length === 0) return

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault()
          setSelectedIndex((prev) => {
            const newIndex = Math.min(prev + 1, filteredDocuments.length - 1)
            setTimeout(() => scrollToSelectedRow(newIndex), 0)
            return newIndex
          })
          break
        case 'ArrowUp':
          e.preventDefault()
          setSelectedIndex((prev) => {
            const newIndex = Math.max(prev - 1, 0)
            setTimeout(() => scrollToSelectedRow(newIndex), 0)
            return newIndex
          })
          break
        case 'Enter':
          e.preventDefault()
          if (filteredDocuments[selectedIndex]) {
            router.push(`/sources/${filteredDocuments[selectedIndex].id}`)
          }
          break
        case 'Home':
          e.preventDefault()
          setSelectedIndex(0)
          setTimeout(() => scrollToSelectedRow(0), 0)
          break
        case 'End':
          e.preventDefault()
          setSelectedIndex(filteredDocuments.length - 1)
          setTimeout(() => scrollToSelectedRow(filteredDocuments.length - 1), 0)
          break
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [filteredDocuments, selectedIndex, router, view, scrollToSelectedRow])

  // Infinite scroll
  useEffect(() => {
    const scrollContainer = scrollContainerRef.current
    if (!scrollContainer) return

    let scrollTimeout: NodeJS.Timeout | null = null
    const handleScroll = () => {
      if (scrollTimeout) clearTimeout(scrollTimeout)
      scrollTimeout = setTimeout(() => {
        if (!scrollContainerRef.current) return
        const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current
        const distanceFromBottom = scrollHeight - scrollTop - clientHeight
        if (distanceFromBottom < 200) {
          fetchMore(false)
        }
      }, 100)
    }

    scrollContainer.addEventListener('scroll', handleScroll)
    handleScroll()
    return () => {
      scrollContainer.removeEventListener('scroll', handleScroll)
      if (scrollTimeout) clearTimeout(scrollTimeout)
    }
  }, [fetchMore, sources.length])

  if (loading) {
    return <DocumentsSkeleton />
  }

  if (sources.length === 0) {
    return (
      <EmptyState
        icon={FileText}
        title="No Documents Yet"
        description="Upload your first SAMP document to start extracting ACM register data."
        action={
          <Button asChild>
            <Link href="/documents?action=upload">
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
        {view === 'table' && (
          <p className="text-xs text-muted-foreground hidden sm:block">
            Use arrow keys to navigate, Enter to open
          </p>
        )}
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
            fetchMore(true)
          }}
        />
      )}

      {/* Document Display */}
      <div ref={scrollContainerRef} className="flex-1 overflow-auto">
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
              onDeleteSource={handleDeleteSource}
              sortBy={tableSortBy}
              sortOrder={tableSortOrder}
              onToggleSort={handleToggleSort}
              selectedIndex={selectedIndex}
              onSelectIndex={setSelectedIndex}
              loadingMore={loadingMore}
            />
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog (for table view) */}
      <ConfirmDialog
        open={deleteDialog.open}
        onOpenChange={(open) => setDeleteDialog({ open, source: deleteDialog.source })}
        title="Delete Document"
        description={`Are you sure you want to delete "${deleteDialog.source?.title || 'this document'}"? This action cannot be undone.`}
        confirmText="Delete"
        confirmVariant="destructive"
        onConfirm={handleDeleteConfirm}
      />
    </div>
  )
}

