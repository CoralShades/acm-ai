'use client'

import { AppShell } from '@/components/layout/AppShell'
import { DashboardSkeleton } from '@/components/skeletons/DashboardSkeleton'

export default function DashboardLoading() {
  return (
    <AppShell>
      <DashboardSkeleton />
    </AppShell>
  )
}
