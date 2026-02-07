'use client'

import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Search, X } from 'lucide-react'
import { Button } from '@/components/ui/button'

export interface DocumentFiltersState {
  search: string
  type: string | null
  status: string | null
  sortBy: 'name' | 'date' | 'records'
  sortOrder: 'asc' | 'desc'
}

interface DocumentFiltersProps {
  filters: DocumentFiltersState
  onChange: (filters: DocumentFiltersState) => void
}

export function DocumentFilters({ filters, onChange }: DocumentFiltersProps) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="Search documents..."
          value={filters.search}
          onChange={(e) => onChange({ ...filters, search: e.target.value })}
          className="pl-9 w-[250px]"
        />
        {filters.search && (
          <Button
            variant="ghost"
            size="sm"
            className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
            onClick={() => onChange({ ...filters, search: '' })}
            aria-label="Clear search"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Document Type */}
      <Select
        value={filters.type || 'all'}
        onValueChange={(v) =>
          onChange({ ...filters, type: v === 'all' ? null : v })
        }
      >
        <SelectTrigger className="w-[150px]">
          <SelectValue placeholder="All Types" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Types</SelectItem>
          <SelectItem value="upload">Uploaded Files</SelectItem>
          <SelectItem value="url">URLs / Links</SelectItem>
        </SelectContent>
      </Select>

      {/* Processing Status */}
      <Select
        value={filters.status || 'all'}
        onValueChange={(v) =>
          onChange({ ...filters, status: v === 'all' ? null : v })
        }
      >
        <SelectTrigger className="w-[150px]">
          <SelectValue placeholder="All Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Status</SelectItem>
          <SelectItem value="completed">Completed</SelectItem>
          <SelectItem value="running">Processing</SelectItem>
          <SelectItem value="failed">Failed</SelectItem>
          <SelectItem value="pending">Pending</SelectItem>
        </SelectContent>
      </Select>

      {/* Sort By */}
      <Select
        value={`${filters.sortBy}-${filters.sortOrder}`}
        onValueChange={(v) => {
          const [sortBy, sortOrder] = v.split('-') as [
            DocumentFiltersState['sortBy'],
            DocumentFiltersState['sortOrder'],
          ]
          onChange({ ...filters, sortBy, sortOrder })
        }}
      >
        <SelectTrigger className="w-[170px]">
          <SelectValue placeholder="Sort by" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="date-desc">Newest First</SelectItem>
          <SelectItem value="date-asc">Oldest First</SelectItem>
          <SelectItem value="name-asc">Name (A-Z)</SelectItem>
          <SelectItem value="name-desc">Name (Z-A)</SelectItem>
          <SelectItem value="records-desc">Most Insights</SelectItem>
          <SelectItem value="records-asc">Fewest Insights</SelectItem>
        </SelectContent>
      </Select>
    </div>
  )
}
