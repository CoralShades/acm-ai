'use client'

import { useCoAgent } from '@copilotkit/react-core'
import { useState, useCallback, useMemo } from 'react'
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

  const defaultState = useMemo<SupervisorAgentState>(
    () => ({
      source_id: sourceId ?? null,
      notebook_id: notebookId ?? null,
      include_acm_context: hasAcmData,
      active_agents: [],
      acm_results: null,
      search_results: null,
    }),
    [sourceId, notebookId, hasAcmData]
  )

  const { state, setState } = useCoAgent<SupervisorAgentState>({
    name: 'supervisor',
    initialState: defaultState,
  })

  const setIncludeAcmContext = useCallback(
    (value: boolean) => {
      setIncludeAcmContextState(value)
      setState((prev: SupervisorAgentState | undefined): SupervisorAgentState => ({
        ...(prev ?? defaultState),
        include_acm_context: value,
      }))
    },
    [setState, defaultState]
  )

  const setScope = useCallback(
    (newSourceId?: string, newNotebookId?: string) => {
      setState((prev: SupervisorAgentState | undefined): SupervisorAgentState => ({
        ...(prev ?? defaultState),
        source_id: newSourceId ?? null,
        notebook_id: newNotebookId ?? null,
      }))
    },
    [setState, defaultState]
  )

  return {
    state,
    includeAcmContext,
    setIncludeAcmContext,
    setScope,
  }
}
