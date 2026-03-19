'use client'

/**
 * UploadWizard — 2-step wizard for uploading a PDF and triggering AI extraction.
 *
 * Step 1: Drop/select PDF file
 * Step 2: Confirm details and trigger upload + AI extraction
 *
 * Story: E33-S1 Upload Wizard + Extraction Progress
 */

import { useRef, useState, useCallback, useEffect, DragEvent, ChangeEvent } from 'react'
import { useRouter } from 'next/navigation'
import { Upload, FileText, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { WizardStepHeader } from '@/components/acm/WizardStepHeader'
import { sourcesApi } from '@/lib/api/sources'
import { acmApi } from '@/lib/api/acm'
import { useToast } from '@/lib/hooks/use-toast'
import { cn } from '@/lib/utils'

type WizardStep = 1 | 2

const STEP_TITLES: Record<WizardStep, string> = {
  1: 'Upload PDF',
  2: 'Confirm & Extract',
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function UploadWizard() {
  const router = useRouter()
  const { error: toastError } = useToast()

  const [step, setStep] = useState<WizardStep>(1)
  const [file, setFile] = useState<File | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [processingStage, setProcessingStage] = useState<'uploading' | 'starting' | null>(null)
  const [fatalError, setFatalError] = useState<string | null>(null)

  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleCancel = useCallback(() => {
    router.push('/jobs')
  }, [router])

  // ─── Step 1: File selection ───────────────────────────────────────────────

  const acceptFile = useCallback((incoming: File | null) => {
    if (!incoming) return
    // Accept only PDF
    if (incoming.type !== 'application/pdf' && !incoming.name.endsWith('.pdf')) {
      toastError('Only PDF files are accepted.')
      return
    }
    setFile(incoming)
  }, [toastError])

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.preventDefault()
      setIsDragOver(false)
      const dropped = e.dataTransfer.files?.[0] ?? null
      acceptFile(dropped)
    },
    [acceptFile]
  )

  const handleFileInputChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const selected = e.target.files?.[0] ?? null
      acceptFile(selected)
    },
    [acceptFile]
  )

  // ─── Step navigation ──────────────────────────────────────────────────────

  const handleNext = useCallback(() => {
    if (step === 1 && file) setStep(2)
  }, [step, file])

  const handleBack = useCallback(() => {
    if (step === 2) setStep(1)
  }, [step])

  // ─── Step 3: Submit ───────────────────────────────────────────────────────

  const handleExtract = useCallback(async () => {
    if (!file || isSubmitting) return
    setIsSubmitting(true)
    setProcessingStage('uploading')
    setFatalError(null)

    let sourceId: string
    try {
      const sourceResponse = await sourcesApi.create({
        type: 'upload',
        title: file.name,
        file,
      })
      sourceId = sourceResponse.id
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Could not upload file. Please try again.'
      setFatalError(message)
      setIsSubmitting(false)
      setProcessingStage(null)
      return
    }

    setProcessingStage('starting')

    try {
      const extractResponse = await acmApi.extract(sourceId)
      const commandId = extractResponse.command_id

      // Persist commandId under the simpler key for extract/page.tsx fallback compatibility
      sessionStorage.setItem(`acm-extraction-${sourceId}`, commandId)

      // Also write the structured key used by useExtractionProgress
      sessionStorage.setItem(
        `acm-extraction-progress-${sourceId}`,
        JSON.stringify({
          commandId,
          phase: 'extracting',
          pipelineState: null,
          logEntries: [],
        })
      )
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Extraction could not be started.'
      toastError(message)
      // Non-fatal: source was created, navigate to jobs page instead
      router.push('/jobs')
      return
    }

    router.push(`/extraction/${encodeURIComponent(sourceId)}`)
  }, [file, isSubmitting, router, toastError])

  // ─── Processing animation state cycling ───────────────────────────────────
  // When submitting, we cycle dots for the current stage label to give a
  // visual indication that work is happening even on slow connections.
  const [dotCount, setDotCount] = useState(0)
  useEffect(() => {
    if (!isSubmitting) {
      setDotCount(0)
      return
    }
    const interval = window.setInterval(() => {
      setDotCount((n) => (n + 1) % 4)
    }, 400)
    return () => window.clearInterval(interval)
  }, [isSubmitting])

  // ─── Render helpers ───────────────────────────────────────────────────────

  const renderProcessing = () => {
    const stages: Array<{ key: 'uploading' | 'starting'; label: string }> = [
      { key: 'uploading', label: 'Uploading document' },
      { key: 'starting', label: 'Starting extraction' },
    ]
    const dots = '.'.repeat(dotCount)

    return (
      <div
        className="flex flex-col items-center justify-center gap-8 py-12"
        data-testid="upload-processing"
        role="status"
        aria-live="polite"
        aria-label="Processing your document"
      >
        <Loader2 className="h-12 w-12 animate-spin text-primary" aria-hidden />

        <div className="space-y-3 w-full max-w-xs">
          {stages.map(({ key, label }) => {
            const isActive = processingStage === key
            const isDone =
              (key === 'uploading' && processingStage === 'starting') ||
              (key === 'uploading' && processingStage === null && !isSubmitting)

            return (
              <div
                key={key}
                className={cn(
                  'flex items-center gap-3 rounded-md border px-4 py-3 transition-colors',
                  isActive && 'border-primary/60 bg-primary/5',
                  isDone && 'border-emerald-500/50 bg-emerald-500/5 text-emerald-700 dark:text-emerald-300',
                  !isActive && !isDone && 'border-border/40 bg-muted/30 text-muted-foreground'
                )}
              >
                {isDone ? (
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500" aria-hidden />
                ) : isActive ? (
                  <Loader2 className="h-4 w-4 shrink-0 animate-spin text-primary" aria-hidden />
                ) : (
                  <span className="h-4 w-4 shrink-0 rounded-full border border-border/60" aria-hidden />
                )}
                <span className="text-sm font-medium">
                  {isActive ? `${label}${dots}` : label}
                </span>
              </div>
            )
          })}
        </div>

        <p className="text-xs text-muted-foreground text-center max-w-xs">
          Please wait — you will be redirected to the extraction progress page automatically.
        </p>
      </div>
    )
  }

  const renderStep1 = () => (
    <div className="space-y-6" data-testid="upload-step-1">
      <div>
        <h2 className="text-xl font-semibold mb-1">Upload Document</h2>
        <p className="text-sm text-muted-foreground">
          Upload an ACM document (PDF) to begin AI extraction.
        </p>
      </div>

      {/* Drop zone */}
      <div
        role="button"
        tabIndex={0}
        aria-label="Drop PDF here or click to select"
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') fileInputRef.current?.click()
        }}
        className={cn(
          'flex flex-col items-center justify-center gap-4 rounded-lg border-2 border-dashed px-8 py-12 text-center transition-colors cursor-pointer',
          isDragOver
            ? 'border-primary bg-primary/5'
            : file
            ? 'border-emerald-500/60 bg-emerald-500/5'
            : 'border-border hover:border-primary/50 hover:bg-muted/30'
        )}
      >
        {file ? (
          <>
            <CheckCircle2 className="h-10 w-10 text-emerald-500" />
            <div>
              <p className="font-medium text-foreground">{file.name}</p>
              <p className="text-sm text-muted-foreground">{formatFileSize(file.size)}</p>
            </div>
            <p className="text-xs text-muted-foreground">Click to replace file</p>
          </>
        ) : (
          <>
            <Upload className="h-10 w-10 text-muted-foreground" />
            <div>
              <p className="font-medium">Drag and drop your PDF here</p>
              <p className="text-sm text-muted-foreground">or click to browse files</p>
            </div>
            <p className="text-xs text-muted-foreground">PDF files only</p>
          </>
        )}
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,application/pdf"
        className="sr-only"
        aria-hidden="true"
        onChange={handleFileInputChange}
        data-testid="file-input"
      />
    </div>
  )

  const renderStep2 = () => {
    // While submitting, replace step content with the animated processing overlay
    if (isSubmitting) {
      return renderProcessing()
    }

    return (
      <div className="space-y-6" data-testid="upload-step-2">
        <div>
          <h2 className="text-xl font-semibold mb-1">Confirm &amp; Start Extraction</h2>
          <p className="text-sm text-muted-foreground">
            Review your document before starting the AI extraction pipeline.
          </p>
        </div>

        {/* Summary card */}
        <Card>
          <CardContent className="pt-6 space-y-4">
            <div className="flex items-start gap-3">
              <FileText className="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground" />
              <div className="min-w-0">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">File</p>
                <p className="truncate font-medium" data-testid="confirm-file-name">
                  {file?.name}
                </p>
                <p className="text-sm text-muted-foreground">
                  {file ? formatFileSize(file.size) : ''}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Extract button */}
        <div className="flex justify-end">
          <Button
            size="lg"
            onClick={handleExtract}
            disabled={isSubmitting}
            data-testid="extract-button"
            className="min-w-32"
          >
            Extract
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full" data-testid="upload-wizard">
      {/* Wizard step header */}
      <WizardStepHeader
        currentStep={step}
        totalSteps={2}
        stepTitle={STEP_TITLES[step]}
        onCancel={handleCancel}
        onNext={step < 2 ? handleNext : undefined}
        nextLabel="Next"
        nextDisabled={step === 1 && !file}
      />

      {/* Step content */}
      <div className="flex-1 overflow-y-auto py-8">
        <div className="max-w-2xl mx-auto px-6">
          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}

          {/* Back button for step 2 */}
          {step === 2 && !isSubmitting && (
            <div className="mt-4">
              <Button variant="ghost" size="sm" onClick={handleBack}>
                Back
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Fatal error dialog (source creation failure) */}
      <Dialog
        open={fatalError !== null}
        onOpenChange={(open) => {
          if (!open) setFatalError(null)
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-destructive" />
              Could not upload file
            </DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">{fatalError}</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setFatalError(null)}>
              Try Again
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
