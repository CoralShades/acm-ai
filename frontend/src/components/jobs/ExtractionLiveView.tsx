'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import {
  Activity,
  Bot,
  Building2,
  CheckCircle2,
  Circle,
  Layers,
  ListChecks,
  PackageCheck,
  Wifi,
  WifiOff,
  Zap,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useV3SSE } from '@/lib/hooks/useV3SSE'
import { cn } from '@/lib/utils'
import type { V3EventEnvelope } from '@/lib/types/v3-streaming'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ExtractionLiveViewProps {
  operationId: string
  enabled?: boolean
  className?: string
}

interface LiveEvent {
  id: string
  type: string
  timestamp: string
  description: string
  category: 'extraction' | 'ai' | 'bulk'
  metrics?: string[]
  isTerminal?: boolean
}

// ---------------------------------------------------------------------------
// Event descriptor helpers
// ---------------------------------------------------------------------------

function describeEvent(envelope: V3EventEnvelope): string {
  const d = envelope.data
  switch (envelope.type) {
    case 'extraction.started': {
      const pages = d.total_pages != null ? `${String(d.total_pages)} pages` : null
      const providers = Array.isArray(d.provider_sequence)
        ? (d.provider_sequence as string[]).join(', ')
        : typeof d.provider_sequence === 'string'
          ? d.provider_sequence
          : null
      const parts = ['Extraction started']
      if (pages) parts.push(pages)
      if (providers) parts.push(`providers: ${providers}`)
      return parts.join(' — ')
    }
    case 'extraction.provider_complete': {
      const provider = typeof d.provider === 'string' ? d.provider : 'Provider'
      const records = d.records_extracted != null ? `${String(d.records_extracted)} records` : null
      const duration = d.duration_ms != null ? `${String(d.duration_ms)}ms` : null
      const parts = [`${provider} finished`]
      if (records) parts.push(records)
      if (duration) parts.push(duration)
      return parts.join(' — ')
    }
    case 'extraction.consensus_complete': {
      const final = d.records_final != null ? `${String(d.records_final)} final records` : null
      const agreed = d.records_agreed != null ? `${String(d.records_agreed)} agreed` : null
      const parts = ['Consensus complete']
      if (final) parts.push(final)
      if (agreed) parts.push(agreed)
      return parts.join(' — ')
    }
    case 'ai.building_extracted': {
      const name =
        typeof d.building_name === 'string' && d.building_name
          ? d.building_name
          : typeof d.building_id === 'string'
            ? d.building_id
            : 'Building'
      const records = d.records_extracted != null ? `${String(d.records_extracted)} records` : null
      const model = typeof d.model_used === 'string' && d.model_used ? d.model_used : null
      const parts = [`Building '${name}' extracted`]
      if (records) parts.push(records)
      if (model) parts.push(`via ${model}`)
      return parts.join(' — ')
    }
    case 'ai.items_extracted': {
      const count = d.items_count != null ? String(d.items_count) : '?'
      const buildingId =
        typeof d.building_id === 'string' ? d.building_id : null
      const parts = [`${count} items extracted`]
      if (buildingId) parts.push(`for building ${buildingId}`)
      return parts.join(' ')
    }
    case 'ai.validation_complete': {
      const valid = d.records_valid != null ? `${String(d.records_valid)} valid` : null
      const corrected = d.records_corrected != null ? `${String(d.records_corrected)} corrected` : null
      const rejected = d.records_rejected != null ? `${String(d.records_rejected)} rejected` : null
      const parts = ['Validation done']
      const stats = [valid, corrected, rejected].filter(Boolean)
      if (stats.length) parts.push(stats.join(', '))
      return parts.join(' — ')
    }
    default:
      return envelope.type.replace(/[._]/g, ' ')
  }
}

function buildMetrics(envelope: V3EventEnvelope): string[] {
  const d = envelope.data
  const metrics: string[] = []
  if (d.duration_ms != null) metrics.push(`${String(d.duration_ms)}ms`)
  if (d.records_extracted != null) metrics.push(`${String(d.records_extracted)} records`)
  if (d.items_count != null) metrics.push(`${String(d.items_count)} items`)
  if (d.records_final != null) metrics.push(`${String(d.records_final)} final`)
  if (d.total_pages != null) metrics.push(`${String(d.total_pages)} pages`)
  return metrics
}

const TERMINAL_EVENT_TYPES = new Set([
  'extraction.consensus_complete',
  'extraction.complete',
  'extraction.failed',
  'ai.save_complete',
  'ai.validation_complete',
  'bulk.complete',
])

function categoryFromType(type: string): 'extraction' | 'ai' | 'bulk' {
  if (type.startsWith('ai.')) return 'ai'
  if (type.startsWith('bulk.')) return 'bulk'
  return 'extraction'
}

// ---------------------------------------------------------------------------
// Icon mapping
// ---------------------------------------------------------------------------

function EventIcon({ type, category }: { type: string; category: LiveEvent['category'] }) {
  const cls = 'h-4 w-4 shrink-0'
  switch (type) {
    case 'extraction.started':
      return <Zap className={cls} />
    case 'extraction.provider_complete':
      return <Layers className={cls} />
    case 'extraction.consensus_complete':
      return <PackageCheck className={cls} />
    case 'ai.building_extracted':
      return <Building2 className={cls} />
    case 'ai.items_extracted':
      return <ListChecks className={cls} />
    case 'ai.validation_complete':
      return <CheckCircle2 className={cls} />
    default:
      if (category === 'ai') return <Bot className={cls} />
      if (category === 'bulk') return <Activity className={cls} />
      return <Circle className={cls} />
  }
}

// ---------------------------------------------------------------------------
// Category colour classes
// ---------------------------------------------------------------------------

const categoryStyles: Record<LiveEvent['category'], {
  row: string
  iconWrapper: string
  badge: string
  terminalRow: string
}> = {
  extraction: {
    row: 'border-l-2 border-cyan-500/60 bg-cyan-50/40 dark:bg-cyan-950/20',
    iconWrapper: 'text-cyan-600 dark:text-cyan-400',
    badge: 'border-cyan-300 bg-cyan-100/60 text-cyan-800 dark:border-cyan-700 dark:bg-cyan-900/40 dark:text-cyan-200',
    terminalRow: 'border-l-2 border-cyan-500 bg-cyan-100/60 dark:bg-cyan-900/30',
  },
  ai: {
    row: 'border-l-2 border-violet-500/60 bg-violet-50/40 dark:bg-violet-950/20',
    iconWrapper: 'text-violet-600 dark:text-violet-400',
    badge: 'border-violet-300 bg-violet-100/60 text-violet-800 dark:border-violet-700 dark:bg-violet-900/40 dark:text-violet-200',
    terminalRow: 'border-l-2 border-violet-500 bg-violet-100/60 dark:bg-violet-900/30',
  },
  bulk: {
    row: 'border-l-2 border-amber-500/60 bg-amber-50/40 dark:bg-amber-950/20',
    iconWrapper: 'text-amber-600 dark:text-amber-400',
    badge: 'border-amber-300 bg-amber-100/60 text-amber-800 dark:border-amber-700 dark:bg-amber-900/40 dark:text-amber-200',
    terminalRow: 'border-l-2 border-amber-500 bg-amber-100/60 dark:bg-amber-900/30',
  },
}

// ---------------------------------------------------------------------------
// Relative time helper
// ---------------------------------------------------------------------------

function relativeTime(isoTimestamp: string): string {
  const then = new Date(isoTimestamp).getTime()
  if (Number.isNaN(then)) return ''
  const diffSec = Math.round((Date.now() - then) / 1000)
  if (diffSec < 5) return 'just now'
  if (diffSec < 60) return `${String(diffSec)}s ago`
  const diffMin = Math.round(diffSec / 60)
  if (diffMin < 60) return `${String(diffMin)}m ago`
  return `${String(Math.round(diffMin / 60))}h ago`
}

// ---------------------------------------------------------------------------
// Connection status indicator
// ---------------------------------------------------------------------------

function ConnectionBadge({ status }: { status: string }) {
  const isConnected = status === 'connected'
  const isReconnecting = status === 'reconnecting'
  const isDone = status === 'done'

  if (isDone) return null

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium border',
        isConnected
          ? 'border-green-300 bg-green-100/60 text-green-700 dark:border-green-700 dark:bg-green-900/30 dark:text-green-300'
          : isReconnecting
            ? 'border-amber-300 bg-amber-100/60 text-amber-700 dark:border-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
            : 'border-muted-foreground/30 bg-muted/40 text-muted-foreground',
      )}
    >
      {isConnected ? (
        <Wifi className="h-3 w-3" />
      ) : (
        <WifiOff className="h-3 w-3" />
      )}
      {isConnected ? 'Live' : isReconnecting ? 'Reconnecting' : 'Connecting'}
    </span>
  )
}

// ---------------------------------------------------------------------------
// Single event row
// ---------------------------------------------------------------------------

function EventRow({ event }: { event: LiveEvent }) {
  const styles = categoryStyles[event.category]
  const rowCls = event.isTerminal ? styles.terminalRow : styles.row

  return (
    <div
      className={cn(
        'flex items-start gap-3 rounded-r-md px-3 py-2.5 transition-colors',
        rowCls,
      )}
    >
      {/* Icon */}
      <span className={cn('mt-0.5', styles.iconWrapper)}>
        <EventIcon type={event.type} category={event.category} />
      </span>

      {/* Body */}
      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium text-foreground leading-snug">
            {event.description}
          </span>
          {event.isTerminal && (
            <Badge
              variant="outline"
              className="border-green-300 bg-green-100/60 text-green-700 dark:border-green-700 dark:bg-green-900/30 dark:text-green-300 text-[10px] px-1.5 py-0"
            >
              complete
            </Badge>
          )}
        </div>
        {event.metrics && event.metrics.length > 0 && (
          <div className="mt-1 flex flex-wrap gap-1">
            {event.metrics.map((m) => (
              <Badge
                key={m}
                variant="outline"
                className={cn('text-[10px] px-1.5 py-0', styles.badge)}
              >
                {m}
              </Badge>
            ))}
          </div>
        )}
      </div>

      {/* Timestamp */}
      <span className="shrink-0 text-[11px] text-muted-foreground mt-0.5 tabular-nums">
        {relativeTime(event.timestamp)}
      </span>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Animated empty-state dots
// ---------------------------------------------------------------------------

function WaitingDots() {
  return (
    <span className="inline-flex gap-1 items-end h-4" aria-hidden>
      <span className="inline-block w-1 h-1 rounded-full bg-muted-foreground/50 animate-bounce [animation-delay:0ms]" />
      <span className="inline-block w-1 h-1 rounded-full bg-muted-foreground/50 animate-bounce [animation-delay:150ms]" />
      <span className="inline-block w-1 h-1 rounded-full bg-muted-foreground/50 animate-bounce [animation-delay:300ms]" />
    </span>
  )
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function ExtractionLiveView({
  operationId,
  enabled = true,
  className,
}: ExtractionLiveViewProps) {
  const [events, setEvents] = useState<LiveEvent[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)
  const counterRef = useRef(0)

  const handleEvent = useCallback((envelope: V3EventEnvelope) => {
    const id = `${envelope.type}-${String(counterRef.current++)}`
    const category = categoryFromType(envelope.type)
    const liveEvent: LiveEvent = {
      id,
      type: envelope.type,
      timestamp: envelope.timestamp,
      description: describeEvent(envelope),
      category,
      metrics: buildMetrics(envelope),
      isTerminal: TERMINAL_EVENT_TYPES.has(envelope.type),
    }
    setEvents((prev) => [...prev, liveEvent])
  }, [])

  // Extraction-category stream
  const extractionSSE = useV3SSE({
    operationId,
    category: 'extraction',
    enabled: enabled && !!operationId,
    onEvent: handleEvent,
  })

  // AI-category stream (separate subscription)
  const aiSSE = useV3SSE({
    operationId,
    category: 'ai',
    enabled: enabled && !!operationId,
    onEvent: handleEvent,
  })

  // Auto-scroll to bottom whenever events change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
  }, [events])

  // Reset events when operationId changes
  useEffect(() => {
    setEvents([])
    counterRef.current = 0
  }, [operationId])

  const combinedStatus = (() => {
    if (extractionSSE.status === 'connected' || aiSSE.status === 'connected') return 'connected'
    if (extractionSSE.status === 'reconnecting' || aiSSE.status === 'reconnecting') return 'reconnecting'
    if (extractionSSE.status === 'done' && aiSSE.status === 'done') return 'done'
    return extractionSSE.status
  })()

  const totalCount = extractionSSE.eventCount + aiSSE.eventCount

  return (
    <Card className={cn('flex flex-col', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between gap-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Activity className="h-4 w-4 text-muted-foreground" />
            Extraction Events
          </CardTitle>
          <div className="flex items-center gap-2">
            {totalCount > 0 && (
              <span className="text-xs text-muted-foreground tabular-nums">
                {String(totalCount)} events
              </span>
            )}
            <ConnectionBadge status={combinedStatus} />
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0 pb-4">
        {/* Scrollable feed */}
        <div
          className="h-64 overflow-y-auto rounded-md border border-border/50 bg-muted/10 flex flex-col"
          role="log"
          aria-label="Extraction event feed"
          aria-live="polite"
        >
          {events.length === 0 ? (
            <div className="flex flex-1 items-center justify-center gap-2 text-sm text-muted-foreground py-8">
              <span>Waiting for extraction events</span>
              <WaitingDots />
            </div>
          ) : (
            <div className="flex flex-col gap-0.5 p-1.5">
              {events.map((event) => (
                <EventRow key={event.id} event={event} />
              ))}
              {/* Sentinel for auto-scroll */}
              <div ref={bottomRef} />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
