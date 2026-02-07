'use client'

import { useState, useCallback, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { acmApi } from '@/lib/api/acm'
import { ACM_QUERY_KEYS } from './use-acm'

export type ExtractionPhase = 'idle' | 'extracting' | 'completed' | 'failed'

interface ExtractionStatus {
  phase: ExtractionPhase
  recordsCreated: number | undefined
  errorMessage: string | undefined
  startTracking: (commandId: string) => void
  dismiss: () => void
}

const SESSION_KEY_PREFIX = 'acm-extraction-'

export function useExtractionStatus(sourceId: string): ExtractionStatus {
  const queryClient = useQueryClient()
  const sessionKey = `${SESSION_KEY_PREFIX}${sourceId}`

  // Read initial commandId from sessionStorage (survives tab navigation)
  const [commandId, setCommandId] = useState<string | null>(() => {
    if (typeof window === 'undefined') return null
    return sessionStorage.getItem(sessionKey) || null
  })

  const [phase, setPhase] = useState<ExtractionPhase>(() => {
    if (typeof window === 'undefined') return 'idle'
    return sessionStorage.getItem(sessionKey) ? 'extracting' : 'idle'
  })

  const [recordsCreated, setRecordsCreated] = useState<number | undefined>(undefined)
  const [errorMessage, setErrorMessage] = useState<string | undefined>(undefined)

  // Poll job status while we have a commandId and phase is extracting
  const { data: jobStatus } = useQuery({
    queryKey: ['extraction-job', commandId],
    queryFn: () => acmApi.getJobStatus(commandId!),
    enabled: !!commandId && phase === 'extracting',
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data) return 3000
      if (data.status === 'new' || data.status === 'running') {
        return 3000
      }
      return false
    },
    staleTime: 0,
    retry: 2,
  })

  // React to job status changes
  useEffect(() => {
    if (!jobStatus || phase !== 'extracting') return

    if (jobStatus.status === 'completed') {
      setPhase('completed')
      setRecordsCreated(jobStatus.result?.records_created)
      sessionStorage.removeItem(sessionKey)

      // Invalidate ACM queries so grid refreshes
      queryClient.invalidateQueries({
        queryKey: ['acm', 'records', sourceId],
      })
      queryClient.invalidateQueries({
        queryKey: ACM_QUERY_KEYS.stats(sourceId),
      })
    } else if (jobStatus.status === 'failed' || jobStatus.status === 'canceled') {
      setPhase('failed')
      setErrorMessage(
        jobStatus.result?.error_message || jobStatus.error_message || 'Extraction failed'
      )
      sessionStorage.removeItem(sessionKey)
    }
  }, [jobStatus, phase, sourceId, sessionKey, queryClient])

  const startTracking = useCallback(
    (newCommandId: string) => {
      setCommandId(newCommandId)
      setPhase('extracting')
      setRecordsCreated(undefined)
      setErrorMessage(undefined)
      sessionStorage.setItem(sessionKey, newCommandId)
    },
    [sessionKey]
  )

  const dismiss = useCallback(() => {
    setPhase('idle')
    setCommandId(null)
    setRecordsCreated(undefined)
    setErrorMessage(undefined)
    sessionStorage.removeItem(sessionKey)
  }, [sessionKey])

  return { phase, recordsCreated, errorMessage, startTracking, dismiss }
}
