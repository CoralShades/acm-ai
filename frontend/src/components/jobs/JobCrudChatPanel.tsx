'use client'

import { useState, useCallback, useEffect } from 'react'
import { CopilotKit } from '@copilotkit/react-core'
import { CopilotChat } from '@copilotkit/react-ui'
import { useCoAgent } from '@copilotkit/react-core'
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

  const { setState } = useCoAgent<CRUDAgentState>({
    name: 'crud',
    initialState: {
      source_id: sourceId,
      model_id: null,
    },
  })

  const setChatModelId = useCallback(
    (modelId: string) => {
      setChatModelIdState(modelId)
      setState((prev: CRUDAgentState | undefined): CRUDAgentState => ({
        ...(prev ?? { source_id: sourceId, model_id: null }),
        model_id: modelId || null,
      }))
    },
    [setState, sourceId],
  )

  // Force source_id sync to backend on mount — initialState alone doesn't trigger sync
  useEffect(() => {
    setState((prev: CRUDAgentState | undefined): CRUDAgentState => ({
      ...(prev ?? { source_id: sourceId, model_id: null }),
      source_id: sourceId,
    }))
  }, [sourceId, setState])

  // Restore model from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('acm-crud-chat-model')
    if (saved) setChatModelId(saved)
  }, [setChatModelId])

  return (
    <>
      <CrudToolRenderers />
      <div className="px-4 py-1.5 border-b flex items-center gap-2">
        <ChatModelSelector
          value={chatModelId}
          onChange={setChatModelId}
          storageKey="acm-crud-chat-model"
        />
      </div>
      <CopilotChat
        className="h-full"
        labels={{
          title: 'ACM CRUD Assistant',
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
