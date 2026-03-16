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
 * BuildingViewDialog -- dialog modal for viewing/editing a single building record.
 * Wraps the existing BuildingDetailForm inside a Dialog with max-w-2xl max-h-[90vh].
 */
export function BuildingViewDialog({
  building,
  open,
  onOpenChange,
  sourceId,
  schema,
}: BuildingViewDialogProps) {
  const updateBuilding = useUpdateBuilding()
  // Local copy of building to allow re-render when building prop changes
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
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-hidden flex flex-col p-0">
        <DialogHeader className="px-6 pt-6 pb-2 shrink-0">
          <DialogTitle>{displayName}</DialogTitle>
          <DialogDescription className="text-xs">
            {localBuilding?.internal_id ?? ''}{' '}
            {localBuilding?.record_count != null && (
              <span className="text-muted-foreground">
                -- {localBuilding.record_count} ACM record
                {localBuilding.record_count !== 1 ? 's' : ''}
              </span>
            )}
          </DialogDescription>
        </DialogHeader>

        {localBuilding && (
          <div className="flex-1 overflow-hidden min-h-0">
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
