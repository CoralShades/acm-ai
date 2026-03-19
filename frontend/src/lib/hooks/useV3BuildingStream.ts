'use client'

import { useCallback, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useV3SSE } from '@/lib/hooks/useV3SSE'
import { useBuildingStore } from '@/lib/stores/buildingStore'
import type { V3EventEnvelope } from '@/lib/types/v3-streaming'

interface UseV3BuildingStreamOptions {
  sourceId: string
  operationId: string | null
  totalBuildings: number
}

interface UseV3BuildingStreamResult {
  isStreaming: boolean
  completedCount: number
  estimatedSecondsRemaining: number | null
  isSaving: boolean
  savedCount: number
  totalToSave: number
}

export function useV3BuildingStream(options: UseV3BuildingStreamOptions): UseV3BuildingStreamResult {
  const { sourceId, operationId, totalBuildings } = options

  const queryClient = useQueryClient()
  const { setBuildingStatus, clearBuildingStatuses } = useBuildingStore()

  const [completedCount, setCompletedCount] = useState(0)
  const [estimatedSecondsRemaining, setEstimatedSecondsRemaining] = useState<number | null>(null)
  // Only show progress bar after first event arrives (avoids showing for stale commandIds)
  const [hasReceivedEvent, setHasReceivedEvent] = useState(false)
  // MCS9: Save progress state
  const [isSaving, setIsSaving] = useState(false)
  const [savedCount, setSavedCount] = useState(0)
  const [totalToSave, setTotalToSave] = useState(0)

  // Rolling average of duration_ms values for ETA
  const durationsRef = useRef<number[]>([])
  const completedCountRef = useRef(0)

  const handleEvent = useCallback(
    (event: V3EventEnvelope) => {
      setHasReceivedEvent(true)
      if (event.type === 'ai.building_extracted') {
        const buildingId = event.data.building_id as string
        const durationMs = event.data.duration_ms as number | undefined

        setBuildingStatus(buildingId, 'extracting')

        completedCountRef.current += 1
        setCompletedCount(completedCountRef.current)

        // Update rolling average for ETA
        if (typeof durationMs === 'number' && durationMs > 0) {
          durationsRef.current.push(durationMs)
          const avgMs =
            durationsRef.current.reduce((sum, d) => sum + d, 0) / durationsRef.current.length
          const remaining = totalBuildings - completedCountRef.current
          if (remaining > 0) {
            setEstimatedSecondsRemaining(Math.round((avgMs * remaining) / 1000))
          } else {
            setEstimatedSecondsRemaining(null)
          }
        }

        // MCS10-Gap2: Buildings ARE in DB at this point — invalidate so grid shows them
        queryClient.invalidateQueries({ queryKey: ['buildings', 'v3', sourceId] })
        // MCS10-Gap3: Do NOT invalidate items here — items don't exist until save
      } else if (event.type === 'ai.items_extracted') {
        const buildingId = event.data.building_id as string
        setBuildingStatus(buildingId, 'validating')
        // MCS10-Gap3: Do NOT invalidate items query — items not saved to DB yet
      } else if (event.type === 'ai.validation_complete') {
        // MCS9: No longer terminal — just update status to show "Saving..." phase
        // Query invalidation moved to ai.save_complete
      } else if (event.type === 'ai.save_started') {
        // MCS9: Save phase begins
        setIsSaving(true)
        setTotalToSave((event.data.total_records as number) || 0)
        setSavedCount(0)
        setEstimatedSecondsRemaining(null)
      } else if (event.type === 'ai.save_progress') {
        // MCS9: Update save progress
        const saved = (event.data.saved as number) || 0
        const currentBuilding = event.data.current_building as string | undefined
        setSavedCount(saved)
        // MCS10: Show per-building "Saving..." status
        if (currentBuilding) {
          setBuildingStatus(currentBuilding, 'saving')
          // MCS10: Per-building items invalidation — items for this building are now being saved
          queryClient.invalidateQueries({ queryKey: ['acm', 'items', sourceId, currentBuilding] })
        }
      } else if (event.type === 'ai.save_complete') {
        // MCS9+MCS10: All records saved — NOW safe to invalidate items queries
        setIsSaving(false)
        clearBuildingStatuses()
        setEstimatedSecondsRemaining(null)
        // MCS10-Gap2: Final buildings refresh (picks up record_count etc.)
        queryClient.invalidateQueries({ queryKey: ['buildings', 'v3', sourceId] })
        // MCS10-Gap3: Items NOW exist in DB — safe to invalidate
        queryClient.invalidateQueries({ queryKey: ['acm', 'items', sourceId] })
      }
    },
    [sourceId, totalBuildings, setBuildingStatus, clearBuildingStatuses, queryClient]
  )

  const { status } = useV3SSE({
    operationId: operationId ?? '',
    category: 'ai',
    enabled: !!operationId,
    onEvent: handleEvent,
  })

  // isStreaming is true only after first event arrives — avoids showing progress bar
  // for stale commandIds from prior extraction sessions
  const isStreaming = !!operationId && hasReceivedEvent && status !== 'done' && status !== 'error'

  return { isStreaming, completedCount, estimatedSecondsRemaining, isSaving, savedCount, totalToSave }
}
