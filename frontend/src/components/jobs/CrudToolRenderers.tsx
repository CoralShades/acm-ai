'use client'

import { useCallback } from 'react'
import { useCopilotAction } from '@copilotkit/react-core'
import { toast } from 'sonner'
import { WriteConfirmationCard } from '@/components/chat/WriteConfirmationCard'

interface CrudToolRenderersProps {
  sourceId: string
}

/**
 * Registers CopilotKit tool renderers for CRUD write previews.
 *
 * Must be rendered inside a CopilotKit provider configured with /copilot-crud.
 */
export function CrudToolRenderers({ sourceId }: CrudToolRenderersProps) {
  const handleConfirm = useCallback((operationId: string) => {
    toast.info(`Type "confirm ${operationId}" in the chat to execute this operation.`, {
      duration: 8000,
    })
  }, [])

  const handleCancel = useCallback((operationId: string) => {
    toast.info(`Type "cancel ${operationId}" in the chat to discard this operation.`, {
      duration: 5000,
    })
  }, [])

  useCopilotAction({
    name: 'preview_acm_write',
    description: 'Preview a proposed ACM record write operation for user confirmation',
    parameters: [],
    available: 'disabled',
    render: ({ result }) => {
      if (!result) return <></>
      const content = typeof result === 'string' ? result : JSON.stringify(result)
      return (
        <WriteConfirmationCard
          content={content}
          onConfirm={handleConfirm}
          onCancel={handleCancel}
        />
      )
    },
  })

  useCopilotAction({
    name: 'write_acm_record',
    description: 'Write (create/update/delete) an ACM record after user confirmation',
    parameters: [],
    available: 'disabled',
    render: ({ status, result }) => {
      if (status === 'executing') {
        return (
          <div className="text-sm text-muted-foreground italic py-2">
            Applying change...
          </div>
        )
      }

      if (!result) return <></>

      const content = typeof result === 'string' ? result : JSON.stringify(result)
      return (
        <WriteConfirmationCard
          content={content}
          onConfirm={handleConfirm}
          onCancel={handleCancel}
        />
      )
    },
  })

  void sourceId

  return null
}
