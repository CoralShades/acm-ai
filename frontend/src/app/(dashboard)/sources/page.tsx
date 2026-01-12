'use client';

import { useState, useEffect, useCallback, useRef, useMemo, useDeferredValue } from 'react';
import { useRouter } from 'next/navigation';
import { sourcesApi } from '@/lib/api/sources';
import { SourceListResponse } from '@/lib/types/api';
import { EmptyState } from '@/components/common/EmptyState';
import { AppShell } from '@/components/layout/AppShell';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import {
  FileText,
  Upload,
  LayoutGrid,
  List,
  Search,
  Plus,
  Trash2,
  X,
} from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import { useLocalStorage } from '@/lib/hooks/use-local-storage';
import { SourcesGridView } from '@/components/sources/SourcesGridView';
import { SourcesTableView } from '@/components/sources/SourcesTableView';
import { Skeleton } from '@/components/ui/skeleton';

export default function SourcesPage() {
  const [sources, setSources] = useState<SourceListResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [sortBy, setSortBy] = useState<'created' | 'updated'>('updated');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [view, setView] = useLocalStorage<'grid' | 'list'>(
    'sources-view',
    'list'
  );
  const [search, setSearch] = useState('');
  const deferredSearch = useDeferredValue(search);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [deleteDialog, setDeleteDialog] = useState<{
    open: boolean;
    source: SourceListResponse | null;
    isBulk?: boolean;
  }>({
    open: false,
    source: null,
    isBulk: false,
  });
  const router = useRouter();
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const offsetRef = useRef(0);
  const loadingMoreRef = useRef(false);
  const hasMoreRef = useRef(true);
  const PAGE_SIZE = 30;

  const fetchSources = useCallback(
    async (reset = false) => {
      try {
        // Check flags before proceeding
        if (!reset && (loadingMoreRef.current || !hasMoreRef.current)) {
          return;
        }

        if (reset) {
          setLoading(true);
          offsetRef.current = 0;
          setSources([]);
          hasMoreRef.current = true;
        } else {
          loadingMoreRef.current = true;
          setLoadingMore(true);
        }

        const data = await sourcesApi.list({
          limit: PAGE_SIZE,
          offset: offsetRef.current,
          sort_by: sortBy,
          sort_order: sortOrder,
        });

        if (reset) {
          setSources(data);
        } else {
          setSources((prev) => [...prev, ...data]);
        }

        // Check if we have more data
        const hasMoreData = data.length === PAGE_SIZE;
        hasMoreRef.current = hasMoreData;
        offsetRef.current += data.length;
      } catch (err) {
        console.error('Failed to fetch sources:', err);
        setError('Failed to load sources');
        toast.error('Failed to load sources');
      } finally {
        setLoading(false);
        setLoadingMore(false);
        loadingMoreRef.current = false;
      }
    },
    [sortBy, sortOrder]
  );

  // Initial load and when sort changes
  useEffect(() => {
    fetchSources(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sortBy, sortOrder]);

  // Filter sources by search (memoized with deferred value for performance)
  const filteredSources = useMemo(
    () =>
      sources?.filter(
        (source) =>
          source.title?.toLowerCase().includes(deferredSearch.toLowerCase()) ||
          source.asset?.url?.toLowerCase().includes(deferredSearch.toLowerCase())
      ) || [],
    [sources, deferredSearch]
  );

  // Keyboard navigation for list view
  useEffect(() => {
    if (view !== 'list' || filteredSources.length === 0) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex((prev) => {
            const newIndex = Math.min(prev + 1, filteredSources.length - 1);
            setTimeout(() => scrollToSelectedRow(newIndex), 0);
            return newIndex;
          });
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex((prev) => {
            const newIndex = Math.max(prev - 1, 0);
            setTimeout(() => scrollToSelectedRow(newIndex), 0);
            return newIndex;
          });
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredSources[selectedIndex]) {
            router.push(`/sources/${filteredSources[selectedIndex].id}`);
          }
          break;
        case 'Home':
          e.preventDefault();
          setSelectedIndex(0);
          setTimeout(() => scrollToSelectedRow(0), 0);
          break;
        case 'End':
          e.preventDefault();
          const lastIndex = filteredSources.length - 1;
          setSelectedIndex(lastIndex);
          setTimeout(() => scrollToSelectedRow(lastIndex), 0);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [filteredSources, selectedIndex, router, view]);

  const scrollToSelectedRow = (index: number) => {
    const scrollContainer = scrollContainerRef.current;
    if (!scrollContainer) return;

    const rows = scrollContainer.querySelectorAll('tbody tr');
    const selectedRow = rows[index] as HTMLElement;
    if (!selectedRow) return;

    const containerRect = scrollContainer.getBoundingClientRect();
    const rowRect = selectedRow.getBoundingClientRect();

    if (rowRect.top < containerRect.top) {
      selectedRow.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else if (rowRect.bottom > containerRect.bottom) {
      selectedRow.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  };

  // Infinite scroll
  useEffect(() => {
    const scrollContainer = scrollContainerRef.current;
    if (!scrollContainer) return;

    let scrollTimeout: NodeJS.Timeout | null = null;

    const handleScroll = () => {
      if (scrollTimeout) {
        clearTimeout(scrollTimeout);
      }

      scrollTimeout = setTimeout(() => {
        if (!scrollContainerRef.current) return;

        const { scrollTop, scrollHeight, clientHeight } =
          scrollContainerRef.current;
        const distanceFromBottom = scrollHeight - scrollTop - clientHeight;

        if (
          distanceFromBottom < 200 &&
          !loadingMoreRef.current &&
          hasMoreRef.current
        ) {
          fetchSources(false);
        }
      }, 100);
    };

    scrollContainer.addEventListener('scroll', handleScroll);
    handleScroll();

    return () => {
      scrollContainer.removeEventListener('scroll', handleScroll);
      if (scrollTimeout) {
        clearTimeout(scrollTimeout);
      }
    };
  }, [fetchSources, sources.length]);

  const toggleSort = (field: 'created' | 'updated') => {
    if (sortBy === field) {
      setSortOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const toggleSelection = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const clearSelection = () => {
    setSelectedIds(new Set());
  };

  const handleDeleteSource = (source: SourceListResponse) => {
    setDeleteDialog({ open: true, source, isBulk: false });
  };

  const handleBulkDelete = () => {
    setDeleteDialog({ open: true, source: null, isBulk: true });
  };

  const handleDeleteConfirm = async () => {
    try {
      if (deleteDialog.isBulk) {
        // Delete all selected sources with partial failure handling
        const deletePromises = Array.from(selectedIds).map((id) =>
          sourcesApi.delete(id).then(() => ({ id, success: true })).catch(() => ({ id, success: false }))
        );
        const results = await Promise.allSettled(deletePromises);
        const successful = results
          .filter((r): r is PromiseFulfilledResult<{ id: string; success: boolean }> =>
            r.status === 'fulfilled' && r.value.success
          )
          .map((r) => r.value.id);
        const failedCount = selectedIds.size - successful.length;

        if (failedCount === 0) {
          toast.success(`${selectedIds.size} sources deleted successfully`);
        } else if (successful.length > 0) {
          toast.warning(`${successful.length} sources deleted, ${failedCount} failed`);
        } else {
          toast.error('Failed to delete sources');
        }

        // Remove only successfully deleted sources
        setSources((prev) => prev.filter((s) => !successful.includes(s.id)));
        clearSelection();
      } else if (deleteDialog.source) {
        await sourcesApi.delete(deleteDialog.source.id);
        toast.success('Source deleted successfully');
        setSources((prev) =>
          prev.filter((s) => s.id !== deleteDialog.source?.id)
        );
        // Also remove from selection if selected
        if (selectedIds.has(deleteDialog.source.id)) {
          toggleSelection(deleteDialog.source.id);
        }
      }
      setDeleteDialog({ open: false, source: null, isBulk: false });
    } catch (err) {
      console.error('Failed to delete source:', err);
      toast.error('Failed to delete source');
    }
  };

  if (loading) {
    return (
      <AppShell>
        <div className="flex flex-col h-full w-full max-w-none px-6 py-6">
          <div className="mb-6 flex-shrink-0">
            <Skeleton className="h-9 w-48 mb-2" />
            <Skeleton className="h-5 w-72" />
          </div>
          <div className="flex items-center gap-4 mb-6">
            <Skeleton className="h-10 w-64" />
            <div className="flex-1" />
            <Skeleton className="h-10 w-24" />
          </div>
          <SourcesLoadingSkeleton view={view} />
        </div>
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell>
        <div className="flex h-full items-center justify-center">
          <div className="text-center">
            <p className="text-red-500 mb-4">{error}</p>
            <Button onClick={() => fetchSources(true)}>Retry</Button>
          </div>
        </div>
      </AppShell>
    );
  }

  if (sources.length === 0 && !search) {
    return (
      <AppShell>
        <EmptyState
          icon={FileText}
          title="No Documents Yet"
          description="Upload your first SAMP document to start extracting ACM register data with AI-powered analysis."
          action={
            <Button asChild>
              <Link href="/sources?action=upload">
                <Upload className="w-4 h-4 mr-2" />
                Upload Document
              </Link>
            </Button>
          }
        />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="flex flex-col h-full w-full max-w-none px-6 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6 flex-shrink-0">
          <div>
            <h1 className="text-3xl font-bold">Sources</h1>
            <p className="text-muted-foreground">
              {view === 'list'
                ? 'Use arrow keys to navigate and Enter to open'
                : 'Click on a card to view details'}
            </p>
          </div>
          <Button asChild>
            <Link href="/sources?action=upload">
              <Plus className="w-4 h-4 mr-2" />
              Upload
            </Link>
          </Button>
        </div>

        {/* Toolbar */}
        <div className="flex items-center gap-4 mb-6 flex-shrink-0">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search sources..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
            {search && (
              <Button
                variant="ghost"
                size="sm"
                className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
                onClick={() => setSearch('')}
                aria-label="Clear search"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>

          {/* Selection actions */}
          {selectedIds.size > 0 && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">
                {selectedIds.size} selected
              </span>
              <Button variant="outline" size="sm" onClick={clearSelection}>
                Clear
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={handleBulkDelete}
              >
                <Trash2 className="w-4 h-4 mr-1" />
                Delete
              </Button>
            </div>
          )}

          {/* View toggle */}
          <div className="flex items-center border rounded-lg p-1">
            <Button
              variant={view === 'grid' ? 'secondary' : 'ghost'}
              size="sm"
              onClick={() => setView('grid')}
              className="px-2"
              aria-label="Grid view"
            >
              <LayoutGrid className="w-4 h-4" />
            </Button>
            <Button
              variant={view === 'list' ? 'secondary' : 'ghost'}
              size="sm"
              onClick={() => setView('list')}
              className="px-2"
              aria-label="List view"
            >
              <List className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Content */}
        <div ref={scrollContainerRef} className="flex-1 overflow-auto">
          {filteredSources.length === 0 ? (
            <SourcesEmptyState hasSearch={!!search} />
          ) : view === 'grid' ? (
            <SourcesGridView
              sources={filteredSources}
              selectedIds={selectedIds}
              onToggleSelection={toggleSelection}
              onDeleteSource={handleDeleteSource}
              loadingMore={loadingMore}
            />
          ) : (
            <div className="rounded-md border">
              <SourcesTableView
                sources={filteredSources}
                selectedIds={selectedIds}
                onToggleSelection={toggleSelection}
                onDeleteSource={handleDeleteSource}
                sortBy={sortBy}
                sortOrder={sortOrder}
                onToggleSort={toggleSort}
                selectedIndex={selectedIndex}
                onSelectIndex={setSelectedIndex}
                loadingMore={loadingMore}
              />
            </div>
          )}
        </div>
      </div>

      <ConfirmDialog
        open={deleteDialog.open}
        onOpenChange={(open) =>
          setDeleteDialog({ open, source: deleteDialog.source })
        }
        title={deleteDialog.isBulk ? 'Delete Sources' : 'Delete Source'}
        description={
          deleteDialog.isBulk
            ? `Are you sure you want to delete ${selectedIds.size} selected sources? This action cannot be undone.`
            : `Are you sure you want to delete "${deleteDialog.source?.title || 'this source'}"? This action cannot be undone.`
        }
        confirmText="Delete"
        confirmVariant="destructive"
        onConfirm={handleDeleteConfirm}
      />
    </AppShell>
  );
}

function SourcesLoadingSkeleton({ view }: { view: 'grid' | 'list' }) {
  if (view === 'grid') {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="rounded-lg border p-4 space-y-3">
            <div className="flex items-center justify-between">
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-8 w-8 rounded" />
            </div>
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-6 w-20" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <div className="p-4 space-y-3">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="flex items-center gap-4">
            <Skeleton className="h-5 w-5" />
            <Skeleton className="h-6 w-20" />
            <Skeleton className="h-5 flex-1" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-12" />
            <Skeleton className="h-6 w-12" />
            <Skeleton className="h-8 w-8" />
          </div>
        ))}
      </div>
    </div>
  );
}

function SourcesEmptyState({ hasSearch }: { hasSearch: boolean }) {
  return (
    <div className="text-center py-12">
      <Upload className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
      <h2 className="text-xl font-semibold mb-2">
        {hasSearch ? 'No sources found' : 'No sources yet'}
      </h2>
      <p className="text-muted-foreground mb-4">
        {hasSearch
          ? 'Try adjusting your search'
          : 'Upload your first document to get started'}
      </p>
      {!hasSearch && (
        <Button asChild>
          <Link href="/sources?action=upload">
            <Upload className="w-4 h-4 mr-2" />
            Upload Document
          </Link>
        </Button>
      )}
    </div>
  );
}
