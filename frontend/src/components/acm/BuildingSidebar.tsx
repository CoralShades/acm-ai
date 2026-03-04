'use client'

import { Building2 } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { useBuildings } from '@/lib/hooks/useBuildings'
import { useBuildingStore } from '@/lib/stores/buildingStore'
import type { BuildingRecord, BuildingValidationStatus } from '@/lib/types/building'

interface BuildingSidebarProps {
  sourceId: string
}

function deriveValidationStatus(b: BuildingRecord): BuildingValidationStatus {
  if (!b.building_name && !b.building_address) return 'unknown'
  if (b.building_name && b.building_address) return 'complete'
  return 'incomplete'
}

const validationBadgeClasses: Record<BuildingValidationStatus, string> = {
  complete: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  incomplete: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  unknown: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400',
}

const validationBadgeLabel: Record<BuildingValidationStatus, string> = {
  complete: 'Complete',
  incomplete: 'Incomplete',
  unknown: 'Unknown',
}

function BuildingDetailPanel({ building }: { building: BuildingRecord }) {
  const fields: Array<{ label: string; value: string | number | null | undefined }> = [
    { label: 'Address', value: building.building_address },
    { label: 'Suburb', value: building.suburb },
    { label: 'Type', value: building.building_type },
    { label: 'Year Built', value: building.building_year },
    { label: 'Levels', value: building.number_of_levels },
    { label: 'Ownership', value: building.owned_or_leased },
    { label: 'Frequency of Use', value: building.frequency_of_use },
    { label: 'Public Access', value: building.public_access },
  ]

  return (
    <div className="p-4 border-t bg-muted/30">
      <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-3">
        Building Details
      </h3>
      <dl className="grid grid-cols-1 gap-y-2">
        {fields.map(({ label, value }) =>
          value != null ? (
            <div key={label} className="flex flex-col gap-0.5">
              <dt className="text-xs text-muted-foreground">{label}</dt>
              <dd className="text-xs font-medium truncate">{String(value)}</dd>
            </div>
          ) : null
        )}
      </dl>
    </div>
  )
}

export function BuildingSidebar({ sourceId }: BuildingSidebarProps) {
  const { data, isLoading, isError } = useBuildings(sourceId)
  const { selectedBuildingId, setSelectedBuilding } = useBuildingStore()

  const buildings = data?.buildings ?? []

  if (isLoading) {
    return (
      <div className="w-72 border-r flex flex-col overflow-hidden shrink-0 bg-background">
        <div className="p-4 border-b">
          <div className="h-5 w-32 rounded bg-muted animate-pulse" />
        </div>
        <div className="flex-1 p-3 space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-16 rounded-lg bg-muted animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="w-72 border-r flex flex-col overflow-hidden shrink-0 bg-background">
        <div className="p-4 border-b">
          <h2 className="text-sm font-semibold">Buildings</h2>
        </div>
        <div className="flex-1 flex items-center justify-center p-6">
          <p className="text-sm text-destructive text-center">Failed to load buildings</p>
        </div>
      </div>
    )
  }

  const selectedBuilding = buildings.find((b) => b.id === selectedBuildingId) ?? null

  return (
    <div className="w-72 border-r flex flex-col overflow-hidden shrink-0 bg-background">
      {/* Sidebar header */}
      <div className="p-4 border-b shrink-0">
        <h2 className="text-sm font-semibold">Buildings</h2>
        <p className="text-xs text-muted-foreground mt-0.5">
          {buildings.length} building{buildings.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Building list */}
      <div className="flex-1 overflow-y-auto">
        {buildings.length === 0 ? (
          <div className="flex flex-col items-center gap-3 p-6 text-center">
            <Building2 className="h-10 w-10 text-muted-foreground/40" />
            <p className="text-sm text-muted-foreground font-medium">No buildings extracted yet</p>
            <p className="text-xs text-muted-foreground">
              Run extraction to populate buildings from the source document.
            </p>
            <Button variant="outline" size="sm" asChild>
              <Link href={`/jobs/${sourceId}/extract`}>Go to Extraction</Link>
            </Button>
          </div>
        ) : (
          <ul className="py-1">
            {buildings.map((building) => {
              const isSelected = building.id === selectedBuildingId
              const status = deriveValidationStatus(building)
              return (
                <li key={building.id}>
                  <button
                    type="button"
                    onClick={() => setSelectedBuilding(building.id)}
                    className={[
                      'w-full text-left px-3 py-3 transition-colors hover:bg-muted/50',
                      isSelected
                        ? 'bg-primary/10 border-l-2 border-primary'
                        : 'border-l-2 border-transparent',
                    ].join(' ')}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium truncate">
                          {building.building_name ?? building.building_code ?? building.internal_id}
                        </p>
                        <p className="text-xs text-muted-foreground font-mono mt-0.5">
                          {building.internal_id}
                        </p>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {building.record_count} item{building.record_count !== 1 ? 's' : ''}
                        </p>
                      </div>
                      <span
                        className={[
                          'inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium shrink-0',
                          validationBadgeClasses[status],
                        ].join(' ')}
                      >
                        {validationBadgeLabel[status]}
                      </span>
                    </div>
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </div>

      {/* Building detail panel */}
      {selectedBuilding && <BuildingDetailPanel building={selectedBuilding} />}
    </div>
  )
}
