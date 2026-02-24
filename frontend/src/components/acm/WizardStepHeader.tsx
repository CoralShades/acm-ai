'use client'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ChevronLeft } from 'lucide-react'

interface WizardStepHeaderProps {
  currentStep: number
  totalSteps: number
  stepTitle: string
  onCancel: () => void
  onNext?: () => void
  nextLabel?: string
  nextDisabled?: boolean
  unassignedCount?: number
}

/**
 * WizardStepHeader — reusable wizard step indicator shown at the top of each review step.
 *
 * Renders:
 *   [Cancel]   Step N of M: {title}   [progress bar]   [Next →]
 *
 * Story: E19-S5 Building Review Wizard Step 1
 */
export function WizardStepHeader({
  currentStep,
  totalSteps,
  stepTitle,
  onCancel,
  onNext,
  nextLabel = 'Next \u2192',
  nextDisabled = false,
  unassignedCount,
}: WizardStepHeaderProps) {
  const progressPercent = Math.round((currentStep / totalSteps) * 100)

  return (
    <div className="flex-shrink-0 border-b bg-background px-6 py-3 space-y-2">
      {/* Main row: cancel | step label + progress | next */}
      <div className="flex items-center gap-4">
        {/* Cancel */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onCancel}
          className="flex items-center gap-1 text-muted-foreground hover:text-foreground"
        >
          <ChevronLeft className="h-4 w-4" />
          Cancel
        </Button>

        {/* Step label and progress */}
        <div className="flex flex-1 items-center gap-3 min-w-0">
          <span className="text-sm font-medium whitespace-nowrap">
            Step {currentStep} of {totalSteps}: {stepTitle}
          </span>

          {/* Progress bar */}
          <div
            className="flex-1 h-2 bg-muted rounded-full overflow-hidden max-w-48"
            role="progressbar"
            aria-valuenow={progressPercent}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Step ${currentStep} of ${totalSteps}`}
          >
            <div
              className="h-full bg-primary rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          <span className="text-xs text-muted-foreground whitespace-nowrap">
            {progressPercent}%
          </span>
        </div>

        {/* Next button */}
        {onNext && (
          <Button
            size="sm"
            onClick={onNext}
            disabled={nextDisabled}
            className="flex-shrink-0"
          >
            {nextLabel}
          </Button>
        )}
      </div>

      {/* Unassigned records warning badge */}
      {unassignedCount != null && unassignedCount > 0 && (
        <div className="flex items-center">
          <span
            className={cn(
              'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
              'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300'
            )}
          >
            {unassignedCount} record{unassignedCount !== 1 ? 's' : ''} not assigned to any building
          </span>
        </div>
      )}
    </div>
  )
}
