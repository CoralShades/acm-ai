'use client'

import { useState } from 'react'
import { Check } from 'lucide-react'

interface ChatChoiceCardProps {
  question: string
  options: { label: string; value: string }[]
  choiceId: string
  onSelect: (value: string) => void
}

/**
 * Renders an ask_user_choice result as an inline card with clickable option buttons.
 * Once an option is selected, the card becomes read-only with the selected option highlighted.
 */
export function ChatChoiceCard({
  question,
  options,
  choiceId,
  onSelect,
}: ChatChoiceCardProps) {
  const [selected, setSelected] = useState<string | null>(null)

  const handleSelect = (value: string) => {
    if (selected !== null) return // already answered — ignore
    setSelected(value)
    onSelect(value)
  }

  return (
    <div
      className="border rounded-lg p-3 my-2 text-sm bg-background"
      aria-label={`Choice prompt: ${question}`}
    >
      {/* Question text */}
      <p className="text-sm font-medium mb-2.5">{question}</p>

      {/* Option buttons */}
      <div className="flex flex-wrap gap-2" role="group" aria-label="Choice options">
        {options.map((option) => {
          const isSelected = selected === option.value
          const isDisabled = selected !== null && !isSelected

          return (
            <button
              key={`${choiceId}-${option.value}`}
              type="button"
              disabled={isDisabled}
              onClick={() => handleSelect(option.value)}
              className={[
                'inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs border transition-colors',
                isSelected
                  ? 'bg-foreground text-background border-foreground cursor-default'
                  : isDisabled
                    ? 'opacity-40 cursor-not-allowed border-border text-muted-foreground'
                    : 'border-border text-foreground hover:bg-muted cursor-pointer',
              ]
                .filter(Boolean)
                .join(' ')}
              aria-pressed={isSelected}
            >
              {isSelected && <Check className="h-3 w-3 shrink-0" />}
              {option.label}
            </button>
          )
        })}
      </div>

      {/* Post-selection confirmation */}
      {selected !== null && (
        <p className="text-xs text-muted-foreground mt-2">
          Selected:{' '}
          <span className="font-medium text-foreground">
            {options.find((o) => o.value === selected)?.label ?? selected}
          </span>
        </p>
      )}
    </div>
  )
}
