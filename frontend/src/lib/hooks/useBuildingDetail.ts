import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { acmApi } from '@/lib/api/acm'
import type { BuildingRecordUpdateRequest } from '@/lib/types/building'

export const BUILDING_DETAIL_QUERY_KEYS = {
  detail: (buildingId: string) => ['building', 'detail', buildingId] as const,
}

/**
 * Fetch a single building record by ID (E33-S7).
 */
export function useBuildingDetail(buildingId: string | null) {
  return useQuery({
    queryKey: BUILDING_DETAIL_QUERY_KEYS.detail(buildingId ?? ''),
    queryFn: () => acmApi.getBuilding(buildingId!),
    enabled: !!buildingId,
    staleTime: 30 * 1000,
  })
}

/**
 * Mutation hook for updating a building record (E33-S7).
 * Invalidates both 'building' and 'buildings' query caches on success.
 */
export function useUpdateBuilding() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      buildingId,
      data,
    }: {
      buildingId: string
      data: BuildingRecordUpdateRequest
    }) => acmApi.updateBuilding(buildingId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['building'] })
      queryClient.invalidateQueries({ queryKey: ['buildings'] })
    },
  })
}
