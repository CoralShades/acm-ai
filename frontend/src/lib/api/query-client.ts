import { QueryClient } from '@tanstack/react-query'

interface ErrorWithResponse {
  response?: {
    status?: number
  }
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      retry: (failureCount, error: unknown) => {
        const errorWithResponse = error as ErrorWithResponse
        const status = errorWithResponse?.response?.status

        // Never retry auth errors
        if (status === 401 || status === 403) return false

        // Never retry validation errors
        if (status === 422 || status === 400) return false

        // Never retry not found
        if (status === 404) return false

        // Retry server errors up to 3 times
        if (status && status >= 500) return failureCount < 3

        // Retry network errors up to 3 times
        if (!status) return failureCount < 3

        return false
      },
      retryDelay: (attemptIndex) => {
        // Exponential backoff: 1s, 2s, 4s, 8s, max 10s
        return Math.min(1000 * Math.pow(2, attemptIndex), 10000)
      }
    },
    mutations: {
      retry: (failureCount, error: unknown) => {
        const errorWithResponse = error as ErrorWithResponse
        const status = errorWithResponse?.response?.status

        // Never retry mutations for client errors (4xx)
        if (status && status >= 400 && status < 500) return false

        // Retry server errors once
        if (status && status >= 500) return failureCount < 1

        // Retry network errors once
        if (!status) return failureCount < 1

        return false
      },
      retryDelay: 2000 // 2 second delay for mutation retries
    },
  },
})

export const QUERY_KEYS = {
  notebooks: ['notebooks'] as const,
  notebook: (id: string) => ['notebooks', id] as const,
  notes: (notebookId?: string) => ['notes', notebookId] as const,
  note: (id: string) => ['notes', id] as const,
  sources: (notebookId?: string) => ['sources', notebookId] as const,
  source: (id: string) => ['sources', id] as const,
  settings: ['settings'] as const,
  sourceChatSessions: (sourceId: string) => ['source-chat', sourceId, 'sessions'] as const,
  sourceChatSession: (sourceId: string, sessionId: string) => ['source-chat', sourceId, 'sessions', sessionId] as const,
  notebookChatSessions: (notebookId: string) => ['notebook-chat', notebookId, 'sessions'] as const,
  notebookChatSession: (sessionId: string) => ['notebook-chat', 'sessions', sessionId] as const,
  podcastEpisodes: ['podcasts', 'episodes'] as const,
  podcastEpisode: (episodeId: string) => ['podcasts', 'episodes', episodeId] as const,
  episodeProfiles: ['podcasts', 'episode-profiles'] as const,
  speakerProfiles: ['podcasts', 'speaker-profiles'] as const,
}
