'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { acmApi } from '@/lib/api/acm'
import { ACM_QUERY_KEYS } from './use-acm'
import { useToast } from './use-toast'
import type { ProgressToastController } from '@/lib/toast-patterns'
import type { PipelineRunState, StageId } from '@/lib/types/pipeline'

export type ExtractionPhase = 'idle' | 'extracting' | 'completed' | 'failed'

interface ExtractionStatus {
  phase: ExtractionPhase
  recordsCreated: number | undefined
  errorMessage: string | undefined
  currentStageId: StageId | undefined
  currentStageLabel: string | undefined
  currentStageIndex: number | undefined
  totalStages: number
  progressPercent: number | undefined
  startTracking: (commandId: string, options?: { showToast?: boolean; sourceName?: string }) => void
  dismiss: () => void
}

const SESSION_KEY_PREFIX = 'acm-extraction-'
const STAGE_ORDER: StageId[] = [
  'STRUCTURE',
  'PREFLIGHT',
  'ORCHESTRATOR',
  'EXTRACT',
  'VALIDATE',
  'CORRECT',
  'STORE',
]
const STAGE_LABELS: Record<StageId, string> = {
  STRUCTURE: 'Document Structure',
  PREFLIGHT: 'Preflight',
  ORCHESTRATOR: 'Orchestrator',
  EXTRACT: 'Extract',
  VALIDATE: 'Validate',
  CORRECT: 'Correct',
  STORE: 'Store',
}

interface StageSnapshot {
  stageId: StageId | undefined
  stageIndex: number | undefined
  progressPercent: number | undefined
}

function getStageSnapshot(state: PipelineRunState | undefined): StageSnapshot {
  if (!state) {
    return {
      stageId: undefined,
      stageIndex: undefined,
      progressPercent: undefined,
    }
  }

  const runningStageId = STAGE_ORDER.find(
    (stageId) => state.stages[stageId]?.status === 'running'
  )
  if (runningStageId) {
    const runningIndex = STAGE_ORDER.indexOf(runningStageId)
    const runningProgress = state.stages[runningStageId]?.progress ?? 0
    return {
      stageId: runningStageId,
      stageIndex: runningIndex + 1,
      progressPercent: Math.round(
        ((runningIndex + Math.max(0, runningProgress)) / STAGE_ORDER.length) * 100
      ),
    }
  }

  const failedStageId = STAGE_ORDER.find(
    (stageId) => state.stages[stageId]?.status === 'failed'
  )
  if (failedStageId) {
    const failedIndex = STAGE_ORDER.indexOf(failedStageId)
    return {
      stageId: failedStageId,
      stageIndex: failedIndex + 1,
      progressPercent: Math.round((failedIndex / STAGE_ORDER.length) * 100),
    }
  }

  const completedStages = STAGE_ORDER.filter(
    (stageId) => state.stages[stageId]?.status === 'complete'
  )
  if (completedStages.length > 0) {
    const lastCompleted = completedStages[completedStages.length - 1]
    return {
      stageId: lastCompleted,
      stageIndex: STAGE_ORDER.indexOf(lastCompleted) + 1,
      progressPercent: Math.round((completedStages.length / STAGE_ORDER.length) * 100),
    }
  }

  return {
    stageId: STAGE_ORDER[0],
    stageIndex: 1,
    progressPercent: 0,
  }
}

export function useExtractionStatus(
  sourceId: string,
  initialCommandId?: string
): ExtractionStatus {
  const queryClient = useQueryClient()
  const { createProgress } = useToast()
  const sessionKey = `${SESSION_KEY_PREFIX}${sourceId}`
  const toastControllerRef = useRef<ProgressToastController | null>(null)

  const [commandId, setCommandId] = useState<string | null>(() => {
    if (typeof window === 'undefined') return null
    return sessionStorage.getItem(sessionKey) || null
  })

  const [phase, setPhase] = useState<ExtractionPhase>(() => {
    if (typeof window === 'undefined') return 'idle'
    return sessionStorage.getItem(sessionKey) ? 'extracting' : 'idle'
  })

  const [recordsCreated, setRecordsCreated] = useState<number | undefined>(undefined)
  const [errorMessage, setErrorMessage] = useState<string | undefined>(undefined)
  const [currentStageId, setCurrentStageId] = useState<StageId | undefined>(undefined)
  const [currentStageIndex, setCurrentStageIndex] = useState<number | undefined>(undefined)
  const [progressPercent, setProgressPercent] = useState<number | undefined>(undefined)

  useEffect(() => {
    if (!initialCommandId || commandId || phase !== 'idle') return

    setCommandId(initialCommandId)
    setPhase('extracting')
    sessionStorage.setItem(sessionKey, initialCommandId)
  }, [commandId, initialCommandId, phase, sessionKey])

  const { data: jobStatus } = useQuery({
    queryKey: ['extraction-job', commandId],
    queryFn: () => acmApi.getJobStatus(commandId!),
    enabled: !!commandId && phase === 'extracting',
    refetchInterval: (query) => {
      const data = query.state.data
      if (!data) return 3000
      if (data.status === 'new' || data.status === 'running') {
        return 3000
      }
      return false
    },
    staleTime: 0,
    retry: 2,
  })

  useEffect(() => {
    if (!jobStatus || phase !== 'extracting') return

    const stageSnapshot = getStageSnapshot(jobStatus.progress?.state)
    setCurrentStageId(stageSnapshot.stageId)
    setCurrentStageIndex(stageSnapshot.stageIndex)
    setProgressPercent(stageSnapshot.progressPercent)

    if (jobStatus.status === 'completed') {
      setPhase('completed')
      setRecordsCreated(jobStatus.result?.records_created)
      sessionStorage.removeItem(sessionKey)

      if (toastControllerRef.current) {
        toastControllerRef.current.complete(
          'Extraction complete',
          `${jobStatus.result?.records_created || 0} records extracted`
        )
        toastControllerRef.current = null
      }

      queryClient.invalidateQueries({
        queryKey: ['acm', 'records', sourceId],
      })
      queryClient.invalidateQueries({
        queryKey: ACM_QUERY_KEYS.stats(sourceId),
      })
    } else if (jobStatus.status === 'failed' || jobStatus.status === 'canceled') {
      const errMsg = jobStatus.result?.error_message || jobStatus.error_message || 'Extraction failed'
      setPhase('failed')
      setErrorMessage(errMsg)
      sessionStorage.removeItem(sessionKey)

      if (toastControllerRef.current) {
        toastControllerRef.current.fail('Extraction failed', errMsg)
        toastControllerRef.current = null
      }
    } else if (jobStatus.status === 'running' && toastControllerRef.current) {
      toastControllerRef.current.updateProgress(
        'Processing document...',
        'AI is analyzing the document'
      )
    }
  }, [jobStatus, phase, sourceId, sessionKey, queryClient])

  const startTracking = useCallback(
    (newCommandId: string, options?: { showToast?: boolean; sourceName?: string }) => {
      setCommandId(newCommandId)
      setPhase('extracting')
      setRecordsCreated(undefined)
      setErrorMessage(undefined)
      setCurrentStageId(undefined)
      setCurrentStageIndex(undefined)
      setProgressPercent(undefined)
      sessionStorage.setItem(sessionKey, newCommandId)

      if (options?.showToast) {
        toastControllerRef.current = createProgress(
          `Extracting ${options.sourceName || 'document'}...`,
          {
            description: 'AI is analyzing the document',
            persistent: true,
          }
        )
      }
    },
    [sessionKey, createProgress]
  )

  const dismiss = useCallback(() => {
    setPhase('idle')
    setCommandId(null)
    setRecordsCreated(undefined)
    setErrorMessage(undefined)
    setCurrentStageId(undefined)
    setCurrentStageIndex(undefined)
    setProgressPercent(undefined)
    sessionStorage.removeItem(sessionKey)

    if (toastControllerRef.current) {
      toastControllerRef.current.dismiss()
      toastControllerRef.current = null
    }
  }, [sessionKey])

  return {
    phase,
    recordsCreated,
    errorMessage,
    currentStageId,
    currentStageLabel: currentStageId ? STAGE_LABELS[currentStageId] : undefined,
    currentStageIndex,
    totalStages: STAGE_ORDER.length,
    progressPercent,
    startTracking,
    dismiss,
  }
}
