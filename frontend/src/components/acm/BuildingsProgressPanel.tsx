'use client'

import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Building2, CheckCircle2, Loader2, Circle } from 'lucide-react'
import { acmApi } from '@/lib/api/acm'
import type { BuildingRecord } from '@/lib/types/building'

interface BuildingsProgressPanelProps {
  sourceId: string
  isExtracting: boolean
}

export function BuildingsProgressPanel({ sourceId, isExtracting }: BuildingsProgressPanelProps) {
  const { data, isLoading } = useQuery({
    queryKey: ['acm', 'buildings', sourceId],
    queryFn: () => acmApi.listBuildings(sourceId),
    enabled: !!sourceId,
    refetchInterval: isExtracting ? 4000 : false,
    staleTime: 5000,
  })

  const buildings: BuildingRecord[] = data?.buildings ?? []
  const buildingCount = buildings.length
  const totalRecords = buildings.reduce((sum, b) => sum + (b.record_count ?? 0), 0)

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Building2 className="h-4 w-4" />
          Buildings
          {buildingCount > 0 && (
            <span className="ml-auto text-sm font-normal text-muted-foreground">
              {buildingCount} building{buildingCount !== 1 ? 's' : ''} &middot; {totalRecords} record{totalRecords !== 1 ? 's' : ''}
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading || (buildingCount === 0 && isExtracting) ? (
          <div className="flex items-center gap-3 py-4 text-sm text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Extracting building information...</span>
          </div>
        ) : buildingCount === 0 ? (
          <p className="text-sm text-muted-foreground py-2">No buildings found yet.</p>
        ) : (
          <div className="space-y-2">
            {buildings.map((building) => {
              const hasRecords = (building.record_count ?? 0) > 0
              return (
                <div
                  key={building.id}
                  className="flex items-center gap-3 rounded-lg border p-3 text-sm"
                >
                  {hasRecords ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-500 flex-shrink-0" />
                  ) : isExtracting ? (
                    <Loader2 className="h-4 w-4 text-teal-500 animate-spin flex-shrink-0" />
                  ) : (
                    <Circle className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">
                      {building.building_name || building.internal_id || 'Unknown Building'}
                    </p>
                    <div className="flex gap-3 text-xs text-muted-foreground mt-0.5">
                      {building.building_type && <span>{building.building_type}</span>}
                      {building.suburb && <span>{building.suburb}</span>}
                      {building.postcode && <span>{building.postcode}</span>}
                    </div>
                  </div>
                  {hasRecords && (
                    <span className="text-xs font-medium text-muted-foreground">
                      {building.record_count} record{building.record_count !== 1 ? 's' : ''}
                    </span>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
