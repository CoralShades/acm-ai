'use client'

import { useState } from 'react'
import { Download, AlertTriangle } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'
import { acmApi } from '@/lib/api/acm'

type ExportFormat = 'sf-csv' | 'sf-excel' | 'bar-excel'

interface ExportOption {
  value: ExportFormat
  label: string
  description: string
}

const EXPORT_OPTIONS: ExportOption[] = [
  {
    value: 'sf-csv',
    label: 'Salesforce CSV',
    description: 'ZIP file with Building__c.csv and Item__c.csv for Data Loader',
  },
  {
    value: 'sf-excel',
    label: 'Salesforce Excel',
    description: 'Two-sheet workbook with Building__c and Item__c tabs',
  },
  {
    value: 'bar-excel',
    label: 'BAR Excel (Legacy)',
    description: 'Single-sheet BAR-format Excel file',
  },
]

export interface ExportDialogProps {
  sourceId: string
  open: boolean
  onOpenChange: (open: boolean) => void
  totalErrors: number
  selectedBuildingIds?: string[]
}

export function ExportDialog({
  sourceId,
  open,
  onOpenChange,
  totalErrors,
  selectedBuildingIds,
}: ExportDialogProps) {
  const [format, setFormat] = useState<ExportFormat>('sf-csv')
  const [selectedOnly, setSelectedOnly] = useState(false)
  const [isExporting, setIsExporting] = useState(false)

  const hasSelectedBuildings = (selectedBuildingIds?.length ?? 0) > 0
  const isBlocked = totalErrors > 0

  const buildingFilter = selectedOnly && hasSelectedBuildings ? selectedBuildingIds : undefined

  const handleExport = async () => {
    setIsExporting(true)
    try {
      let blob: Blob
      let filename: string

      if (format === 'sf-csv') {
        blob = await acmApi.exportSfCsv(sourceId, buildingFilter)
        filename = `acm-sf-export-${sourceId}.zip`
      } else if (format === 'sf-excel') {
        blob = await acmApi.exportSfExcel(sourceId, buildingFilter)
        filename = `acm-sf-export-${sourceId}.xlsx`
      } else {
        blob = await acmApi.exportExcel(sourceId)
        filename = `acm-register-${sourceId}.xlsx`
      }

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)

      onOpenChange(false)
    } finally {
      setIsExporting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Export ACM Register</DialogTitle>
          <DialogDescription>
            Choose a format to download the ACM register data.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4 py-2">
          {/* Validation error warning */}
          {isBlocked && (
            <div className="flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/10 px-3 py-2 text-sm text-destructive">
              <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
              <span>
                Export blocked: {totalErrors} validation error{totalErrors !== 1 ? 's' : ''} must
                be resolved first.
              </span>
            </div>
          )}

          {/* Format selection */}
          <RadioGroup
            value={format}
            onValueChange={(v) => setFormat(v as ExportFormat)}
            className="gap-3"
          >
            {EXPORT_OPTIONS.map((option) => (
              <div
                key={option.value}
                className={cn(
                  'flex items-start gap-3 rounded-md border px-3 py-3 cursor-pointer transition-colors',
                  format === option.value
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/40'
                )}
                onClick={() => setFormat(option.value)}
              >
                <RadioGroupItem value={option.value} id={`format-${option.value}`} className="mt-0.5 shrink-0" />
                <div className="flex flex-col gap-0.5">
                  <Label
                    htmlFor={`format-${option.value}`}
                    className="cursor-pointer font-medium leading-none"
                  >
                    {option.label}
                  </Label>
                  <p className="text-xs text-muted-foreground">{option.description}</p>
                </div>
              </div>
            ))}
          </RadioGroup>

          {/* Selected buildings checkbox */}
          <div
            className={cn(
              'flex items-center gap-2',
              !hasSelectedBuildings && 'opacity-50 cursor-not-allowed'
            )}
          >
            <Checkbox
              id="selected-only"
              checked={selectedOnly}
              onCheckedChange={(checked) => setSelectedOnly(checked === true)}
              disabled={!hasSelectedBuildings}
            />
            <Label
              htmlFor="selected-only"
              className={cn('cursor-pointer', !hasSelectedBuildings && 'cursor-not-allowed')}
            >
              Export selected buildings only
              {!hasSelectedBuildings && (
                <span className="ml-1 text-xs text-muted-foreground">(no buildings selected)</span>
              )}
            </Label>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isExporting}>
            Cancel
          </Button>
          <Button onClick={handleExport} disabled={isBlocked || isExporting}>
            <Download className="mr-1 h-4 w-4" />
            {isExporting ? 'Exporting...' : 'Export'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
