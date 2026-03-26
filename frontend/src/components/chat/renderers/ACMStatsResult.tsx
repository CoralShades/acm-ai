'use client'

import { motion } from 'framer-motion'
import { Badge } from '@/components/ui/badge'
import { TableProperties, Building2, DoorOpen, AlertTriangle } from 'lucide-react'
import { BuildingListResult } from './BuildingListResult'
import { RiskDistributionChart } from './RiskDistributionChart'
import { useCountUp } from '@/lib/hooks/useCountUp'

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

  const animatedTotal = useCountUp(totalRecords)
  const animatedBuildings = useCountUp(buildingCount)
  const animatedRooms = useCountUp(roomCount)
  const animatedHigh = useCountUp(highRisk)
  const animatedMedium = useCountUp(mediumRisk)
  const animatedLow = useCountUp(lowRisk)

  // If it looks like a building list, delegate to BuildingListResult
  const buildings = data.buildings as Array<Record<string, unknown>> | undefined
  if (buildings) {
    return <BuildingListResult buildings={buildings} />
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}
      className="rounded-lg border overflow-hidden my-2"
    >
      <div className="px-3 py-2 bg-muted/50 flex items-center gap-2 text-xs font-medium">
        <TableProperties className="h-3.5 w-3.5" />
        ACM Statistics
      </div>
      <div className="grid grid-cols-3 gap-2 p-3">
        <div className="text-center">
          <div className="text-lg font-bold font-mono tabular-nums">{animatedTotal}</div>
          <div className="text-xs text-muted-foreground">Total Records</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold font-mono tabular-nums">{animatedBuildings}</div>
          <div className="text-xs text-muted-foreground flex items-center justify-center gap-1">
            <Building2 className="h-3 w-3" />
            Buildings
          </div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold font-mono tabular-nums">{animatedRooms}</div>
          <div className="text-xs text-muted-foreground flex items-center justify-center gap-1">
            <DoorOpen className="h-3 w-3" />
            Rooms
          </div>
        </div>
      </div>
      <div className="px-3 pb-3 flex items-center gap-2 justify-center">
        {highRisk > 0 && (
          <Badge className="bg-risk-high-bg text-risk-high-foreground text-xs gap-1">
            <AlertTriangle className="h-2.5 w-2.5" />
            <span className="font-mono tabular-nums">{animatedHigh}</span> High
          </Badge>
        )}
        {mediumRisk > 0 && (
          <Badge className="bg-risk-medium-bg text-risk-medium-foreground text-xs">
            <span className="font-mono tabular-nums">{animatedMedium}</span> Medium
          </Badge>
        )}
        {lowRisk > 0 && (
          <Badge className="bg-risk-low-bg text-risk-low-foreground text-xs">
            <span className="font-mono tabular-nums">{animatedLow}</span> Low
          </Badge>
        )}
      </div>
      {(highRisk > 0 || mediumRisk > 0 || lowRisk > 0) && (
        <div className="px-3 pb-3">
          <RiskDistributionChart
            high={highRisk}
            medium={mediumRisk}
            low={lowRisk}
            total={highRisk + mediumRisk + lowRisk}
          />
        </div>
      )}
    </motion.div>
  )
}
