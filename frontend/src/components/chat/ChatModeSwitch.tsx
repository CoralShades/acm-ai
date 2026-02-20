'use client'

import { useState, useEffect } from 'react'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { MessageSquare, Sparkles } from 'lucide-react'
import type { ChatMode } from '@/lib/types/smart-chat'

interface ChatModeSwitchProps {
  onChange: (mode: ChatMode) => void
  defaultMode?: ChatMode
  storageKey?: string
}

export function ChatModeSwitch({
  onChange,
  defaultMode = 'classic',
  storageKey = 'chat-mode',
}: ChatModeSwitchProps) {
  const [mode, setMode] = useState<ChatMode>(() => {
    if (typeof window !== 'undefined') {
      const saved = sessionStorage.getItem(storageKey)
      if (saved === 'classic' || saved === 'smart') return saved
    }
    return defaultMode
  })

  useEffect(() => {
    sessionStorage.setItem(storageKey, mode)
    onChange(mode)
  }, [mode, storageKey, onChange])

  return (
    <Tabs value={mode} onValueChange={(v) => setMode(v as ChatMode)}>
      <TabsList className="h-8">
        <TabsTrigger value="classic" className="gap-1 text-xs px-3 h-7">
          <MessageSquare className="h-3 w-3" />
          Classic
        </TabsTrigger>
        <TabsTrigger value="smart" className="gap-1 text-xs px-3 h-7">
          <Sparkles className="h-3 w-3" />
          Smart Chat
        </TabsTrigger>
      </TabsList>
    </Tabs>
  )
}
