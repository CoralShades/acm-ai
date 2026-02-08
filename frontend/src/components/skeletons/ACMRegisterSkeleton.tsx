import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

export function ACMRegisterSkeleton() {
  return (
    <div className="space-y-6 p-6" aria-busy="true">
      <span className="sr-only" role="status">Loading ACM register</span>
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Skeleton className="h-8 w-8 rounded" />
          <Skeleton className="h-8 w-48" />
        </div>
        <Skeleton className="h-4 w-96" />
      </div>
      <div className="rounded-lg border p-6 space-y-4">
        <div className="space-y-2">
          <Skeleton className="h-5 w-48" />
          <Skeleton className="h-4 w-80" />
        </div>
        <Skeleton className="h-10 w-full max-w-md" />
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-lg border p-4 space-y-2">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-7 w-12" />
          </div>
        ))}
      </div>
      <div className="rounded-lg border p-6 space-y-4">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Skeleton className="h-5 w-5" />
            <Skeleton className="h-5 w-32" />
          </div>
          <Skeleton className="h-4 w-96" />
        </div>
        <div className="flex items-center gap-3 flex-wrap">
          <Skeleton className="h-9 w-64" />
          <div className="flex gap-1">
            <Skeleton className="h-8 w-20 rounded-full" />
            <Skeleton className="h-8 w-24 rounded-full" />
            <Skeleton className="h-8 w-28 rounded-full" />
          </div>
          <div className="ml-auto flex gap-2">
            <Skeleton className="h-9 w-32" />
            <Skeleton className="h-9 w-9" />
            <Skeleton className="h-9 w-9" />
          </div>
        </div>
        <div className="rounded-lg border overflow-hidden">
          <div className="flex border-b bg-muted/30 p-2 gap-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton
                key={i}
                className="h-4 flex-1"
                style={{ maxWidth: i === 0 ? 40 : undefined }}
              />
            ))}
          </div>
          {Array.from({ length: 10 }).map((_, row) => (
            <div key={row} className="flex border-b p-3 gap-2">
              {Array.from({ length: 8 }).map((_, col) => (
                <Skeleton
                  key={col}
                  className={cn('h-4 flex-1', col === 0 && 'max-w-[40px]')}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
