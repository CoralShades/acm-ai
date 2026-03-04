import { useQuery } from '@tanstack/react-query'
import { acmApi } from '@/lib/api/acm'

export const ACM_ITEMS_QUERY_KEYS = {
  byBuilding: (sourceId: string, buildingId: string | null) =>
    ['acm', 'items', sourceId, buildingId] as const,
  fieldSchema: () => ['acm', 'field-schema'] as const,
}

export function useACMItems(sourceId: string, buildingId: string | null) {
  return useQuery({
    queryKey: ACM_ITEMS_QUERY_KEYS.byBuilding(sourceId, buildingId),
    queryFn: () =>
      acmApi.list({ source_id: sourceId, building_id: buildingId ?? undefined, limit: 500 }),
    enabled: !!sourceId && !!buildingId,
    staleTime: 30 * 1000,
  })
}

export function useFieldSchema() {
  return useQuery({
    queryKey: ACM_ITEMS_QUERY_KEYS.fieldSchema(),
    queryFn: () => acmApi.getFieldSchema(),
    staleTime: Infinity, // schema is session-stable
  })
}
