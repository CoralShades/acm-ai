'use client'

import { Building2, AlertTriangle, FileText } from 'lucide-react'

interface BuildingSummaryData {
  building_name: string
  building_id?: string
  record_count?: number
  high_risk_count?: number
  address?: string
}

interface BuildingSummaryCardProps {
  data: BuildingSummaryData
}

export function BuildingSummaryCard({ data }: BuildingSummaryCardProps) {
  const { building_name, building_id, record_count, high_risk_count, address } = data

  return (
    <div className="border rounded-lg p-3 my-1">
      <div className="flex items-start gap-2">
        <Building2 className="h-4 w-4 text-primary mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="font-medium text-sm truncate">{building_name}</div>
          {building_id && (
            <div className="text-xs text-muted-foreground font-mono">{building_id}</div>
          )}
          {address && (
            <div className="text-xs text-muted-foreground mt-0.5">{address}</div>
          )}
          <div className="flex items-center gap-3 mt-2 text-xs">
            {record_count != null && (
              <span className="flex items-center gap-1 text-muted-foreground">
                <FileText className="h-3 w-3" />
                {record_count} records
              </span>
            )}
            {high_risk_count != null && high_risk_count > 0 && (
              <span className="flex items-center gap-1 text-amber-600 dark:text-amber-400">
                <AlertTriangle className="h-3 w-3" />
                {high_risk_count} high risk
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
