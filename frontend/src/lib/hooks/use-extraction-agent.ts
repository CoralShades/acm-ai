'use client'

import { useMemo } from 'react'
import { useCoAgent } from '@copilotkit/react-core'
import type { ExtractionAgentState } from '@/lib/types/pipeline'

/**
 * useExtractionAgent — connects CopilotKit useCoAgent to the AG-UI
 * extraction stream for incremental record display in the AG Grid.
 *
 * The co-agent name 'extraction' must match an agent registered in
 * the CopilotKit runtime at /api/copilotkit/route.ts. Currently the
 * backend has no dedicated extraction AG-UI endpoint — when it is
 * implemented, register it in the runtime's agents map.
 *
 * Story: E17-S2 Incremental Record Streaming to AG Grid
 */
export function useExtractionAgent(sourceId: string) {
  const initialState = useMemo<ExtractionAgentState>(
    () => ({
      source_id: sourceId,
      records: [],
      current_chunk_index: 0,
      total_chunks: 0,
      current_step: null,
      validation_result: null,
      final_count: null,
    }),
    [sourceId]
  )

  const { state } = useCoAgent<ExtractionAgentState>({
    name: 'extraction',
    initialState,
  })

  return {
    previewRecords: state?.records ?? [],
    chunksProcessed: state?.current_chunk_index ?? 0,
    chunksTotal: state?.total_chunks ?? 0,
    currentStep: state?.current_step ?? null,
    isConnected: !!state,
  }
}
