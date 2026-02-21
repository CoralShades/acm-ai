'use client'

import { useState, useRef, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { ChevronDown, ChevronUp, Brain } from 'lucide-react'

interface ExtractionThinkingPanelProps {
  reasoningText: string
}

/**
 * Collapsible panel displaying reasoning tokens from DeepSeek R1 or
 * Claude extended thinking during extraction.
 *
 * Story: E17-S3 Reasoning Token Display
 */
export function ExtractionThinkingPanel({ reasoningText }: ExtractionThinkingPanelProps) {
  const [expanded, setExpanded] = useState(false)
  const scrollRef = useRef<HTMLPreElement>(null)

  // Auto-scroll to bottom when new reasoning text arrives
  useEffect(() => {
    if (expanded && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [reasoningText, expanded])

  if (!reasoningText) return null

  return (
    <div className="space-y-1">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setExpanded(!expanded)}
        className="h-7 gap-1.5 px-2"
      >
        <Brain className="h-3 w-3" />
        {expanded ? (
          <>
            <ChevronUp className="h-3 w-3" />
            <span className="text-xs">Hide Thinking</span>
          </>
        ) : (
          <>
            <ChevronDown className="h-3 w-3" />
            <span className="text-xs">Agent Thinking</span>
          </>
        )}
      </Button>
      {expanded && (
        <pre
          ref={scrollRef}
          className="max-h-48 overflow-auto rounded-md bg-muted/50 p-3 font-mono text-xs leading-relaxed text-muted-foreground"
        >
          {reasoningText}
          <span className="animate-pulse">|</span>
        </pre>
      )}
    </div>
  )
}
