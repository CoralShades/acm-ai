'use client'

import { AppShell } from '@/components/layout/AppShell'
import { ACMRegisterSkeleton } from '@/components/skeletons/ACMRegisterSkeleton'

export default function ACMLoading() {
  return (
    <AppShell>
      <ACMRegisterSkeleton />
    </AppShell>
  )
}
