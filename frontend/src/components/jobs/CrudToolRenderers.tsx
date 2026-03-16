'use client'

import React from 'react'
import { useRenderToolCall, useDefaultTool, useLangGraphInterrupt } from '@copilotkit/react-core'
import { AgentActivityIndicator } from '@/components/chat/renderers/AgentActivityIndicator'
import { HITLApprovalDialog } from '@/components/chat/renderers/HITLApprovalDialog'
import { ToolErrorCard } from '@/components/chat/renderers/ToolErrorCard'
import { isErrorResult } from '@/lib/utils/tool-result'

/**
 * Registers CopilotKit tool-call renderers for CRUD write previews.
 *
 * Uses useLangGraphInterrupt for HITL approval dialogs (replaces the old
 * toast-based confirmation pattern), and useRenderToolCall for in-progress
 * and result states.
 *
 * Must be rendered inside a CopilotKit provider configured with /copilot-crud.
 */
export function CrudToolRenderers() {
  // HITL: Render approval dialog when the backend graph interrupts for write approval
  useLangGraphInterrupt({
    enabled: ({ eventValue }) => eventValue?.type === 'write_approval',
    render: ({ event, resolve }) => {
      const preview = event.value?.preview
      if (!preview) return <></>

      return (
        <HITLApprovalDialog
          preview={preview}
          onApprove={(edits) =>
            resolve(JSON.stringify({ approved: true, edits: edits || {} }))
          }
          onReject={() => resolve(JSON.stringify({ approved: false }))}
        />
      )
    },
  })

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
        <div className="border rounded-lg p-3 my-2 text-sm bg-muted/10">
          <div className="text-xs font-medium text-muted-foreground mb-1">Query Results</div>
          <pre className="text-xs whitespace-pre-wrap overflow-auto max-h-60">
            {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )
    },
  })

  // Render preview_write tool results as loading indicators
  // (the actual approval UI comes from useLangGraphInterrupt above)
  useRenderToolCall({
    name: 'preview_write',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') {
        return <AgentActivityIndicator tool="preview_write" status="executing" />
      }
      if (isErrorResult(result))
        return <ToolErrorCard tool="preview_write" />
      // Preview result is handled by the interrupt approval dialog
      return <></>
    },
  })

  // Render write_acm_record results
  useRenderToolCall({
    name: 'write_acm_record',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') {
        return <AgentActivityIndicator tool="write_acm_record" status="executing" />
      }
      if (isErrorResult(result))
        return <ToolErrorCard tool="write_acm_record" />
      if (!result) return <></>
      const content = typeof result === 'string' ? result : JSON.stringify(result)
      return (
        <div className="text-sm text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/20 rounded px-3 py-2 my-1">
          {content}
        </div>
      )
    },
  })

  // Fallback renderer for any unregistered tools
  useDefaultTool({
    render: ({ name, status, result }): React.ReactElement => {
      if (status === 'inProgress' || status === 'executing') {
        return <AgentActivityIndicator tool={name} status="executing" />
      }
      if (isErrorResult(result)) return <ToolErrorCard tool={name} />
      if (!result) return <></>
      return (
        <div className="border rounded-lg p-3 my-1 text-sm bg-muted/30">
          <div className="text-xs font-medium text-muted-foreground mb-1">{name}</div>
          <pre className="text-xs whitespace-pre-wrap overflow-auto max-h-40">
            {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )
    },
  })

  return null
}
