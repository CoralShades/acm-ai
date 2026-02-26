'use client'

import { AppShell } from '@/components/layout/AppShell'
import { Skeleton } from '@/components/ui/skeleton'

export default function BuildingReviewLoading() {
  return (
    <AppShell>
      <div className="w-full space-y-4 p-6" aria-busy="true">
        <span className="sr-only" role="status">Loading building review</span>

        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <div className="flex items-center gap-4">
            <Skeleton className="h-8 w-20" />
            <Skeleton className="h-5 w-72" />
            <Skeleton className="h-2 w-40" />
            <Skeleton className="ml-auto h-9 w-44" />
          </div>
        </div>

        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <div className="mb-4 flex flex-wrap items-center gap-3">
            <Skeleton className="h-9 w-64" />
            <Skeleton className="h-8 w-20 rounded-full" />
            <Skeleton className="h-8 w-24 rounded-full" />
            <Skeleton className="h-8 w-24 rounded-full" />
            <div className="ml-auto">
              <Skeleton className="h-9 w-32" />
            </div>
          </div>

          <div className="rounded-lg border">
            <div className="flex gap-2 border-b p-2">
              {Array.from({ length: 10 }).map((_, index) => (
                <Skeleton key={index} className="h-4 flex-1" />
              ))}
            </div>
            {Array.from({ length: 10 }).map((_, row) => (
              <div key={row} className="flex gap-2 border-b p-3">
                {Array.from({ length: 10 }).map((_, col) => (
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
