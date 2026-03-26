'use client'

import { useState, useRef, useEffect, type KeyboardEvent } from 'react'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Send, Loader2, TableProperties } from 'lucide-react'

const IS_MAC =
  typeof navigator !== 'undefined' &&
  navigator.userAgent.toUpperCase().indexOf('MAC') >= 0

interface SmartChatInputProps {
  inProgress: boolean
  onSend: (message: string) => void
  hasAcmData?: boolean
  includeAcmContext?: boolean
  onAcmToggle?: (value: boolean) => void
  [key: string]: unknown
}

export function SmartChatInput({
  inProgress,
  onSend,
  hasAcmData = false,
  includeAcmContext = false,
  onAcmToggle,
}: SmartChatInputProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const prevInProgress = useRef(false)

  // Clear input when send starts (handles CopilotKit internal sends)
  useEffect(() => {
    if (inProgress && !prevInProgress.current) {
      setInput('')
    }
    prevInProgress.current = inProgress
  }, [inProgress])

  const keyHint = IS_MAC ? '\u2318+Enter' : 'Ctrl+Enter'

  const handleSend = () => {
    if (input.trim() && !inProgress) {
      onSend(input.trim())
      setInput('')
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    const isModifierPressed = IS_MAC ? e.metaKey : e.ctrlKey
    if (e.key === 'Enter' && isModifierPressed) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex-shrink-0 p-4 space-y-3 border-t">
      {/* ACM toggle row */}
      {hasAcmData && onAcmToggle && (
        <div className="flex items-center gap-2">
          <TableProperties className="h-4 w-4 text-muted-foreground" />
          <Label htmlFor="smart-acm-context" className="text-xs cursor-pointer">
            ACM Data
          </Label>
          <Switch
            id="smart-acm-context"
            checked={includeAcmContext}
            onCheckedChange={onAcmToggle}
            disabled={inProgress}
          />
        </div>
      )}

      <div className="flex gap-2 items-end">
        <Textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={`Ask a question... (${keyHint} to send)`}
          disabled={inProgress}
          className="flex-1 min-h-[40px] max-h-[100px] resize-none py-2 px-3"
          rows={1}
        />
        <Button
          onClick={handleSend}
          disabled={!input.trim() || inProgress}
          size="icon"
          className="h-[40px] w-[40px] flex-shrink-0"
        >
          {inProgress ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  )
}
