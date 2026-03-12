'use client'

/**
 * QuickUploadDialog — lightweight modal for uploading a PDF without leaving the current page.
 *
 * - Single-step: drop/select PDF → immediate upload + extraction (standard mode)
 * - Shows inline progress (uploading → extracting → done)
 * - On success: toast with link to extraction progress, stays on current page
 * - "Use full wizard" link for users who want mode selection (routes to /upload)
 */

import { useRef, useState, useCallback, DragEvent, ChangeEvent } from 'react'
import { useRouter } from 'next/navigation'
import { Upload, CheckCircle2, Loader2, ExternalLink, FileText } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { sourcesApi } from '@/lib/api/sources'
import { acmApi } from '@/lib/api/acm'
import { useToast } from '@/lib/hooks/use-toast'
import { cn } from '@/lib/utils'
import Link from 'next/link'

type UploadPhase = 'idle' | 'uploading' | 'extracting' | 'done' | 'error'

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

interface QuickUploadDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function QuickUploadDialog({ open, onOpenChange }: QuickUploadDialogProps) {
  const router = useRouter()
  const { error: toastError, success: toastSuccess } = useToast()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const [file, setFile] = useState<File | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const [phase, setPhase] = useState<UploadPhase>('idle')
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [resultSourceId, setResultSourceId] = useState<string | null>(null)

  const reset = useCallback(() => {
    setFile(null)
    setPhase('idle')
    setErrorMsg(null)
    setResultSourceId(null)
  }, [])

  const handleClose = useCallback((nextOpen: boolean) => {
    if (!nextOpen && phase !== 'uploading' && phase !== 'extracting') {
      reset()
      onOpenChange(false)
    }
  }, [phase, reset, onOpenChange])

  const acceptFile = useCallback((incoming: File | null) => {
    if (!incoming) return
    if (incoming.type !== 'application/pdf' && !incoming.name.endsWith('.pdf')) {
      toastError('Only PDF files are accepted.')
      return
    }
    setFile(incoming)
    setErrorMsg(null)
  }, [toastError])

  const handleDragOver = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragOver(false)
    acceptFile(e.dataTransfer.files?.[0] ?? null)
  }, [acceptFile])

  const handleFileInputChange = useCallback((e: ChangeEvent<HTMLInputElement>) => {
    acceptFile(e.target.files?.[0] ?? null)
  }, [acceptFile])

  const handleUploadAndExtract = useCallback(async () => {
    if (!file) return
    setPhase('uploading')
    setErrorMsg(null)

    let sourceId: string
    try {
      const sourceResponse = await sourcesApi.create({
        type: 'upload',
        title: file.name,
        file,
      })
      sourceId = sourceResponse.id
    } catch (err: unknown) {
      setPhase('error')
      setErrorMsg(err instanceof Error ? err.message : 'Upload failed. Please try again.')
      return
    }

    setPhase('extracting')
    try {
      const extractResponse = await acmApi.extract(sourceId)
      const commandId = extractResponse.command_id

      sessionStorage.setItem(`acm-extraction-${sourceId}`, commandId)
      sessionStorage.setItem(
        `acm-extraction-progress-${sourceId}`,
        JSON.stringify({ commandId, phase: 'extracting', pipelineState: null, logEntries: [] })
      )

      setResultSourceId(sourceId)
      setPhase('done')
      toastSuccess('Extraction started! Track progress from the notification below.')
    } catch (err: unknown) {
      setPhase('error')
      setErrorMsg(err instanceof Error ? err.message : 'Extraction could not be started.')
    }
  }, [file, toastSuccess])

  const handleGoToProgress = useCallback(() => {
    if (resultSourceId) {
      onOpenChange(false)
      reset()
      router.push(`/extraction/${encodeURIComponent(resultSourceId)}`)
    }
  }, [resultSourceId, onOpenChange, reset, router])

  const isProcessing = phase === 'uploading' || phase === 'extracting'

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md" data-testid="quick-upload-dialog">
        <DialogHeader>
          <DialogTitle>Quick Upload</DialogTitle>
          <DialogDescription>
            Drop a SAMP PDF to start extraction immediately.
          </DialogDescription>
        </DialogHeader>

        {phase === 'done' && resultSourceId ? (
          /* Success state */
          <div className="flex flex-col items-center gap-4 py-6">
            <CheckCircle2 className="h-12 w-12 text-emerald-500" />
            <div className="text-center">
              <p className="font-medium">Extraction started!</p>
              <p className="text-sm text-muted-foreground mt-1">
                Your document is being processed in the background.
              </p>
            </div>
            <div className="flex gap-2">
              <Button onClick={handleGoToProgress}>
                View Progress
              </Button>
              <Button
                variant="outline"
                onClick={() => {
                  reset()
                }}
              >
                Upload Another
              </Button>
            </div>
          </div>
        ) : (
          /* Upload state */
          <div className="space-y-4">
            {/* Drop zone */}
            <div
              role="button"
              tabIndex={0}
              aria-label="Drop PDF here or click to select"
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => !isProcessing && fileInputRef.current?.click()}
              onKeyDown={(e) => {
                if (!isProcessing && (e.key === 'Enter' || e.key === ' ')) fileInputRef.current?.click()
              }}
              className={cn(
                'flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed px-6 py-8 text-center transition-colors',
                isProcessing
                  ? 'cursor-default border-border bg-muted/20'
                  : isDragOver
                    ? 'cursor-pointer border-primary bg-primary/5'
                    : file
                      ? 'cursor-pointer border-emerald-500/60 bg-emerald-500/5'
                      : 'cursor-pointer border-border hover:border-primary/50 hover:bg-muted/30'
              )}
            >
              {isProcessing ? (
                <>
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                  <p className="text-sm font-medium">
                    {phase === 'uploading' ? 'Uploading...' : 'Starting extraction...'}
                  </p>
                </>
              ) : file ? (
                <>
                  <FileText className="h-8 w-8 text-emerald-500" />
                  <div>
                    <p className="font-medium text-sm">{file.name}</p>
                    <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                  </div>
                  <p className="text-xs text-muted-foreground">Click to replace</p>
                </>
              ) : (
                <>
                  <Upload className="h-8 w-8 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium">Drop your PDF here</p>
                    <p className="text-xs text-muted-foreground">or click to browse</p>
                  </div>
                </>
              )}
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              className="sr-only"
              aria-hidden="true"
              onChange={handleFileInputChange}
            />

            {/* Error message */}
            {phase === 'error' && errorMsg && (
              <p className="text-sm text-destructive">{errorMsg}</p>
            )}

            {/* Actions */}
            <div className="flex items-center justify-between">
              <Link
                href="/upload"
                onClick={() => onOpenChange(false)}
                className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors"
              >
                <ExternalLink className="h-3 w-3" />
                Full wizard (mode selection)
              </Link>
              <Button
                onClick={handleUploadAndExtract}
                disabled={!file || isProcessing}
                size="sm"
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                    Processing...
                  </>
                ) : (
                  'Upload & Extract'
                )}
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
