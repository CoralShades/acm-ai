'use client'

import { useEffect, useRef, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useStreamingStore } from '@/lib/stores/streamingStore'
import type { V3EventEnvelope, V3EventCategory } from '@/lib/types/v3-streaming'

interface UseV3SSEOptions {
  operationId: string
  category: V3EventCategory
  enabled?: boolean
  onEvent?: (event: V3EventEnvelope) => void
  invalidateQueryKeys?: unknown[][]
}

const TERMINAL_EVENT_TYPES = new Set([
  'extraction.consensus_complete',
  'extraction.complete',
  'extraction.failed',
  'ai.save_complete',
  'bulk.complete',
  'hitl.schema_mapping_resumed',
])

const RETRY_DELAYS_MS = [1000, 2000, 4000, 8000, 16000]
const MAX_RETRIES = 5
const RETRY_DELAY_CAP_MS = 30000

export function useV3SSE(options: UseV3SSEOptions): {
  status: string
  lastEventType: string | null
  eventCount: number
  disconnect: () => void
} {
  const { operationId, category, enabled = true, onEvent, invalidateQueryKeys } = options

  const queryClient = useQueryClient()
  const { registerStream, updateStream, removeStream, activeStreams } = useStreamingStore()

  const eventSourceRef = useRef<EventSource | null>(null)
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const retryCountRef = useRef(0)
  const isUnmountedRef = useRef(false)
  const eventCountRef = useRef(0)

  const streamState = activeStreams.get(operationId)

  const cancelReconnect = useCallback(() => {
    if (reconnectTimerRef.current !== null) {
      clearTimeout(reconnectTimerRef.current)
      reconnectTimerRef.current = null
    }
  }, [])

  const closeEventSource = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
  }, [])

  const connect = useCallback(() => {
    if (isUnmountedRef.current) return

    const url = `/api/v3/stream/${category}/${operationId}`
    const es = new EventSource(url)
    eventSourceRef.current = es

    es.onmessage = (event: MessageEvent) => {
      if (isUnmountedRef.current) return

      // Reset retry counter on first successful message
      retryCountRef.current = 0

      try {
        const envelope: V3EventEnvelope = JSON.parse(event.data as string)

        eventCountRef.current += 1
        updateStream(operationId, {
          status: 'connected',
          lastEventType: envelope.type,
          lastEventTimestamp: envelope.timestamp,
          eventCount: eventCountRef.current,
          retryCount: 0,
        })

        onEvent?.(envelope)

        if (TERMINAL_EVENT_TYPES.has(envelope.type)) {
          for (const queryKey of invalidateQueryKeys ?? []) {
            queryClient.invalidateQueries({ queryKey })
          }
          updateStream(operationId, { status: 'done' })
          closeEventSource()
        }
      } catch {
        // Malformed JSON — ignore and continue
      }
    }

    // Handle named 'done' event from server
    es.addEventListener('done', () => {
      if (isUnmountedRef.current) return
      updateStream(operationId, { status: 'done' })
      closeEventSource()
    })

    // Handle named 'error' event from server (not the onerror callback)
    es.addEventListener('error', (event: Event) => {
      if (isUnmountedRef.current) return
      // Only treat as server-sent error event when the EventSource is OPEN
      // (i.e., the server explicitly sent event: error, not a network error)
      if (es.readyState === EventSource.OPEN) {
        try {
          const msgEvent = event as MessageEvent
          const parsed = JSON.parse(msgEvent.data as string) as { message?: string }
          console.error('[useV3SSE] Server error event:', parsed.message)
        } catch {
          // ignore parse error
        }
        updateStream(operationId, { status: 'error' })
        closeEventSource()
      }
    })

    es.onerror = () => {
      if (isUnmountedRef.current) return
      // Network-level connection error — attempt reconnect
      closeEventSource()

      const currentRetry = retryCountRef.current
      if (currentRetry >= MAX_RETRIES) {
        updateStream(operationId, { status: 'error', retryCount: currentRetry })
        return
      }

      const delayMs = Math.min(
        RETRY_DELAYS_MS[currentRetry] ?? RETRY_DELAYS_MS[RETRY_DELAYS_MS.length - 1],
        RETRY_DELAY_CAP_MS
      )
      retryCountRef.current = currentRetry + 1
      updateStream(operationId, {
        status: 'reconnecting',
        retryCount: retryCountRef.current,
      })

      reconnectTimerRef.current = setTimeout(() => {
        reconnectTimerRef.current = null
        connect()
      }, delayMs)
    }
  }, [
    operationId,
    category,
    onEvent,
    invalidateQueryKeys,
    queryClient,
    updateStream,
    closeEventSource,
  ])

  const disconnect = useCallback(() => {
    cancelReconnect()
    closeEventSource()
    eventCountRef.current = 0
    updateStream(operationId, { status: 'done' })
  }, [cancelReconnect, closeEventSource, updateStream, operationId])

  useEffect(() => {
    if (!enabled) return

    isUnmountedRef.current = false
    retryCountRef.current = 0
    eventCountRef.current = 0
    registerStream(operationId, category)
    connect()

    return () => {
      isUnmountedRef.current = true
      cancelReconnect()
      closeEventSource()
      removeStream(operationId)
    }
    // connect is stable across renders for the same operationId/category; listing
    // it would cause infinite reconnects when streamState.eventCount changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [operationId, category, enabled])

  return {
    status: streamState?.status ?? 'connecting',
    lastEventType: streamState?.lastEventType ?? null,
    eventCount: streamState?.eventCount ?? 0,
    disconnect,
  }
}
