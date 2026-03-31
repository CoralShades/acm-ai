'use client'

import React, { useMemo, useEffect, useRef } from 'react'
import { CopilotChat } from '@copilotkit/react-ui'
import { useCopilotReadable, useLangGraphInterrupt } from '@copilotkit/react-core'
import { SmartChatProvider } from './SmartChatProvider'
import { useUnifiedChat } from '@/lib/hooks/useUnifiedChat'
import { UnifiedToolRenderers } from './UnifiedToolRenderers'
import { ACMAssistantMessage } from './ACMAssistantMessage'
import { SmartChatInput } from './SmartChatInput'
import { ChatModelSelector } from './ChatModelSelector'
import { SessionDropdown } from './SessionDropdown'
import { HITLApprovalCard } from './renderers/HITLApprovalCard'
import { useChatSessionStore } from '@/lib/stores/chatSessionStore'
import { cn } from '@/lib/utils'

interface UnifiedChatPanelProps {
  sourceId?: string
  notebookId?: string
  hasAcmData?: boolean
  sessionId?: string
  activeTab?: string
  className?: string
}

/**
 * UnifiedChatPanel — single chat panel combining read + write + HITL.
 *
 * Replaces both SmartChatPanel (supervisor read-only) and
 * JobCrudChatPanel (CRUD writes). Uses the unified backend at
 * /api/agui/chat with all 15 tools.
 */
class UnifiedChatErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false, error: null }
  }
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }
  componentDidCatch(error: Error) {
    console.warn('[UnifiedChatPanel] Error caught:', error.message)
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-full p-6 text-center text-muted-foreground">
          <p className="text-sm font-medium">Chat temporarily unavailable</p>
          <p className="text-xs mt-1 max-w-[300px] break-words">
            {this.state.error?.message || 'Connection error'}
          </p>
          <button
            type="button"
            onClick={() => this.setState({ hasError: false, error: null })}
            className="mt-3 text-xs text-primary underline"
          >
            Retry
          </button>
        </div>
      )
    }
    return this.props.children
  }
}

export function UnifiedChatPanel({
  sourceId,
  notebookId,
  hasAcmData = false,
  sessionId,
  activeTab,
  className,
}: UnifiedChatPanelProps) {
  return (
    <UnifiedChatErrorBoundary>
      <UnifiedChatPanelContent
        sourceId={sourceId}
        notebookId={notebookId}
        hasAcmData={hasAcmData}
        sessionId={sessionId}
        activeTab={activeTab}
        className={className}
      />
    </UnifiedChatErrorBoundary>
  )
}

function UnifiedChatPanelContent({
  sourceId,
  notebookId,
  hasAcmData = false,
  sessionId: sessionIdProp,
  activeTab,
  className,
}: UnifiedChatPanelProps) {
  const { activeSessionId, fetchSessions } = useChatSessionStore()

  // Fetch sessions when we have a sourceId, and auto-activate the most recent
  useEffect(() => {
    if (sourceId) {
      fetchSessions(sourceId)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sourceId])

  // Resolve effective session: store's active takes priority, then the prop
  const effectiveSessionId = activeSessionId ?? sessionIdProp

  const { state: agentState, includeAcmContext, setIncludeAcmContext, chatModelId, setChatModelId } =
    useUnifiedChat({
      sourceId,
      notebookId,
      hasAcmData,
      sessionId: effectiveSessionId ?? undefined,
    })

  // Option B: capture CopilotKit's auto-generated thread_id and store back
  // to SurrealDB session so future page loads can resume the same thread.
  const savedThreadRef = useRef<string | null>(null)
  useEffect(() => {
    const ckThreadId = agentState?.thread_id
    if (!ckThreadId || !sourceId || !effectiveSessionId) return
    if (savedThreadRef.current === ckThreadId) return
    savedThreadRef.current = ckThreadId
    // Fire-and-forget: persist CopilotKit's thread_id to the session record
    fetch(`/api/sources/${encodeURIComponent(sourceId)}/unified-sessions/${encodeURIComponent(effectiveSessionId)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ thread_id: ckThreadId }),
    }).catch(() => { /* non-critical */ })
  }, [agentState?.thread_id, sourceId, effectiveSessionId])

  const readableValue = useMemo(
    () => ({
      sourceId: sourceId || null,
      notebookId: notebookId || null,
      hasAcmData,
      acmContextEnabled: includeAcmContext,
    }),
    [sourceId, notebookId, hasAcmData, includeAcmContext]
  )

  useCopilotReadable({
    description:
      'Current page context: source ID, notebook ID, and ACM data availability',
    value: readableValue,
  })

  // Native interrupt-based HITL for write approvals.
  // When the backend's approval_node calls interrupt(), CopilotKit surfaces
  // the payload here. The user approves/rejects via the HITLApprovalCard,
  // and resolve() resumes the graph with Command(resume=...).
  useLangGraphInterrupt({
    enabled: ({ eventValue }: { eventValue: Record<string, unknown> }) =>
      eventValue?.type === 'write_approval',
    render: ({
      event,
      resolve,
    }: {
      event: { value: Record<string, unknown> }
      resolve: (value: string) => void
    }) => (
      <HITLApprovalCard
        payload={event.value as unknown as Parameters<typeof HITLApprovalCard>[0]['payload']}
        onApprove={(edits) =>
          resolve(JSON.stringify({ approved: true, edits }))
        }
        onReject={() => resolve(JSON.stringify({ approved: false }))}
      />
    ),
  })

  // Static quick-start suggestions — useCopilotChatSuggestions doesn't work with
  // custom AG-UI backends (copilotkitSuggest tool never injected into LangGraph).
  // Static suggestions are faster, free, and more reliable.
  const suggestions = useMemo(
    () =>
      hasAcmData
        ? [
            { title: 'Show ACM statistics summary', message: 'Give me a summary of ACM statistics for this document' },
            { title: 'List all buildings', message: 'What buildings are in this document?' },
            { title: 'Find high risk items', message: 'Show me all high risk ACM items' },
          ]
        : [
            { title: 'Summarize this document', message: 'Give me a summary of this document' },
            { title: 'Key findings', message: 'What are the key findings in this document?' },
          ],
    [hasAcmData]
  )

  return (
    <SmartChatProvider
      sourceId={sourceId}
      notebookId={notebookId}
      hasAcmData={hasAcmData}
      activeTab={activeTab}
    >
      <UnifiedToolRenderers />
      <div className={cn('flex flex-col h-full', className)}>
        {/* Header: session switcher + model selector */}
        <div className="px-4 py-1.5 border-b flex items-center gap-2">
          {sourceId && <SessionDropdown sourceId={sourceId} />}
          <ChatModelSelector
            value={chatModelId}
            onChange={setChatModelId}
            storageKey="acm-unified-chat-model"
          />
        </div>

        {/* Key on effectiveSessionId to force remount when switching sessions */}
        <div className="flex-1 min-h-0" key={effectiveSessionId || 'default'}>
          <CopilotChat
            className="h-full"
            suggestions={suggestions}
            labels={{
              title: 'ACM-AI Chat',
              initial: sourceId
                ? 'Ask about this document, query records, or make changes...'
                : 'Ask about your notebook sources...',
            }}
            AssistantMessage={ACMAssistantMessage}
            Input={(props) => (
              <SmartChatInput
                {...props}
                hasAcmData={hasAcmData}
                includeAcmContext={includeAcmContext}
                onAcmToggle={setIncludeAcmContext}
              />
            )}
          />
        </div>

        {/* ACM toggle is in SmartChatInput — no duplicate badge needed */}
      </div>
    </SmartChatProvider>
  )
}
