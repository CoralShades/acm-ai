'use client'

import { useState, useEffect } from 'react'
import { X, Lightbulb } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface OnboardingHintProps {
  id: string
  message: string
}

export function OnboardingHint({ id, message }: OnboardingHintProps) {
  const [dismissed, setDismissed] = useState(true) // default hidden until checked

  useEffect(() => {
    const key = `acm-hint-${id}`
    setDismissed(localStorage.getItem(key) === 'dismissed')
  }, [id])

  if (dismissed) return null

  const handleDismiss = () => {
    localStorage.setItem(`acm-hint-${id}`, 'dismissed')
    setDismissed(true)
  }

  return (
    <div className="flex items-center gap-3 rounded-lg border border-primary/20 bg-primary/5 px-4 py-3 text-sm">
      <Lightbulb className="h-4 w-4 shrink-0 text-primary" />
      <span className="flex-1 text-muted-foreground">{message}</span>
      <Button
        variant="ghost"
        size="icon"
        className="h-6 w-6 shrink-0"
        onClick={handleDismiss}
        aria-label="Dismiss hint"
      >
        <X className="h-3.5 w-3.5" />
      </Button>
    </div>
  )
}
