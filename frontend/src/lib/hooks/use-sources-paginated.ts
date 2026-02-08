'use client'

import { useState, useRef, useCallback, useEffect } from 'react'
import { sourcesApi } from '@/lib/api/sources'
import type { SourceListResponse } from '@/lib/types/api'

interface UseSourcesPaginatedParams {
  limit?: number
  sortBy?: 'created' | 'updated'
  sortOrder?: 'asc' | 'desc'
}

export function useSourcesPaginated({
  limit = 30,
  sortBy = 'updated',
  sortOrder = 'desc',
}: UseSourcesPaginatedParams = {}) {
  const [sources, setSources] = useState<SourceListResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const offsetRef = useRef(0)
  const hasMoreRef = useRef(true)
  const loadingMoreRef = useRef(false)

  const fetchMore = useCallback(
    async (reset = false) => {
      if (!reset && (loadingMoreRef.current || !hasMoreRef.current)) return

      if (reset) {
        setLoading(true)
        offsetRef.current = 0
        setSources([])
        hasMoreRef.current = true
      } else {
        loadingMoreRef.current = true
        setLoadingMore(true)
      }

      try {
        const data = await sourcesApi.list({
          limit,
          offset: offsetRef.current,
          sort_by: sortBy,
          sort_order: sortOrder,
        })

        if (reset) {
          setSources(data)
        } else {
          setSources((prev) => [...prev, ...data])
        }

        hasMoreRef.current = data.length === limit
        offsetRef.current += data.length
      } catch (error) {
        console.error('Failed to fetch sources:', error)
      } finally {
        setLoading(false)
        setLoadingMore(false)
        loadingMoreRef.current = false
      }
    },
    [limit, sortBy, sortOrder]
  )

  useEffect(() => {
    fetchMore(true)
  }, [fetchMore])

  return {
    sources,
    loading,
    loadingMore,
    fetchMore,
    hasMore: hasMoreRef.current,
  }
}
