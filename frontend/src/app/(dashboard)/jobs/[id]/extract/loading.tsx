'use client'

import { AppShell } from '@/components/layout/AppShell'
import { Skeleton } from '@/components/ui/skeleton'

export default function ExtractLoading() {
  return (
    <AppShell>
      <div className="w-full space-y-4 p-6" aria-busy="true">
        <span className="sr-only" role="status">Loading extraction progress</span>

        <div className="space-y-2">
          <Skeleton className="h-4 w-72" />
          <Skeleton className="h-8 w-96" />
          <Skeleton className="h-4 w-[30rem]" />
        </div>

        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <Skeleton className="h-6 w-52" />
          <div className="mt-3 flex flex-wrap gap-2">
            {Array.from({ length: 7 }).map((_, index) => (
              <Skeleton key={index} className="h-8 w-28 rounded-full" />
            ))}
          </div>
          <Skeleton className="mt-4 h-2 w-full" />
        </div>

        <div className="rounded-xl border bg-card p-4 shadow-sm">
          <Skeleton className="h-5 w-40" />
          <div className="mt-4 rounded-lg border">
            <div className="flex gap-2 border-b p-2">
              {Array.from({ length: 8 }).map((_, index) => (
                <Skeleton key={index} className="h-4 flex-1" />
              ))}
            </div>
            {Array.from({ length: 8 }).map((_, row) => (
              <div key={row} className="flex gap-2 border-b p-3">
                {Array.from({ length: 8 }).map((_, col) => (
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
