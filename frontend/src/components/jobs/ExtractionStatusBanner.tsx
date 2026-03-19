'use client'

import { useEffect, useRef, useState } from 'react'
import { Activity, CheckCircle2, XCircle, Zap } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useExtractionStream } from '@/lib/hooks/useExtractionStream'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ExtractionStatusBannerProps {
  operationId: string
  enabled?: boolean
  className?: string
}

// ---------------------------------------------------------------------------
// Elapsed time hook
// ---------------------------------------------------------------------------

function useElapsedSeconds(startedAt: string | null): number {
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    if (!startedAt) {
      setElapsed(0)
      return
    }
    const startMs = new Date(startedAt).getTime()
    if (Number.isNaN(startMs)) return

    const tick = () => setElapsed(Math.round((Date.now() - startMs) / 1000))
    tick()
    const id = setInterval(tick, 1000)
    return () => clearInterval(id)
  }, [startedAt])

  return elapsed
}

// ---------------------------------------------------------------------------
// Phase icon
// ---------------------------------------------------------------------------

function PhaseIcon({ phase }: { phase: string }) {
  const cls = 'h-3.5 w-3.5 shrink-0'
  switch (phase) {
    case 'started':
      return <Zap className={cn(cls, 'animate-pulse text-cyan-400')} />
    case 'processing':
      return <Activity className={cn(cls, 'animate-pulse text-violet-400')} />
    case 'complete':
      return <CheckCircle2 className={cn(cls, 'text-emerald-400')} />
    case 'failed':
      return <XCircle className={cn(cls, 'text-red-400')} />
    default:
      return null
  }
}

// ---------------------------------------------------------------------------
// Phase badge
// ---------------------------------------------------------------------------

const phaseBadgeClass: Record<string, string> = {
  started:
    'border-cyan-700 bg-cyan-900/40 text-cyan-300',
  processing:
    'border-violet-700 bg-violet-900/40 text-violet-300',
  complete:
    'border-emerald-700 bg-emerald-900/40 text-emerald-300',
  failed:
    'border-red-700 bg-red-900/40 text-red-300',
}

const phaseLabel: Record<string, string> = {
  started: 'starting',
  processing: 'processing',
  complete: 'complete',
  failed: 'failed',
}

// ---------------------------------------------------------------------------
// Status text
// ---------------------------------------------------------------------------

function StatusText({
  phase,
  totalPages,
  recordsSaved,
  buildingsCount,
  durationMs,
  error,
  elapsed,
}: {
  phase: string
  totalPages: number
  recordsSaved: number
  buildingsCount: number
  durationMs: number
  error: string | null
  elapsed: number
}) {
  switch (phase) {
    case 'started':
      return (
        <span className="text-sm text-zinc-300">
          Extraction started
          {totalPages > 0 && (
            <>
              {' — analyzing '}
              <span className="font-mono text-zinc-100">{totalPages}</span>
              {' pages'}
            </>
          )}
          {elapsed > 0 && (
            <span className="ml-2 font-mono text-xs text-zinc-500">
              {elapsed}s
            </span>
          )}
        </span>
      )
    case 'processing':
      return (
        <span className="text-sm text-zinc-300">
          Processing extraction data
          {elapsed > 0 && (
            <span className="ml-2 font-mono text-xs text-zinc-500">
              {elapsed}s
            </span>
          )}
          <span className="ml-1 inline-flex gap-0.5 items-end">
            <span className="inline-block w-1 h-1 rounded-full bg-zinc-500 animate-bounce [animation-delay:0ms]" />
            <span className="inline-block w-1 h-1 rounded-full bg-zinc-500 animate-bounce [animation-delay:150ms]" />
            <span className="inline-block w-1 h-1 rounded-full bg-zinc-500 animate-bounce [animation-delay:300ms]" />
          </span>
        </span>
      )
    case 'complete':
      return (
        <span className="text-sm text-zinc-300">
          Extraction complete{' — '}
          <span className="font-mono text-zinc-100">{recordsSaved}</span>
          {' records, '}
          <span className="font-mono text-zinc-100">{buildingsCount}</span>
          {' buildings in '}
          <span className="font-mono text-zinc-100">
            {(durationMs / 1000).toFixed(1)}s
          </span>
        </span>
      )
    case 'failed':
      return (
        <span className="text-sm text-zinc-300">
          Extraction failed
          {error && (
            <>
              {' — '}
              <span className="text-red-300">{error}</span>
            </>
          )}
        </span>
      )
    default:
      return null
  }
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

const AUTO_DISMISS_MS = 5000

export function ExtractionStatusBanner({
  operationId,
  enabled = true,
  className,
}: ExtractionStatusBannerProps) {
  const { phase, totalPages, recordsSaved, buildingsCount, durationMs, error, startedAt } =
    useExtractionStream(operationId, enabled)

  const elapsed = useElapsedSeconds(
    phase === 'started' || phase === 'processing' ? startedAt : null
  )

  // Auto-dismiss after completion
  const [dismissed, setDismissed] = useState(false)
  const [fading, setFading] = useState(false)
  const dismissTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (phase === 'complete') {
      setDismissed(false)
      setFading(false)
      // Start fade after AUTO_DISMISS_MS - 500ms, then hide
      dismissTimerRef.current = setTimeout(() => {
        setFading(true)
        setTimeout(() => setDismissed(true), 500)
      }, AUTO_DISMISS_MS - 500)
    }
    return () => {
      if (dismissTimerRef.current !== null) {
        clearTimeout(dismissTimerRef.current)
      }
    }
  }, [phase])

  // Reset dismissed state when a new extraction starts
  useEffect(() => {
    if (phase === 'started') {
      setDismissed(false)
      setFading(false)
    }
  }, [phase])

  if (phase === 'idle' || dismissed) return null

  return (
    <div
      className={cn(
        'flex items-center gap-2.5 rounded-lg border border-zinc-700 bg-zinc-900 px-3.5 py-2 transition-opacity duration-500',
        fading ? 'opacity-0' : 'opacity-100',
        className
      )}
      role="status"
      aria-live="polite"
    >
      <PhaseIcon phase={phase} />

      <Badge
        variant="outline"
        className={cn(
          'shrink-0 text-[10px] px-1.5 py-0 font-medium',
          phaseBadgeClass[phase] ?? ''
        )}
      >
        {phaseLabel[phase] ?? phase}
      </Badge>

      <StatusText
        phase={phase}
        totalPages={totalPages}
        recordsSaved={recordsSaved}
        buildingsCount={buildingsCount}
        durationMs={durationMs}
        error={error}
        elapsed={elapsed}
      />
    </div>
  )
}
