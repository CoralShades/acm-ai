'use client'

import { Building2, ExternalLink } from 'lucide-react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { useBuildings } from '@/lib/hooks/useBuildings'
import { useBuildingStore } from '@/lib/stores/buildingStore'
import { useValidationSummary } from '@/lib/hooks/useACMItems'
import type { BuildingRecord, BuildingValidationStatus } from '@/lib/types/building'
import type { BuildingStreamStatus } from '@/lib/stores/buildingStore'

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

const streamingBadgeClasses: Record<BuildingStreamStatus, string> = {
  extracting: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
  validating: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
  complete: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
  error: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
}

const streamingBadgeLabel: Record<BuildingStreamStatus, string> = {
  extracting: 'Extracting...',
  validating: 'Validating...',
  complete: 'Complete',
  error: 'Error',
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
  const { selectedBuildingId, setSelectedBuilding, buildingStatus, selectedBuildingIds, toggleBuildingSelection } = useBuildingStore()
  const { data: validationSummary } = useValidationSummary(sourceId)

  // Build a quick lookup map: building_id -> error_count
  const validationErrorMap = new Map<string, number>(
    (validationSummary?.buildings ?? []).map((b) => [b.building_id, b.error_count])
  )

  const buildings = data?.buildings ?? []

  if (isLoading) {
    return (
      <div className="w-72 border-r flex flex-col overflow-hidden shrink-0 bg-background" data-testid="building-sidebar">
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
      <div className="w-72 border-r flex flex-col overflow-hidden shrink-0 bg-background" data-testid="building-sidebar">
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
    <div className="w-72 border-r flex flex-col overflow-hidden shrink-0 bg-background" data-testid="building-sidebar">
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
              const validationStatus = deriveValidationStatus(building)
              const streamStatus = buildingStatus.get(building.internal_id)
              const errorCount = validationErrorMap.get(building.id) ?? 0
              return (
                <li key={building.id}>
                  <div
                    className={[
                      'flex items-start gap-1 px-3 py-3 transition-colors hover:bg-muted/50',
                      isSelected
                        ? 'bg-primary/10 border-l-2 border-primary'
                        : 'border-l-2 border-transparent',
                    ].join(' ')}
                  >
                    {/* Building selection checkbox for bulk export (E34-S2) */}
                    <input
                      type="checkbox"
                      checked={selectedBuildingIds.has(building.internal_id)}
                      onChange={() => toggleBuildingSelection(building.internal_id)}
                      onClick={(e) => e.stopPropagation()}
                      className="mt-1 mr-1 h-3.5 w-3.5 shrink-0 cursor-pointer"
                      aria-label={`Select ${building.building_name ?? building.internal_id} for export`}
                    />
                    {/* Main clickable area — selects the building */}
                    <button
                      type="button"
                      onClick={() => setSelectedBuilding(building.id)}
                      className="min-w-0 flex-1 text-left"
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
                          {errorCount > 0 && (
                            <span className="inline-flex items-center mt-1 text-xs bg-red-100 text-red-700 dark:bg-red-950/30 dark:text-red-400 px-1.5 py-0.5 rounded-full">
                              {errorCount} error{errorCount !== 1 ? 's' : ''}
                            </span>
                          )}
                        </div>
                        {streamStatus !== undefined ? (
                          <span
                            className={[
                              'inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium shrink-0',
                              streamingBadgeClasses[streamStatus],
                            ].join(' ')}
                          >
                            {streamingBadgeLabel[streamStatus]}
                          </span>
                        ) : (
                          <span
                            className={[
                              'inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium shrink-0',
                              validationBadgeClasses[validationStatus],
                            ].join(' ')}
                          >
                            {validationBadgeLabel[validationStatus]}
                          </span>
                        )}
                      </div>
                    </button>

                    {/* Details link — navigates to building detail page (E33-S7) */}
                    <Link
                      href={`/source/${sourceId}/building/${encodeURIComponent(building.id)}`}
                      title="View building details"
                      className="shrink-0 p-1 rounded text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                      aria-label={`Edit details for ${building.building_name ?? building.internal_id}`}
                    >
                      <ExternalLink className="h-3.5 w-3.5" />
                    </Link>
                  </div>
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
