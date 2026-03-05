import { useQuery } from '@tanstack/react-query'
import { acmApi } from '@/lib/api/acm'

export function useProvenance(recordId: string | null) {
  return useQuery({
    queryKey: ['acm', 'provenance', recordId] as const,
    queryFn: () => acmApi.getProvenance(recordId!),
    enabled: !!recordId,
    staleTime: 60 * 1000,
  })
}
