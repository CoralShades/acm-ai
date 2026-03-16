'use client'

import { useState, useEffect, useMemo } from 'react'
import { ChevronDown, Check } from 'lucide-react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { useModels } from '@/lib/hooks/use-models'
import { cn } from '@/lib/utils'

interface ChatModelSelectorProps {
  value: string
  onChange: (modelId: string) => void
  storageKey?: string
}

export function ChatModelSelector({
  value,
  onChange,
  storageKey = 'acm-chat-model',
}: ChatModelSelectorProps) {
  const { data: models, isLoading } = useModels()
  const [open, setOpen] = useState(false)

  const languageModels = useMemo(
    () => models?.filter((m) => m.type === 'language') || [],
    [models],
  )
  const currentModel = languageModels.find((m) => m.id === value)
  const displayName = currentModel?.name || 'Default'

  // Restore from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem(storageKey)
    if (saved && !value && languageModels.length > 0) {
      const exists = languageModels.some((m) => m.id === saved)
      if (exists) onChange(saved)
    }
  }, [storageKey, value, languageModels, onChange])

  // Persist selection
  useEffect(() => {
    if (value) localStorage.setItem(storageKey, value)
  }, [value, storageKey])

  if (isLoading || languageModels.length <= 1) return null

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          className={cn(
            'inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs',
            'text-muted-foreground hover:text-foreground hover:bg-accent transition-colors',
          )}
        >
          {displayName}
          <ChevronDown
            className={cn(
              'h-3 w-3 transition-transform',
              open && 'rotate-180',
            )}
          />
        </button>
      </PopoverTrigger>
      <PopoverContent align="start" className="w-56 p-1">
        {languageModels.map((model) => (
          <button
            key={model.id}
            type="button"
            onClick={() => {
              onChange(model.id)
              setOpen(false)
            }}
            className={cn(
              'flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-xs',
              'hover:bg-accent transition-colors',
              model.id === value && 'bg-accent',
            )}
          >
            <Check
              className={cn(
                'h-3 w-3 shrink-0',
                model.id === value ? 'opacity-100' : 'opacity-0',
              )}
            />
            <span className="flex-1 text-left">{model.name}</span>
            <span className="text-muted-foreground">{model.provider}</span>
          </button>
        ))}
      </PopoverContent>
    </Popover>
  )
}
