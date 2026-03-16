'use client'

import { AppShell } from '@/components/layout/AppShell'
import { Skeleton } from '@/components/ui/skeleton'

export default function ExtractionSettingsLoading() {
  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto p-6" aria-busy="true">
        <span className="sr-only" role="status">Loading extraction settings</span>
        <div className="max-w-4xl space-y-6">
          <Skeleton className="h-8 w-48" />

          <div className="rounded-xl border p-6 space-y-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-28" />
                <Skeleton className="h-10 w-full" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  )
}
