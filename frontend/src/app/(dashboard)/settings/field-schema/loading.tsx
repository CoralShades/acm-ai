'use client'

import { AppShell } from '@/components/layout/AppShell'
import { Skeleton } from '@/components/ui/skeleton'

export default function FieldSchemaLoading() {
  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto p-6" aria-busy="true">
        <span className="sr-only" role="status">Loading field schema</span>
        <div className="max-w-4xl space-y-6">
          <div className="flex items-center justify-between">
            <Skeleton className="h-8 w-40" />
            <Skeleton className="h-9 w-28" />
          </div>

          <div className="rounded-xl border">
            <div className="flex gap-4 p-3 border-b">
              <Skeleton className="h-4 w-36" />
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-16" />
            </div>
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="flex gap-4 p-3 border-b">
                <Skeleton className="h-4 w-36" />
                <Skeleton className="h-4 w-28" />
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-4 w-16" />
              </div>
            ))}
          </div>
        </div>
      </div>
    </AppShell>
  )
}
