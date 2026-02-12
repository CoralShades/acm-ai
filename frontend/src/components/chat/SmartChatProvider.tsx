'use client'

import { createContext, useContext, type ReactNode } from 'react'

interface SmartChatScope {
  sourceId?: string
  notebookId?: string
  hasAcmData: boolean
}

const SmartChatContext = createContext<SmartChatScope>({
  hasAcmData: false,
})

export function useSmartChatScope() {
  return useContext(SmartChatContext)
}

interface SmartChatProviderProps extends SmartChatScope {
  children: ReactNode
}

export function SmartChatProvider({
  children,
  sourceId,
  notebookId,
  hasAcmData,
}: SmartChatProviderProps) {
  return (
    <SmartChatContext.Provider value={{ sourceId, notebookId, hasAcmData }}>
      {children}
    </SmartChatContext.Provider>
  )
}
