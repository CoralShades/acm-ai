'use client'

import { Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

/**
 * Sparkle icon with subtle rotate + pulse animation on hover.
 * Used for the AI-Editor sidebar navigation item.
 *
 * Animation: 600ms ease-in-out rotate(12deg) + scale(1.08) on parent hover.
 * CSS-only — no JS animation libraries.
 */
export function AnimatedSparkleIcon({ className }: { className?: string }) {
  return (
    <Sparkles
      className={cn(
        'transition-transform duration-500 ease-in-out',
        'group-hover/ai-editor:rotate-12 group-hover/ai-editor:scale-108',
        className
      )}
    />
  )
}
