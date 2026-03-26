'use client'

import { useCoAgent } from '@copilotkit/react-core'
import { useState, useCallback, useEffect, useMemo, useRef } from 'react'
import type { UnifiedAgentState } from '@/lib/types/unified-chat'

interface UseUnifiedChatOptions {
  sourceId?: string
  notebookId?: string
  hasAcmData?: boolean
  sessionId?: string
}

/**
 * useUnifiedChat — bridge between React and the unified CopilotKit agent.
 *
 * Replaces both useSmartChat (supervisor) and the inline useCoAgent in
 * JobCrudChatPanel (CRUD). Uses the stable useRef pattern to prevent
 * infinite re-renders from useCoAgent's unstable setState reference.
 */
export function useUnifiedChat({
  sourceId,
  notebookId,
  hasAcmData = false,
  sessionId,
}: UseUnifiedChatOptions) {
  const [includeAcmContext, setIncludeAcmContextState] = useState(hasAcmData)
  const [chatModelId, setChatModelIdState] = useState('')
  const didSyncRef = useRef(false)

  const defaultState = useMemo<UnifiedAgentState>(
    () => ({
      source_id: sourceId ?? null,
      notebook_id: notebookId ?? null,
      include_acm_context: hasAcmData,
      model_id: null,
      pending_operation: null,
      session_id: sessionId ?? null,
    }),
    [sourceId, notebookId, hasAcmData, sessionId]
  )

  const { state, setState } = useCoAgent<UnifiedAgentState>({
    name: 'acm_agent',
    initialState: defaultState,
  })

  // Stable ref to setState — CopilotKit returns a new reference each render.
  const setStateRef = useRef(setState)
  setStateRef.current = setState

  // Reset sync guard when scope changes
  useEffect(() => {
    didSyncRef.current = false
  }, [sourceId, notebookId, sessionId])

  // Force state sync to backend once on mount or scope change.
  useEffect(() => {
    if (didSyncRef.current) return
    didSyncRef.current = true
    setStateRef.current((prev: UnifiedAgentState | undefined): UnifiedAgentState => ({
      ...(prev ?? defaultState),
      source_id: sourceId ?? null,
      notebook_id: notebookId ?? null,
      session_id: sessionId ?? null,
    }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sourceId, notebookId, sessionId])

  const setIncludeAcmContext = useCallback(
    (value: boolean) => {
      setIncludeAcmContextState(value)
      setStateRef.current((prev: UnifiedAgentState | undefined): UnifiedAgentState => ({
        ...(prev ?? defaultState),
        include_acm_context: value,
      }))
    },
    [defaultState]
  )

  const setChatModelId = useCallback(
    (modelId: string) => {
      setChatModelIdState(modelId)
      setStateRef.current((prev: UnifiedAgentState | undefined): UnifiedAgentState => ({
        ...(prev ?? defaultState),
        model_id: modelId || null,
      }))
    },
    [defaultState]
  )

  const setScope = useCallback(
    (newSourceId?: string, newNotebookId?: string) => {
      setStateRef.current((prev: UnifiedAgentState | undefined): UnifiedAgentState => ({
        ...(prev ?? defaultState),
        source_id: newSourceId ?? null,
        notebook_id: newNotebookId ?? null,
      }))
    },
    [defaultState]
  )

  return {
    state,
    includeAcmContext,
    setIncludeAcmContext,
    chatModelId,
    setChatModelId,
    setScope,
  }
}
