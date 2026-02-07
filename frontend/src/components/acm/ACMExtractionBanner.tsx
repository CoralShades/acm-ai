'use client'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Loader2, CheckCircle2, XCircle } from 'lucide-react'
import type { ExtractionPhase } from '@/lib/hooks/use-extraction-status'

interface ACMExtractionBannerProps {
  phase: ExtractionPhase
  recordsCreated?: number
  errorMessage?: string
  onDismiss: () => void
}

export function ACMExtractionBanner({
  phase,
  recordsCreated,
  errorMessage,
  onDismiss,
}: ACMExtractionBannerProps) {
  if (phase === 'idle') return null

  if (phase === 'extracting') {
    return (
      <Alert>
        <Loader2 className="h-4 w-4 animate-spin" />
        <AlertTitle>Extracting ACM Records</AlertTitle>
        <AlertDescription>
          AI is analyzing the document. This may take up to a minute...
        </AlertDescription>
      </Alert>
    )
  }

  if (phase === 'completed') {
    return (
      <Alert>
        <CheckCircle2 className="h-4 w-4 text-green-600" />
        <AlertTitle>Extraction Complete</AlertTitle>
        <AlertDescription className="flex items-center justify-between">
          <span>
            {recordsCreated !== undefined
              ? `${recordsCreated} record${recordsCreated !== 1 ? 's' : ''} found.`
              : 'Extraction finished successfully.'}
          </span>
          <Button variant="ghost" size="sm" onClick={onDismiss}>
            Dismiss
          </Button>
        </AlertDescription>
      </Alert>
    )
  }

  // phase === 'failed'
  return (
    <Alert variant="destructive">
      <XCircle className="h-4 w-4" />
      <AlertTitle>Extraction Failed</AlertTitle>
      <AlertDescription className="flex items-center justify-between">
        <span>{errorMessage || 'An unexpected error occurred during extraction.'}</span>
        <Button variant="ghost" size="sm" onClick={onDismiss}>
          Dismiss
        </Button>
      </AlertDescription>
    </Alert>
  )
}
