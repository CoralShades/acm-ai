'use client'

import { useCoAgent } from '@copilotkit/react-core'
import { useState, useCallback, useEffect, useMemo, useRef } from 'react'
import type { SupervisorAgentState } from '@/lib/types/smart-chat'

interface UseSmartChatOptions {
  sourceId?: string
  notebookId?: string
  hasAcmData?: boolean
}

export function useSmartChat({
  sourceId,
  notebookId,
  hasAcmData = false,
}: UseSmartChatOptions) {
  const [includeAcmContext, setIncludeAcmContextState] = useState(hasAcmData)
  const [chatModelId, setChatModelIdState] = useState('')
  const didSyncRef = useRef(false)

  const defaultState = useMemo<SupervisorAgentState>(
    () => ({
      source_id: sourceId ?? null,
      notebook_id: notebookId ?? null,
      include_acm_context: hasAcmData,
      active_agents: [],
      acm_results: null,
      search_results: null,
      model_id: null,
    }),
    [sourceId, notebookId, hasAcmData]
  )

  const { state, setState } = useCoAgent<SupervisorAgentState>({
    name: 'supervisor',
    initialState: defaultState,
  })

  // Keep a stable ref to setState to avoid re-render loops.
  // CopilotKit's useCoAgent may return a new setState reference on each
  // render, which would cause useEffect to re-fire endlessly.
  const setStateRef = useRef(setState)
  setStateRef.current = setState

  // Reset sync guard when sourceId/notebookId changes
  useEffect(() => {
    didSyncRef.current = false
  }, [sourceId, notebookId])

  // Force state sync to backend once on mount (or when scope changes).
  // Uses ref guard to prevent re-render loop — useCoAgent's setState
  // may return a new reference that would cause deps to cycle.
  useEffect(() => {
    if (didSyncRef.current) return
    didSyncRef.current = true
    setStateRef.current((prev: SupervisorAgentState | undefined): SupervisorAgentState => ({
      ...(prev ?? defaultState),
      source_id: sourceId ?? null,
      notebook_id: notebookId ?? null,
    }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sourceId, notebookId])

  const setIncludeAcmContext = useCallback(
    (value: boolean) => {
      setIncludeAcmContextState(value)
      setStateRef.current((prev: SupervisorAgentState | undefined): SupervisorAgentState => ({
        ...(prev ?? defaultState),
        include_acm_context: value,
      }))
    },
    [defaultState]
  )

  const setChatModelId = useCallback(
    (modelId: string) => {
      setChatModelIdState(modelId)
      setStateRef.current((prev: SupervisorAgentState | undefined): SupervisorAgentState => ({
        ...(prev ?? defaultState),
        model_id: modelId || null,
      }))
    },
    [defaultState]
  )

  const setScope = useCallback(
    (newSourceId?: string, newNotebookId?: string) => {
      setStateRef.current((prev: SupervisorAgentState | undefined): SupervisorAgentState => ({
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
