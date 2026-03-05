'use client'

/**
 * useExtractionSSE — thin facade that composes useExtractionProgress + useAGUIStream
 * into a single API for the ExtractionProgress page.
 *
 * Story: E33-S1 Upload Wizard + Extraction Progress
 */

import { useExtractionProgress, type ExtractionPhase } from './use-extraction-progress'
import { useAGUIStream } from './use-agui-stream'
import type { PipelineRunState } from '@/lib/types/pipeline'

export interface ExtractionSSEResult {
  phase: ExtractionPhase
  pipelineState: PipelineRunState | null
  logEntries: string[]
  recordsCreated: number | undefined
  errorMessage: string | undefined
  commandId: string | null
  aguiStep: string | null
  aguiConnected: boolean
  reasoningText: string | undefined
  startTracking: (commandId: string) => void
  dismiss: () => void
}

const SESSION_KEY_PREFIX = 'acm-extraction-progress-'

export function useExtractionSSE(sourceId: string): ExtractionSSEResult {
  // Delegate all SSE/polling logic to the existing hook
  const {
    phase,
    pipelineState,
    logEntries,
    recordsCreated,
    errorMessage,
    startTracking,
    dismiss,
  } = useExtractionProgress(sourceId)

  // Derive the active commandId from sessionStorage unconditionally so that
  // the AG-UI stream reconnects correctly on page reload (phase is briefly
  // 'idle' on first render, so gating on phase === 'extracting' would miss
  // the stored commandId).
  let commandId: string | null = null
  if (typeof window !== 'undefined') {
    try {
      const stored = sessionStorage.getItem(`${SESSION_KEY_PREFIX}${sourceId}`)
      if (stored) {
        commandId = JSON.parse(stored).commandId ?? null
      }
    } catch {
      // Ignore malformed session data
    }
  }

  // Connect AG-UI stream using the derived commandId
  const { currentStep, reasoningTokens, connected } = useAGUIStream(commandId)

  return {
    phase,
    pipelineState,
    logEntries,
    recordsCreated,
    errorMessage,
    commandId,
    aguiStep: currentStep,
    aguiConnected: connected,
    reasoningText: reasoningTokens || undefined,
    startTracking,
    dismiss,
  }
}
