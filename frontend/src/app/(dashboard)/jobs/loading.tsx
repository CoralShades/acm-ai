'use client'

import { AppShell } from '@/components/layout/AppShell'
import { Skeleton } from '@/components/ui/skeleton'

export default function JobsLoading() {
  return (
    <AppShell>
      <div className="w-full space-y-4 p-6" aria-busy="true">
        <span className="sr-only" role="status">Loading jobs</span>

        <div className="space-y-2">
          <Skeleton className="h-8 w-32" />
          <Skeleton className="h-4 w-80" />
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="rounded-xl border bg-card p-4 shadow-sm">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="mt-3 h-8 w-12" />
            </div>
          ))}
        </div>

        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <div className="flex flex-wrap items-center gap-3">
            <Skeleton className="h-9 w-64" />
            <Skeleton className="h-8 w-20 rounded-full" />
            <Skeleton className="h-8 w-24 rounded-full" />
            <Skeleton className="h-8 w-28 rounded-full" />
            <div className="ml-auto">
              <Skeleton className="h-9 w-28" />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 8 }).map((_, index) => (
            <div key={index} className="rounded-xl border bg-card p-4 shadow-sm">
              <Skeleton className="h-5 w-3/4" />
              <Skeleton className="mt-3 h-5 w-28 rounded-full" />
              <Skeleton className="mt-3 h-3 w-32" />
              <Skeleton className="mt-1 h-3 w-24" />
              <Skeleton className="mt-4 h-8 w-full" />
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  )
}
