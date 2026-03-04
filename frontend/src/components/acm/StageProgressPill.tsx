'use client'

import { CheckCircle2, XCircle, Loader2, Circle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { StageState } from '@/lib/types/pipeline'

interface StageProgressPillProps {
  stage: StageState
}

const STAGE_LABELS: Record<string, string> = {
  STRUCTURE: 'Structure',
  PREFLIGHT: 'Preflight',
  ORCHESTRATOR: 'Orchestrate',
  DOCLING_EXTRACTION: 'Docling Tables',
  EXTRACT: 'Extract',
  VALIDATE: 'Validate',
  CORRECT: 'Correct',
  NO_ACCESS_RECOVERY: 'Recovery',
  STORE: 'Store',
}

export function StageProgressPill({ stage }: StageProgressPillProps) {
  const label = STAGE_LABELS[stage.id] || stage.id
  const durationMs = stage.duration_ms

  const formatDuration = (ms: number | null) => {
    if (!ms) return null
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  const getStatusStyles = () => {
    switch (stage.status) {
      case 'running':
        return {
          container: 'bg-primary text-primary-foreground animate-pulse',
          icon: <Loader2 className="h-3 w-3 animate-spin" />,
        }
      case 'complete':
        return {
          container: 'bg-emerald-500 text-white',
          icon: <CheckCircle2 className="h-3 w-3" />,
        }
      case 'failed':
        return {
          container: 'bg-destructive text-destructive-foreground',
          icon: <XCircle className="h-3 w-3" />,
        }
      case 'skipped':
        return {
          container: 'bg-muted text-muted-foreground',
          icon: <Circle className="h-3 w-3" />,
          strikethrough: true,
        }
      case 'pending':
      default:
        return {
          container: 'bg-muted text-muted-foreground',
          icon: <Circle className="h-3 w-3" />,
        }
    }
  }

  const { container, icon, strikethrough } = getStatusStyles()

  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium transition-all',
        container
      )}
    >
      {icon}
      <span className={cn(strikethrough && 'line-through')}>{label}</span>
      {stage.status === 'complete' && durationMs && (
        <span className="opacity-75">({formatDuration(durationMs)})</span>
      )}
    </div>
  )
}
