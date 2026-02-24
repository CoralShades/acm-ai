'use client'

import { AppShell } from '@/components/layout/AppShell'
import { DocumentsSkeleton } from '@/components/skeletons/DocumentsSkeleton'

export default function JobsLoading() {
  return (
    <AppShell>
      <DocumentsSkeleton />
    </AppShell>
  )
}
