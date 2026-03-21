'use client'

import { useState, useEffect, useCallback } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { BuildingDetailForm } from '@/components/acm/BuildingDetailForm'
import { useUpdateBuilding } from '@/lib/hooks/useBuildingDetail'
import { Building2 } from 'lucide-react'
import type { BuildingRecord } from '@/lib/types/building'
import type { SFFieldSchemaConfig } from '@/lib/types/sf-schema'

interface BuildingViewDialogProps {
  building: BuildingRecord | null
  open: boolean
  onOpenChange: (open: boolean) => void
  sourceId: string
  schema: SFFieldSchemaConfig | null
}

/**
 * BuildingViewDialog — full-height responsive dialog for viewing/editing
 * a single building record. Uses max-w-5xl on desktop, near-full-screen
 * on mobile, with a scrollable form body.
 */
export function BuildingViewDialog({
  building,
  open,
  onOpenChange,
  sourceId,
  schema,
}: BuildingViewDialogProps) {
  const updateBuilding = useUpdateBuilding()
  const [localBuilding, setLocalBuilding] = useState<BuildingRecord | null>(building)

  useEffect(() => {
    if (building) {
      setLocalBuilding(building)
    }
  }, [building])

  const handleSave = useCallback(
    (data: Partial<BuildingRecord>) => {
      if (!localBuilding) return
      updateBuilding.mutate(
        {
          buildingId: localBuilding.id,
          data,
        },
        {
          onSuccess: () => {
            onOpenChange(false)
          },
        }
      )
    },
    [localBuilding, updateBuilding, onOpenChange]
  )

  const handleOpenChange = useCallback(
    (nextOpen: boolean) => {
      if (!updateBuilding.isPending) {
        onOpenChange(nextOpen)
      }
    },
    [updateBuilding.isPending, onOpenChange]
  )

  const displayName =
    localBuilding?.building_name ??
    localBuilding?.building_code ??
    localBuilding?.internal_id ??
    'Building'

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent
        className={[
          // Reset base grid to flex column layout
          '!grid-cols-none !grid-rows-none flex flex-col',
          // Sizing: near-full on mobile, capped at 5xl on desktop
          'w-[calc(100vw-2rem)] max-w-5xl',
          // Height: full viewport minus padding on mobile, 90vh on desktop
          'h-[calc(100dvh-2rem)] sm:h-[min(90dvh,56rem)]',
          // Remove base padding — form manages its own
          'p-0 gap-0',
          // Contain overflow — scrolling handled by form body
          'overflow-hidden',
        ].join(' ')}
      >
        {/* Header — fixed at top */}
        <DialogHeader className="shrink-0 border-b px-5 pt-5 pb-3 sm:px-6 sm:pt-6">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Building2 className="h-4.5 w-4.5" />
            </div>
            <div className="min-w-0">
              <DialogTitle className="truncate text-base sm:text-lg">
                {displayName}
              </DialogTitle>
              <DialogDescription className="text-xs mt-0.5">
                {localBuilding?.internal_id ?? ''}{' '}
                {localBuilding?.record_count != null && (
                  <span className="text-muted-foreground">
                    &mdash; {localBuilding.record_count} ACM record
                    {localBuilding.record_count !== 1 ? 's' : ''}
                  </span>
                )}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {/* Form body — fills remaining space, scrolls internally */}
        {localBuilding && (
          <div className="flex-1 min-h-0">
            <BuildingDetailForm
              building={localBuilding}
              sourceId={sourceId}
              schema={schema}
              onSave={handleSave}
              isSaving={updateBuilding.isPending}
            />
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
