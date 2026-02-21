'use client'

/**
 * PreviewRecordBadge — visual indicator for streaming/preview records
 * in the AG Grid during an active extraction.
 *
 * Story: E17-S2 Incremental Record Streaming to AG Grid
 */
export function PreviewRecordBadge() {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-xs font-medium text-primary">
      <span className="relative flex h-2 w-2">
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
      </span>
      Streaming
    </span>
  )
}
