'use client'

import { useQuery } from '@tanstack/react-query'
import { acmApi } from '@/lib/api/acm'
import type { SourceIntelligence } from '@/lib/types/intelligence'
import type { ExtractionPhase } from './use-extraction-progress'

/**
 * React Query hook for fetching pre-extraction intelligence (E30-S9).
 *
 * Polls every 5s while extraction is running, stops when done.
 */
export function useSourceIntelligence(
  sourceId: string,
  extractionPhase?: ExtractionPhase
) {
  const isRunning = extractionPhase === 'extracting'

  return useQuery<SourceIntelligence | null>({
    queryKey: ['source-intelligence', sourceId],
    queryFn: () => acmApi.getIntelligence(sourceId),
    enabled: !!sourceId,
    refetchInterval: isRunning ? 5000 : false,
    staleTime: isRunning ? 0 : 60_000,
    retry: 1,
  })
}
