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

export function useV3BuildingStream(options: UseV3BuildingStreamOptions): {
  isStreaming: boolean
  completedCount: number
  estimatedSecondsRemaining: number | null
} {
  const { sourceId, operationId, totalBuildings } = options

  const queryClient = useQueryClient()
  const { setBuildingStatus, clearBuildingStatuses } = useBuildingStore()

  const [completedCount, setCompletedCount] = useState(0)
  const [estimatedSecondsRemaining, setEstimatedSecondsRemaining] = useState<number | null>(null)
  // Only show progress bar after first event arrives (avoids showing for stale commandIds)
  const [hasReceivedEvent, setHasReceivedEvent] = useState(false)

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

        // Invalidate items query broadly so ItemGrid refetches for any building
        queryClient.invalidateQueries({ queryKey: ['acm', 'items', sourceId] })
      } else if (event.type === 'ai.items_extracted') {
        const buildingId = event.data.building_id as string
        setBuildingStatus(buildingId, 'validating')
      } else if (event.type === 'ai.validation_complete') {
        clearBuildingStatuses()
        setEstimatedSecondsRemaining(null)
        queryClient.invalidateQueries({ queryKey: ['buildings', 'v3', sourceId] })
      }
    },
    [sourceId, totalBuildings, setBuildingStatus, clearBuildingStatuses, queryClient, setHasReceivedEvent]
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

  return { isStreaming, completedCount, estimatedSecondsRemaining }
}
