'use client'

import Image from 'next/image'
import { cn } from '@/lib/utils'
import { BRANDING } from '@/config/branding'

interface LogoProps {
  variant?: 'full' | 'icon'
  className?: string
  iconClassName?: string
}

/**
 * VAEA ACM-AI Logo Component
 *
 * Uses the official VAEA Ripple logo (SVG) for government branding compliance.
 * Full variant uses acm-logo-bg.svg (dark background with mark).
 * Icon variant uses acm-icon.svg (transparent mark only).
 */
export function Logo({ variant = 'full', className, iconClassName }: LogoProps) {
  const icon = (
    <Image
      src={variant === 'icon' ? '/acm-icon.svg' : '/acm-logo-bg.svg'}
      alt="VAEA - Victorian Asbestos Eradication Agency"
      width={32}
      height={32}
      className={cn('w-8 h-8 rounded-md', iconClassName)}
      priority
    />
  )

  if (variant === 'icon') {
    return (
      <div className={className}>
        {icon}
      </div>
    )
  }

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {icon}
      <span className="font-semibold text-lg text-foreground">{BRANDING.name}</span>
    </div>
  )
}

export default Logo
