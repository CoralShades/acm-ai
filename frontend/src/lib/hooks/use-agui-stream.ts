'use client'

import { useState, useEffect, useRef, useCallback } from 'react'

/**
 * AG-UI event types emitted by the backend AGUIEventEmitter.
 */
export interface AGUIEvent {
  type: string
  sequence: number
  timestamp: string
  [key: string]: unknown
}

interface AGUIStreamState {
  /** Current pipeline step name (from StepStarted/StepFinished) */
  currentStep: string | null
  /** Active tool call info (from ToolCallStart/ToolCallEnd) */
  activeToolCall: { name: string; id: string } | null
  /** Accumulated reasoning/thinking text (from ReasoningContent) */
  reasoningTokens: string
  /** Recent events for log display */
  events: AGUIEvent[]
  /** Whether the SSE connection is active */
  connected: boolean
}

const MAX_EVENTS = 100
const MAX_REASONING_CHARS = 5000

/**
 * Hook that connects to the AG-UI SSE endpoint for an extraction run.
 * Returns real-time step progress, tool call activity, and reasoning tokens.
 *
 * Story: E17-S3/S4 AG-UI Observability
 */
export function useAGUIStream(commandId: string | null): AGUIStreamState {
  const [currentStep, setCurrentStep] = useState<string | null>(null)
  const [activeToolCall, setActiveToolCall] = useState<{
    name: string
    id: string
  } | null>(null)
  const [reasoningTokens, setReasoningTokens] = useState('')
  const [events, setEvents] = useState<AGUIEvent[]>([])
  const [connected, setConnected] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)

  const handleEvent = useCallback((event: AGUIEvent) => {
    setEvents((prev) => [...prev.slice(-(MAX_EVENTS - 1)), event])

    switch (event.type) {
      case 'StepStarted':
        setCurrentStep(event.step_name as string)
        break
      case 'StepFinished':
        setCurrentStep(null)
        break
      case 'ToolCallStart':
        setActiveToolCall({
          name: event.tool_name as string,
          id: event.tool_call_id as string,
        })
        break
      case 'ToolCallEnd':
        setActiveToolCall(null)
        break
      case 'ReasoningContent':
        setReasoningTokens((prev) => {
          const next = prev + (event.delta as string)
          return next.length > MAX_REASONING_CHARS
            ? next.slice(-MAX_REASONING_CHARS)
            : next
        })
        break
      case 'RunFinished':
      case 'RunError':
        // Terminal — connection will close itself
        setCurrentStep(null)
        setActiveToolCall(null)
        break
    }
  }, [])

  useEffect(() => {
    if (!commandId) return

    const eventSource = new EventSource(
      `/api/agui/extraction/${commandId}/stream`
    )
    eventSourceRef.current = eventSource

    // Listen for all named event types from the backend
    const eventTypes = [
      'RunStarted',
      'StepStarted',
      'StepFinished',
      'StateDelta',
      'ToolCallStart',
      'ToolCallArgs',
      'ToolCallEnd',
      'ReasoningContent',
      'RunFinished',
      'RunError',
    ]

    for (const eventType of eventTypes) {
      eventSource.addEventListener(eventType, (e: MessageEvent) => {
        try {
          const data: AGUIEvent = JSON.parse(e.data)
          handleEvent(data)
        } catch {
          // Ignore malformed events
        }
      })
    }

    eventSource.addEventListener('done', () => {
      setConnected(false)
      eventSource.close()
    })

    eventSource.onopen = () => {
      setConnected(true)
    }

    eventSource.onerror = () => {
      // SSE will auto-reconnect, but mark disconnected
      setConnected(false)
      eventSource.close()
    }

    return () => {
      eventSource.close()
      eventSourceRef.current = null
      setConnected(false)
    }
  }, [commandId, handleEvent])

  return {
    currentStep,
    activeToolCall,
    reasoningTokens,
    events,
    connected,
  }
}
