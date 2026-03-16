'use client'

import { useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { TableProperties } from 'lucide-react'
import { useModalManager } from '@/lib/hooks/use-modal-manager'

interface ACMTableResultProps {
  data: Record<string, unknown>
  queryType: string
}

const ROW_CAP = 20

function getRiskColorClass(risk: string | null | undefined) {
  switch (risk?.toLowerCase()) {
    case 'high':
      return 'bg-risk-high-bg text-risk-high-foreground'
    case 'medium':
      return 'bg-risk-medium-bg text-risk-medium-foreground'
    case 'low':
      return 'bg-risk-low-bg text-risk-low-foreground'
    default:
      return ''
  }
}

export function ACMTableResult({ data, queryType }: ACMTableResultProps) {
  const { openModal } = useModalManager()
  const records = (data.records as Array<Record<string, unknown>>) || []
  const total = (data.total as number) || records.length
  const [showAll, setShowAll] = useState(false)

  if (records.length === 0) {
    return (
      <div className="rounded-lg border p-3 my-2 text-sm text-muted-foreground">
        No ACM records found for this {queryType.toLowerCase()} query.
      </div>
    )
  }

  const visibleRecords = showAll ? records : records.slice(0, ROW_CAP)
  const hasMore = records.length > ROW_CAP

  return (
    <div className="rounded-lg border overflow-hidden my-2">
      <div className="px-3 py-2 bg-muted/50 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-medium">
          <TableProperties className="h-3.5 w-3.5" />
          ACM Records ({queryType})
        </div>
        <span className="text-xs text-muted-foreground">
          {records.length} of {total} results
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[480px] text-xs">
          <caption className="sr-only">ACM Records — {queryType}</caption>
          <thead>
            <tr className="border-b bg-muted/30">
              <th className="px-3 py-1.5 text-left font-medium">Building</th>
              <th className="px-3 py-1.5 text-left font-medium">Room</th>
              <th className="px-3 py-1.5 text-left font-medium">Product</th>
              <th className="px-3 py-1.5 text-left font-medium">Risk</th>
              <th className="px-3 py-1.5 text-left font-medium">Result</th>
            </tr>
          </thead>
          <tbody>
            {visibleRecords.map((record, idx) => (
              <tr
                key={(record.id as string) || idx}
                className="border-b last:border-0 hover:bg-muted/20 cursor-pointer"
                onClick={() => {
                  if (record.id) {
                    openModal('source', record.id as string)
                  }
                }}
              >
                <td className="px-3 py-1.5">
                  {(record.building_name as string) || '-'}
                </td>
                <td className="px-3 py-1.5">
                  {(record.room_name as string) || '-'}
                </td>
                <td className="px-3 py-1.5 max-w-[150px] truncate">
                  {(record.product as string) || '-'}
                </td>
                <td className="px-3 py-1.5">
                  <Badge
                    variant="outline"
                    className={`text-xs ${getRiskColorClass(record.risk_status as string)}`}
                  >
                    {(record.risk_status as string) || 'Unknown'}
                  </Badge>
                </td>
                <td className="px-3 py-1.5">
                  {(record.result as string) || '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {hasMore && !showAll && (
        <button
          type="button"
          onClick={() => setShowAll(true)}
          className="w-full px-3 py-2 text-xs text-muted-foreground hover:text-foreground hover:bg-muted/30 transition-colors border-t"
        >
          Show all {records.length} results
        </button>
      )}
    </div>
  )
}
