import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { sourcesApi } from '@/lib/api/sources'
import { QUERY_KEYS } from '@/lib/api/query-client'
import { SourceListResponse } from '@/lib/types/api'

export type ProcessingGroup = 'inProgress' | 'pending' | 'completed' | 'failed'

export interface ProcessingStats {
  inProgress: number
  pending: number
  completed: number
  failed: number
  total: number
}

function getProcessingStatus(source: SourceListResponse): ProcessingGroup {
  const status = source.status || (source.embedded ? 'completed' : 'pending')
  switch (status) {
    case 'running':
      return 'inProgress'
    case 'queued':
    case 'new':
      return 'pending'
    case 'completed':
      return 'completed'
    case 'failed':
      return 'failed'
    default:
      return source.embedded ? 'completed' : 'pending'
  }
}

export function useProcessingStatus() {
  const { data: sources, isLoading, refetch } = useQuery({
    queryKey: QUERY_KEYS.sources(),
    queryFn: () => sourcesApi.list(),
    staleTime: 0,
    refetchInterval: (query) => {
      const data = query.state.data as SourceListResponse[] | undefined
      if (!data) return 5000
      const hasActive = data.some((s) => {
        const status = s.status || (s.embedded ? 'completed' : 'pending')
        return status === 'running' || status === 'queued' || status === 'new'
      })
      return hasActive ? 3000 : 15000
    },
  })

  const groups = useMemo(() => {
    if (!sources) {
      return {
        inProgress: [] as SourceListResponse[],
        pending: [] as SourceListResponse[],
        completed: [] as SourceListResponse[],
        failed: [] as SourceListResponse[],
      }
    }

    const result = {
      inProgress: [] as SourceListResponse[],
      pending: [] as SourceListResponse[],
      completed: [] as SourceListResponse[],
      failed: [] as SourceListResponse[],
    }

    for (const source of sources) {
      const group = getProcessingStatus(source)
      result[group].push(source)
    }

    // Sort completed by date descending (most recent first)
    result.completed.sort(
      (a, b) => new Date(b.updated).getTime() - new Date(a.updated).getTime()
    )

    return result
  }, [sources])

  const stats: ProcessingStats = useMemo(
    () => ({
      inProgress: groups.inProgress.length,
      pending: groups.pending.length,
      completed: groups.completed.length,
      failed: groups.failed.length,
      total: (sources || []).length,
    }),
    [groups, sources]
  )

  return {
    groups,
    stats,
    isLoading,
    refetch,
  }
}
