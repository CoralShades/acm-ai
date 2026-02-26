'use client'

import { AppShell } from '@/components/layout/AppShell'
import { Skeleton } from '@/components/ui/skeleton'

export default function JobDetailLoading() {
  return (
    <AppShell>
      <div className="w-full space-y-4 p-6" aria-busy="true">
        <span className="sr-only" role="status">Loading job details</span>

        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <div className="flex items-center justify-between gap-3">
            <Skeleton className="h-4 w-56" />
            <div className="flex gap-2">
              <Skeleton className="h-8 w-24" />
              <Skeleton className="h-8 w-24" />
              <Skeleton className="h-8 w-24" />
            </div>
          </div>
          <div className="mt-4 flex items-center gap-3">
            <Skeleton className="h-8 w-64" />
            <Skeleton className="h-6 w-28 rounded-full" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>

        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <div className="mb-4 flex items-center gap-2">
            <Skeleton className="h-9 w-24" />
            <Skeleton className="h-9 w-24" />
            <Skeleton className="h-9 w-24" />
            <Skeleton className="h-9 w-28" />
          </div>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="rounded-lg border p-4">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="mt-2 h-7 w-14" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  )
}
