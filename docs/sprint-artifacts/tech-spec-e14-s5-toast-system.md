# Tech Spec: E14-S5 - Enhance Toast System with Promise-Based Patterns

> **Story:** E14-S5
> **Epic:** E14 - UX & Enterprise Readiness
> **Status:** Ready for Dev
> **Created:** 2026-02-08
> **Complexity:** Medium (3-5 days)

---

## Overview

This story enhances the toast notification system using Sonner's advanced patterns to provide informative, context-aware feedback during long-running operations. The implementation focuses on promise-based toasts for async operations, manual ID-based toasts for progress tracking, risk-aware styling, and action buttons for human-in-the-loop workflows.

**Current State:**
- `useToast` hook provides basic `success` and `error` (destructive) toasts
- Sonner is configured with theme awareness in `frontend/src/components/ui/sonner.tsx`
- Extraction uses polling via `useExtractionStatus` + `ACMExtractionBanner` component
- Export operations (`useExportACMCsv`, `useExportACMExcel`) show simple success/error toasts

**Target State:**
- Typed toast patterns utility with promise-based, loading, and risk-aware variants
- Extraction operations use `toast.promise()` for start feedback, loading toast with ID for progress
- Export operations use `toast.promise()` for download lifecycle
- Risk-aware toasts with border-l-4 styling using VAEA semantic colors
- Persistent toasts for critical alerts with explicit dismiss
- Action buttons in toasts for navigation and retry workflows

---

## User Story

**As a** user
**I want** informative toast notifications during long operations
**So that** I know what's happening with extraction, export, and processing

---

## Acceptance Criteria

- [ ] Sonner `toast.promise()` used for extraction start/complete/fail
- [ ] Sonner `toast.promise()` used for Excel/CSV export
- [ ] Loading toast with manual ID for SSE/polling progress updates
- [ ] Risk-aware toast variants (border-l-4 with risk colors)
- [ ] Persistent toasts (`duration: Infinity`) for critical alerts
- [ ] Action buttons in toasts for human-in-the-loop workflows

---

## Technical Design

### 1. Toast Patterns Utility

Create a centralized utility that provides typed helpers for common toast patterns.

**File:** `frontend/src/lib/toast-patterns.ts` (new)

```typescript
/**
 * Toast Pattern Utilities
 *
 * Provides typed helpers for common toast patterns using Sonner.
 * All patterns support theme-aware styling via globals.css CSS variables.
 */

import { toast } from 'sonner'
import type { ExternalToast } from 'sonner'

// ============================================================================
// TYPES
// ============================================================================

export type RiskLevel = 'low' | 'medium' | 'high' | 'presumed'

export interface ToastAction {
  label: string
  onClick: () => void
}

export interface RiskToastOptions {
  level: RiskLevel
  title: string
  description?: string
  action?: ToastAction
  persistent?: boolean
  closeButton?: boolean
}

export interface ProgressToastController {
  updateProgress: (message: string, description?: string) => void
  complete: (message: string, description?: string) => void
  fail: (message: string, description?: string) => void
  dismiss: () => void
}

// ============================================================================
// PROMISE-BASED TOASTS
// ============================================================================

/**
 * Promise-based toast for async operations
 * Automatically shows loading, success, or error based on promise state
 *
 * @example
 * const extractPromise = acmApi.extract(sourceId)
 * toastPromise(extractPromise, {
 *   loading: 'Starting extraction...',
 *   success: (result) => `Extraction started: ${result.message}`,
 *   error: 'Failed to start extraction'
 * })
 */
export function toastPromise<T>(
  promise: Promise<T>,
  messages: {
    loading: string
    success: string | ((data: T) => string)
    error: string | ((error: any) => string)
  },
  options?: ExternalToast
) {
  return toast.promise(promise, messages, options)
}

// ============================================================================
// PROGRESS TOASTS (Manual ID-based)
// ============================================================================

/**
 * Create a loading toast that can be updated with progress
 * Returns a controller for updating, completing, or failing the toast
 *
 * @example
 * const progress = createProgressToast('Processing document...', {
 *   description: 'Stage 1/7: Structure Analysis'
 * })
 *
 * // Later, update it:
 * progress.updateProgress('Processing document...', 'Stage 2/7: Preflight')
 *
 * // When done:
 * progress.complete('Extraction complete', '12 records extracted')
 */
export function createProgressToast(
  message: string,
  options?: { description?: string; persistent?: boolean }
): ProgressToastController {
  const toastId = toast.loading(message, {
    description: options?.description,
    duration: options?.persistent ? Infinity : undefined,
  })

  return {
    updateProgress: (newMessage: string, description?: string) => {
      toast.loading(newMessage, {
        id: toastId,
        description,
        duration: options?.persistent ? Infinity : undefined,
      })
    },
    complete: (successMessage: string, description?: string) => {
      toast.success(successMessage, {
        id: toastId,
        description,
        duration: 5000,
      })
    },
    fail: (errorMessage: string, description?: string) => {
      toast.error(errorMessage, {
        id: toastId,
        description,
        duration: 10000,
      })
    },
    dismiss: () => {
      toast.dismiss(toastId)
    },
  }
}

// ============================================================================
// RISK-AWARE TOASTS
// ============================================================================

/**
 * Risk-aware toast with colored left border
 * Uses VAEA semantic colors from globals.css
 *
 * Risk colors (from globals.css):
 * - low: oklch(0.75 0.15 150) - green
 * - medium: oklch(0.7 0.18 75) - amber
 * - high: oklch(0.6 0.22 25) - red
 * - presumed: oklch(0.65 0.15 300) - purple
 *
 * @example
 * riskToast({
 *   level: 'high',
 *   title: 'High Risk Materials Detected',
 *   description: '3 items flagged for immediate attention',
 *   action: { label: 'Review', onClick: () => router.push('/acm?filter=high') },
 *   persistent: true
 * })
 */
export function riskToast(options: RiskToastOptions): string | number {
  const borderColorClass = {
    low: 'border-l-[hsl(var(--risk-low))]',
    medium: 'border-l-[hsl(var(--risk-medium))]',
    high: 'border-l-[hsl(var(--risk-high))]',
    presumed: 'border-l-[hsl(var(--risk-presumed))]',
  }[options.level]

  const toastOptions: ExternalToast = {
    description: options.description,
    duration: options.persistent ? Infinity : 5000,
    closeButton: options.closeButton ?? options.persistent,
    className: `border-l-4 ${borderColorClass}`,
    action: options.action,
  }

  // Use info variant for all risk toasts to avoid semantic color conflicts
  return toast.info(options.title, toastOptions)
}

// ============================================================================
// ACTION TOASTS
// ============================================================================

/**
 * Toast with action button
 *
 * @example
 * actionToast({
 *   title: 'Extraction needs review',
 *   description: '3 records have low confidence scores',
 *   action: { label: 'Review Now', onClick: () => router.push('/acm?filter=low-confidence') },
 *   variant: 'warning',
 *   persistent: true
 * })
 */
export function actionToast(options: {
  title: string
  description?: string
  action: ToastAction
  variant?: 'default' | 'warning' | 'error' | 'info'
  persistent?: boolean
}): string | number {
  const toastOptions: ExternalToast = {
    description: options.description,
    duration: options.persistent ? Infinity : 5000,
    closeButton: options.persistent,
    action: options.action,
  }

  switch (options.variant) {
    case 'warning':
      return toast.warning(options.title, toastOptions)
    case 'error':
      return toast.error(options.title, toastOptions)
    case 'info':
      return toast.info(options.title, toastOptions)
    default:
      return toast(options.title, toastOptions)
  }
}

// ============================================================================
// PERSISTENT CRITICAL TOASTS
// ============================================================================

/**
 * Critical alert toast that persists until manually dismissed
 *
 * @example
 * criticalToast({
 *   title: 'Database Connection Lost',
 *   description: 'Please check your network connection',
 *   action: { label: 'Retry', onClick: checkConnection }
 * })
 */
export function criticalToast(options: {
  title: string
  description?: string
  action?: ToastAction
}): string | number {
  return toast.error(options.title, {
    description: options.description,
    duration: Infinity,
    closeButton: true,
    action: options.action,
  })
}
```

### 2. Enhanced useToast Hook

Update the existing `useToast` hook to expose additional Sonner methods while maintaining backward compatibility.

**File:** `frontend/src/lib/hooks/use-toast.ts` (modify)

```typescript
import { toast as sonnerToast } from 'sonner'
import {
  toastPromise,
  createProgressToast,
  riskToast,
  actionToast,
  criticalToast,
  type RiskToastOptions,
  type ToastAction,
} from '@/lib/toast-patterns'

type ToastProps = {
  title?: string
  description?: string
  variant?: 'default' | 'destructive'
}

export function useToast() {
  return {
    // Legacy API (backward compatible)
    toast: ({ title, description, variant = 'default' }: ToastProps) => {
      if (variant === 'destructive') {
        sonnerToast.error(title || 'Error', {
          description,
        })
      } else {
        sonnerToast.success(title || 'Success', {
          description,
        })
      }
    },

    // Advanced APIs
    promise: toastPromise,
    loading: sonnerToast.loading,
    success: sonnerToast.success,
    error: sonnerToast.error,
    info: sonnerToast.info,
    warning: sonnerToast.warning,
    dismiss: sonnerToast.dismiss,

    // Pattern utilities
    createProgress: createProgressToast,
    riskToast,
    actionToast,
    criticalToast,
  }
}

// Re-export types
export type { RiskToastOptions, ToastAction }
```

### 3. Update ACM Extraction Hook

Modify `useExtractACM` to use promise-based toasts.

**File:** `frontend/src/lib/hooks/use-acm.ts` (modify)

```typescript
/**
 * Hook to trigger ACM extraction
 */
export function useExtractACM(onCommandStarted?: (commandId: string) => void) {
  const { promise } = useToast()

  return useMutation({
    mutationFn: (sourceId: string) => {
      const extractPromise = acmApi.extract(sourceId)

      // Wrap with promise toast
      promise(extractPromise, {
        loading: 'Starting ACM extraction...',
        success: (result) => result.message || 'Extraction started successfully',
        error: 'Failed to start ACM extraction',
      })

      return extractPromise
    },
    onSuccess: (result) => {
      if (onCommandStarted && result.command_id) {
        onCommandStarted(result.command_id)
      }
    },
  })
}
```

### 4. Update Export Hooks

Modify `useExportACMCsv` and `useExportACMExcel` to use promise-based toasts.

**File:** `frontend/src/lib/hooks/use-acm.ts` (modify)

```typescript
/**
 * Hook to export ACM records as CSV
 */
export function useExportACMCsv() {
  const { promise } = useToast()

  return useMutation({
    mutationFn: async (sourceId: string) => {
      const exportPromise = acmApi.exportCsv(sourceId).then((blob) => {
        // Create download link
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `acm_export_${sourceId}.csv`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        return blob
      })

      promise(exportPromise, {
        loading: 'Generating CSV export...',
        success: 'CSV downloaded successfully',
        error: 'Failed to export CSV',
      })

      return exportPromise
    },
  })
}

/**
 * Hook to export ACM records as Excel
 */
export function useExportACMExcel() {
  const { promise } = useToast()

  return useMutation({
    mutationFn: async (sourceId: string) => {
      const exportPromise = acmApi.exportExcel(sourceId).then((blob) => {
        // Create download link
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `acm_export_${sourceId}.xlsx`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        return blob
      })

      promise(exportPromise, {
        loading: 'Generating Excel export...',
        success: 'Excel file downloaded successfully',
        error: 'Failed to export Excel file',
      })

      return exportPromise
    },
  })
}
```

### 5. Progress Toast Integration with Extraction Status

Update `useExtractionStatus` to support progress toast updates.

**File:** `frontend/src/lib/hooks/use-extraction-status.ts` (modify)

Add optional toast integration:

```typescript
'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { acmApi } from '@/lib/api/acm'
import { ACM_QUERY_KEYS } from './use-acm'
import { useToast } from './use-toast'
import type { ProgressToastController } from '@/lib/toast-patterns'

export type ExtractionPhase = 'idle' | 'extracting' | 'completed' | 'failed'

interface ExtractionStatus {
  phase: ExtractionPhase
  recordsCreated: number | undefined
  errorMessage: string | undefined
  startTracking: (commandId: string, options?: { showToast?: boolean; sourceName?: string }) => void
  dismiss: () => void
}

const SESSION_KEY_PREFIX = 'acm-extraction-'

export function useExtractionStatus(sourceId: string): ExtractionStatus {
  const queryClient = useQueryClient()
  const { createProgress } = useToast()
  const sessionKey = `${SESSION_KEY_PREFIX}${sourceId}`
  const toastControllerRef = useRef<ProgressToastController | null>(null)

  // Read initial commandId from sessionStorage (survives tab navigation)
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

  // Poll job status while we have a commandId and phase is extracting
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

  // React to job status changes
  useEffect(() => {
    if (!jobStatus || phase !== 'extracting') return

    if (jobStatus.status === 'completed') {
      setPhase('completed')
      setRecordsCreated(jobStatus.result?.records_created)
      sessionStorage.removeItem(sessionKey)

      // Update toast if exists
      if (toastControllerRef.current) {
        toastControllerRef.current.complete(
          'Extraction complete',
          `${jobStatus.result?.records_created || 0} records extracted`
        )
        toastControllerRef.current = null
      }

      // Invalidate ACM queries so grid refreshes
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

      // Update toast if exists
      if (toastControllerRef.current) {
        toastControllerRef.current.fail('Extraction failed', errMsg)
        toastControllerRef.current = null
      }
    } else if (jobStatus.status === 'running' && toastControllerRef.current) {
      // Update progress toast with current stage if available
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
      sessionStorage.setItem(sessionKey, newCommandId)

      // Create progress toast if requested
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
    sessionStorage.removeItem(sessionKey)

    // Dismiss toast if exists
    if (toastControllerRef.current) {
      toastControllerRef.current.dismiss()
      toastControllerRef.current = null
    }
  }, [sessionKey])

  return { phase, recordsCreated, errorMessage, startTracking, dismiss }
}
```

### 6. Risk-Aware Toast Example Usage

Example component showing risk-aware toast usage (not a file to create, just documentation):

```typescript
// In a component that detects high-risk ACM records
import { useToast } from '@/lib/hooks/use-toast'
import { useRouter } from 'next/navigation'

function ACMRiskAlert({ riskLevel, count, sourceId }: {
  riskLevel: 'high' | 'medium' | 'low'
  count: number
  sourceId: string
}) {
  const { riskToast } = useToast()
  const router = useRouter()

  useEffect(() => {
    if (riskLevel === 'high' && count > 0) {
      riskToast({
        level: 'high',
        title: 'High Risk Materials Detected',
        description: `${count} items flagged for immediate attention`,
        action: {
          label: 'Review',
          onClick: () => router.push(`/sources/${sourceId}?tab=acm&filter=high`)
        },
        persistent: true,
        closeButton: true
      })
    }
  }, [riskLevel, count, sourceId])

  return null
}
```

### 7. Action Toast for Human-in-the-Loop

Example showing action toast for low-confidence extraction results:

```typescript
// In extraction completion handler
const { actionToast } = useToast()

if (jobStatus.result?.low_confidence_count > 0) {
  actionToast({
    title: 'Extraction needs review',
    description: `${jobStatus.result.low_confidence_count} records have low confidence scores`,
    action: {
      label: 'Review Now',
      onClick: () => router.push(`/sources/${sourceId}?tab=acm&filter=low-confidence`)
    },
    variant: 'warning',
    persistent: true
  })
}
```

---

## File Changes

| File | Type | Description |
|------|------|-------------|
| `frontend/src/lib/toast-patterns.ts` | Create | Toast pattern utilities with typed helpers |
| `frontend/src/lib/hooks/use-toast.ts` | Modify | Expose advanced Sonner APIs and pattern utilities |
| `frontend/src/lib/hooks/use-acm.ts` | Modify | Update `useExtractACM`, `useExportACMCsv`, `useExportACMExcel` to use promise toasts |
| `frontend/src/lib/hooks/use-extraction-status.ts` | Modify | Add optional progress toast integration |

**Notes:**
- `frontend/src/components/acm/ACMExtractionBanner.tsx` can remain as-is for now (banner UI still valid)
- `frontend/src/components/ui/sonner.tsx` requires no changes (already theme-aware)
- `frontend/src/app/globals.css` already has risk color CSS variables (no changes needed)

---

## Dependencies

### Must Exist Before Implementation
- [ ] Sonner library installed (`sonner` package)
- [ ] Theme-aware Toaster component (`frontend/src/components/ui/sonner.tsx`)
- [ ] Risk color CSS variables in `globals.css`
- [ ] `useExtractionStatus` hook with polling
- [ ] ACM API client methods (`acmApi.extract`, `acmApi.exportCsv`, `acmApi.exportExcel`)

### Optional Enhancements (Future Stories)
- **E14-S6**: Multi-stage pipeline progress store (will enhance progress toasts with stage-level detail)
- **E14-S7**: SSE/WebSocket integration (will replace polling with real-time updates)
- **AG-UI Integration**: CopilotKit events for extraction pipeline stages

---

## Testing

### Unit Tests
Create `frontend/src/lib/__tests__/toast-patterns.test.ts`:

```typescript
import { describe, it, expect, vi } from 'vitest'
import { toast } from 'sonner'
import {
  toastPromise,
  createProgressToast,
  riskToast,
  actionToast,
  criticalToast
} from '../toast-patterns'

vi.mock('sonner', () => ({
  toast: {
    promise: vi.fn(),
    loading: vi.fn(() => 'toast-id'),
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    dismiss: vi.fn()
  }
}))

describe('toast-patterns', () => {
  it('toastPromise calls toast.promise with correct args', () => {
    const promise = Promise.resolve('data')
    const messages = {
      loading: 'Loading',
      success: 'Success',
      error: 'Error'
    }
    toastPromise(promise, messages)
    expect(toast.promise).toHaveBeenCalledWith(promise, messages, undefined)
  })

  it('createProgressToast returns controller', () => {
    const controller = createProgressToast('Processing')
    expect(controller).toHaveProperty('updateProgress')
    expect(controller).toHaveProperty('complete')
    expect(controller).toHaveProperty('fail')
    expect(controller).toHaveProperty('dismiss')
  })

  it('riskToast applies correct border class', () => {
    riskToast({
      level: 'high',
      title: 'High Risk',
      description: 'Test'
    })
    expect(toast.info).toHaveBeenCalledWith(
      'High Risk',
      expect.objectContaining({
        className: expect.stringContaining('border-l-4')
      })
    )
  })

  it('criticalToast sets duration to Infinity', () => {
    criticalToast({ title: 'Critical' })
    expect(toast.error).toHaveBeenCalledWith(
      'Critical',
      expect.objectContaining({
        duration: Infinity,
        closeButton: true
      })
    )
  })
})
```

### Integration Tests
Test ACM hooks with promise toasts:

```typescript
import { renderHook, waitFor } from '@testing-library/react'
import { useExtractACM, useExportACMCsv } from '../use-acm'
import { toast } from 'sonner'

describe('useExtractACM with promise toast', () => {
  it('shows loading, then success toast', async () => {
    const { result } = renderHook(() => useExtractACM())

    result.current.mutate('source:123')

    await waitFor(() => {
      expect(toast.promise).toHaveBeenCalledWith(
        expect.any(Promise),
        expect.objectContaining({
          loading: 'Starting ACM extraction...'
        })
      )
    })
  })
})
```

### Manual Testing Checklist

**Promise Toasts:**
- [ ] Trigger ACM extraction - verify loading → success toast
- [ ] Trigger extraction with API error - verify loading → error toast
- [ ] Export CSV - verify loading → success toast with download
- [ ] Export Excel - verify loading → success toast with download

**Progress Toasts:**
- [ ] Trigger extraction with progress toast enabled
- [ ] Verify loading toast appears with "Processing document..."
- [ ] Poll job status - verify toast updates stay visible
- [ ] Wait for completion - verify toast transitions to success with record count
- [ ] Trigger extraction that fails - verify toast transitions to error

**Risk-Aware Toasts:**
- [ ] Simulate high-risk detection - verify red border-left toast
- [ ] Simulate medium-risk - verify amber border-left toast
- [ ] Simulate low-risk - verify green border-left toast
- [ ] Verify persistent toast requires manual dismiss

**Action Toasts:**
- [ ] Trigger low-confidence extraction result
- [ ] Verify action toast with "Review Now" button
- [ ] Click action button - verify navigation to filtered ACM register
- [ ] Verify persistent action toast has close button

**Theme Awareness:**
- [ ] Toggle light/dark mode - verify toast colors adapt correctly
- [ ] Verify risk border colors are visible in both themes

---

## Implementation Notes

### Risk Color Mapping (from globals.css)
```css
/* Light mode */
--risk-low: oklch(0.75 0.15 150);         /* Green */
--risk-medium: oklch(0.7 0.18 75);        /* Amber */
--risk-high: oklch(0.6 0.22 25);          /* Red */
--risk-presumed: oklch(0.65 0.15 300);    /* Purple */
```

These are already defined in `frontend/src/app/globals.css` and automatically adapt to dark mode via the `.dark` selector.

### Toast Duration Guidelines
- **Default success/info:** 5000ms (5 seconds)
- **Loading/progress:** `Infinity` until manually updated
- **Error:** 10000ms (10 seconds) - longer for users to read
- **Critical:** `Infinity` with close button
- **Action toasts:** `Infinity` or 10000ms depending on urgency

### Sonner Configuration
Current Toaster config in `frontend/src/components/ui/sonner.tsx` is already theme-aware and requires no changes. It uses CSS variables for styling which automatically work with the new risk-aware toast patterns.

### Backward Compatibility
The enhanced `useToast` hook maintains the existing `toast({ title, description, variant })` API. All existing code will continue to work without modification. New code can adopt the advanced patterns incrementally.

---

## Estimated Complexity

**Medium (3-5 days)**

- **Day 1:** Create `toast-patterns.ts` with typed utilities
- **Day 2:** Update `use-toast.ts` hook, modify `use-acm.ts` hooks (extraction + export)
- **Day 3:** Enhance `use-extraction-status.ts` with progress toast integration
- **Day 4:** Write unit tests, integration tests
- **Day 5:** Manual testing, documentation, edge case fixes

**Risk Factors:**
- Toast timing coordination with polling (mitigated by using ref for controller)
- Theme color contrast in risk toasts (mitigated by using existing tested CSS variables)
- User confusion if too many toasts appear (mitigated by dismissing previous toasts on new operations)

**Definition of Done:**
- All acceptance criteria met
- Unit tests pass (>80% coverage on new utility)
- Integration tests pass for ACM hooks
- Manual testing checklist completed
- Toast patterns documented in `docs/development/ui-patterns.md` (or create if not exists)
- No console errors in browser during toast lifecycle
- Dark mode verified working for all toast variants
