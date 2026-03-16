'use client'

import { Loader2, CheckCircle2 } from 'lucide-react'

interface ExtractionProgressProps {
  status: string
  stage?: string
  progress?: number
  message?: string
}

export function ExtractionProgress({
  status,
  stage,
  progress,
  message,
}: ExtractionProgressProps) {
  const isComplete = status === 'complete'

  return (
    <div className="border rounded-lg p-3 my-2 text-sm">
      <div className="flex items-center gap-2 mb-1">
        {isComplete ? (
          <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400" />
        ) : (
          <Loader2 className="h-4 w-4 text-primary animate-spin" />
        )}
        <span className="font-medium">
          {isComplete ? 'Extraction Complete' : 'Extracting...'}
        </span>
      </div>
      {stage && (
        <div className="text-xs text-muted-foreground mb-1">Stage: {stage}</div>
      )}
      {message && (
        <div className="text-xs text-muted-foreground">{message}</div>
      )}
      {progress != null && (
        <div className="mt-2">
          <div className="h-1.5 bg-gray-200 dark:bg-muted rounded-full overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-all duration-300"
              style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
            />
          </div>
          <div className="text-xs text-muted-foreground mt-0.5 text-right">
            {Math.round(progress)}%
          </div>
        </div>
      )}
    </div>
  )
}
