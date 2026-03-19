import { useQuery } from '@tanstack/react-query'
import { acmApi } from '@/lib/api/acm'

/**
 * Hook to fetch buildings from the legacy jobs endpoint.
 * Uses GET /api/acm/jobs/{sourceId}/buildings which derives buildings from
 * acm_record data — works even when no V3 building_record entities exist.
 *
 * Falls back to the V3 endpoint (useBuildings) if the jobs endpoint returns
 * no results, but typically this is the one that works for all extraction modes.
 */
export function useJobBuildings(sourceId: string) {
  return useQuery({
    queryKey: ['job-buildings', sourceId],
    queryFn: () => acmApi.listJobBuildings(sourceId),
    enabled: !!sourceId,
    staleTime: 30 * 1000,
    retry: 1,
  })
}
