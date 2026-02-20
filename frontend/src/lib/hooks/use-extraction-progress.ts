'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { acmApi } from '@/lib/api/acm'
import { ACM_QUERY_KEYS } from './use-acm'
import { useToast } from './use-toast'
import type { ProgressToastController } from '@/lib/toast-patterns'
import type { PipelineRunState, ExtractionProgressEvent } from '@/lib/types/pipeline'

export type ExtractionPhase = 'idle' | 'extracting' | 'completed' | 'failed'

interface ExtractionProgress {
  phase: ExtractionPhase
  pipelineState: PipelineRunState | null
  logEntries: string[]
  recordsCreated: number | undefined
  errorMessage: string | undefined
  startTracking: (commandId: string, options?: { showToast?: boolean; sourceName?: string }) => void
  dismiss: () => void
}

const SESSION_KEY_PREFIX = 'acm-extraction-progress-'
const SSE_TIMEOUT_MS = 3000

export function useExtractionProgress(sourceId: string): ExtractionProgress {
  const queryClient = useQueryClient()
  const { createProgress } = useToast()
  const sessionKey = `${SESSION_KEY_PREFIX}${sourceId}`
  const toastControllerRef = useRef<ProgressToastController | null>(null)
  const eventSourceRef = useRef<EventSource | null>(null)
  const sseTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const fallbackToPollingRef = useRef(false)

  // Restore state from sessionStorage
  const [commandId, setCommandId] = useState<string | null>(() => {
    if (typeof window === 'undefined') return null
    const stored = sessionStorage.getItem(sessionKey)
    return stored ? JSON.parse(stored).commandId : null
  })

  const [phase, setPhase] = useState<ExtractionPhase>(() => {
    if (typeof window === 'undefined') return 'idle'
    const stored = sessionStorage.getItem(sessionKey)
    return stored ? JSON.parse(stored).phase : 'idle'
  })

  const [pipelineState, setPipelineState] = useState<PipelineRunState | null>(() => {
    if (typeof window === 'undefined') return null
    const stored = sessionStorage.getItem(sessionKey)
    return stored ? JSON.parse(stored).pipelineState : null
  })

  const [logEntries, setLogEntries] = useState<string[]>(() => {
    if (typeof window === 'undefined') return []
    const stored = sessionStorage.getItem(sessionKey)
    return stored ? JSON.parse(stored).logEntries : []
  })

  const [recordsCreated, setRecordsCreated] = useState<number | undefined>(undefined)
  const [errorMessage, setErrorMessage] = useState<string | undefined>(undefined)

  // Enhanced polling using getJobStatus (fallback when SSE fails)
  const { data: jobStatus } = useQuery({
    queryKey: ['extraction-job', commandId],
    queryFn: () => acmApi.getJobStatus(commandId!),
    enabled: !!commandId && phase === 'extracting' && fallbackToPollingRef.current,
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

  // Handle SSE connection
  useEffect(() => {
    if (!commandId || phase !== 'extracting' || fallbackToPollingRef.current) {
      return
    }

    // Set timeout to fallback to polling if SSE doesn't connect
    sseTimeoutRef.current = setTimeout(() => {
      console.log('[ExtractionProgress] SSE timeout, falling back to polling')
      fallbackToPollingRef.current = true
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
    }, SSE_TIMEOUT_MS)

    // Create SSE connection
    const eventSource = new EventSource(`/api/acm/extraction-progress/${commandId}/stream`)
    eventSourceRef.current = eventSource

    eventSource.onmessage = (event) => {
      // Clear timeout on first message
      if (sseTimeoutRef.current) {
        clearTimeout(sseTimeoutRef.current)
        sseTimeoutRef.current = null
      }

      try {
        const data: ExtractionProgressEvent = JSON.parse(event.data)

        // Update state
        setPipelineState(data.state)
        setLogEntries(data.log_entries || [])

        // Persist to sessionStorage
        sessionStorage.setItem(
          sessionKey,
          JSON.stringify({
            commandId,
            phase: 'extracting',
            pipelineState: data.state,
            logEntries: data.log_entries || [],
          })
        )

        // Update toast with stage progress
        if (toastControllerRef.current && data.state.status === 'running') {
          const runningStage = Object.values(data.state.stages).find(
            (stage) => stage.status === 'running'
          )
          if (runningStage) {
            toastControllerRef.current.updateProgress(
              `Processing: ${runningStage.id}`,
              runningStage.message || 'AI is analyzing the document'
            )
          }
        }

        // Handle completion
        if (data.state.status === 'completed' || data.state.status === 'partial') {
          setPhase('completed')
          setRecordsCreated(data.state.total_records)
          sessionStorage.removeItem(sessionKey)

          if (toastControllerRef.current) {
            toastControllerRef.current.complete(
              'Extraction complete',
              `${data.state.total_records} records extracted`
            )
            toastControllerRef.current = null
          }

          // Invalidate queries
          queryClient.invalidateQueries({
            queryKey: ['acm', 'records', sourceId],
          })
          queryClient.invalidateQueries({
            queryKey: ACM_QUERY_KEYS.stats(sourceId),
          })

          // Close SSE
          eventSource.close()
        } else if (data.state.status === 'failed') {
          const failedStage = Object.values(data.state.stages).find(
            (stage) => stage.status === 'failed'
          )
          const errMsg = failedStage?.error?.message || 'Extraction failed'

          setPhase('failed')
          setErrorMessage(errMsg)
          sessionStorage.removeItem(sessionKey)

          if (toastControllerRef.current) {
            toastControllerRef.current.fail('Extraction failed', errMsg)
            toastControllerRef.current = null
          }

          // Close SSE
          eventSource.close()
        }
      } catch (error) {
        console.error('[ExtractionProgress] Failed to parse SSE message:', error)
      }
    }

    eventSource.onerror = () => {
      console.error('[ExtractionProgress] SSE connection error, falling back to polling')
      fallbackToPollingRef.current = true
      eventSource.close()
    }

    return () => {
      if (sseTimeoutRef.current) {
        clearTimeout(sseTimeoutRef.current)
      }
      eventSource.close()
    }
  }, [commandId, phase, sourceId, sessionKey, queryClient])

  // Handle polling fallback
  useEffect(() => {
    if (!jobStatus || phase !== 'extracting' || !fallbackToPollingRef.current) return

    // Extract progress state from job result
    if (jobStatus.progress?.state) {
      setPipelineState(jobStatus.progress.state)

      // Persist to sessionStorage
      sessionStorage.setItem(
        sessionKey,
        JSON.stringify({
          commandId,
          phase: 'extracting',
          pipelineState: jobStatus.progress.state,
          logEntries: logEntries,
        })
      )
    }

    if (jobStatus.status === 'completed') {
      const state = jobStatus.progress?.state
      setPhase('completed')
      setRecordsCreated(state?.total_records || jobStatus.result?.records_created)
      sessionStorage.removeItem(sessionKey)

      if (toastControllerRef.current) {
        toastControllerRef.current.complete(
          'Extraction complete',
          `${state?.total_records || jobStatus.result?.records_created || 0} records extracted`
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
      const state = jobStatus.progress?.state
      if (state) {
        const runningStage = Object.values(state.stages).find(
          (stage) => stage.status === 'running'
        )
        if (runningStage) {
          toastControllerRef.current.updateProgress(
            `Processing: ${runningStage.id}`,
            runningStage.message || 'AI is analyzing the document'
          )
        }
      }
    }
  }, [jobStatus, phase, sourceId, sessionKey, queryClient, commandId, logEntries])

  const startTracking = useCallback(
    (newCommandId: string, options?: { showToast?: boolean; sourceName?: string }) => {
      setCommandId(newCommandId)
      setPhase('extracting')
      setPipelineState(null)
      setLogEntries([])
      setRecordsCreated(undefined)
      setErrorMessage(undefined)
      fallbackToPollingRef.current = false

      sessionStorage.setItem(
        sessionKey,
        JSON.stringify({
          commandId: newCommandId,
          phase: 'extracting',
          pipelineState: null,
          logEntries: [],
        })
      )

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
    setPipelineState(null)
    setLogEntries([])
    setRecordsCreated(undefined)
    setErrorMessage(undefined)
    sessionStorage.removeItem(sessionKey)

    if (toastControllerRef.current) {
      toastControllerRef.current.dismiss()
      toastControllerRef.current = null
    }

    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
  }, [sessionKey])

  return {
    phase,
    pipelineState,
    logEntries,
    recordsCreated,
    errorMessage,
    startTracking,
    dismiss,
  }
}
