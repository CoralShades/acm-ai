'use client'

import { UnifiedChatPanel } from '@/components/chat'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { Card, CardContent } from '@/components/ui/card'
import { AlertCircle } from 'lucide-react'
import type { ContextSelections } from '../[id]/page'

interface ChatColumnProps {
  notebookId: string
  contextSelections: ContextSelections
}

export function ChatColumn({ notebookId }: ChatColumnProps) {
  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 min-h-0">
        <UnifiedChatPanel notebookId={notebookId} />
      </div>
    </div>
  )
}
