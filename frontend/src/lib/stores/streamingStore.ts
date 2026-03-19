'use client'

import { create } from 'zustand'

export interface StreamState {
  operationId: string
  category: 'extraction' | 'ai' | 'bulk' | 'hitl'
  status: 'connecting' | 'connected' | 'reconnecting' | 'done' | 'error'
  lastEventType: string | null
  lastEventTimestamp: string | null
  retryCount: number
  eventCount: number
}

interface V3StreamingState {
  activeStreams: Map<string, StreamState>
  isConnected: boolean

  registerStream: (operationId: string, category: StreamState['category']) => void
  updateStream: (operationId: string, patch: Partial<StreamState>) => void
  removeStream: (operationId: string) => void
  clearAll: () => void
}

export const useStreamingStore = create<V3StreamingState>((set) => ({
  activeStreams: new Map(),
  isConnected: false,

  registerStream: (operationId, category) =>
    set((state) => {
      const newMap = new Map(state.activeStreams)
      newMap.set(operationId, {
        operationId,
        category,
        status: 'connecting',
        lastEventType: null,
        lastEventTimestamp: null,
        retryCount: 0,
        eventCount: 0,
      })
      return {
        activeStreams: newMap,
        isConnected: [...newMap.values()].some((s) => s.status === 'connected'),
      }
    }),

  updateStream: (operationId, patch) =>
    set((state) => {
      const existing = state.activeStreams.get(operationId)
      if (!existing) return state
      const newMap = new Map(state.activeStreams)
      newMap.set(operationId, { ...existing, ...patch })
      return {
        activeStreams: newMap,
        isConnected: [...newMap.values()].some((s) => s.status === 'connected'),
      }
    }),

  removeStream: (operationId) =>
    set((state) => {
      const newMap = new Map(state.activeStreams)
      newMap.delete(operationId)
      return {
        activeStreams: newMap,
        isConnected: [...newMap.values()].some((s) => s.status === 'connected'),
      }
    }),

  clearAll: () =>
    set({
      activeStreams: new Map(),
      isConnected: false,
    }),
}))
