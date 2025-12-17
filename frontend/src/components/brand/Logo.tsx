'use client'

import { cn } from '@/lib/utils'

interface LogoProps {
  variant?: 'full' | 'icon'
  className?: string
  iconClassName?: string
}

/**
 * ACM-AI Logo Component
 *
 * Shield design representing:
 * - Safety and compliance (shield shape)
 * - Document/data analysis (horizontal lines)
 * - AI capability (circuit node)
 */
export function Logo({ variant = 'full', className, iconClassName }: LogoProps) {
  const icon = (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn('w-8 h-8', iconClassName)}
      aria-hidden="true"
    >
      {/* Shield shape */}
      <path
        d="M16 2L4 7v9c0 8.4 5.12 16.24 12 18 6.88-1.76 12-9.6 12-18V7L16 2z"
        className="fill-primary"
      />
      {/* Document lines representing data/registers */}
      <path
        d="M10 11h12M10 15h12M10 19h8"
        stroke="white"
        strokeWidth="2"
        strokeLinecap="round"
      />
      {/* AI circuit node */}
      <circle cx="22" cy="19" r="2.5" fill="white" />
      <circle cx="22" cy="19" r="1" className="fill-primary" />
    </svg>
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
      <span className="font-semibold text-lg text-foreground">ACM-AI</span>
    </div>
  )
}

export default Logo
