'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { CopilotKit } from '@copilotkit/react-core'
import { CopilotChat } from '@copilotkit/react-ui'
import { useCoAgent, useCopilotReadable } from '@copilotkit/react-core'
import { cn } from '@/lib/utils'
import { CrudToolRenderers } from './CrudToolRenderers'
import { ChatModelSelector } from '@/components/chat/ChatModelSelector'

interface CRUDAgentState {
  source_id: string | null
  model_id: string | null
}

interface CrudChatContentProps {
  sourceId: string
}

function CrudChatContent({ sourceId }: CrudChatContentProps) {
  const [chatModelId, setChatModelIdState] = useState('')
  const didSyncRef = useRef(false)

  const { setState } = useCoAgent<CRUDAgentState>({
    name: 'crud',
    initialState: {
      source_id: sourceId,
      model_id: null,
    },
  })

  // Pass source_id as CopilotKit readable context — this ends up in
  // input.context on every request, independent of useCoAgent state sync.
  useCopilotReadable({
    description: 'Current job source ID for scoping all queries and writes',
    value: JSON.stringify({ source_id: sourceId }),
  })

  // Reset sync guard when sourceId changes so state re-syncs
  useEffect(() => {
    didSyncRef.current = false
  }, [sourceId])

  // Force source_id sync once on mount (or when sourceId changes) — use ref guard
  // to prevent re-render loop (useCoAgent's setState may return a new reference)
  useEffect(() => {
    if (didSyncRef.current) return
    didSyncRef.current = true
    setState((prev: CRUDAgentState | undefined): CRUDAgentState => ({
      ...(prev ?? { source_id: sourceId, model_id: null }),
      source_id: sourceId,
    }))
    // Restore model from localStorage
    const saved = localStorage.getItem('acm-crud-chat-model')
    if (saved) {
      setChatModelIdState(saved)
      setState((prev: CRUDAgentState | undefined): CRUDAgentState => ({
        ...(prev ?? { source_id: sourceId, model_id: null }),
        model_id: saved,
      }))
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sourceId])

  const setChatModelId = useCallback(
    (modelId: string) => {
      setChatModelIdState(modelId)
      setState((prev: CRUDAgentState | undefined): CRUDAgentState => ({
        ...(prev ?? { source_id: sourceId, model_id: null }),
        model_id: modelId || null,
      }))
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [sourceId],
  )

  return (
    <>
      <CrudToolRenderers />
      <div className="px-3 py-1.5 border-b flex items-center gap-2">
        <ChatModelSelector
          value={chatModelId}
          onChange={setChatModelId}
          storageKey="acm-crud-chat-model"
        />
      </div>
      <CopilotChat
        className="h-full"
        labels={{
          title: 'CRUD Assistant',
          initial:
            "Ask me to update, create, or delete ACM records for this job. I'll preview any changes before applying them.",
        }}
        makeSystemMessage={(contextString) =>
          `You are an ACM (Asbestos Containing Material) compliance data editor. ` +
          `Your role is to help users create, update, and delete ACM records through natural language. ` +
          `Current job source: ${sourceId}. ` +
          `IMPORTANT: Always preview write operations before executing them. ` +
          `The system will present an approval dialog for write operations. ` +
          `Never apply changes without explicit user approval.` +
          (contextString ? `\n\nAdditional context:\n${contextString}` : '')
        }
      />
    </>
  )
}

interface JobCrudChatPanelProps {
  sourceId: string
  className?: string
}

/**
 * Inline CRUD chat panel for job detail context.
 */
export function JobCrudChatPanel({ sourceId, className }: JobCrudChatPanelProps) {
  return (
    <CopilotKit runtimeUrl="/copilot-crud" showDevConsole={false}>
      <div className={cn('flex h-full min-h-0 flex-col overflow-hidden', className)}>
        <CrudChatContent sourceId={sourceId} />
      </div>
    </CopilotKit>
  )
}
