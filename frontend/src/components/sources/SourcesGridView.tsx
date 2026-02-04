'use client';

import { BentoGrid } from '@/components/ui/bento-grid';
import {
  BentoCard,
  BentoCardHeader,
  BentoCardTitle,
  BentoCardContent,
  BentoCardFooter,
} from '@/components/ui/bento-card';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  MoreHorizontal,
  Eye,
  Trash2,
  Link as LinkIcon,
  Upload,
  AlignLeft,
} from 'lucide-react';
import Link from 'next/link';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { SourceListResponse } from '@/lib/types/api';
import { cn } from '@/lib/utils';
import { formatCreatedDate } from '@/lib/utils/format-date';

interface SourcesGridViewProps {
  sources: SourceListResponse[];
  selectedIds: Set<string>;
  onToggleSelection: (id: string) => void;
  onDeleteSource: (source: SourceListResponse) => void;
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

export function SourcesGridView({
  sources,
  selectedIds,
  onToggleSelection,
  onDeleteSource,
  loadingMore,
}: SourcesGridViewProps) {
  return (
    <div className="space-y-4">
      <BentoGrid columns={3} gap="md">
        {sources.map((source) => (
          <SourceCard
            key={source.id}
            source={source}
            isSelected={selectedIds.has(source.id)}
            onToggleSelection={() => onToggleSelection(source.id)}
            onDelete={() => onDeleteSource(source)}
          />
        ))}
      </BentoGrid>
      {loadingMore && (
        <div className="flex items-center justify-center py-4">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary" />
          <span className="ml-2 text-muted-foreground">Loading more sources...</span>
        </div>
      )}
    </div>
  );
}

function SourceCard({
  source,
  isSelected,
  onToggleSelection,
  onDelete,
}: {
  source: SourceListResponse;
  isSelected: boolean;
  onToggleSelection: () => void;
  onDelete: () => void;
}) {
  const formattedDate = source.created ? formatCreatedDate(source.created) : '';

  return (
    <Link href={`/sources/${source.id}`} className="block group">
      <BentoCard
        size="sm"
        interactive
        className={cn(isSelected && 'ring-2 ring-primary')}
      >
        <BentoCardHeader>
          <div className="flex items-center gap-2">
            <Checkbox
              checked={isSelected}
              onCheckedChange={onToggleSelection}
              onClick={(e) => e.stopPropagation()}
              aria-label={`Select ${source.title || 'Untitled'}`}
            />
            <div className="flex items-center gap-1.5 text-muted-foreground">
              {getSourceIcon(source)}
              <Badge variant="secondary" className="text-xs">
                {getSourceType(source)}
              </Badge>
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                aria-label="Source actions"
                onClick={(e) => e.preventDefault()}
              >
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
              <DropdownMenuItem
                className="text-destructive"
                onClick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                  onDelete();
                }}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </BentoCardHeader>

        <BentoCardContent>
          <BentoCardTitle className="truncate mb-2 group-hover:text-primary transition-colors">
            {source.title || 'Untitled'}
          </BentoCardTitle>
          {formattedDate && (
            <p className="text-sm text-muted-foreground">{formattedDate}</p>
          )}
          {source.asset?.url && (
            <p className="text-xs text-muted-foreground truncate mt-1">
              {source.asset.url}
            </p>
          )}
        </BentoCardContent>

        <BentoCardFooter>
          <div className="flex items-center gap-2">
            {source.embedded && (
              <Badge variant="outline" className="text-xs">
                Embedded
              </Badge>
            )}
            {source.insights_count > 0 && (
              <Badge variant="secondary" className="text-xs">
                {source.insights_count} insights
              </Badge>
            )}
          </div>
        </BentoCardFooter>
      </BentoCard>
    </Link>
  );
}
