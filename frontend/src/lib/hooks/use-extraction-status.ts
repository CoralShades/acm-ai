'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { acmApi } from '@/lib/api/acm'
import { ACM_QUERY_KEYS } from './use-acm'
import { useToast } from './use-toast'
import type { ProgressToastController } from '@/lib/toast-patterns'

export type ExtractionPhase = 'idle' | 'extracting' | 'completed' | 'failed'

interface ExtractionStatus {
  phase: ExtractionPhase
  recordsCreated: number | undefined
  errorMessage: string | undefined
  startTracking: (commandId: string, options?: { showToast?: boolean; sourceName?: string }) => void
  dismiss: () => void
}

const SESSION_KEY_PREFIX = 'acm-extraction-'

export function useExtractionStatus(sourceId: string): ExtractionStatus {
  const queryClient = useQueryClient()
  const { createProgress } = useToast()
  const sessionKey = `${SESSION_KEY_PREFIX}${sourceId}`
  const toastControllerRef = useRef<ProgressToastController | null>(null)

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

  useEffect(() => {
    if (!jobStatus || phase !== 'extracting') return

    if (jobStatus.status === 'completed') {
      setPhase('completed')
      setRecordsCreated(jobStatus.result?.records_created)
      sessionStorage.removeItem(sessionKey)

      if (toastControllerRef.current) {
        toastControllerRef.current.complete(
          'Extraction complete',
          `${jobStatus.result?.records_created || 0} records extracted`
        )
        toastControllerRef.current = null
      }

      queryClient.invalidateQueries({
        queryKey: ['acm', 'records', sourceId],
      })
      queryClient.invalidateQueries({
        queryKey: ACM_QUERY_KEYS.stats(sourceId),
      })
    } else if (jobStatus.status === 'failed' || jobStatus.status === 'canceled') {
      const errMsg = jobStatus.result?.error_message || jobStatus.error_message || 'Extraction failed'
      setPhase('failed')
      setErrorMessage(errMsg)
      sessionStorage.removeItem(sessionKey)

      if (toastControllerRef.current) {
        toastControllerRef.current.fail('Extraction failed', errMsg)
        toastControllerRef.current = null
      }
    } else if (jobStatus.status === 'running' && toastControllerRef.current) {
      toastControllerRef.current.updateProgress(
        'Processing document...',
        'AI is analyzing the document'
      )
    }
  }, [jobStatus, phase, sourceId, sessionKey, queryClient])

  const startTracking = useCallback(
    (newCommandId: string, options?: { showToast?: boolean; sourceName?: string }) => {
      setCommandId(newCommandId)
      setPhase('extracting')
      setRecordsCreated(undefined)
      setErrorMessage(undefined)
      sessionStorage.setItem(sessionKey, newCommandId)

      if (options?.showToast) {
        toastControllerRef.current = createProgress(
          `Extracting ${options.sourceName || 'document'}...`,
          {
            description: 'AI is analyzing the document',
            persistent: true,
          }
        )
      }
    },
    [sessionKey, createProgress]
  )

  const dismiss = useCallback(() => {
    setPhase('idle')
    setCommandId(null)
    setRecordsCreated(undefined)
    setErrorMessage(undefined)
    sessionStorage.removeItem(sessionKey)

    if (toastControllerRef.current) {
      toastControllerRef.current.dismiss()
      toastControllerRef.current = null
    }
  }, [sessionKey])

  return { phase, recordsCreated, errorMessage, startTracking, dismiss }
}
