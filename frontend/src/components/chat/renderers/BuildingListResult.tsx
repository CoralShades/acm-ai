'use client'

import { Badge } from '@/components/ui/badge'
import { Building2 } from 'lucide-react'

interface BuildingListResultProps {
  buildings: Array<Record<string, unknown>>
}

export function BuildingListResult({ buildings }: BuildingListResultProps) {
  return (
    <div className="rounded-lg border overflow-hidden my-2">
      <div className="px-3 py-2 bg-muted/50 flex items-center gap-2 text-xs font-medium">
        <Building2 className="h-3.5 w-3.5" />
        Buildings with ACM Data
      </div>
      <div className="p-3 space-y-1">
        {buildings.map((b, i) => (
          <div key={i} className="flex items-center justify-between text-xs">
            <span>{(b.name as string) || (b.building_name as string) || 'Unknown'}</span>
            <Badge variant="outline" className="text-xs">
              {(b.record_count as number) ?? '?'} records
            </Badge>
          </div>
        ))}
      </div>
    </div>
  )
}
