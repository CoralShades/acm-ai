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
 * Uses the official VAEA Ripple logo for government branding compliance.
 */
export function Logo({ variant = 'full', className, iconClassName }: LogoProps) {
  const icon = (
    <Image
      src="/logo.png"
      alt="VAEA Logo"
      width={32}
      height={32}
      className={cn('w-8 h-8', iconClassName)}
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
