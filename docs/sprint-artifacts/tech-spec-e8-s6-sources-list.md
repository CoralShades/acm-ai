# Tech Spec: E8-S6 - Redesign Sources List Page

> **Story:** E8-S6
> **Epic:** UI Refresh (Bento Grid Design)
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Redesign the sources list page with a bento card grid view option alongside the existing table view.

---

## User Story

**As a** user
**I want** the sources page to use bento layout
**So that** it's easier to scan and navigate

---

## Acceptance Criteria

- [ ] Grid view option (bento cards)
- [ ] List view option (current table)
- [ ] View toggle persisted
- [ ] Source cards show: title, type, date, ACM status
- [ ] Quick actions on hover
- [ ] Batch selection mode

---

## Technical Design

### 1. Sources Page with View Toggle

Update `frontend/src/app/(dashboard)/sources/page.tsx`:

```tsx
'use client';

import { useState } from 'react';
import { useSources } from '@/hooks/use-sources';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { LayoutGrid, List, Search, Upload, Plus } from 'lucide-react';
import { cn } from '@/lib/utils';
import Link from 'next/link';
import { SourcesGridView } from '@/components/sources/SourcesGridView';
import { SourcesTableView } from '@/components/sources/SourcesTableView';
import { useLocalStorage } from '@/hooks/use-local-storage';

export default function SourcesPage() {
  const { data: sources, isLoading } = useSources();
  const [view, setView] = useLocalStorage<'grid' | 'list'>('sources-view', 'grid');
  const [search, setSearch] = useState('');
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Filter sources by search
  const filteredSources = sources?.filter((source) =>
    source.title?.toLowerCase().includes(search.toLowerCase())
  ) || [];

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

  const selectAll = () => {
    setSelectedIds(new Set(filteredSources.map((s) => s.id)));
  };

  const clearSelection = () => {
    setSelectedIds(new Set());
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">Sources</h1>
          <p className="text-muted-foreground">
            Manage your uploaded documents
          </p>
        </div>
        <Button asChild>
          <Link href="/sources/new">
            <Plus className="w-4 h-4 mr-2" />
            Upload
          </Link>
        </Button>
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-4 mb-6">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search sources..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
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
            <Button variant="destructive" size="sm">
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
          >
            <LayoutGrid className="w-4 h-4" />
          </Button>
          <Button
            variant={view === 'list' ? 'secondary' : 'ghost'}
            size="sm"
            onClick={() => setView('list')}
            className="px-2"
          >
            <List className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Content */}
      {isLoading ? (
        <SourcesLoadingSkeleton view={view} />
      ) : filteredSources.length === 0 ? (
        <SourcesEmptyState hasSearch={!!search} />
      ) : view === 'grid' ? (
        <SourcesGridView
          sources={filteredSources}
          selectedIds={selectedIds}
          onToggleSelection={toggleSelection}
        />
      ) : (
        <SourcesTableView
          sources={filteredSources}
          selectedIds={selectedIds}
          onToggleSelection={toggleSelection}
        />
      )}
    </div>
  );
}

function SourcesLoadingSkeleton({ view }: { view: 'grid' | 'list' }) {
  // Loading skeleton based on view
  return <div>Loading...</div>;
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
          <Link href="/sources/new">
            <Upload className="w-4 h-4 mr-2" />
            Upload Document
          </Link>
        </Button>
      )}
    </div>
  );
}
```

### 2. Grid View Component

Create `frontend/src/components/sources/SourcesGridView.tsx`:

```tsx
'use client';

import { BentoGrid } from '@/components/ui/bento-grid';
import { BentoCard, BentoCardHeader, BentoCardTitle, BentoCardContent, BentoCardFooter } from '@/components/ui/bento-card';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { formatDistanceToNow } from 'date-fns';
import { FileText, MoreHorizontal, Eye, Trash2, Shield } from 'lucide-react';
import Link from 'next/link';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface Source {
  id: string;
  title: string;
  created_at: string;
  has_acm_data?: boolean;
  acm_count?: number;
}

interface SourcesGridViewProps {
  sources: Source[];
  selectedIds: Set<string>;
  onToggleSelection: (id: string) => void;
}

export function SourcesGridView({
  sources,
  selectedIds,
  onToggleSelection,
}: SourcesGridViewProps) {
  return (
    <BentoGrid columns={3} gap="md">
      {sources.map((source) => (
        <SourceCard
          key={source.id}
          source={source}
          isSelected={selectedIds.has(source.id)}
          onToggleSelection={() => onToggleSelection(source.id)}
        />
      ))}
    </BentoGrid>
  );
}

function SourceCard({
  source,
  isSelected,
  onToggleSelection,
}: {
  source: Source;
  isSelected: boolean;
  onToggleSelection: () => void;
}) {
  return (
    <BentoCard
      size="sm"
      interactive
      className={isSelected ? 'ring-2 ring-primary' : ''}
    >
      <BentoCardHeader>
        <div className="flex items-center gap-2">
          <Checkbox
            checked={isSelected}
            onCheckedChange={onToggleSelection}
            onClick={(e) => e.stopPropagation()}
          />
          <FileText className="w-5 h-5 text-muted-foreground" />
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <MoreHorizontal className="w-4 h-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem asChild>
              <Link href={`/sources/${source.id}`}>
                <Eye className="w-4 h-4 mr-2" />
                View
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem className="text-destructive">
              <Trash2 className="w-4 h-4 mr-2" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </BentoCardHeader>

      <BentoCardContent>
        <Link href={`/sources/${source.id}`} className="block">
          <BentoCardTitle className="truncate mb-2">
            {source.title || 'Untitled'}
          </BentoCardTitle>
          <p className="text-sm text-muted-foreground">
            {formatDistanceToNow(new Date(source.created_at), { addSuffix: true })}
          </p>
        </Link>
      </BentoCardContent>

      <BentoCardFooter>
        {source.has_acm_data && (
          <Badge variant="secondary" className="gap-1">
            <Shield className="w-3 h-3" />
            {source.acm_count} ACM
          </Badge>
        )}
      </BentoCardFooter>
    </BentoCard>
  );
}
```

### 3. Local Storage Hook

Create `frontend/src/hooks/use-local-storage.ts`:

```typescript
import { useState, useEffect } from 'react';

export function useLocalStorage<T>(key: string, initialValue: T): [T, (value: T) => void] {
  const [storedValue, setStoredValue] = useState<T>(initialValue);

  useEffect(() => {
    try {
      const item = window.localStorage.getItem(key);
      if (item) {
        setStoredValue(JSON.parse(item));
      }
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
    }
  }, [key]);

  const setValue = (value: T) => {
    try {
      setStoredValue(value);
      window.localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error);
    }
  };

  return [storedValue, setValue];
}
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/app/(dashboard)/sources/page.tsx` | Redesign with view toggle |
| `frontend/src/components/sources/SourcesGridView.tsx` | New component |
| `frontend/src/components/sources/SourcesTableView.tsx` | Update existing |
| `frontend/src/hooks/use-local-storage.ts` | New hook |

---

## Dependencies

- E8-S3: BentoCard component
- E8-S4: BentoGrid component

---

## Testing

1. Toggle between grid and list views
2. Verify view preference persists on reload
3. Test search filtering
4. Test selection checkboxes
5. Verify ACM badge shows for ACM sources
6. Test dropdown menu actions
7. Test responsive layout

---

## Estimated Complexity

**Medium** - View toggle with state persistence

---
