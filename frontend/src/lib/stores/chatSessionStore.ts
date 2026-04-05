import { create } from 'zustand'
import type { ChatSessionSummary, MessageHistoryResponse, SessionListResponse } from '@/lib/types/chat-session'

interface ChatSessionStoreState {
  sessions: ChatSessionSummary[]
  activeSessionId: string | null
  isLoading: boolean
  /** Session ID for which message history has been loaded (prevents cross-session race). */
  messagesLoadedFor: string | null

  fetchSessions: (sourceId: string) => Promise<void>
  createSession: (sourceId: string, title?: string) => Promise<ChatSessionSummary | null>
  renameSession: (sourceId: string, sessionId: string, title: string) => Promise<void>
  deleteSession: (sourceId: string, sessionId: string) => Promise<void>
  setActive: (sessionId: string | null) => void
  loadMessages: (sourceId: string, sessionId: string) => Promise<MessageHistoryResponse>
}

function sessionsUrl(sourceId: string) {
  return `/api/sources/${encodeURIComponent(sourceId)}/unified-sessions`
}

function sessionUrl(sourceId: string, sessionId: string) {
  return `/api/sources/${encodeURIComponent(sourceId)}/unified-sessions/${encodeURIComponent(sessionId)}`
}

function sessionMessagesUrl(sourceId: string, sessionId: string) {
  return `/api/sources/${encodeURIComponent(sourceId)}/unified-sessions/${encodeURIComponent(sessionId)}/messages`
}

/** ISO timestamp threshold: sessions updated within 10 minutes are considered recent. */
const RECENT_SESSION_MS = 10 * 60 * 1000

export const useChatSessionStore = create<ChatSessionStoreState>((set, get) => ({
  sessions: [],
  activeSessionId: null,
  isLoading: false,
  messagesLoadedFor: null,

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
        const mostRecent = sorted[0]
        const updatedAt = mostRecent.updated ?? mostRecent.created ?? null
        const isRecent =
          updatedAt !== null &&
          Date.now() - new Date(updatedAt).getTime() < RECENT_SESSION_MS
        // Activate most-recent session; clear messagesLoadedFor so history is fetched
        // only when the session was recently active (within 10 min threshold).
        set({ activeSessionId: mostRecent.id, messagesLoadedFor: isRecent ? null : mostRecent.id })
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
    // Clear messagesLoadedFor so the panel re-fetches history for the new session
    set({ activeSessionId: sessionId, messagesLoadedFor: null })
  },

  loadMessages: async (sourceId: string, sessionId: string) => {
    try {
      const res = await fetch(sessionMessagesUrl(sourceId, sessionId))
      if (!res.ok) {
        console.debug(
          `[chatSessionStore] loadMessages: non-OK response ${res.status} for session ${sessionId}`
        )
        set({ messagesLoadedFor: sessionId })
        return { messages: [], total: 0 }
      }
      const data: MessageHistoryResponse = await res.json()
      set({ messagesLoadedFor: sessionId })
      return data
    } catch (err) {
      console.error('[chatSessionStore] loadMessages error:', err)
      set({ messagesLoadedFor: sessionId })
      return { messages: [], total: 0 }
    }
  },
}))
