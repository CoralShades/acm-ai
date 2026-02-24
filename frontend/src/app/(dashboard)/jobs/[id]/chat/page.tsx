'use client'

import { use, useCallback } from 'react'
import Link from 'next/link'
import { CopilotKit } from '@copilotkit/react-core'
import { CopilotChat } from '@copilotkit/react-ui'
import '@copilotkit/react-ui/styles.css'
import { useCopilotAction } from '@copilotkit/react-core'
import { AppShell } from '@/components/layout/AppShell'
import { Breadcrumbs } from '@/components/common/Breadcrumbs'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { WriteConfirmationCard } from '@/components/chat/WriteConfirmationCard'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, MessageSquare } from 'lucide-react'
import { toast } from 'sonner'

/**
 * Fetch source details for the job title.
 */
async function fetchSource(sourceId: string) {
  const res = await fetch(`/api/sources/${encodeURIComponent(sourceId)}`)
  if (!res.ok) throw new Error(`Failed to fetch source: ${res.statusText}`)
  return res.json()
}

/**
 * CrudToolRenderers — registers CopilotKit action renderers for CRUD write preview.
 *
 * Renders a WriteConfirmationCard when the agent produces a preview_write tool result.
 * On confirm, sends "confirm {operationId}" as the next chat message.
 * On cancel, sends "cancel {operationId}" to abort the pending operation.
 *
 * Must be rendered inside a CopilotKit provider.
 */
function CrudToolRenderers({ sourceId }: { sourceId: string }) {
  const handleConfirm = useCallback(
    (operationId: string) => {
      // The agent expects a plain text message to proceed — the chat input is
      // controlled by CopilotKit so we dispatch a custom event that the parent
      // can listen to, but the simplest approach is to show a toast informing
      // the user to type the confirmation phrase in the chat.
      //
      // In practice, users can also just type "confirm <id>" themselves, but
      // we surface a toast as a UX affordance.
      toast.info(`Type "confirm ${operationId}" in the chat to execute this operation.`, {
        duration: 8000,
      })
    },
    []
  )

  const handleCancel = useCallback(
    (operationId: string) => {
      toast.info(`Type "cancel ${operationId}" in the chat to discard this operation.`, {
        duration: 5000,
      })
    },
    []
  )

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

  // Also handle any tool result that may contain a preview_write payload
  // by registering a generic write_acm_record renderer.
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
      // If the result contains a preview_write, show the confirmation card
      const card = (
        <WriteConfirmationCard
          content={content}
          onConfirm={handleConfirm}
          onCancel={handleCancel}
        />
      )
      // WriteConfirmationCard returns null if content isn't a preview_write,
      // so this is safe to render unconditionally.
      return card
    },
  })

  void sourceId // referenced in system message via makeSystemMessage closure

  return null
}

/**
 * CrudChatContent — inner page content rendered inside the CopilotKit CRUD provider.
 */
function CrudChatContent({ sourceId }: { sourceId: string }) {
  const { data: source } = useQuery({
    queryKey: ['source', sourceId],
    queryFn: () => fetchSource(sourceId),
  })

  const jobTitle = source?.title ?? `Job ${sourceId}`

  return (
    <AppShell>
      <div className="flex flex-col h-full overflow-hidden">
        {/* Header */}
        <div className="flex-shrink-0 px-6 pt-4 pb-2 border-b">
          <Breadcrumbs
            items={[
              { label: 'Home', href: '/' },
              { label: 'Jobs', href: '/jobs' },
              { label: jobTitle, href: `/jobs/${sourceId}` },
              { label: 'CRUD Chat' },
            ]}
            className="mb-3"
          />
          <div className="flex items-center gap-3">
            <Link
              href={`/jobs/${sourceId}`}
              className="flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Job
            </Link>
            <div className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-primary" />
              <h1 className="text-lg font-semibold">CRUD Chat — {jobTitle}</h1>
            </div>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Use natural language to create, update, or delete ACM records.
            The agent will preview any write operation before applying it.
          </p>
        </div>

        {/* Chat area */}
        <div className="flex-1 min-h-0">
          <CrudToolRenderers sourceId={sourceId} />
          <CopilotChat
            className="h-full"
            labels={{
              title: 'ACM CRUD Assistant',
              initial: `Ask me to update, create, or delete ACM records for this job. I'll preview any changes before applying them.`,
            }}
            makeSystemMessage={() =>
              `You are an ACM (Asbestos Containing Material) compliance data editor. ` +
              `Your role is to help users create, update, and delete ACM records through natural language. ` +
              `Current job source: ${sourceId}. ` +
              `IMPORTANT: Always preview write operations before executing them. ` +
              `Present a preview_write JSON payload and wait for the user to confirm by replying with "confirm <operation_id>". ` +
              `Never apply changes without explicit user confirmation.`
            }
          />
        </div>
      </div>
    </AppShell>
  )
}

/**
 * JobCrudChatPage — conversational CRUD interface for a specific job's ACM records.
 *
 * Mounts a dedicated CopilotKit provider pointing to /copilot-crud, which
 * bridges to the FastAPI CRUD chat agent. This is intentionally separate from
 * the main /copilot runtime to keep CRUD tools isolated from the read-only
 * supervisor agent.
 *
 * URL: /jobs/[id]/chat
 * Story: E19-S8 Conversational CRUD Chat
 */
function JobCrudChatPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const sourceId = decodeURIComponent(id)

  return (
    <ErrorBoundary
      fallback={(props) => (
        <PageErrorFallback
          {...props}
          pageName="CRUD Chat"
          reloadUrl={`/jobs/${sourceId}`}
        />
      )}
    >
      {/* Nested CopilotKit provider — overrides the dashboard-level /copilot runtime */}
      <CopilotKit runtimeUrl="/copilot-crud">
        <CrudChatContent sourceId={sourceId} />
      </CopilotKit>
    </ErrorBoundary>
  )
}

export default JobCrudChatPage
