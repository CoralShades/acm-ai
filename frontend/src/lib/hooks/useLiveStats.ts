'use client'

import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api/client'

export interface LiveStats {
  tables_count: number
  buildings_count: number
  records_count: number
  site_name: string | null
  consultant_name: string | null
}

export function useLiveStats(sourceId: string, enabled: boolean) {
  return useQuery<LiveStats>({
    queryKey: ['source-live-stats', sourceId],
    queryFn: async () => {
      const response = await apiClient.get<LiveStats>(
        `/sources/${encodeURIComponent(sourceId)}/live-stats`
      )
      return response.data
    },
    enabled,
    refetchInterval: enabled ? 5000 : false,
    staleTime: 3000,
    // Return null gracefully if endpoint doesn't exist yet
    retry: false,
  })
}
