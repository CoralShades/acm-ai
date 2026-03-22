import { create } from 'zustand'
import type { ChatSessionSummary, SessionListResponse } from '@/lib/types/chat-session'

interface ChatSessionStoreState {
  sessions: ChatSessionSummary[]
  activeSessionId: string | null
  isLoading: boolean

  fetchSessions: (sourceId: string) => Promise<void>
  createSession: (sourceId: string, title?: string) => Promise<ChatSessionSummary | null>
  renameSession: (sourceId: string, sessionId: string, title: string) => Promise<void>
  deleteSession: (sourceId: string, sessionId: string) => Promise<void>
  setActive: (sessionId: string | null) => void
}

function sessionsUrl(sourceId: string) {
  return `/api/sources/${encodeURIComponent(sourceId)}/unified-sessions`
}

function sessionUrl(sourceId: string, sessionId: string) {
  return `/api/sources/${encodeURIComponent(sourceId)}/unified-sessions/${encodeURIComponent(sessionId)}`
}

export const useChatSessionStore = create<ChatSessionStoreState>((set, get) => ({
  sessions: [],
  activeSessionId: null,
  isLoading: false,

  fetchSessions: async (sourceId: string) => {
    set({ isLoading: true })
    try {
      const res = await fetch(sessionsUrl(sourceId))
      if (!res.ok) throw new Error(`Failed to fetch sessions: ${res.status}`)
      const data: SessionListResponse = await res.json()
      const sessions = data.sessions ?? []
      set({ sessions, isLoading: false })
      // Auto-activate the most-recently-updated session if none is active
      const current = get().activeSessionId
      if (!current && sessions.length > 0) {
        const sorted = [...sessions].sort((a, b) => {
          const ta = a.updated ?? a.created ?? ''
          const tb = b.updated ?? b.created ?? ''
          return tb.localeCompare(ta)
        })
        set({ activeSessionId: sorted[0].id })
      }
    } catch (err) {
      // Graceful degradation: if sessions endpoint isn't available (e.g., API
      // server predates the unified_sessions router), log quietly and continue.
      // Chat still works without session management.
      if (err instanceof Error && err.message.includes('404')) {
        console.debug('[chatSessionStore] Session endpoint not available (404) — chat works without sessions')
      } else {
        console.error('[chatSessionStore] fetchSessions error:', err)
      }
      set({ isLoading: false })
    }
  },

  createSession: async (sourceId: string, title?: string) => {
    try {
      const res = await fetch(sessionsUrl(sourceId), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: title ?? null }),
      })
      if (!res.ok) throw new Error(`Failed to create session: ${res.status}`)
      const session: ChatSessionSummary = await res.json()
      set((state) => ({
        sessions: [session, ...state.sessions],
        activeSessionId: session.id,
      }))
      return session
    } catch (err) {
      console.error('[chatSessionStore] createSession error:', err)
      return null
    }
  },

  renameSession: async (sourceId: string, sessionId: string, title: string) => {
    try {
      const res = await fetch(sessionUrl(sourceId, sessionId), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
      })
      if (!res.ok) throw new Error(`Failed to rename session: ${res.status}`)
      const updated: ChatSessionSummary = await res.json()
      set((state) => ({
        sessions: state.sessions.map((s) =>
          s.id === sessionId ? { ...s, title: updated.title, updated: updated.updated } : s
        ),
      }))
    } catch (err) {
      console.error('[chatSessionStore] renameSession error:', err)
    }
  },

  deleteSession: async (sourceId: string, sessionId: string) => {
    try {
      const res = await fetch(sessionUrl(sourceId, sessionId), { method: 'DELETE' })
      if (!res.ok) throw new Error(`Failed to delete session: ${res.status}`)
      const remaining = get().sessions.filter((s) => s.id !== sessionId)
      const nextActive =
        get().activeSessionId === sessionId
          ? (remaining[0]?.id ?? null)
          : get().activeSessionId
      set({ sessions: remaining, activeSessionId: nextActive })
    } catch (err) {
      console.error('[chatSessionStore] deleteSession error:', err)
    }
  },

  setActive: (sessionId: string | null) => {
    set({ activeSessionId: sessionId })
  },
}))
