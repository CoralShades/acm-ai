'use client'

import { AppShell } from '@/components/layout/AppShell'
import { Skeleton } from '@/components/ui/skeleton'

export default function ChatLoading() {
  return (
    <AppShell>
      <div className="flex flex-col h-full" aria-busy="true">
        <span className="sr-only" role="status">Loading chat</span>

        <div className="p-4 border-b flex items-center gap-3">
          <Skeleton className="h-9 w-24" />
          <Skeleton className="h-6 w-48" />
        </div>

        <div className="flex-1 p-4 space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className={`flex ${i % 2 === 0 ? 'justify-start' : 'justify-end'}`}
            >
              <div className="space-y-2 max-w-md">
                <Skeleton className={`h-16 ${i % 2 === 0 ? 'w-72' : 'w-48'} rounded-xl`} />
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 border-t">
          <Skeleton className="h-12 w-full rounded-xl" />
        </div>
      </div>
    </AppShell>
  )
}
