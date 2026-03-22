'use client'

import React, { useMemo, useEffect } from 'react'
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
import { TableProperties } from 'lucide-react'

interface UnifiedChatPanelProps {
  sourceId?: string
  notebookId?: string
  hasAcmData?: boolean
  sessionId?: string
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
  className,
}: UnifiedChatPanelProps) {
  return (
    <UnifiedChatErrorBoundary>
      <UnifiedChatPanelContent
        sourceId={sourceId}
        notebookId={notebookId}
        hasAcmData={hasAcmData}
        sessionId={sessionId}
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

  const { includeAcmContext, setIncludeAcmContext, chatModelId, setChatModelId } =
    useUnifiedChat({
      sourceId,
      notebookId,
      hasAcmData,
      sessionId: effectiveSessionId ?? undefined,
    })

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

  return (
    <SmartChatProvider
      sourceId={sourceId}
      notebookId={notebookId}
      hasAcmData={hasAcmData}
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
            makeSystemMessage={(contextString) =>
              `You are ACM-AI, an intelligent assistant for Asbestos Containing Material compliance data. ` +
              `You can both query and modify ACM records for the current job. ` +
              (sourceId ? `Current source: ${sourceId}. ` : '') +
              (notebookId ? `Current notebook: ${notebookId}. ` : '') +
              (includeAcmContext
                ? `ACM context is enabled - use ACM tools for structured data queries and modifications. `
                : `ACM context is disabled - focus on document content only. `) +
              (contextString ? `\n\nAdditional context:\n${contextString}` : '')
            }
          />
        </div>

        {/* ACM toggle badge */}
        {hasAcmData && (
          <div className="px-4 py-2 border-t flex items-center gap-2">
            <button
              type="button"
              onClick={() => setIncludeAcmContext(!includeAcmContext)}
              aria-label={`Toggle ACM data context: currently ${includeAcmContext ? 'on' : 'off'}`}
              className={cn(
                'inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
                includeAcmContext
                  ? 'border-transparent bg-primary text-primary-foreground hover:bg-primary/80'
                  : 'border-input bg-background text-foreground hover:bg-accent hover:text-accent-foreground'
              )}
            >
              <TableProperties className="h-3 w-3" />
              ACM Data {includeAcmContext ? 'ON' : 'OFF'}
            </button>
          </div>
        )}
      </div>
    </SmartChatProvider>
  )
}
