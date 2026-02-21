'use client'

import { useState, useEffect, useRef } from 'react'
import apiClient from '@/lib/api/client'
import type { PipelineRunState, ExtractionProgressEvent } from '@/lib/types/pipeline'
import type { ExtractionPhase } from '@/lib/hooks/use-extraction-progress'

interface DocumentLogPanelState {
  pipelineState: PipelineRunState | null
  logEntries: string[]
  phase: ExtractionPhase
  isLoading: boolean
}

const POLLING_INTERVAL_MS = 3000

export function useDocumentLogPanel(
  commandId: string | undefined,
  isActive: boolean
): DocumentLogPanelState {
  const [pipelineState, setPipelineState] = useState<PipelineRunState | null>(null)
  const [logEntries, setLogEntries] = useState<string[]>([])
  const [phase, setPhase] = useState<ExtractionPhase>('idle')
  const [isLoading, setIsLoading] = useState(false)

  const eventSourceRef = useRef<EventSource | null>(null)
  const pollingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const isFallbackRef = useRef(false)

  // Fetch once from REST endpoint for completed/failed docs
  const fetchRestSnapshot = async (cmdId: string) => {
    try {
      const response = await apiClient.get<{
        status: string
        state: PipelineRunState
        log_entries: string[]
      }>(`/acm/extraction-progress/${cmdId}`)
      const data = response.data
      setPipelineState(data.state ?? null)
      setLogEntries(data.log_entries ?? [])

      const s = data.status
      if (s === 'completed' || s === 'partial') {
        setPhase('completed')
      } else if (s === 'failed') {
        setPhase('failed')
      } else {
        // Treat anything else as extracting when polling
        setPhase('extracting')
      }
    } catch (err) {
      console.error('[useDocumentLogPanel] REST fetch failed:', err)
    } finally {
      setIsLoading(false)
    }
  }

  // Start polling fallback every POLLING_INTERVAL_MS
  const startPolling = (cmdId: string) => {
    if (pollingTimerRef.current) return
    pollingTimerRef.current = setInterval(() => {
      fetchRestSnapshot(cmdId)
    }, POLLING_INTERVAL_MS)
  }

  const stopPolling = () => {
    if (pollingTimerRef.current) {
      clearInterval(pollingTimerRef.current)
      pollingTimerRef.current = null
    }
  }

  const closeSSE = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
  }

  useEffect(() => {
    if (!commandId) {
      // No commandId — reset to idle
      setPipelineState(null)
      setLogEntries([])
      setPhase('idle')
      setIsLoading(false)
      return
    }

    // Reset state when commandId changes
    setPipelineState(null)
    setLogEntries([])
    isFallbackRef.current = false
    setIsLoading(true)

    if (!isActive) {
      // Completed or failed doc — single REST fetch
      setPhase('completed') // provisional, will be overwritten by fetch
      fetchRestSnapshot(commandId)
      return
    }

    // Active doc — SSE stream
    setPhase('extracting')

    const eventSource = new EventSource(
      `/api/acm/extraction-progress/${commandId}/stream`
    )
    eventSourceRef.current = eventSource

    eventSource.onopen = () => {
      setIsLoading(false)
    }

    eventSource.onmessage = (event) => {
      setIsLoading(false)
      try {
        const data: ExtractionProgressEvent = JSON.parse(event.data)
        setPipelineState(data.state ?? null)
        setLogEntries(data.log_entries ?? [])

        const s = data.state?.status
        if (s === 'completed' || s === 'partial') {
          setPhase('completed')
          closeSSE()
          stopPolling()
        } else if (s === 'failed') {
          setPhase('failed')
          closeSSE()
          stopPolling()
        }
      } catch (err) {
        console.error('[useDocumentLogPanel] Failed to parse SSE message:', err)
      }
    }

    eventSource.onerror = () => {
      if (isFallbackRef.current) return
      console.warn('[useDocumentLogPanel] SSE error — falling back to polling')
      isFallbackRef.current = true
      closeSSE()
      // Do an immediate fetch then start interval
      fetchRestSnapshot(commandId)
      startPolling(commandId)
    }

    return () => {
      closeSSE()
      stopPolling()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [commandId, isActive])

  return { pipelineState, logEntries, phase, isLoading }
}
