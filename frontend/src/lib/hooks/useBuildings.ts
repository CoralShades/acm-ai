import { useQuery } from '@tanstack/react-query'
import { acmApi } from '@/lib/api/acm'

export const BUILDING_QUERY_KEYS = {
  list: (sourceId: string) => ['buildings', 'v3', sourceId] as const,
}

export function useBuildings(sourceId: string) {
  return useQuery({
    queryKey: BUILDING_QUERY_KEYS.list(sourceId),
    queryFn: () => acmApi.listBuildings(sourceId),
    enabled: !!sourceId,
    staleTime: 30 * 1000,
    // Limit retries to avoid console error noise for sources with no building data (E35-S8)
    retry: 1,
  })
}
