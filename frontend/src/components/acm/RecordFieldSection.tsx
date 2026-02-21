'use client'

import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'

export type FieldType = 'text' | 'boolean' | 'confidence' | 'risk'

export interface SectionField {
  label: string
  value: string | number | boolean | null | undefined
  type?: FieldType
}

interface RecordFieldSectionProps {
  title: string
  fields: SectionField[]
  className?: string
}

const riskVariants: Record<string, string> = {
  High: 'bg-risk-high-bg text-risk-high-foreground',
  Medium: 'bg-risk-medium-bg text-risk-medium-foreground',
  Low: 'bg-risk-low-bg text-risk-low-foreground',
  Presumed: 'bg-risk-presumed-bg text-risk-presumed-foreground',
}

function FieldValue({ value, type }: { value: SectionField['value']; type?: FieldType }) {
  if (value === null || value === undefined || value === '') {
    return <span className="text-muted-foreground">—</span>
  }

  if (type === 'boolean' || typeof value === 'boolean') {
    const isYes = value === true || value === 'true' || value === 'YES'
    return (
      <Badge
        variant="secondary"
        className={isYes ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-muted text-muted-foreground'}
      >
        {isYes ? 'YES' : 'NO'}
      </Badge>
    )
  }

  if (type === 'confidence' && typeof value === 'number') {
    const pct = Math.round(value * (value <= 1 ? 100 : 1))
    const color =
      pct >= 80 ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      : pct >= 50 ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
      : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
    return (
      <Badge variant="secondary" className={color}>
        {pct}%
      </Badge>
    )
  }

  if (type === 'risk') {
    const str = String(value)
    return (
      <Badge variant="secondary" className={riskVariants[str] || ''}>
        {str}
      </Badge>
    )
  }

  return <span className="text-sm">{String(value)}</span>
}

export function RecordFieldSection({ title, fields, className }: RecordFieldSectionProps) {
  return (
    <div className={cn('space-y-3', className)}>
      <div className="flex items-center gap-2">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          {title}
        </h3>
        <Separator className="flex-1" />
      </div>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-3">
        {fields.map((field) => (
          <div key={field.label} className="space-y-0.5 min-w-0">
            <dt className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide truncate">
              {field.label}
            </dt>
            <dd className="text-sm break-words">
              <FieldValue value={field.value} type={field.type} />
            </dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
