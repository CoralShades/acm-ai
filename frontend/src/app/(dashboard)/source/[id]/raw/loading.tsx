'use client'

import { AppShell } from '@/components/layout/AppShell'
import { Skeleton } from '@/components/ui/skeleton'

export default function RawTablesLoading() {
  return (
    <AppShell>
      <div className="w-full space-y-4 p-6" aria-busy="true">
        <span className="sr-only" role="status">Loading raw tables</span>

        <Skeleton className="h-9 w-24" />
        <Skeleton className="h-8 w-48" />

        <div className="rounded-xl border">
          <div className="flex gap-4 p-3 border-b">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-4 w-28" />
            ))}
          </div>
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="flex gap-4 p-3 border-b">
              {Array.from({ length: 5 }).map((_, j) => (
                <Skeleton key={j} className="h-4 w-28" />
              ))}
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  )
}
