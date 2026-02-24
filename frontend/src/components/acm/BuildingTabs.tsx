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

export const UNASSIGNED_TAB_ID = '__unassigned__'

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
  const { buildings, unassignedCount, unassignedHasHighRisk } = useMemo(() => {
    const buildingMap = new Map<string, BuildingTab>()
    let localUnassignedCount = 0
    let localUnassignedHighRisk = false

    records.forEach((record) => {
      const buildingId = record.building_id?.trim()
      if (!buildingId || buildingId.toLowerCase() === 'unknown') {
        localUnassignedCount++
        if (record.risk_status === 'High') {
          localUnassignedHighRisk = true
        }
        return
      }

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
    return {
      buildings: Array.from(buildingMap.values()).sort((a, b) =>
        a.building_code.localeCompare(b.building_code)
      ),
      unassignedCount: localUnassignedCount,
      unassignedHasHighRisk: localUnassignedHighRisk,
    }
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
        {/* All Records tab */}
        <TabsTrigger value="all">
          All Records ({records.length})
        </TabsTrigger>

        {/* Unassigned Records tab */}
        {unassignedCount > 0 && (
          <TabsTrigger
            value={UNASSIGNED_TAB_ID}
            className={cn(
              'border-l-2 border-l-amber-500',
              unassignedHasHighRisk && 'border-r-2 border-r-destructive'
            )}
          >
            Unassigned ({unassignedCount})
            {unassignedHasHighRisk && (
              <AlertTriangle className="w-3 h-3 ml-1 text-destructive" />
            )}
          </TabsTrigger>
        )}

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
