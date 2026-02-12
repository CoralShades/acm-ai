'use client'

import { CopilotChat } from '@copilotkit/react-ui'
import { SmartChatProvider } from './SmartChatProvider'
import { useSmartChat } from '@/lib/hooks/useSmartChat'
import { ToolResultRenderers } from './ToolResultRenderers'
import { ACMAssistantMessage } from './ACMAssistantMessage'
import { SmartChatInput } from './SmartChatInput'
import { Badge } from '@/components/ui/badge'
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
            <Badge
              variant={includeAcmContext ? 'default' : 'outline'}
              className="cursor-pointer text-xs"
              onClick={() => setIncludeAcmContext(!includeAcmContext)}
            >
              <TableProperties className="h-3 w-3 mr-1" />
              ACM Data {includeAcmContext ? 'ON' : 'OFF'}
            </Badge>
          </div>
        )}
      </div>
    </SmartChatProvider>
  )
}
