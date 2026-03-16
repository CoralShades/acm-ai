'use client'

import { CopilotKit } from '@copilotkit/react-core'
import { CopilotChat } from '@copilotkit/react-ui'
import { cn } from '@/lib/utils'
import { CrudToolRenderers } from './CrudToolRenderers'

interface JobCrudChatPanelProps {
  sourceId: string
  className?: string
}

/**
 * Inline CRUD chat panel for job detail context.
 */
export function JobCrudChatPanel({ sourceId, className }: JobCrudChatPanelProps) {
  return (
    <CopilotKit runtimeUrl="/copilot-crud">
      <div className={cn('flex h-full min-h-0 flex-col overflow-hidden', className)}>
        <CrudToolRenderers sourceId={sourceId} />
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
      </div>
    </CopilotKit>
  )
}
