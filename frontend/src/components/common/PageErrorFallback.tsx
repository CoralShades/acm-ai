import { AlertTriangle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface PageErrorFallbackProps {
  error?: Error
  resetError: () => void
  pageName: string
  reloadUrl?: string
}

export function PageErrorFallback({
  error,
  resetError,
  pageName,
  reloadUrl
}: PageErrorFallbackProps) {
  return (
    <div className="flex items-center justify-center min-h-[60vh] p-6">
      <div className="text-center space-y-4 max-w-md">
        <div className="mx-auto w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
          <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />
        </div>
        <h2 className="text-lg font-semibold text-foreground">
          Failed to load {pageName}
        </h2>
        <p className="text-sm text-muted-foreground">
          {error?.message || `An unexpected error occurred while loading the ${pageName} page.`}
        </p>
        <div className="flex gap-2 justify-center">
          <Button onClick={resetError} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Try Again
          </Button>
          {reloadUrl && (
            <Button onClick={() => window.location.href = reloadUrl}>
              Reload Page
            </Button>
          )}
        </div>
        {process.env.NODE_ENV === 'development' && error && (
          <details className="text-xs text-left bg-muted p-3 rounded border mt-4">
            <summary className="cursor-pointer font-medium">Error Details</summary>
            <pre className="mt-2 whitespace-pre-wrap break-all">{error.stack}</pre>
          </details>
        )}
      </div>
    </div>
  )
}
