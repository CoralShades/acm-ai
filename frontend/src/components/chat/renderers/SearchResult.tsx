'use client'

import { Badge } from '@/components/ui/badge'
import { FileText, Search } from 'lucide-react'
import { useModalManager } from '@/lib/hooks/use-modal-manager'

interface SearchResultProps {
  data: Record<string, unknown>
  searchType: 'Vector' | 'Text'
}

export function SearchResult({ data, searchType }: SearchResultProps) {
  const { openModal } = useModalManager()
  const results = (data.results as Array<Record<string, unknown>>) || []

  if (results.length === 0) {
    return (
      <div className="rounded-lg border p-3 text-sm text-muted-foreground">
        No documents found for this {searchType.toLowerCase()} search.
      </div>
    )
  }

  return (
    <div className="rounded-lg border overflow-hidden my-2">
      <div className="px-3 py-2 bg-muted/50 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-medium">
          <Search className="h-3.5 w-3.5" />
          Document Results ({searchType})
        </div>
        <span className="text-xs text-muted-foreground">
          {results.length} results
        </span>
      </div>
      <div className="divide-y">
        {results.map((result, idx) => {
          const score = result.score as number | undefined
          const sourceId = result.source_id as string | undefined

          return (
            <div
              key={idx}
              className="px-3 py-2 hover:bg-muted/20 cursor-pointer"
              onClick={() => {
                if (sourceId) openModal('source', sourceId)
              }}
            >
              <div className="flex items-start gap-2">
                <FileText className="h-3.5 w-3.5 mt-0.5 flex-shrink-0 text-muted-foreground" />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium truncate">
                      {(result.title as string) || 'Untitled'}
                    </span>
                    {score !== undefined && (
                      <Badge variant="outline" className="text-xs flex-shrink-0">
                        {(score * 100).toFixed(0)}%
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2">
                    {(result.snippet as string) || (result.content as string) || ''}
                  </p>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
