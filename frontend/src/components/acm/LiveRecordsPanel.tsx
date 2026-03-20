'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ClipboardList, Loader2 } from 'lucide-react'
import { acmApi } from '@/lib/api/acm'
import { cn } from '@/lib/utils'
import type { BuildingRecord } from '@/lib/types/building'

interface LiveRecordsPanelProps {
  sourceId: string
  isExtracting: boolean
  buildings: BuildingRecord[]
}

export function LiveRecordsPanel({ sourceId, isExtracting, buildings }: LiveRecordsPanelProps) {
  const [selectedBuildingId, setSelectedBuildingId] = useState<string | null>(null)

  // Poll for records during extraction
  const { data: recordsData, isLoading } = useQuery({
    queryKey: ['acm', 'records', sourceId, selectedBuildingId],
    queryFn: () =>
      acmApi.list({
        source_id: sourceId,
        ...(selectedBuildingId ? { building_id: selectedBuildingId } : {}),
        limit: 100,
      }),
    enabled: !!sourceId,
    refetchInterval: isExtracting ? 5000 : false,
    staleTime: 5000,
  })

  const records = recordsData?.records ?? []
  const totalRecords = recordsData?.total ?? records.length

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <ClipboardList className="h-4 w-4" />
          ACM Records
          {totalRecords > 0 && (
            <span className="ml-auto text-sm font-normal text-muted-foreground">
              {totalRecords} record{totalRecords !== 1 ? 's' : ''}
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Building selector */}
        {buildings.length > 1 && (
          <div className="flex gap-1.5 mb-3 flex-wrap">
            <button
              onClick={() => setSelectedBuildingId(null)}
              className={cn(
                'px-2.5 py-1 rounded-md text-xs font-medium transition-colors',
                !selectedBuildingId
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:text-foreground'
              )}
            >
              All
            </button>
            {buildings.map((b) => (
              <button
                key={b.id}
                onClick={() => setSelectedBuildingId(b.id)}
                className={cn(
                  'px-2.5 py-1 rounded-md text-xs font-medium transition-colors',
                  selectedBuildingId === b.id
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted text-muted-foreground hover:text-foreground'
                )}
              >
                {b.building_name || b.internal_id || 'Unknown'}
                {b.record_count != null && (
                  <span className="ml-1 opacity-70">({b.record_count})</span>
                )}
              </button>
            ))}
          </div>
        )}

        {isLoading || (totalRecords === 0 && isExtracting) ? (
          <div className="flex items-center gap-3 py-4 text-sm text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
            <span>Records will appear as buildings complete extraction...</span>
          </div>
        ) : totalRecords === 0 ? (
          <p className="text-sm text-muted-foreground py-2">No records extracted yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-xs text-muted-foreground">
                  <th className="pb-2 pr-3 font-medium">Building</th>
                  <th className="pb-2 pr-3 font-medium">Room</th>
                  <th className="pb-2 pr-3 font-medium">Product</th>
                  <th className="pb-2 pr-3 font-medium">Location</th>
                  <th className="pb-2 pr-3 font-medium">Friable</th>
                  <th className="pb-2 pr-3 font-medium">Condition</th>
                  <th className="pb-2 font-medium">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {records.slice(0, 50).map((record, idx) => (
                  <tr key={record.id || idx} className="border-b last:border-0">
                    <td className="py-2 pr-3 truncate max-w-[120px]">{record.building_name || '-'}</td>
                    <td className="py-2 pr-3 truncate max-w-[100px]">{record.room_name || '-'}</td>
                    <td className="py-2 pr-3 truncate max-w-[120px]">{record.product || '-'}</td>
                    <td className="py-2 pr-3 truncate max-w-[120px]">{record.location || '-'}</td>
                    <td className="py-2 pr-3">{record.friable || '-'}</td>
                    <td className="py-2 pr-3">{record.material_condition || '-'}</td>
                    <td className="py-2">
                      <span
                        className={cn(
                          'text-xs px-1.5 py-0.5 rounded',
                          record.extraction_confidence === 'high'
                            ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
                            : record.extraction_confidence === 'medium'
                              ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
                              : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
                        )}
                      >
                        {record.extraction_confidence || '?'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {totalRecords > 50 && (
              <p className="text-xs text-muted-foreground mt-2">
                Showing first 50 of {totalRecords} records
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
