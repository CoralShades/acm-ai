'use client'

import { AppShell } from '@/components/layout/AppShell'
import { Skeleton } from '@/components/ui/skeleton'

export default function RecordsReviewLoading() {
  return (
    <AppShell>
      <div className="w-full space-y-4 p-6" aria-busy="true">
        <span className="sr-only" role="status">Loading records review</span>

        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <div className="flex items-center gap-4">
            <Skeleton className="h-8 w-20" />
            <Skeleton className="h-5 w-72" />
            <Skeleton className="h-2 w-40" />
            <Skeleton className="ml-auto h-9 w-36" />
          </div>
        </div>

        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <div className="mb-4 flex gap-2 overflow-x-auto pb-2">
            {Array.from({ length: 6 }).map((_, index) => (
              <Skeleton key={index} className="h-8 w-32 rounded-full" />
            ))}
          </div>

          <div className="mb-4 flex flex-wrap items-center gap-3">
            <Skeleton className="h-9 w-64" />
            <Skeleton className="h-8 w-24 rounded-full" />
            <Skeleton className="h-8 w-36 rounded-full" />
            <div className="ml-auto flex gap-2">
              <Skeleton className="h-9 w-28" />
              <Skeleton className="h-9 w-28" />
            </div>
          </div>

          <div className="rounded-lg border">
            <div className="flex gap-2 border-b p-2">
              {Array.from({ length: 12 }).map((_, index) => (
                <Skeleton key={index} className="h-4 flex-1" />
              ))}
            </div>
            {Array.from({ length: 10 }).map((_, row) => (
              <div key={row} className="flex gap-2 border-b p-3">
                {Array.from({ length: 12 }).map((_, col) => (
                  <Skeleton key={`${row}-${col}`} className="h-4 flex-1" />
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  )
}
