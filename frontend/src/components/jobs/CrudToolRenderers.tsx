'use client'

import { useRenderToolCall, useLangGraphInterrupt } from '@copilotkit/react-core'
import { HITLApprovalDialog } from '@/components/chat/renderers/HITLApprovalDialog'
import { ToolErrorCard } from '@/components/chat/renderers/ToolErrorCard'

interface CrudToolRenderersProps {
  sourceId: string
}

function isErrorResult(result: unknown): boolean {
  if (!result) return false
  if (typeof result === 'string') {
    try {
      const parsed = JSON.parse(result)
      return typeof parsed === 'object' && parsed !== null && 'error' in parsed
    } catch {
      return false
    }
  }
  return typeof result === 'object' && result !== null && 'error' in result
}

/**
 * Registers CopilotKit tool-call renderers for CRUD write previews.
 *
 * Uses useLangGraphInterrupt for HITL approval dialogs (replaces the old
 * toast-based confirmation pattern), and useRenderToolCall for in-progress
 * and result states.
 *
 * Must be rendered inside a CopilotKit provider configured with /copilot-crud.
 */
export function CrudToolRenderers({ sourceId }: CrudToolRenderersProps) {
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

  // Render preview_write tool results as loading indicators
  // (the actual approval UI comes from useLangGraphInterrupt above)
  useRenderToolCall({
    name: 'preview_acm_write',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') {
        return (
          <div className="text-sm text-muted-foreground italic py-2">
            Preparing write preview...
          </div>
        )
      }
      if (isErrorResult(result))
        return <ToolErrorCard tool="preview_acm_write" />
      // Preview result is handled by the interrupt approval dialog
      return <></>
    },
  })

  // Render write_acm_record results
  useRenderToolCall({
    name: 'write_acm_record',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') {
        return (
          <div className="text-sm text-muted-foreground italic py-2">
            Applying change...
          </div>
        )
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

  void sourceId

  return null
}
