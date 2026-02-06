'use client'

import { SourceListResponse } from '@/lib/types/api'
import { DocumentCard } from './DocumentCard'
import { Checkbox } from '@/components/ui/checkbox'

interface DocumentGridProps {
  documents: SourceListResponse[]
  selectedIds: Set<string>
  onSelect: (id: string) => void
  onSelectAll: () => void
  onRefetch: () => void
}

export function DocumentGrid({
  documents,
  selectedIds,
  onSelect,
  onSelectAll,
  onRefetch,
}: DocumentGridProps) {
  return (
    <div className="space-y-3">
      {/* Select All */}
      <div className="flex items-center gap-2 px-1">
        <Checkbox
          checked={
            selectedIds.size === documents.length && documents.length > 0
          }
          onCheckedChange={onSelectAll}
        />
        <span className="text-sm text-muted-foreground">
          {selectedIds.size === documents.length && documents.length > 0
            ? 'Deselect all'
            : 'Select all'}
        </span>
        <span className="text-sm text-muted-foreground ml-auto">
          {documents.length} document{documents.length !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {documents.map((doc) => (
          <DocumentCard
            key={doc.id}
            document={doc}
            isSelected={selectedIds.has(doc.id)}
            onSelect={() => onSelect(doc.id)}
            onRefetch={onRefetch}
          />
        ))}
      </div>
    </div>
  )
}
