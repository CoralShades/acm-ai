'use client'

import { useCoAgent } from '@copilotkit/react-core'
import { useState, useCallback, useEffect, useMemo, useRef } from 'react'
import type { UnifiedAgentState } from '@/lib/types/unified-chat'
import { useChatSessionStore } from '@/lib/stores/chatSessionStore'

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
 *
 * Session/thread alignment:
 * - Option A: passes the session's thread_id from SurrealDB into agent state,
 *   so the backend can use it for LangGraph checkpointer persistence
 * - Option B: captures CopilotKit's auto-generated thread_id and stores it
 *   back to the SurrealDB session (handled in UnifiedChatPanel via state watch)
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

  // Option A: look up the session's thread_id from the store
  const sessions = useChatSessionStore((s) => s.sessions)
  const sessionThreadId = useMemo(() => {
    if (!sessionId) return null
    const session = sessions.find((s) => s.id === sessionId)
    return session?.thread_id ?? null
  }, [sessionId, sessions])

  const defaultState = useMemo<UnifiedAgentState>(
    () => ({
      source_id: sourceId ?? null,
      notebook_id: notebookId ?? null,
      include_acm_context: hasAcmData,
      model_id: null,
      pending_operation: null,
      session_id: sessionId ?? null,
      thread_id: sessionThreadId,
    }),
    [sourceId, notebookId, hasAcmData, sessionId, sessionThreadId]
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
  }, [sourceId, notebookId, sessionId, sessionThreadId])

  // Force state sync to backend once on mount or scope change.
  useEffect(() => {
    if (didSyncRef.current) return
    didSyncRef.current = true
    setStateRef.current((prev: UnifiedAgentState | undefined): UnifiedAgentState => ({
      ...(prev ?? defaultState),
      source_id: sourceId ?? null,
      notebook_id: notebookId ?? null,
      session_id: sessionId ?? null,
      thread_id: sessionThreadId,
    }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sourceId, notebookId, sessionId, sessionThreadId])

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
