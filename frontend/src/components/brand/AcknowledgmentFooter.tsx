'use client'

import { cn } from '@/lib/utils'
import { BRANDING } from '@/config/branding'

interface AcknowledgmentFooterProps {
  className?: string
}

/**
 * Aboriginal and Torres Strait Islander Acknowledgment
 * Required for Victorian government applications
 */
export function AcknowledgmentFooter({ className }: AcknowledgmentFooterProps) {
  return (
    <footer className={cn(
      'text-xs text-center text-muted-foreground leading-relaxed',
      'border-t border-border px-6 py-4',
      className
    )}>
      <p>{BRANDING.footer.acknowledgment}</p>
    </footer>
  )
}
