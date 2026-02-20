'use client'

import { useEffect, useRef, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Copy, Check } from 'lucide-react'

interface ExtractionLogStreamProps {
  logEntries: string[]
}

export function ExtractionLogStream({ logEntries }: ExtractionLogStreamProps) {
  const logEndRef = useRef<HTMLDivElement>(null)
  const [copied, setCopied] = useState(false)

  // Auto-scroll to bottom when new entries arrive
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [logEntries])

  const handleCopy = async () => {
    const logText = logEntries.join('\n')
    await navigator.clipboard.writeText(logText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (logEntries.length === 0) {
    return (
      <div className="rounded-md border bg-muted/50 p-4 text-center text-sm text-muted-foreground">
        No logs available yet
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">Extraction Logs</span>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopy}
          className="h-7 gap-1.5 px-2"
        >
          {copied ? (
            <>
              <Check className="h-3 w-3" />
              <span className="text-xs">Copied</span>
            </>
          ) : (
            <>
              <Copy className="h-3 w-3" />
              <span className="text-xs">Copy All</span>
            </>
          )}
        </Button>
      </div>
      <div className="max-h-80 overflow-y-auto rounded-md border bg-muted/50 p-3">
        <div className="space-y-0.5 font-mono text-xs">
          {logEntries.map((entry, index) => (
            <div key={index} className="text-foreground/80">
              {entry}
            </div>
          ))}
          <div ref={logEndRef} />
        </div>
      </div>
    </div>
  )
}
