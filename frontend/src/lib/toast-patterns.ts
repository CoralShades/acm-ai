import { toast } from 'sonner'
import type { ExternalToast } from 'sonner'

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

export function toastPromise<T>(
  promise: Promise<T>,
  messages: {
    loading: string
    success: string | ((data: T) => string)
    error: string | ((error: unknown) => string)
  }
) {
  return toast.promise(promise, {
    loading: messages.loading,
    success: messages.success,
    error: messages.error,
  })
}

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

  return toast.info(options.title, toastOptions)
}

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
