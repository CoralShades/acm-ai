'use client'

import { AlertCircle } from 'lucide-react'

const TOOL_LABELS: Record<string, string> = {
  search_acm_by_risk: 'ACM risk search',
  search_acm_by_building: 'ACM building search',
  search_acm_by_room: 'ACM room search',
  search_acm_by_product: 'ACM product search',
  get_acm_stats: 'ACM statistics',
  get_acm_record_detail: 'ACM record detail',
  list_acm_buildings: 'building list',
  search_documents_vector: 'vector search',
  search_documents_text: 'text search',
  preview_acm_write: 'write preview',
  write_acm_record: 'record write',
}

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
