'use client'

import { Badge } from '@/components/ui/badge'
import { TableProperties, Building2, DoorOpen, AlertTriangle } from 'lucide-react'

interface ACMStatsResultProps {
  data: Record<string, unknown>
}

export function ACMStatsResult({ data }: ACMStatsResultProps) {
  const totalRecords = (data.total_records as number) ?? 0
  const highRisk = (data.high_risk_count as number) ?? 0
  const mediumRisk = (data.medium_risk_count as number) ?? 0
  const lowRisk = (data.low_risk_count as number) ?? 0
  const buildingCount = (data.building_count as number) ?? 0
  const roomCount = (data.room_count as number) ?? 0

  // If it looks like a building list, render that instead
  const buildings = data.buildings as Array<Record<string, unknown>> | undefined
  if (buildings) {
    return (
      <div className="rounded-lg border overflow-hidden">
        <div className="px-3 py-2 bg-muted/50 flex items-center gap-2 text-xs font-medium">
          <Building2 className="h-3.5 w-3.5" />
          Buildings with ACM Data
        </div>
        <div className="p-3 space-y-1">
          {buildings.map((b, i) => (
            <div key={i} className="flex items-center justify-between text-xs">
              <span>{(b.name as string) || (b.building_name as string) || 'Unknown'}</span>
              <Badge variant="outline" className="text-[10px]">
                {(b.record_count as number) ?? '?'} records
              </Badge>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-lg border overflow-hidden">
      <div className="px-3 py-2 bg-muted/50 flex items-center gap-2 text-xs font-medium">
        <TableProperties className="h-3.5 w-3.5" />
        ACM Statistics
      </div>
      <div className="grid grid-cols-3 gap-2 p-3">
        <div className="text-center">
          <div className="text-lg font-bold">{totalRecords}</div>
          <div className="text-[10px] text-muted-foreground">Total Records</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold flex items-center justify-center gap-1">
            <Building2 className="h-3.5 w-3.5" />
            {buildingCount}
          </div>
          <div className="text-[10px] text-muted-foreground">Buildings</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold flex items-center justify-center gap-1">
            <DoorOpen className="h-3.5 w-3.5" />
            {roomCount}
          </div>
          <div className="text-[10px] text-muted-foreground">Rooms</div>
        </div>
      </div>
      <div className="px-3 pb-3 flex items-center gap-2 justify-center">
        {highRisk > 0 && (
          <Badge className="bg-risk-high-bg text-risk-high-foreground text-[10px] gap-1">
            <AlertTriangle className="h-2.5 w-2.5" />
            {highRisk} High
          </Badge>
        )}
        {mediumRisk > 0 && (
          <Badge className="bg-risk-medium-bg text-risk-medium-foreground text-[10px]">
            {mediumRisk} Medium
          </Badge>
        )}
        {lowRisk > 0 && (
          <Badge className="bg-risk-low-bg text-risk-low-foreground text-[10px]">
            {lowRisk} Low
          </Badge>
        )}
      </div>
    </div>
  )
}
