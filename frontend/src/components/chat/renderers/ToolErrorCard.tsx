'use client'

import { AlertCircle } from 'lucide-react'
import { TOOL_LABELS } from '@/lib/constants/tool-labels'

interface ToolErrorCardProps {
  tool: string
}

export function ToolErrorCard({ tool }: ToolErrorCardProps) {
  const label = TOOL_LABELS[tool] || tool

  return (
    <div className="flex items-center gap-2 text-xs text-destructive py-1 px-2 rounded bg-destructive/10">
      <AlertCircle className="h-3 w-3 shrink-0" />
      <span>Failed to execute {label}. Try rephrasing your request.</span>
    </div>
  )
}
