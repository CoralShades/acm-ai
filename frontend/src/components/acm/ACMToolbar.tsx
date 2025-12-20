'use client'

import { useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ChevronDown, ChevronRight, Download, Plus, RefreshCw, Search, Sparkles, X } from 'lucide-react'

interface ACMToolbarProps {
  onAddNew: () => void
  onExtract: () => void
  onExport: () => void
  onRefresh: () => void
  onExpandAll?: () => void
  onCollapseAll?: () => void
  riskFilter?: string
  onRiskFilterChange: (value: string | undefined) => void
  isExtracting?: boolean
  isExporting?: boolean
  disabled?: boolean
  showGroupingControls?: boolean
  // Search functionality
  searchText?: string
  onSearchChange?: (value: string) => void
  // Result count display
  visibleCount?: number
  totalCount?: number
}

export function ACMToolbar({
  onAddNew,
  onExtract,
  onExport,
  onRefresh,
  onExpandAll,
  onCollapseAll,
  riskFilter,
  onRiskFilterChange,
  isExtracting = false,
  isExporting = false,
  disabled = false,
  showGroupingControls = true,
  searchText = '',
  onSearchChange,
  visibleCount,
  totalCount,
}: ACMToolbarProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)

  // Keyboard shortcut: Ctrl/Cmd+F to focus search
  // Only intercept when focus is within this component or no specific element is focused
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'f') {
        // Check if focus is within our container or on body (no specific focus)
        const activeElement = document.activeElement
        const isWithinContainer = containerRef.current?.contains(activeElement)
        const isOnBody = activeElement === document.body

        if (isWithinContainer || isOnBody) {
          e.preventDefault()
          searchInputRef.current?.focus()
        }
        // Otherwise, let browser handle Ctrl+F for page search
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  const handleClearSearch = () => {
    onSearchChange?.('')
    searchInputRef.current?.focus()
  }

  const showResultCount = totalCount !== undefined && totalCount > 0

  return (
    <div ref={containerRef} className="flex flex-col gap-3">
      {/* Search Bar Row */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            ref={searchInputRef}
            type="text"
            placeholder="Search all columns... (Ctrl+F)"
            value={searchText}
            onChange={(e) => onSearchChange?.(e.target.value)}
            className="pl-9 pr-9"
            disabled={disabled}
          />
          {searchText && (
            <Button
              variant="ghost"
              size="sm"
              className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
              onClick={handleClearSearch}
              aria-label="Clear search"
            >
              <X className="h-4 w-4" />
              <span className="sr-only">Clear search</span>
            </Button>
          )}
        </div>

        {/* Result Count */}
        {showResultCount && (
          <span className="text-sm text-muted-foreground whitespace-nowrap">
            Showing {visibleCount ?? totalCount} of {totalCount} records
          </span>
        )}
      </div>

      {/* Controls Row */}
      <div className="flex flex-wrap items-center gap-2 justify-between">
        <div className="flex items-center gap-2">
          {/* Risk Status Filter */}
          <Select
            value={riskFilter || 'all'}
            onValueChange={(value) => onRiskFilterChange(value === 'all' ? undefined : value)}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Risk Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Risks</SelectItem>
              <SelectItem value="High">High Risk</SelectItem>
              <SelectItem value="Medium">Medium Risk</SelectItem>
              <SelectItem value="Low">Low Risk</SelectItem>
            </SelectContent>
          </Select>

          {/* Expand/Collapse All Buttons */}
          {showGroupingControls && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={onExpandAll}
                disabled={disabled}
                title="Expand all groups"
              >
                <ChevronDown className="mr-1 h-4 w-4" />
                Expand All
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={onCollapseAll}
                disabled={disabled}
                title="Collapse all groups"
              >
                <ChevronRight className="mr-1 h-4 w-4" />
                Collapse All
              </Button>
            </>
          )}

          {/* Refresh Button */}
          <Button variant="outline" size="icon" onClick={onRefresh} disabled={disabled}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex items-center gap-2">
          {/* Extract ACM Button */}
          <Button
            variant="outline"
            onClick={onExtract}
            disabled={disabled || isExtracting}
          >
            <Sparkles className="mr-2 h-4 w-4" />
            {isExtracting ? 'Extracting...' : 'Extract ACM'}
          </Button>

          {/* Export CSV Button */}
          <Button
            variant="outline"
            onClick={onExport}
            disabled={disabled || isExporting}
          >
            <Download className="mr-2 h-4 w-4" />
            {isExporting ? 'Exporting...' : 'Export CSV'}
          </Button>

          {/* Add New Button */}
          <Button onClick={onAddNew} disabled={disabled}>
            <Plus className="mr-2 h-4 w-4" />
            Add Record
          </Button>
        </div>
      </div>
    </div>
  )
}
