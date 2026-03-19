'use client'

import { useRef } from 'react'
import { Skeleton } from '@/components/ui/skeleton'
import { useBuildingStore } from '@/lib/stores/buildingStore'
import type { BuildingRecord } from '@/lib/types/building'
import type { BuildingStreamStatus } from '@/lib/stores/buildingStore'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface BuildingTabStripProps {
  buildings: BuildingRecord[]
  isLoading: boolean
  selectedBuildingId: string | null
  onSelect: (id: string | null) => void
  validationSummary: { buildings: Array<{ building_id: string; error_count: number }> } | null | undefined
}

export function BuildingTabStrip({
  buildings,
  isLoading,
  selectedBuildingId,
  onSelect,
  validationSummary,
}: BuildingTabStripProps) {
  const scrollRef = useRef<HTMLDivElement>(null)
  const { buildingStatus } = useBuildingStore()

  const errorMap = new Map<string, number>(
    (validationSummary?.buildings ?? []).map((b) => [b.building_id, b.error_count])
  )

  const scroll = (dir: 'left' | 'right') => {
    scrollRef.current?.scrollBy({ left: dir === 'left' ? -200 : 200, behavior: 'smooth' })
  }

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 border-b shrink-0 bg-muted/20">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-9 w-36 rounded-md" />
        ))}
      </div>
    )
  }

  if (buildings.length === 0) return null

  const streamBadge = (status: BuildingStreamStatus | undefined) => {
    if (!status) return null
    const classes: Record<BuildingStreamStatus, string> = {
      detected: 'bg-blue-400',
      extracting: 'bg-blue-500',
      validating: 'bg-yellow-500',
      saving: 'bg-purple-500',
      complete: 'bg-green-500',
      error: 'bg-red-500',
    }
    return <span className={cn('inline-block h-2 w-2 rounded-full shrink-0', classes[status])} />
  }

  const totalRecordCount = buildings.reduce((sum, b) => sum + b.record_count, 0)

  return (
    <div className="flex items-center border-b shrink-0 bg-muted/20">
      <button
        type="button"
        onClick={() => scroll('left')}
        className="shrink-0 px-1.5 py-2 text-muted-foreground hover:text-foreground"
        aria-label="Scroll tabs left"
      >
        <ChevronLeft className="h-4 w-4" />
      </button>
      <div
        ref={scrollRef}
        className="flex-1 flex items-center gap-1 overflow-x-auto scrollbar-none py-1.5"
        style={{ scrollbarWidth: 'none' }}
      >
        {/* "All Records" tab */}
        <button
          type="button"
          onClick={() => onSelect(null)}
          className={cn(
            'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm whitespace-nowrap transition-colors shrink-0',
            selectedBuildingId === null
              ? 'bg-primary text-primary-foreground shadow-sm'
              : 'hover:bg-muted text-muted-foreground hover:text-foreground'
          )}
        >
          <span className="font-medium">All Records</span>
          <span className={cn(
            'text-xs tabular-nums',
            selectedBuildingId === null ? 'text-primary-foreground/70' : 'text-muted-foreground'
          )}>
            {totalRecordCount}
          </span>
        </button>

        {buildings.map((b) => {
          const isSelected = b.id === selectedBuildingId
          const errorCount = errorMap.get(b.id) ?? 0
          const status = buildingStatus.get(b.internal_id)
          return (
            <button
              key={b.id}
              type="button"
              onClick={() => onSelect(b.id)}
              className={cn(
                'flex items-center gap-2 px-3 py-1.5 rounded-md text-sm whitespace-nowrap transition-colors shrink-0',
                isSelected
                  ? 'bg-primary text-primary-foreground shadow-sm'
                  : 'hover:bg-muted text-muted-foreground hover:text-foreground'
              )}
            >
              {streamBadge(status)}
              <span className="font-medium truncate max-w-40">
                {b.building_name ?? b.building_code ?? b.internal_id}
              </span>
              <span className={cn(
                'text-xs tabular-nums',
                isSelected ? 'text-primary-foreground/70' : 'text-muted-foreground'
              )}>
                {b.record_count}
              </span>
              {errorCount > 0 && (
                <span className="text-xs bg-red-100 text-red-700 dark:bg-red-950/40 dark:text-red-400 px-1 py-0.5 rounded-full leading-none">
                  {errorCount}
                </span>
              )}
            </button>
          )
        })}
      </div>
      <button
        type="button"
        onClick={() => scroll('right')}
        className="shrink-0 px-1.5 py-2 text-muted-foreground hover:text-foreground"
        aria-label="Scroll tabs right"
      >
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  )
}
