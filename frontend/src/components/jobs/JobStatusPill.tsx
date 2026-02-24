import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

const statusLabel: Record<string, string> = {
  extracting: 'Extracting',
  pending_review: 'Pending Review',
  building_review: 'Review: Buildings',
  acm_review: 'Review: Records',
  published: 'Published',
}

const statusClassName: Record<string, string> = {
  extracting:
    'bg-blue-100 text-blue-800 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800 animate-pulse',
  pending_review:
    'bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800',
  building_review:
    'bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800',
  acm_review:
    'bg-amber-100 text-amber-800 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800',
  published:
    'bg-green-100 text-green-800 border-green-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-800',
}

interface JobStatusPillProps {
  review_status?: string | null
  className?: string
}

export function JobStatusPill({ review_status, className }: JobStatusPillProps) {
  // Null/undefined legacy data defaults to 'published'
  const status = review_status ?? 'published'
  const label = statusLabel[status] ?? 'Published'
  const pillClassName = statusClassName[status] ?? statusClassName.published

  return (
    <Badge
      variant="outline"
      className={cn(pillClassName, className)}
    >
      {label}
    </Badge>
  )
}
