'use client'

import { useMemo } from 'react'
import { AlertTriangle } from 'lucide-react'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { cn } from '@/lib/utils'
import type { ACMRecord } from '@/lib/types/acm'

interface BuildingTab {
  id: string
  label: string
  count: number
  hasHighRisk: boolean
}

export interface BuildingTabFilterProps {
  records: ACMRecord[]
  selectedBuilding: string | null
  onBuildingChange: (buildingId: string | null) => void
}

const ALL_RECORDS_TAB_ID = '__all__'
export const UNASSIGNED_TAB_ID = '__unassigned__'

export function getRecordBuildingTabId(record: ACMRecord): string {
  const buildingId = record.building_id?.trim()
  if (!buildingId || buildingId.toLowerCase() === 'unknown') {
    return UNASSIGNED_TAB_ID
  }

  return buildingId
}

export function BuildingTabFilter({
  records,
  selectedBuilding,
  onBuildingChange,
}: BuildingTabFilterProps) {
  const { buildingTabs, unassignedTab } = useMemo(() => {
    const tabMap = new Map<string, BuildingTab>()
    let unassignedCount = 0
    let unassignedHasHighRisk = false

    records.forEach((record) => {
      const tabId = getRecordBuildingTabId(record)
      const hasHighRisk = record.risk_status === 'High'

      if (tabId === UNASSIGNED_TAB_ID) {
        unassignedCount += 1
        unassignedHasHighRisk = unassignedHasHighRisk || hasHighRisk
        return
      }

      const existingTab = tabMap.get(tabId)
      const tabLabel =
        record.building_name?.trim() ||
        record.building_id?.trim() ||
        'Unknown Building'

      if (existingTab) {
        existingTab.count += 1
        existingTab.hasHighRisk = existingTab.hasHighRisk || hasHighRisk
        if (!existingTab.label || existingTab.label === existingTab.id) {
          existingTab.label = tabLabel
        }
        return
      }

      tabMap.set(tabId, {
        id: tabId,
        label: tabLabel,
        count: 1,
        hasHighRisk,
      })
    })

    return {
      buildingTabs: Array.from(tabMap.values()).sort((a, b) =>
        a.label.localeCompare(b.label)
      ),
      unassignedTab:
        unassignedCount > 0
          ? {
              id: UNASSIGNED_TAB_ID,
              label: 'Unassigned',
              count: unassignedCount,
              hasHighRisk: unassignedHasHighRisk,
            }
          : null,
    }
  }, [records])

  const selectedTab = selectedBuilding ?? ALL_RECORDS_TAB_ID

  return (
    <Tabs
      value={selectedTab}
      onValueChange={(value) =>
        onBuildingChange(value === ALL_RECORDS_TAB_ID ? null : value)
      }
      className="w-full"
    >
      <div className="w-full overflow-x-auto border-b pb-2">
        <TabsList
          aria-label="Filter records by building"
          className="h-auto min-w-max flex-nowrap items-center justify-start gap-1 whitespace-nowrap"
        >
          <TabsTrigger
            value={ALL_RECORDS_TAB_ID}
            className="h-8 flex-none whitespace-nowrap px-3"
          >
            All Records ({records.length})
          </TabsTrigger>

          {unassignedTab && (
            <TabsTrigger
              value={unassignedTab.id}
              className={cn(
                'h-8 flex-none whitespace-nowrap border-l-2 border-l-amber-500 px-3',
                unassignedTab.hasHighRisk && 'border-r-2 border-r-destructive'
              )}
            >
              {unassignedTab.label} ({unassignedTab.count})
              {unassignedTab.hasHighRisk && (
                <AlertTriangle className="h-3 w-3 text-destructive" />
              )}
            </TabsTrigger>
          )}

          {buildingTabs.map((building) => (
            <TabsTrigger
              key={building.id}
              value={building.id}
              className={cn(
                'h-8 flex-none whitespace-nowrap px-3',
                building.hasHighRisk && 'border-l-2 border-l-destructive'
              )}
            >
              {building.label} ({building.count})
              {building.hasHighRisk && (
                <AlertTriangle className="h-3 w-3 text-destructive" />
              )}
            </TabsTrigger>
          ))}
        </TabsList>
      </div>
    </Tabs>
  )
}
