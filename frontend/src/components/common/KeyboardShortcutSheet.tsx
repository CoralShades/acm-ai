'use client'

import { useEffect, useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'

interface ShortcutEntry {
  keys: string[]
  description: string
}

interface ShortcutCategory {
  title: string
  shortcuts: ShortcutEntry[]
}

const shortcutCategories: ShortcutCategory[] = [
  {
    title: 'Global',
    shortcuts: [
      { keys: ['Ctrl', 'K'], description: 'Open command palette' },
      { keys: ['Esc'], description: 'Close dialog / Cancel' },
      { keys: ['?'], description: 'Show keyboard shortcuts' },
    ],
  },
  {
    title: 'Navigation (press G then key)',
    shortcuts: [
      { keys: ['G', 'D'], description: 'Go to Dashboard' },
      { keys: ['G', 'S'], description: 'Go to Sources' },
      { keys: ['G', 'A'], description: 'Go to ACM Register' },
      { keys: ['G', 'M'], description: 'Go to Models' },
      { keys: ['G', 'H'], description: 'Go to Search' },
    ],
  },
  {
    title: 'Actions',
    shortcuts: [
      { keys: ['Ctrl', 'K'], description: 'Search commands and navigate' },
    ],
  },
  {
    title: 'Grid Navigation',
    shortcuts: [
      { keys: ['\u2190', '\u2191', '\u2192', '\u2193'], description: 'Navigate between cells' },
      { keys: ['Enter'], description: 'View cell details / citation' },
      { keys: ['Space'], description: 'Expand / collapse group row' },
      { keys: ['E'], description: 'Edit selected record' },
      { keys: ['Delete'], description: 'Delete selected record' },
      { keys: ['Tab'], description: 'Move to next cell' },
      { keys: ['Ctrl', 'F'], description: 'Search within grid' },
    ],
  },
]

export function KeyboardShortcutSheet() {
  const [open, setOpen] = useState(false)

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Skip if focus is inside editable elements
      const target = e.target as HTMLElement | null
      if (
        target &&
        (target.isContentEditable ||
          ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName))
      ) {
        return
      }

      // ? key (Shift + /) to open shortcut sheet
      if (e.key === '?' && e.shiftKey) {
        e.preventDefault()
        setOpen((prev) => !prev)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Keyboard Shortcuts</DialogTitle>
          <DialogDescription>
            Available keyboard shortcuts for navigating and interacting with the application.
          </DialogDescription>
        </DialogHeader>
        <ScrollArea className="max-h-[60vh]">
          <div className="space-y-6 pr-4">
            {shortcutCategories.map((category) => (
              <div key={category.title}>
                <h3 className="text-sm font-semibold text-muted-foreground mb-3">
                  {category.title}
                </h3>
                <div className="space-y-2">
                  {category.shortcuts.map((shortcut) => (
                    <div
                      key={shortcut.description}
                      className="flex items-center justify-between py-1"
                    >
                      <span className="text-sm">{shortcut.description}</span>
                      <div className="flex items-center gap-1">
                        {shortcut.keys.map((key, index) => (
                          <span key={index} className="flex items-center gap-1">
                            {index > 0 && (
                              <span className="text-xs text-muted-foreground">+</span>
                            )}
                            <Badge variant="outline" className="px-1.5 py-0.5 text-xs font-mono">
                              {key}
                            </Badge>
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  )
}
