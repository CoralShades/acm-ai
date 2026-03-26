'use client'

import { useState, useRef } from 'react'
import { ChevronDown, Plus, Pencil, Trash2, Check, X } from 'lucide-react'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { useChatSessionStore } from '@/lib/stores/chatSessionStore'
import { cn } from '@/lib/utils'

interface SessionDropdownProps {
  sourceId: string
}

export function SessionDropdown({ sourceId }: SessionDropdownProps) {
  const { sessions, activeSessionId, isLoading, createSession, renameSession, deleteSession, setActive } =
    useChatSessionStore()
  const [open, setOpen] = useState(false)
  const [renamingId, setRenamingId] = useState<string | null>(null)
  const [renameValue, setRenameValue] = useState('')
  const renameInputRef = useRef<HTMLInputElement>(null)

  const activeSession = sessions.find((s) => s.id === activeSessionId)
  const displayTitle = activeSession?.title ?? 'New Chat'

  function handleNewChat() {
    createSession(sourceId)
    setOpen(false)
  }

  function handleSelect(sessionId: string) {
    setActive(sessionId)
    setOpen(false)
  }

  function startRename(sessionId: string, currentTitle: string | null) {
    setRenamingId(sessionId)
    setRenameValue(currentTitle ?? '')
    // Focus the input on next tick after render
    setTimeout(() => renameInputRef.current?.focus(), 50)
  }

  function cancelRename() {
    setRenamingId(null)
    setRenameValue('')
  }

  async function commitRename(sessionId: string) {
    const trimmed = renameValue.trim()
    if (trimmed) {
      await renameSession(sourceId, sessionId, trimmed)
    }
    cancelRename()
  }

  function handleRenameKeyDown(e: React.KeyboardEvent, sessionId: string) {
    if (e.key === 'Enter') {
      e.preventDefault()
      commitRename(sessionId)
    } else if (e.key === 'Escape') {
      cancelRename()
    }
  }

  async function handleDelete(sessionId: string, title: string | null) {
    const label = title || 'this session'
    if (!window.confirm(`Delete "${label}"? This cannot be undone.`)) return
    await deleteSession(sourceId, sessionId)
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          className={cn(
            'inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs',
            'text-muted-foreground hover:text-foreground hover:bg-accent transition-colors',
            'max-w-[160px]',
          )}
          aria-label="Switch chat session"
        >
          <span className="truncate">{isLoading ? 'Loading...' : displayTitle}</span>
          <ChevronDown
            className={cn('h-3 w-3 shrink-0 transition-transform', open && 'rotate-180')}
          />
        </button>
      </PopoverTrigger>

      <PopoverContent align="start" className="w-64 p-1 rounded-lg">
        {/* New Chat button */}
        <button
          type="button"
          onClick={handleNewChat}
          className={cn(
            'flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs font-medium',
            'text-primary hover:bg-accent transition-colors',
          )}
        >
          <Plus className="h-3 w-3 shrink-0" />
          New Chat
        </button>

        {sessions.length > 0 && <div className="my-1 border-t" />}

        {/* Session list */}
        <ul className="max-h-64 overflow-y-auto" role="listbox" aria-label="Chat sessions">
          {sessions.map((session) => {
            const isActive = session.id === activeSessionId
            const isRenaming = renamingId === session.id

            return (
              <li key={session.id} role="option" aria-selected={isActive}>
                {isRenaming ? (
                  <div className="flex items-center gap-1 px-2 py-1">
                    <input
                      ref={renameInputRef}
                      type="text"
                      value={renameValue}
                      onChange={(e) => setRenameValue(e.target.value)}
                      onKeyDown={(e) => handleRenameKeyDown(e, session.id)}
                      className={cn(
                        'flex-1 min-w-0 rounded border bg-background px-1.5 py-0.5 text-xs',
                        'focus:outline-none focus:ring-1 focus:ring-ring',
                      )}
                      aria-label="Rename session"
                    />
                    <button
                      type="button"
                      onClick={() => commitRename(session.id)}
                      className="shrink-0 rounded p-0.5 hover:bg-accent focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                      aria-label="Confirm rename"
                    >
                      <Check className="h-3 w-3 text-primary" />
                    </button>
                    <button
                      type="button"
                      onClick={cancelRename}
                      className="shrink-0 rounded p-0.5 hover:bg-accent focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                      aria-label="Cancel rename"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </div>
                ) : (
                  <div
                    className={cn(
                      'group flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-xs',
                      'hover:bg-accent transition-colors cursor-pointer',
                      isActive && 'bg-accent/50',
                    )}
                  >
                    {/* Active indicator dot */}
                    <span
                      className={cn(
                        'h-1.5 w-1.5 shrink-0 rounded-full',
                        isActive ? 'bg-primary' : 'bg-transparent',
                      )}
                      aria-hidden="true"
                    />

                    {/* Title — click to select */}
                    <button
                      type="button"
                      onClick={() => handleSelect(session.id)}
                      className="flex-1 min-w-0 text-left truncate focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring rounded"
                    >
                      {session.title ?? 'Untitled'}
                    </button>

                    {/* Overflow actions — only visible on hover */}
                    <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          startRename(session.id, session.title)
                        }}
                        className="rounded p-0.5 hover:bg-background focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                        aria-label={`Rename "${session.title ?? 'Untitled'}"`}
                      >
                        <Pencil className="h-3 w-3 text-muted-foreground" />
                      </button>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation()
                          handleDelete(session.id, session.title)
                        }}
                        className="rounded p-0.5 hover:bg-background focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                        aria-label={`Delete "${session.title ?? 'Untitled'}"`}
                      >
                        <Trash2 className="h-3 w-3 text-destructive" />
                      </button>
                    </div>
                  </div>
                )}
              </li>
            )
          })}
        </ul>

        {sessions.length === 0 && !isLoading && (
          <p className="px-2 py-2 text-xs text-muted-foreground text-center">
            No sessions yet
          </p>
        )}
      </PopoverContent>
    </Popover>
  )
}
