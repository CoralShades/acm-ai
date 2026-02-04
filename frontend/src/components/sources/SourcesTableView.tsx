'use client';

import { useRef, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { SourceListResponse } from '@/lib/types/api';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { cn } from '@/lib/utils';
import { formatCreatedDate } from '@/lib/utils/format-date';
import {
  Link as LinkIcon,
  Upload,
  AlignLeft,
  Trash2,
  ArrowUpDown,
} from 'lucide-react';

interface SourcesTableViewProps {
  sources: SourceListResponse[];
  selectedIds: Set<string>;
  onToggleSelection: (id: string) => void;
  onDeleteSource: (source: SourceListResponse) => void;
  sortBy: 'created' | 'updated';
  sortOrder: 'asc' | 'desc';
  onToggleSort: (field: 'created' | 'updated') => void;
  selectedIndex: number;
  onSelectIndex: (index: number) => void;
  loadingMore?: boolean;
}

function getSourceIcon(source: SourceListResponse) {
  if (source.asset?.url) return <LinkIcon className="h-4 w-4" />;
  if (source.asset?.file_path) return <Upload className="h-4 w-4" />;
  return <AlignLeft className="h-4 w-4" />;
}

function getSourceType(source: SourceListResponse) {
  if (source.asset?.url) return 'Link';
  if (source.asset?.file_path) return 'File';
  return 'Text';
}

export function SourcesTableView({
  sources,
  selectedIds,
  onToggleSelection,
  onDeleteSource,
  sortBy,
  sortOrder,
  onToggleSort,
  selectedIndex,
  onSelectIndex,
  loadingMore,
}: SourcesTableViewProps) {
  const router = useRouter();
  const tableRef = useRef<HTMLTableElement>(null);

  useEffect(() => {
    if (sources.length > 0 && tableRef.current) {
      tableRef.current.focus();
    }
  }, [sources]);

  const handleRowClick = useCallback(
    (index: number, sourceId: string) => {
      onSelectIndex(index);
      router.push(`/sources/${sourceId}`);
    },
    [router, onSelectIndex]
  );

  const handleDeleteClick = useCallback(
    (e: React.MouseEvent, source: SourceListResponse) => {
      e.stopPropagation();
      onDeleteSource(source);
    },
    [onDeleteSource]
  );

  return (
    <table
      ref={tableRef}
      tabIndex={0}
      className="w-full min-w-[800px] outline-none table-fixed"
    >
      <colgroup>
        <col className="w-[40px]" />
        <col className="w-[100px]" />
        <col className="w-auto" />
        <col className="w-[140px]" />
        <col className="w-[100px]" />
        <col className="w-[100px]" />
        <col className="w-[80px]" />
      </colgroup>
      <thead className="sticky top-0 bg-background z-10">
        <tr className="border-b bg-muted/50">
          <th className="h-12 px-2 text-center align-middle">
            <Checkbox
              checked={
                sources.length > 0 && selectedIds.size === sources.length
              }
              onCheckedChange={(checked) => {
                // Select all: add all sources not already selected
                // Deselect all: remove all sources that are selected
                sources.forEach((s) => {
                  const isSelected = selectedIds.has(s.id);
                  if (checked && !isSelected) {
                    onToggleSelection(s.id);
                  } else if (!checked && isSelected) {
                    onToggleSelection(s.id);
                  }
                });
              }}
              aria-label="Select all"
            />
          </th>
          <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
            Type
          </th>
          <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground">
            Title
          </th>
          <th className="h-12 px-4 text-left align-middle font-medium text-muted-foreground hidden sm:table-cell">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onToggleSort('created')}
              className="h-8 px-2 hover:bg-muted"
            >
              Created
              <ArrowUpDown
                className={cn(
                  'ml-2 h-3 w-3',
                  sortBy === 'created' ? 'opacity-100' : 'opacity-30'
                )}
              />
              {sortBy === 'created' && (
                <span className="ml-1 text-xs">
                  {sortOrder === 'asc' ? '\u2191' : '\u2193'}
                </span>
              )}
            </Button>
          </th>
          <th className="h-12 px-4 text-center align-middle font-medium text-muted-foreground hidden md:table-cell">
            Insights
          </th>
          <th className="h-12 px-4 text-center align-middle font-medium text-muted-foreground hidden lg:table-cell">
            Embedded
          </th>
          <th className="h-12 px-4 text-right align-middle font-medium text-muted-foreground">
            Actions
          </th>
        </tr>
      </thead>
      <tbody>
        {sources.map((source, index) => (
          <tr
            key={source.id}
            onClick={() => handleRowClick(index, source.id)}
            onMouseEnter={() => onSelectIndex(index)}
            className={cn(
              'border-b transition-colors cursor-pointer',
              selectedIndex === index ? 'bg-accent' : 'hover:bg-muted/50'
            )}
          >
            <td className="h-12 px-2 text-center">
              <Checkbox
                checked={selectedIds.has(source.id)}
                onCheckedChange={() => onToggleSelection(source.id)}
                onClick={(e) => e.stopPropagation()}
                aria-label={`Select ${source.title || 'Untitled'}`}
              />
            </td>
            <td className="h-12 px-4">
              <div className="flex items-center gap-2">
                {getSourceIcon(source)}
                <Badge variant="secondary" className="text-xs">
                  {getSourceType(source)}
                </Badge>
              </div>
            </td>
            <td className="h-12 px-4">
              <div className="flex flex-col overflow-hidden">
                <span className="font-medium truncate">
                  {source.title || 'Untitled Source'}
                </span>
                {source.asset?.url && (
                  <span className="text-xs text-muted-foreground truncate">
                    {source.asset.url}
                  </span>
                )}
              </div>
            </td>
            <td className="h-12 px-4 text-muted-foreground text-sm hidden sm:table-cell">
              {source.created ? formatCreatedDate(source.created) : ''}
            </td>
            <td className="h-12 px-4 text-center hidden md:table-cell">
              <span className="text-sm font-medium">
                {source.insights_count || 0}
              </span>
            </td>
            <td className="h-12 px-4 text-center hidden lg:table-cell">
              <Badge
                variant={source.embedded ? 'default' : 'secondary'}
                className="text-xs"
              >
                {source.embedded ? 'Yes' : 'No'}
              </Badge>
            </td>
            <td className="h-12 px-4 text-right">
              <Button
                variant="ghost"
                size="icon"
                onClick={(e) => handleDeleteClick(e, source)}
                className="text-destructive hover:text-destructive"
                aria-label={`Delete ${source.title || 'Untitled'}`}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </td>
          </tr>
        ))}
        {loadingMore && (
          <tr>
            <td colSpan={7} className="h-16 text-center">
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary" />
                <span className="ml-2 text-muted-foreground">
                  Loading more sources...
                </span>
              </div>
            </td>
          </tr>
        )}
      </tbody>
    </table>
  );
}
