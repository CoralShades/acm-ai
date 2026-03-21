'use client'

import React, { useMemo } from 'react'
import { CopilotChat } from '@copilotkit/react-ui'
import { useCopilotReadable } from '@copilotkit/react-core'
import { SmartChatProvider } from './SmartChatProvider'
import { useSmartChat } from '@/lib/hooks/useSmartChat'
import { ToolResultRenderers } from './ToolResultRenderers'
import { ACMAssistantMessage } from './ACMAssistantMessage'
import { SmartChatInput } from './SmartChatInput'
import { ChatModelSelector } from './ChatModelSelector'
import { cn } from '@/lib/utils'
import { TableProperties } from 'lucide-react'

interface SmartChatPanelProps {
  sourceId?: string
  notebookId?: string
  hasAcmData?: boolean
}

/**
 * SmartChatPanel — supervisor chat with its own CopilotKit provider.
 *
 * CopilotKit is mounted lazily here (not in the layout) so the AG-UI
 * connection only starts when the user actually opens the chat panel.
 * This prevents AG-UI errors from blocking page loads.
 */
class SmartChatErrorBoundary extends React.Component<
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
  componentDidCatch(error: Error, info: React.ErrorInfo) {
    console.warn('[SmartChatPanel] CopilotKit error caught:', error.message, error.stack?.substring(0, 500))
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-full p-6 text-center text-muted-foreground">
          <p className="text-sm font-medium">Chat temporarily unavailable</p>
          <p className="text-xs mt-1 max-w-[300px] break-words">{this.state.error?.message || 'Connection error'}</p>
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

export function SmartChatPanel({
  sourceId,
  notebookId,
  hasAcmData = false,
}: SmartChatPanelProps) {
  return (
    <SmartChatErrorBoundary>
      <SmartChatPanelContent
        sourceId={sourceId}
        notebookId={notebookId}
        hasAcmData={hasAcmData}
      />
    </SmartChatErrorBoundary>
  )
}

function SmartChatPanelContent({
  sourceId,
  notebookId,
  hasAcmData = false,
}: SmartChatPanelProps) {
  const { includeAcmContext, setIncludeAcmContext, chatModelId, setChatModelId } = useSmartChat({
    sourceId,
    notebookId,
    hasAcmData,
  })

  // Memoize the readable value to prevent infinite re-render loops.
  // CopilotKit internally compares the value reference — a new object
  // on every render triggers updates that cause more renders.
  const readableValue = useMemo(() => ({
    sourceId: sourceId || null,
    notebookId: notebookId || null,
    hasAcmData,
    acmContextEnabled: includeAcmContext,
  }), [sourceId, notebookId, hasAcmData, includeAcmContext])

  useCopilotReadable({
    description: 'Current page context: source ID, notebook ID, and ACM data availability',
    value: readableValue,
  })

  return (
    <SmartChatProvider
      sourceId={sourceId}
      notebookId={notebookId}
      hasAcmData={hasAcmData}
    >
      <ToolResultRenderers />
      <div className="flex flex-col h-full">
        {/* Model selector header */}
        <div className="px-4 py-1.5 border-b flex items-center gap-2">
          <ChatModelSelector
            value={chatModelId}
            onChange={setChatModelId}
            storageKey="acm-smart-chat-model"
          />
        </div>

        <div className="flex-1 min-h-0">
          <CopilotChat
            className="h-full"
            labels={{
              title: 'Smart Chat',
              initial: sourceId
                ? 'Ask about this document or its ACM data...'
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
              `You are an ACM (Asbestos Containing Material) compliance assistant. ` +
              `Help users query and understand asbestos register data, building surveys, and compliance requirements. ` +
              (sourceId ? `Current source: ${sourceId}. ` : '') +
              (notebookId ? `Current notebook: ${notebookId}. ` : '') +
              (includeAcmContext
                ? `ACM context is enabled - use ACM tools for structured data queries. `
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
