'use client'

import { CopilotChat } from '@copilotkit/react-ui'
import { useCopilotReadable, useCopilotChatSuggestions, useCoAgentStateRender } from '@copilotkit/react-core'
import { SmartChatProvider } from './SmartChatProvider'
import { useSmartChat } from '@/lib/hooks/useSmartChat'
import { ToolResultRenderers } from './ToolResultRenderers'
import { ACMAssistantMessage } from './ACMAssistantMessage'
import { SmartChatInput } from './SmartChatInput'
import { cn } from '@/lib/utils'
import { TableProperties } from 'lucide-react'

interface SmartChatPanelProps {
  sourceId?: string
  notebookId?: string
  hasAcmData?: boolean
}

export function SmartChatPanel({
  sourceId,
  notebookId,
  hasAcmData = false,
}: SmartChatPanelProps) {
  const { includeAcmContext, setIncludeAcmContext } = useSmartChat({
    sourceId,
    notebookId,
    hasAcmData,
  })

  // Expose page-level context to the LLM as structured data.
  // This supplements the system message with machine-readable context
  // that the agent can reference in tool calls and responses.
  useCopilotReadable({
    description: 'Current page context: source ID, notebook ID, and ACM data availability',
    value: {
      sourceId: sourceId || null,
      notebookId: notebookId || null,
      hasAcmData,
      acmContextEnabled: includeAcmContext,
    },
  })

  // Domain-aware chat suggestions to guide users toward useful queries.
  useCopilotChatSuggestions(
    {
      instructions: hasAcmData && includeAcmContext
        ? 'Suggest 2-3 ACM compliance queries relevant to this document. Examples: risk summaries, building searches, material lookups, statistics.'
        : 'Suggest 2-3 general document queries. Examples: summarize content, find specific sections, explain terminology.',
      maxSuggestions: 3,
    },
    [hasAcmData, includeAcmContext],
  )

  // Show a lightweight in-chat indicator while the supervisor agent is running
  useCoAgentStateRender({
    name: 'supervisor',
    render: ({ nodeName, status }) => {
      if (status !== 'inProgress') return null
      return (
        <div className="text-xs text-muted-foreground italic px-4 py-1 flex items-center gap-2">
          <span className="inline-block h-2 w-2 bg-primary rounded-full animate-pulse" />
          {nodeName === 'tools'
            ? 'Searching...'
            : 'Thinking...'}
        </div>
      )
    },
  })

  return (
    <SmartChatProvider
      sourceId={sourceId}
      notebookId={notebookId}
      hasAcmData={hasAcmData}
    >
      <ToolResultRenderers />
      <div className="flex flex-col h-full">
        {/* ACM context indicator */}
        {hasAcmData && includeAcmContext && (
          <div className="px-4 py-2 bg-primary/10 text-primary text-xs flex items-center gap-2 border-b">
            <TableProperties className="h-3 w-3" />
            ACM Register data included in context
          </div>
        )}

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
