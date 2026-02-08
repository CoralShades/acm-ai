'use client'

import { cn } from '@/lib/utils'
import { BRANDING } from '@/config/branding'

interface VendorAttributionProps {
  className?: string
}

/**
 * CoralShades vendor attribution for sidebar footer
 */
export function VendorAttribution({ className }: VendorAttributionProps) {
  return (
    <div className={cn('flex items-center gap-2 px-4 py-2', className)}>
      <div className="w-4 h-4 rounded-full opacity-60" style={{ background: 'linear-gradient(to bottom right, #EB787A, #DC6668)' }} />
      <span className="text-xs text-muted-foreground">
        {BRANDING.footer.vendor}
      </span>
    </div>
  )
}
