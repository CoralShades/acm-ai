'use client'

import { use } from 'react'
import Link from 'next/link'
import '@copilotkit/react-ui/styles.css'
import { AppShell } from '@/components/layout/AppShell'
import { Breadcrumbs } from '@/components/common/Breadcrumbs'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { UnifiedChatPanel } from '@/components/chat/UnifiedChatPanel'
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
 * UnifiedChatContent — full-page chat experience for a job.
 */
function UnifiedChatContent({ sourceId }: { sourceId: string }) {
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
              { label: 'Chat' },
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
              <h1 className="text-lg font-semibold">ACM-AI Chat — {jobTitle}</h1>
            </div>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Query records, make changes, and explore ACM data using natural language.
          </p>
        </div>

        {/* Chat area */}
        <div className="flex-1 min-h-0">
          <UnifiedChatPanel sourceId={sourceId} hasAcmData />
        </div>
      </div>
    </AppShell>
  )
}

/**
 * JobChatPage — unified chat interface for a specific job's ACM records.
 *
 * URL: /jobs/[id]/chat
 */
function JobChatPage({
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
          pageName="Chat"
          reloadUrl={`/jobs/${sourceId}`}
        />
      )}
    >
      <UnifiedChatContent sourceId={sourceId} />
    </ErrorBoundary>
  )
}

export default JobChatPage
