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
    'border-[color:var(--vaea-teal-300)] bg-[color:var(--vaea-teal-100)]/50 text-[color:var(--vaea-teal-900)] dark:border-[color:var(--vaea-teal-700)] dark:bg-[color:var(--vaea-teal-900)]/30 dark:text-[color:var(--vaea-teal-100)] animate-pulse',
  pending_review:
    'border-[color:var(--vaea-gold)]/40 bg-[color:var(--vaea-gold)]/15 text-[color:var(--vaea-grey-700)] dark:text-[color:var(--vaea-gold)]',
  building_review:
    'border-[color:var(--vaea-gold)]/40 bg-[color:var(--vaea-gold)]/15 text-[color:var(--vaea-grey-700)] dark:text-[color:var(--vaea-gold)]',
  acm_review:
    'border-[color:var(--vaea-gold)]/40 bg-[color:var(--vaea-gold)]/15 text-[color:var(--vaea-grey-700)] dark:text-[color:var(--vaea-gold)]',
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
