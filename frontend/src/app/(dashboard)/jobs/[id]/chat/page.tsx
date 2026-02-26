'use client'

import { use } from 'react'
import Link from 'next/link'
import '@copilotkit/react-ui/styles.css'
import { AppShell } from '@/components/layout/AppShell'
import { Breadcrumbs } from '@/components/common/Breadcrumbs'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { JobCrudChatPanel } from '@/components/jobs/JobCrudChatPanel'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, MessageSquare } from 'lucide-react'

/**
 * Fetch source details for the job title.
 */
async function fetchSource(sourceId: string) {
  const res = await fetch(`/api/sources/${encodeURIComponent(sourceId)}`)
  if (!res.ok) throw new Error(`Failed to fetch source: ${res.statusText}`)
  return res.json()
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
          <JobCrudChatPanel sourceId={sourceId} />
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
 * the main /api/copilotkit runtime to keep CRUD tools isolated from the read-only
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
      <CrudChatContent sourceId={sourceId} />
    </ErrorBoundary>
  )
}

export default JobCrudChatPage
