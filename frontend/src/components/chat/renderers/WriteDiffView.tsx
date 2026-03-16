'use client'

interface WriteDiffViewProps {
  field: string
  oldValue?: string
  newValue: string
}

export function WriteDiffView({ field, oldValue, newValue }: WriteDiffViewProps) {
  return (
    <div role="region" aria-label={`Field change: ${field}`} className="border rounded-lg p-3 my-2 text-sm">
      <div className="text-xs font-medium text-muted-foreground mb-2">Field Change</div>
      <div className="font-mono text-xs">
        <span className="font-medium">{field}</span>
      </div>
      <div className="mt-1.5 flex items-center gap-2 flex-wrap">
        {oldValue && (
          <>
            <span className="bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400 px-2 py-0.5 rounded line-through">
              {oldValue}
            </span>
            <span className="text-muted-foreground" aria-hidden="true">→</span>
          </>
        )}
        <span className="bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400 px-2 py-0.5 rounded">
          {newValue}
        </span>
      </div>
    </div>
  )
}
