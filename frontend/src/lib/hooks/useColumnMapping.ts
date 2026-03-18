'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { useV3SSE } from './useV3SSE'
import type {
  V3EventEnvelope,
  SchemaMappingReviewPayload,
  SchemaMappingResponse,
} from '@/lib/types/v3-streaming'

export interface ColumnMappingState {
  /** Whether the HITL dialog should be shown. */
  isOpen: boolean
  /** The mapping data from schema inference. */
  payload: SchemaMappingReviewPayload | null
  /** Whether a submission is in progress. */
  isSubmitting: boolean
  /** Error from the last submit attempt. */
  error: string | null
}

interface UseColumnMappingOptions {
  operationId: string
  enabled?: boolean
}

interface UseColumnMappingReturn extends ColumnMappingState {
  /** Submit the user's mapping decision. */
  submit: (response: SchemaMappingResponse) => Promise<void>
  /** Close the dialog without submitting (will auto-approve after timeout). */
  dismiss: () => void
}

export function useColumnMapping(
  options: UseColumnMappingOptions
): UseColumnMappingReturn {
  const { operationId, enabled = true } = options

  const [state, setState] = useState<ColumnMappingState>({
    isOpen: false,
    payload: null,
    isSubmitting: false,
    error: null,
  })

  const payloadRef = useRef<SchemaMappingReviewPayload | null>(null)

  const handleEvent = useCallback((event: V3EventEnvelope) => {
    if (event.type === 'hitl.schema_mapping_review') {
      const data = event.data as unknown as SchemaMappingReviewPayload
      payloadRef.current = data
      setState({
        isOpen: true,
        payload: data,
        isSubmitting: false,
        error: null,
      })
    }
    if (event.type === 'hitl.schema_mapping_resumed') {
      setState((prev) => ({ ...prev, isOpen: false, isSubmitting: false }))
    }
  }, [])

  // Subscribe to HITL SSE events
  useV3SSE({
    operationId,
    category: 'hitl',
    enabled,
    onEvent: handleEvent,
  })

  // Also check for pending HITL requests on mount (in case SSE event was missed)
  useEffect(() => {
    if (!enabled || !operationId) return

    const checkPending = async () => {
      try {
        const response = await fetch('/api/acm/hitl/pending')
        if (response.ok) {
          const pending = (await response.json()) as Array<{
            operation_id: string
            interrupt_data: SchemaMappingReviewPayload
          }>
          const match = pending.find((p) => p.operation_id === operationId)
          if (match && !payloadRef.current) {
            const data = match.interrupt_data as SchemaMappingReviewPayload
            payloadRef.current = data
            setState({
              isOpen: true,
              payload: data,
              isSubmitting: false,
              error: null,
            })
          }
        }
      } catch {
        // Silently ignore — SSE will deliver the event
      }
    }

    checkPending()
  }, [operationId, enabled])

  const submit = useCallback(
    async (response: SchemaMappingResponse) => {
      setState((prev) => ({ ...prev, isSubmitting: true, error: null }))
      try {
        const body: Record<string, unknown> = {
          operation_id: operationId,
          action: response.action,
        }
        if (response.mappings) {
          body.mappings = response.mappings
        }

        const res = await fetch('/api/acm/hitl/resume', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
        })

        if (!res.ok) {
          const detail = await res.text()
          throw new Error(`Failed to submit: ${detail}`)
        }

        setState((prev) => ({ ...prev, isOpen: false, isSubmitting: false }))
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error'
        setState((prev) => ({ ...prev, isSubmitting: false, error: message }))
      }
    },
    [operationId]
  )

  const dismiss = useCallback(() => {
    setState((prev) => ({ ...prev, isOpen: false }))
  }, [])

  return {
    ...state,
    submit,
    dismiss,
  }
}
