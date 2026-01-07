'use client'

import { useMemo } from 'react'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { ACMRecord } from '@/lib/types/acm'

interface BuildingTab {
  building_id: string
  building_code: string
  record_count: number
  hasHighRisk: boolean
}

interface BuildingTabsProps {
  records: ACMRecord[]
  selectedBuilding: string | null
  onBuildingChange: (buildingId: string | null) => void
}

export function BuildingTabs({
  records,
  selectedBuilding,
  onBuildingChange,
}: BuildingTabsProps) {
  // Extract unique buildings with counts and risk indicators
  const buildings = useMemo(() => {
    const buildingMap = new Map<string, BuildingTab>()

    records.forEach((record) => {
      const buildingId = record.building_id || 'unknown'
      const existing = buildingMap.get(buildingId)
      const isHighRisk = record.risk_status === 'High'

      if (existing) {
        existing.record_count++
        existing.hasHighRisk = existing.hasHighRisk || isHighRisk
        // Update building_code if we find a better name
        if (!existing.building_code || existing.building_code === existing.building_id) {
          existing.building_code = record.building_name || existing.building_code
        }
      } else {
        buildingMap.set(buildingId, {
          building_id: buildingId,
          building_code: record.building_name || record.building_id || 'Unknown',
          record_count: 1,
          hasHighRisk: isHighRisk,
        })
      }
    })

    // Sort alphabetically by building code
    return Array.from(buildingMap.values()).sort((a, b) =>
      a.building_code.localeCompare(b.building_code)
    )
  }, [records])

  // Don't render tabs if no records
  if (records.length === 0) {
    return null
  }

  return (
    <Tabs
      value={selectedBuilding || 'all'}
      onValueChange={(value) =>
        onBuildingChange(value === 'all' ? null : value)
      }
    >
      <TabsList className="flex flex-wrap h-auto gap-1">
        {/* All Buildings tab */}
        <TabsTrigger value="all">
          All Buildings ({records.length})
        </TabsTrigger>

        {/* Individual building tabs */}
        {buildings.map((building) => (
          <TabsTrigger
            key={building.building_id}
            value={building.building_id}
            className={cn(
              building.hasHighRisk && 'border-l-2 border-l-destructive'
            )}
          >
            {building.building_code} ({building.record_count})
            {building.hasHighRisk && (
              <AlertTriangle className="w-3 h-3 ml-1 text-destructive" />
            )}
          </TabsTrigger>
        ))}
      </TabsList>
    </Tabs>
  )
}
