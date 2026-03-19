'use client'

import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { RefreshCw, AlertTriangle } from 'lucide-react'
import { useBuildings } from '@/lib/hooks/useBuildings'
import { acmApi } from '@/lib/api/acm'
import type { BuildingRecord } from '@/lib/types/building'

interface FailedBuildingsTabProps {
  sourceId: string
}

export function FailedBuildingsTab({ sourceId }: FailedBuildingsTabProps) {
  const queryClient = useQueryClient()
  const { data: buildingsData, isLoading } = useBuildings(sourceId)
  const [retryingId, setRetryingId] = useState<string | null>(null)

  const failedBuildings = (buildingsData?.buildings ?? []).filter(
    (b) => (b.record_count ?? 0) === 0
  )

  const handleRetry = async (building: BuildingRecord) => {
    setRetryingId(building.id)
    try {
      // Re-extract the full source (force mode) — single-building retry is a future enhancement
      await acmApi.extract(sourceId, { force: true })
      await queryClient.invalidateQueries({ queryKey: ['buildings', 'v3', sourceId] })
      await queryClient.invalidateQueries({ queryKey: ['acm-records', sourceId] })
    } finally {
      setRetryingId(null)
    }
  }

  if (isLoading) {
    return (
      <Card className="rounded-xl shadow-sm">
        <CardContent className="p-6 text-sm text-muted-foreground">
          Loading buildings...
        </CardContent>
      </Card>
    )
  }

  if (failedBuildings.length === 0) {
    return (
      <Card className="rounded-xl shadow-sm">
        <CardContent className="p-6 text-center text-sm text-muted-foreground">
          All buildings have records extracted successfully.
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="rounded-xl shadow-sm">
      <CardHeader className="pb-2 pt-4 px-4">
        <CardTitle className="text-sm font-semibold flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-destructive" />
          Buildings with No Records ({failedBuildings.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="px-4 pb-4">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-muted-foreground border-b">
                <th className="text-left py-2 px-2 font-medium">Building Name</th>
                <th className="text-left py-2 px-2 font-medium">Building Code</th>
                <th className="text-center py-2 px-2 font-medium">Records</th>
                <th className="text-right py-2 px-2 font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {failedBuildings.map((b) => (
                <tr key={b.id} className="border-b last:border-b-0">
                  <td className="py-2 px-2 font-medium">
                    {b.building_name ?? 'Unknown'}
                  </td>
                  <td className="py-2 px-2 text-muted-foreground">
                    {b.building_code ?? '—'}
                  </td>
                  <td className="py-2 px-2 text-center">
                    <Badge variant="destructive" className="text-xs">
                      0
                    </Badge>
                  </td>
                  <td className="py-2 px-2 text-right">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={retryingId === b.id}
                      onClick={() => handleRetry(b)}
                    >
                      {retryingId === b.id ? (
                        <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                      ) : (
                        <>
                          <RefreshCw className="h-3.5 w-3.5 mr-1" />
                          Retry
                        </>
                      )}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
