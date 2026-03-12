'use client'

/**
 * UploadWizard — 3-step wizard for uploading a SAMP PDF and triggering extraction.
 *
 * Step 1: Drop/select PDF file
 * Step 2: Select extraction mode (standard | ai_enhanced)
 * Step 3: Confirm details and trigger upload + extraction
 *
 * Story: E33-S1 Upload Wizard + Extraction Progress
 */

import { useRef, useState, useCallback, DragEvent, ChangeEvent } from 'react'
import { useRouter } from 'next/navigation'
import { Upload, FileText, Zap, CheckCircle2, AlertCircle } from 'lucide-react'
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

type WizardStep = 1 | 2 | 3
type ExtractionMode = 'standard' | 'ai_enhanced'

const STEP_TITLES: Record<WizardStep, string> = {
  1: 'Upload PDF',
  2: 'Select Extraction Mode',
  3: 'Confirm & Extract',
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
  const [mode, setMode] = useState<ExtractionMode>('standard')
  const [isDragOver, setIsDragOver] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
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
    else if (step === 2) setStep(3)
  }, [step, file])

  const handleBack = useCallback(() => {
    if (step === 2) setStep(1)
    else if (step === 3) setStep(2)
  }, [step])

  // ─── Step 3: Submit ───────────────────────────────────────────────────────

  const handleExtract = useCallback(async () => {
    if (!file || isSubmitting) return
    setIsSubmitting(true)
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
      return
    }

    try {
      const extractResponse = await acmApi.extract(sourceId, { mode })
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
  }, [file, isSubmitting, mode, router, toastError])

  // ─── Render helpers ───────────────────────────────────────────────────────

  const renderStep1 = () => (
    <div className="space-y-6" data-testid="upload-step-1">
      <div>
        <h2 className="text-xl font-semibold mb-1">Upload SAMP Document</h2>
        <p className="text-sm text-muted-foreground">
          Upload the School Asbestos Management Plan PDF to begin extraction.
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

  const renderStep2 = () => (
    <div className="space-y-6" data-testid="upload-step-2">
      <div>
        <h2 className="text-xl font-semibold mb-1">Select Extraction Mode</h2>
        <p className="text-sm text-muted-foreground">
          Choose how the AI should process your document.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {/* Standard mode card */}
        <button
          type="button"
          aria-pressed={mode === 'standard'}
          onClick={() => setMode('standard')}
          className={cn(
            'flex flex-col items-start gap-3 rounded-lg border-2 p-5 text-left transition-colors',
            mode === 'standard'
              ? 'border-primary bg-primary/5'
              : 'border-border hover:border-primary/40'
          )}
          data-testid="mode-standard"
        >
          <div className="flex items-center gap-2">
            <FileText
              className={cn(
                'h-5 w-5',
                mode === 'standard' ? 'text-primary' : 'text-muted-foreground'
              )}
            />
            <span className="font-semibold">Standard</span>
            {mode === 'standard' && (
              <CheckCircle2 className="ml-auto h-4 w-4 text-primary" />
            )}
          </div>
          <p className="text-sm text-muted-foreground">
            Fast extraction using Docling table detection. Best for clean, well-formatted
            SAMP documents.
          </p>
          <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
            Recommended
          </span>
        </button>

        {/* AI-Enhanced mode card */}
        <button
          type="button"
          aria-pressed={mode === 'ai_enhanced'}
          onClick={() => setMode('ai_enhanced')}
          className={cn(
            'flex flex-col items-start gap-3 rounded-lg border-2 p-5 text-left transition-colors',
            mode === 'ai_enhanced'
              ? 'border-primary bg-primary/5'
              : 'border-border hover:border-primary/40'
          )}
          data-testid="mode-ai-enhanced"
        >
          <div className="flex items-center gap-2">
            <Zap
              className={cn(
                'h-5 w-5',
                mode === 'ai_enhanced' ? 'text-primary' : 'text-muted-foreground'
              )}
            />
            <span className="font-semibold">AI-Enhanced</span>
            {mode === 'ai_enhanced' && (
              <CheckCircle2 className="ml-auto h-4 w-4 text-primary" />
            )}
          </div>
          <p className="text-sm text-muted-foreground">
            Slower. Uses AI reasoning to recover records from non-standard layouts and
            damaged tables.
          </p>
          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-700 dark:bg-amber-900/30 dark:text-amber-300">
            Slower — use for complex documents
          </span>
        </button>
      </div>
    </div>
  )

  const renderStep3 = () => (
    <div className="space-y-6" data-testid="upload-step-3">
      <div>
        <h2 className="text-xl font-semibold mb-1">Confirm &amp; Start Extraction</h2>
        <p className="text-sm text-muted-foreground">
          Review your selections before starting the extraction pipeline.
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

          <div className="flex items-start gap-3">
            {mode === 'ai_enhanced' ? (
              <Zap className="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground" />
            ) : (
              <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground" />
            )}
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">Mode</p>
              <p className="font-medium">
                {mode === 'ai_enhanced' ? 'AI-Enhanced' : 'Standard'}
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
          {isSubmitting ? 'Uploading...' : 'Extract'}
        </Button>
      </div>
    </div>
  )

  return (
    <div className="flex flex-col h-full" data-testid="upload-wizard">
      {/* Wizard step header */}
      <WizardStepHeader
        currentStep={step}
        totalSteps={3}
        stepTitle={STEP_TITLES[step]}
        onCancel={handleCancel}
        onNext={step < 3 ? handleNext : undefined}
        nextLabel="Next"
        nextDisabled={step === 1 && !file}
      />

      {/* Step content */}
      <div className="flex-1 overflow-y-auto py-8">
        <div className="max-w-2xl mx-auto px-6">
          {step === 1 && renderStep1()}
          {step === 2 && renderStep2()}
          {step === 3 && renderStep3()}

          {/* Back button for steps 2 and 3 */}
          {step > 1 && (
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
