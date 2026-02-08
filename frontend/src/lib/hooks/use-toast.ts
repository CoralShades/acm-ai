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

    promise: toastPromise,
    loading: sonnerToast.loading,
    success: sonnerToast.success,
    error: sonnerToast.error,
    info: sonnerToast.info,
    warning: sonnerToast.warning,
    dismiss: sonnerToast.dismiss,

    createProgress: createProgressToast,
    riskToast,
    actionToast,
    criticalToast,
  }
}

export type { RiskToastOptions, ToastAction }