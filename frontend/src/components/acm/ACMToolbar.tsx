'use client'

import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Download, Plus, RefreshCw, Sparkles } from 'lucide-react'

interface ACMToolbarProps {
  onAddNew: () => void
  onExtract: () => void
  onExport: () => void
  onRefresh: () => void
  riskFilter?: string
  onRiskFilterChange: (value: string | undefined) => void
  isExtracting?: boolean
  isExporting?: boolean
  disabled?: boolean
}

export function ACMToolbar({
  onAddNew,
  onExtract,
  onExport,
  onRefresh,
  riskFilter,
  onRiskFilterChange,
  isExtracting = false,
  isExporting = false,
  disabled = false,
}: ACMToolbarProps) {
  return (
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
  )
}
