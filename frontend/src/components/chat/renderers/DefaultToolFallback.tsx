'use client'

import { Loader2, AlertCircle, CheckCircle2 } from 'lucide-react'

interface DefaultToolFallbackProps {
  name: string
  args?: Record<string, unknown>
  status: string
  result?: unknown
}

export function DefaultToolFallback({
  name,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  args: _args,
  status,
  result,
}: DefaultToolFallbackProps) {
  return (
    <div className="border rounded-lg p-3 my-2 text-sm bg-muted/20">
      <div className="flex items-center gap-2 mb-1">
        {status === 'inProgress' || status === 'executing' ? (
          <Loader2 className="h-3.5 w-3.5 text-primary animate-spin" />
        ) : status === 'complete' ? (
          <CheckCircle2 className="h-3.5 w-3.5 text-green-600 dark:text-green-400" />
        ) : (
          <AlertCircle className="h-3.5 w-3.5 text-red-500" />
        )}
        <span className="font-medium text-xs">{name}</span>
      </div>
      {Boolean(result) && status === 'complete' && (
        <pre className="text-xs whitespace-pre-wrap overflow-auto max-h-32 mt-1 p-1.5 bg-background rounded">
          {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  )
}
