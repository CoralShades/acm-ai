'use client'

import ReactMarkdown from 'react-markdown'
import {
  convertReferencesToCompactMarkdown,
  createCompactReferenceLinkComponent,
} from '@/lib/utils/source-references'
import { MessageActions } from '@/components/source/MessageActions'
import { useModalManager } from '@/lib/hooks/use-modal-manager'
import { useSmartChatScope } from './SmartChatProvider'
import { toast } from 'sonner'
import { Loader2 } from 'lucide-react'
import type { AssistantMessageProps } from '@copilotkit/react-ui'

/**
 * Detect if the message content looks like short "thinking" text
 * that shouldn't be rendered as a full message bubble.
 * Examples: "Let me search for that...", "I'll look up the records"
 */
function isThinkingContent(content: string): boolean {
  if (!content) return false
  const trimmed = content.trim()
  // Short messages that are still generating are likely intermediate thoughts
  if (trimmed.length > 200) return false
  // Check for common thinking patterns
  const thinkingPatterns = [
    /^(let me|i'll|i will|searching|looking|querying|checking|analyzing|loading|fetching|getting)/i,
    /^(one moment|just a moment|hold on|working on|processing)/i,
    /\.\.\.\s*$/,  // ends with ellipsis
  ]
  return thinkingPatterns.some((p) => p.test(trimmed))
}

export function ACMAssistantMessage({
  message,
  isLoading,
  isGenerating,
  isCurrentMessage,
}: AssistantMessageProps) {
  const { openModal } = useModalManager()
  const { notebookId } = useSmartChatScope()

  const handleReferenceClick = (type: string, id: string) => {
    const modalType =
      type === 'source_insight'
        ? 'insight'
        : (type as 'source' | 'note' | 'insight')
    try {
      openModal(modalType, id)
    } catch {
      const typeLabel = type === 'source_insight' ? 'insight' : type
      toast.error(`This ${typeLabel} could not be found`)
    }
  }

  const rawContent = message?.content ?? ''

  // Render tool call UI from useRenderToolCall registrations.
  // CopilotKit attaches tool renders as generativeUI on the message.
  // Without this, all useRenderToolCall results are silently dropped.
  const toolUI = message?.generativeUI?.() ?? null

  // Don't process references while still generating (partial refs like [source: are invalid)
  const content =
    isGenerating && isCurrentMessage
      ? rawContent
      : convertReferencesToCompactMarkdown(rawContent)

  const LinkComponent = createCompactReferenceLinkComponent(handleReferenceClick)

  // Show loading/thinking indicator when the agent is processing (no content yet)
  if (isLoading) {
    return (
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2 py-1.5 text-muted-foreground">
          <Loader2 className="h-3.5 w-3.5 animate-spin text-primary/60" />
          <span className="text-xs">Thinking...</span>
        </div>
        {toolUI}
      </div>
    )
  }

  // Compact thinking indicator for short intermediate messages while still generating
  if (isGenerating && isCurrentMessage && isThinkingContent(rawContent)) {
    return (
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2 py-1.5 text-muted-foreground">
          <Loader2 className="h-3.5 w-3.5 animate-spin text-primary/60" />
          <span className="text-xs">{rawContent.trim().replace(/\.{3,}$/, '...')}</span>
        </div>
        {toolUI}
      </div>
    )
  }

  // Tool-only message (no text content) — render just the tool UI
  if (!rawContent.trim() && !isGenerating) {
    return toolUI ? <div className="my-1">{toolUI}</div> : null
  }

  return (
    <div className="flex flex-col gap-2">
      {/* Tool call renders (from useRenderToolCall) — shown before text content */}
      {toolUI}
      <div className="prose prose-sm prose-neutral dark:prose-invert max-w-none break-words prose-headings:font-semibold prose-a:text-blue-600 prose-a:break-all prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-p:mb-4 prose-p:leading-7 prose-li:mb-2">
        <ReactMarkdown
          components={{
            a: LinkComponent,
            p: ({ children }) => <p className="mb-4">{children}</p>,
            h1: ({ children }) => <h1 className="mb-4 mt-6">{children}</h1>,
            h2: ({ children }) => <h2 className="mb-3 mt-5">{children}</h2>,
            h3: ({ children }) => <h3 className="mb-3 mt-4">{children}</h3>,
            li: ({ children }) => <li className="mb-1">{children}</li>,
            ul: ({ children }) => (
              <ul className="mb-4 space-y-1">{children}</ul>
            ),
            ol: ({ children }) => (
              <ol className="mb-4 space-y-1">{children}</ol>
            ),
          }}
        >
          {content}
        </ReactMarkdown>
        {/* Streaming cursor — visible while tokens are arriving */}
        {isGenerating && isCurrentMessage && (
          <span
            aria-hidden="true"
            className="inline-block w-0.5 h-4 bg-primary/70 align-text-bottom ml-0.5 animate-pulse"
          />
        )}
      </div>
      {!isLoading && !isGenerating && (
        <MessageActions content={rawContent} notebookId={notebookId} />
      )}
    </div>
  )
}
