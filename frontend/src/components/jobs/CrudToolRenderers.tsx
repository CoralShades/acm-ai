'use client'

import React from 'react'
import {
  useRenderToolCall,
  useDefaultTool,
  useCopilotChat,
} from '@copilotkit/react-core'
import { TextMessage, Role } from '@copilotkit/runtime-client-gql'
import { AgentActivityIndicator } from '@/components/chat/renderers/AgentActivityIndicator'
import { HITLApprovalDialog } from '@/components/chat/renderers/HITLApprovalDialog'
import { ToolErrorCard } from '@/components/chat/renderers/ToolErrorCard'
import { isErrorResult } from '@/lib/utils/tool-result'

/**
 * Parse a value that may be a JSON string or an already-parsed object.
 */
function parseJsonSafe(val: unknown): Record<string, unknown> | null {
  if (!val) return null
  if (typeof val === 'object') return val as Record<string, unknown>
  if (typeof val === 'string') {
    try {
      const parsed = JSON.parse(val)
      return typeof parsed === 'object' ? parsed : null
    } catch {
      return null
    }
  }
  return null
}

/**
 * Registers CopilotKit tool-call renderers for CRUD operations.
 *
 * Uses preview_write tool renderer to render approval UI from the tool result
 * and sends the decision as a chat message.
 *
 * Must be rendered inside a CopilotKit provider configured with /copilot-crud.
 */
export function CrudToolRenderers() {
  const { appendMessage } = useCopilotChat()

  // Render query_job_records results
  useRenderToolCall({
    name: 'query_job_records',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') {
        return <AgentActivityIndicator tool="query_job_records" status="executing" />
      }
      if (isErrorResult(result)) return <ToolErrorCard tool="query_job_records" />
      if (!result) return <></>
      return (
        <div className="border rounded-lg p-3 my-2 text-sm bg-background">
          <div className="text-xs text-muted-foreground mb-1">Query Results</div>
          <pre className="text-xs whitespace-pre-wrap overflow-auto max-h-60 leading-relaxed">
            {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )
    },
  })

  // Render preview_write — show approval dialog from tool result as fallback
  useRenderToolCall({
    name: 'preview_write',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') {
        return <AgentActivityIndicator tool="preview_write" status="executing" />
      }
      if (isErrorResult(result)) return <ToolErrorCard tool="preview_write" />
      if (!result) return <></>

      // Parse the preview_write result
      const parsed = parseJsonSafe(result)
      if (!parsed || parsed.type !== 'preview_write') return <></>

      return (
        <HITLApprovalDialog
          preview={parsed as never}
          onApprove={(edits) => {
            const opId = parsed.operation_id as string
            const editStr = edits ? ` with edits: ${JSON.stringify(edits)}` : ''
            appendMessage(
              new TextMessage({
                role: Role.User,
                content: `Approved. Execute operation #${opId}${editStr}`,
              })
            )
          }}
          onReject={() => {
            const opId = parsed.operation_id as string
            appendMessage(
              new TextMessage({
                role: Role.User,
                content: `Rejected. Cancel operation #${opId}`,
              })
            )
          }}
        />
      )
    },
  })

  // Render write_acm_record / execute_pending_write results
  useRenderToolCall({
    name: 'execute_pending_write',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') {
        return <AgentActivityIndicator tool="execute_pending_write" status="executing" />
      }
      if (isErrorResult(result)) return <ToolErrorCard tool="execute_pending_write" />
      if (!result) return <></>
      const content = typeof result === 'string' ? result : JSON.stringify(result)
      return (
        <div className="text-xs border border-green-200 dark:border-green-900 rounded-lg px-3 py-2 my-1 text-green-700 dark:text-green-400">
          {content}
        </div>
      )
    },
  })

  // Fallback for any unregistered tools
  useDefaultTool({
    render: ({ name, status, result }): React.ReactElement => {
      if (status === 'inProgress' || status === 'executing') {
        return <AgentActivityIndicator tool={name} status="executing" />
      }
      if (isErrorResult(result)) return <ToolErrorCard tool={name} />
      if (!result) return <></>
      return (
        <div className="border rounded-lg p-3 my-1 text-sm bg-background">
          <div className="text-xs text-muted-foreground mb-1">{name}</div>
          <pre className="text-xs whitespace-pre-wrap overflow-auto max-h-40">
            {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )
    },
  })

  return null
}
