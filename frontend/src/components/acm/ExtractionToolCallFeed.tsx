'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { ChevronDown, ChevronUp, CheckCircle2, Loader2, Wrench } from 'lucide-react'

export interface ToolCallEntry {
  id: string
  name: string
  status: 'running' | 'completed'
  args?: string
  result?: string
  startedAt: number
  completedAt?: number
}

interface ExtractionToolCallFeedProps {
  toolCalls: ToolCallEntry[]
}

/**
 * Live feed of active extraction operations. Shows each graph node
 * transition as a tool call entry with status, args, and results.
 *
 * Story: E17-S4 Extraction Tool Call Observability
 */
export function ExtractionToolCallFeed({ toolCalls }: ExtractionToolCallFeedProps) {
  const [expanded, setExpanded] = useState(false)

  if (toolCalls.length === 0) return null

  const runningCount = toolCalls.filter((t) => t.status === 'running').length

  return (
    <div className="space-y-1">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setExpanded(!expanded)}
        className="h-7 gap-1.5 px-2"
      >
        <Wrench className="h-3 w-3" />
        {expanded ? (
          <>
            <ChevronUp className="h-3 w-3" />
            <span className="text-xs">Hide Operations</span>
          </>
        ) : (
          <>
            <ChevronDown className="h-3 w-3" />
            <span className="text-xs">
              Active Operations ({runningCount} running, {toolCalls.length} total)
            </span>
          </>
        )}
      </Button>
      {expanded && (
        <div className="max-h-48 space-y-1 overflow-auto rounded-md border p-2">
          {toolCalls.map((tc) => (
            <ToolCallRow key={tc.id} entry={tc} />
          ))}
        </div>
      )}
    </div>
  )
}

function ToolCallRow({ entry }: { entry: ToolCallEntry }) {
  const elapsed = entry.completedAt
    ? ((entry.completedAt - entry.startedAt) / 1000).toFixed(1)
    : ((Date.now() - entry.startedAt) / 1000).toFixed(1)

  return (
    <div className="flex items-center gap-2 text-xs">
      {entry.status === 'running' ? (
        <Loader2 className="h-3 w-3 animate-spin text-primary" />
      ) : (
        <CheckCircle2 className="h-3 w-3 text-green-500" />
      )}
      <span className="font-mono font-medium">{entry.name}</span>
      {entry.args && (
        <span className="truncate text-muted-foreground" title={entry.args}>
          {entry.args}
        </span>
      )}
      {entry.result && (
        <span className="text-muted-foreground">{entry.result}</span>
      )}
      <span className="ml-auto shrink-0 text-muted-foreground">{elapsed}s</span>
    </div>
  )
}
