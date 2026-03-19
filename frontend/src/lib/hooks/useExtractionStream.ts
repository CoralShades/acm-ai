'use client'

import { useState, useCallback } from 'react'
import { useV3SSE } from '@/lib/hooks/useV3SSE'
import type { V3EventEnvelope } from '@/lib/types/v3-streaming'

export type ExtractionPhase = 'idle' | 'started' | 'processing' | 'complete' | 'failed'

export interface ExtractionStreamState {
  phase: ExtractionPhase
  sourceId: string | null
  totalPages: number
  recordsSaved: number
  buildingsCount: number
  durationMs: number
  error: string | null
  startedAt: string | null
}

const INITIAL_STATE: ExtractionStreamState = {
  phase: 'idle',
  sourceId: null,
  totalPages: 0,
  recordsSaved: 0,
  buildingsCount: 0,
  durationMs: 0,
  error: null,
  startedAt: null,
}

export function useExtractionStream(operationId: string, enabled = true) {
  const [state, setState] = useState<ExtractionStreamState>(INITIAL_STATE)

  const handleEvent = useCallback((event: V3EventEnvelope) => {
    const d = event.data
    switch (event.type) {
      case 'extraction.started':
        setState({
          ...INITIAL_STATE,
          phase: 'started',
          sourceId: (d.source_id as string) ?? null,
          totalPages: (d.total_pages as number) ?? 0,
          startedAt: event.timestamp,
        })
        break
      case 'extraction.provider_complete':
        setState((prev) => ({ ...prev, phase: 'processing' }))
        break
      case 'extraction.consensus_complete':
        setState((prev) => ({ ...prev, phase: 'processing' }))
        break
      case 'extraction.complete':
        setState((prev) => ({
          ...prev,
          phase: 'complete',
          recordsSaved: (d.records_saved as number) ?? 0,
          buildingsCount: (d.buildings_count as number) ?? 0,
          durationMs: (d.duration_ms as number) ?? 0,
        }))
        break
      case 'extraction.failed':
        setState((prev) => ({
          ...prev,
          phase: 'failed',
          error: (d.error as string) ?? 'Unknown error',
        }))
        break
    }
  }, [])

  const { status: sseStatus, disconnect } = useV3SSE({
    operationId,
    category: 'extraction',
    enabled,
    onEvent: handleEvent,
    invalidateQueryKeys: [
      ['acm-records', state.sourceId ?? ''],
      ['buildings', state.sourceId ?? ''],
      ['acm-stats', state.sourceId ?? ''],
    ],
  })

  return { ...state, sseStatus, disconnect }
}
