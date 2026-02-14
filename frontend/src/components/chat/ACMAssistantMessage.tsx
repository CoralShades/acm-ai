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
import type { AssistantMessageProps } from '@copilotkit/react-ui'

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

  // Don't process references while still generating (partial refs like [source: are invalid)
  const content =
    isGenerating && isCurrentMessage
      ? rawContent
      : convertReferencesToCompactMarkdown(rawContent)

  const LinkComponent = createCompactReferenceLinkComponent(handleReferenceClick)

  return (
    <div className="flex flex-col gap-2">
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
      </div>
      {!isLoading && !isGenerating && (
        <MessageActions content={rawContent} notebookId={notebookId} />
      )}
    </div>
  )
}
