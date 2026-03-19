'use client'

import type { BuildingStreamStatus } from '@/lib/stores/buildingStore'

const STATUS_CONFIG: Record<BuildingStreamStatus, { label: string; className: string }> = {
  detected: {
    label: 'Detected',
    className: 'bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/20',
  },
  extracting: {
    label: 'Extracting',
    className: 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/20 animate-pulse',
  },
  validating: {
    label: 'Validating',
    className: 'bg-purple-500/15 text-purple-600 dark:text-purple-400 border-purple-500/20 animate-pulse',
  },
  saving: {
    label: 'Saving',
    className: 'bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border-cyan-500/20 animate-pulse',
  },
  complete: {
    label: 'Saved',
    className: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/20',
  },
  error: {
    label: 'Error',
    className: 'bg-red-500/15 text-red-600 dark:text-red-400 border-red-500/20',
  },
}

interface BuildingStatusBadgeProps {
  status: BuildingStreamStatus
}

export function BuildingStatusBadge({ status }: BuildingStatusBadgeProps) {
  const config = STATUS_CONFIG[status]
  return (
    <span
      className={`inline-flex items-center rounded-md border px-1.5 py-0.5 text-[10px] font-medium leading-none ${config.className}`}
    >
      {config.label}
    </span>
  )
}
