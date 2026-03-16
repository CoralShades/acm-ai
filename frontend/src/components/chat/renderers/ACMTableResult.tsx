'use client'

import { Badge } from '@/components/ui/badge'
import { TableProperties } from 'lucide-react'
import { useModalManager } from '@/lib/hooks/use-modal-manager'

interface ACMTableResultProps {
  data: Record<string, unknown>
  queryType: string
}

function getRiskBadgeVariant(risk: string | null | undefined) {
  switch (risk?.toLowerCase()) {
    case 'high':
      return 'destructive' as const
    case 'medium':
      return 'secondary' as const
    case 'low':
      return 'outline' as const
    default:
      return 'outline' as const
  }
}

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

  if (records.length === 0) {
    return (
      <div className="rounded-lg border p-3 text-sm text-muted-foreground">
        No ACM records found for this {queryType.toLowerCase()} query.
      </div>
    )
  }

  return (
    <div className="rounded-lg border overflow-hidden">
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
            {records.map((record, idx) => (
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
                    variant={getRiskBadgeVariant(record.risk_status as string)}
                    className={`text-[10px] ${getRiskColorClass(record.risk_status as string)}`}
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
    </div>
  )
}
