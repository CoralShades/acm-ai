# Tech Spec: E14-S8 - Improve Error Recovery and Disconnect Handling

> **Story:** E14-S8
> **Epic:** E14 - UX & Enterprise Readiness
> **Status:** Ready for Dev
> **Created:** 2026-02-08
> **Author:** Technical Writer (BMad Method)

---

## Overview

This story enhances the application's resilience to network issues, connection failures, and session timeouts. Users should never lose work or encounter confusing error states when connections drop or sessions expire. This spec implements comprehensive recovery patterns across frontend components, API client, and route-level error boundaries.

**Key Enhancements:**
- Exponential backoff reconnection in `ConnectionGuard`
- Network status detection using browser APIs (`navigator.onLine`, visibility events)
- Offline indicator banner with reconnection countdown
- Session timeout detection with re-authentication prompt
- Route-level error boundaries on all dashboard pages
- Retry logic in API client with smart failure classification
- Window focus event handler for background tab reconnection

---

## User Story

**As a** user
**I want** graceful handling of connection drops and errors
**So that** I don't lose my work or get confused when something fails

---

## Acceptance Criteria

- [ ] Enhanced `ConnectionGuard` with exponential backoff reconnection attempts
- [ ] Session timeout detection with re-authentication prompt
- [ ] `OfflineBanner` component with reconnection countdown
- [ ] Route-level error boundaries on all dashboard pages
- [ ] Retry logic in API client for transient failures
- [ ] Network status check on window focus (tab activation)

---

## Technical Design

### 1. Enhanced ConnectionGuard

**File:** `frontend/src/components/common/ConnectionGuard.tsx`

**Current State:**
- Checks connection once on mount
- Uses `getConfig()` to validate API + DB status
- Shows `ConnectionErrorOverlay` if connection fails
- Supports keyboard shortcut (R) to retry

**Enhancements:**

#### 1.1 Exponential Backoff Reconnection

Add automatic retry with exponential backoff when connection fails:

```typescript
interface RetryState {
  attempt: number
  nextRetryMs: number
  maxRetries: number
}

const INITIAL_RETRY_DELAY = 2000 // 2 seconds
const MAX_RETRY_DELAY = 30000 // 30 seconds
const MAX_RETRIES = 5

function calculateBackoff(attempt: number): number {
  const delay = Math.min(
    INITIAL_RETRY_DELAY * Math.pow(2, attempt),
    MAX_RETRY_DELAY
  )
  // Add jitter (±20%) to avoid thundering herd
  const jitter = delay * 0.2 * (Math.random() * 2 - 1)
  return Math.floor(delay + jitter)
}
```

**Integration Pattern:**
```typescript
const [retryState, setRetryState] = useState<RetryState>({
  attempt: 0,
  nextRetryMs: 0,
  maxRetries: MAX_RETRIES
})

useEffect(() => {
  if (!error || retryState.attempt >= retryState.maxRetries) return

  const timeoutId = setTimeout(() => {
    console.log(`Auto-retry ${retryState.attempt + 1}/${retryState.maxRetries}`)
    checkConnection()
    setRetryState(prev => ({
      ...prev,
      attempt: prev.attempt + 1,
      nextRetryMs: calculateBackoff(prev.attempt + 1)
    }))
  }, retryState.nextRetryMs)

  return () => clearTimeout(timeoutId)
}, [error, retryState])
```

#### 1.2 Online/Offline Event Listeners

Listen to browser network events:

```typescript
useEffect(() => {
  const handleOffline = () => {
    setError({
      type: 'api-unreachable',
      details: {
        message: 'Your device appears to be offline',
        technicalMessage: 'No network connection detected'
      }
    })
  }

  const handleOnline = () => {
    console.log('Network connection restored, checking API...')
    checkConnection()
  }

  window.addEventListener('offline', handleOffline)
  window.addEventListener('online', handleOnline)

  return () => {
    window.removeEventListener('offline', handleOffline)
    window.removeEventListener('online', handleOnline)
  }
}, [checkConnection])
```

#### 1.3 Periodic Health Check

Poll API health while app is active (only if no error):

```typescript
useEffect(() => {
  if (error) return // Don't poll while showing error overlay

  const interval = setInterval(async () => {
    try {
      const config = await getConfig()
      if (config.dbStatus === 'offline') {
        setError({
          type: 'database-offline',
          details: { message: 'Database connection lost' }
        })
      }
    } catch (err) {
      setError({
        type: 'api-unreachable',
        details: {
          message: 'Connection to server lost',
          technicalMessage: err instanceof Error ? err.message : 'Unknown error'
        }
      })
    }
  }, 30000) // Check every 30 seconds

  return () => clearInterval(interval)
}, [error])
```

#### 1.4 Reset Retry State on Success

When connection succeeds, reset retry counter:

```typescript
const checkConnection = useCallback(async () => {
  setIsChecking(true)
  setError(null)
  resetConfig()

  try {
    const config = await getConfig()

    if (config.dbStatus === 'offline') {
      setError({
        type: 'database-offline',
        details: {
          message: 'The API server is running, but the database is not accessible',
          attemptedUrl: config.apiUrl,
        },
      })
      setIsChecking(false)
      return
    }

    // SUCCESS: Reset retry state
    setError(null)
    setRetryState({ attempt: 0, nextRetryMs: INITIAL_RETRY_DELAY, maxRetries: MAX_RETRIES })
    setIsChecking(false)
  } catch (err) {
    // ... existing error handling ...
    setIsChecking(false)
  }
}, [])
```

---

### 2. Offline Banner Component

**File:** `frontend/src/components/common/OfflineBanner.tsx` (new)

A persistent banner at the top of the dashboard when network is offline or API unreachable.

**Design:**

```typescript
'use client'

import { useEffect, useState } from 'react'
import { WifiOff, RefreshCw } from 'lucide-react'
import { cn } from '@/lib/utils'
import { getConfig, resetConfig } from '@/lib/config'

export function OfflineBanner() {
  const [isOffline, setIsOffline] = useState(false)
  const [isReconnecting, setIsReconnecting] = useState(false)
  const [nextRetrySeconds, setNextRetrySeconds] = useState<number | null>(null)

  const checkConnection = async () => {
    setIsReconnecting(true)
    resetConfig()

    try {
      const config = await getConfig()
      if (config.dbStatus === 'offline') {
        setIsOffline(true)
      } else {
        setIsOffline(false)
      }
    } catch {
      setIsOffline(true)
    } finally {
      setIsReconnecting(false)
    }
  }

  // Check on mount and when network status changes
  useEffect(() => {
    checkConnection()

    const handleOffline = () => setIsOffline(true)
    const handleOnline = () => checkConnection()

    window.addEventListener('offline', handleOffline)
    window.addEventListener('online', handleOnline)

    return () => {
      window.removeEventListener('offline', handleOffline)
      window.removeEventListener('online', handleOnline)
    }
  }, [])

  // Auto-retry with countdown
  useEffect(() => {
    if (!isOffline || isReconnecting) return

    let countdown = 10
    setNextRetrySeconds(countdown)

    const countdownInterval = setInterval(() => {
      countdown -= 1
      setNextRetrySeconds(countdown)

      if (countdown <= 0) {
        clearInterval(countdownInterval)
        checkConnection()
      }
    }, 1000)

    return () => clearInterval(countdownInterval)
  }, [isOffline, isReconnecting])

  // Check on window focus (user returns to tab)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && isOffline) {
        checkConnection()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [isOffline])

  if (!isOffline) return null

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-yellow-500 dark:bg-yellow-600 text-yellow-950 dark:text-yellow-50 px-4 py-2">
      <div className="flex items-center justify-center gap-3 text-sm font-medium">
        <WifiOff className="h-4 w-4" />
        <span>
          {isReconnecting
            ? 'Reconnecting...'
            : `Connection lost. Retrying in ${nextRetrySeconds}s`
          }
        </span>
        <button
          onClick={checkConnection}
          disabled={isReconnecting}
          className={cn(
            "ml-2 flex items-center gap-1 px-2 py-1 rounded bg-yellow-600 dark:bg-yellow-700 hover:bg-yellow-700 dark:hover:bg-yellow-800 transition-colors",
            isReconnecting && "opacity-50 cursor-not-allowed"
          )}
        >
          <RefreshCw className={cn("h-3 w-3", isReconnecting && "animate-spin")} />
          Retry Now
        </button>
      </div>
    </div>
  )
}
```

**Integration:** Add to `frontend/src/app/(dashboard)/layout.tsx`:

```typescript
import { OfflineBanner } from '@/components/common/OfflineBanner'

export default function DashboardLayout({ children }) {
  return (
    <>
      <OfflineBanner />
      {/* existing layout */}
    </>
  )
}
```

---

### 3. Route-Level Error Boundaries

**Files:**
- `frontend/src/app/(dashboard)/page.tsx` (Dashboard)
- `frontend/src/app/(dashboard)/sources/page.tsx` (Documents)
- `frontend/src/app/(dashboard)/acm/page.tsx` (ACM Register)
- `frontend/src/app/(dashboard)/search/page.tsx` (Search)
- `frontend/src/app/(dashboard)/settings/page.tsx` (Settings)
- `frontend/src/app/(dashboard)/notebooks/[id]/page.tsx` (Notebook Detail)

**Pattern:**

Each page wraps its content in `ErrorBoundary` with a custom fallback:

```typescript
// Example: frontend/src/app/(dashboard)/sources/page.tsx

import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { DocumentsPageContent } from '@/components/sources/DocumentsPageContent'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

function DocumentsErrorFallback({ error, resetError }: { error?: Error; resetError: () => void }) {
  return (
    <div className="flex items-center justify-center min-h-[60vh] p-6">
      <div className="text-center space-y-4 max-w-md">
        <div className="mx-auto w-12 h-12 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
          <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />
        </div>
        <h2 className="text-lg font-semibold text-foreground">Failed to load documents</h2>
        <p className="text-sm text-muted-foreground">
          {error?.message || 'An unexpected error occurred while loading the documents page.'}
        </p>
        <div className="flex gap-2 justify-center">
          <Button onClick={resetError} variant="outline">
            <RefreshCw className="w-4 h-4 mr-2" />
            Try Again
          </Button>
          <Button onClick={() => window.location.href = '/sources'}>
            Reload Page
          </Button>
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

export default function DocumentsPage() {
  return (
    <ErrorBoundary fallback={DocumentsErrorFallback}>
      <DocumentsPageContent />
    </ErrorBoundary>
  )
}
```

**Reusable Fallback Component:**

Create a generic fallback for consistency:

```typescript
// frontend/src/components/common/PageErrorFallback.tsx

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
```

**Usage:**

```typescript
// Any page
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'

export default function ACMPage() {
  return (
    <ErrorBoundary
      fallback={(props) => (
        <PageErrorFallback
          {...props}
          pageName="ACM Register"
          reloadUrl="/acm"
        />
      )}
    >
      <ACMRegisterContent />
    </ErrorBoundary>
  )
}
```

---

### 4. API Client Retry Logic

**File:** `frontend/src/lib/api/client.ts`

**Current State:**
- 5-minute timeout (300,000ms)
- No built-in retry logic (React Query handles retries)
- 401 responses clear auth and redirect to login

**Enhancement: Retry Logic with Exponential Backoff**

Add retry interceptor using `axios-retry` library:

```bash
npm install axios-retry
```

```typescript
import axios, { AxiosResponse } from 'axios'
import axiosRetry from 'axios-retry'
import { getApiUrl } from '@/lib/config'

export const apiClient = axios.create({
  timeout: 300000, // 5 minutes
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
})

// Configure retry logic
axiosRetry(apiClient, {
  retries: 3,
  retryDelay: axiosRetry.exponentialDelay, // 1s, 2s, 4s
  retryCondition: (error) => {
    // Retry on network errors or 5xx server errors
    if (axiosRetry.isNetworkOrIdempotentRequestError(error)) {
      return true
    }

    const status = error.response?.status

    // Retry 5xx server errors
    if (status && status >= 500 && status < 600) {
      console.warn(`Retrying request after ${status} error`)
      return true
    }

    // Retry 429 (rate limit) with backoff
    if (status === 429) {
      console.warn('Rate limited, retrying with backoff')
      return true
    }

    // DO NOT retry auth errors (401, 403)
    if (status === 401 || status === 403) {
      return false
    }

    // DO NOT retry validation errors (422)
    if (status === 422) {
      return false
    }

    // DO NOT retry client errors (400, 404, etc.)
    if (status && status >= 400 && status < 500) {
      return false
    }

    return false
  },
  onRetry: (retryCount, error, requestConfig) => {
    console.log(
      `Retry attempt ${retryCount} for ${requestConfig.method?.toUpperCase()} ${requestConfig.url}`
    )
  }
})

// Request interceptor (existing)
apiClient.interceptors.request.use(async (config) => {
  // Set the base URL dynamically from runtime config
  if (!config.baseURL) {
    const apiUrl = await getApiUrl()
    config.baseURL = `${apiUrl}/api`
  }

  if (typeof window !== 'undefined') {
    const authStorage = localStorage.getItem('auth-storage')
    if (authStorage) {
      try {
        const { state } = JSON.parse(authStorage)
        if (state?.token) {
          config.headers.Authorization = `Bearer ${state.token}`
        }
      } catch (error) {
        console.error('Error parsing auth storage:', error)
      }
    }
  }

  // Handle FormData vs JSON content types
  if (config.data instanceof FormData) {
    delete config.headers['Content-Type']
  } else if (config.method && ['post', 'put', 'patch'].includes(config.method.toLowerCase())) {
    config.headers['Content-Type'] = 'application/json'
  }

  return config
})

// Response interceptor (existing + enhancement)
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear auth and redirect to login
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth-storage')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient
```

**Alternative: React Query Retry Configuration**

If avoiding `axios-retry` dependency, enhance React Query defaults in `query-client.ts`:

```typescript
import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      retry: (failureCount, error: any) => {
        const status = error?.response?.status

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
      retry: (failureCount, error: any) => {
        const status = error?.response?.status

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
```

**Recommendation:** Use React Query retry configuration (no new dependency).

---

### 5. Session Timeout Detection

**File:** `frontend/src/app/(dashboard)/layout.tsx`

**Current State:**
- `auth-store` checks auth on mount via `useAuth` hook
- `lastAuthCheck` throttles checks to 30-second intervals
- No periodic re-validation after initial check

**Enhancement: Periodic Session Check**

Add interval-based session validation in dashboard layout:

```typescript
'use client'

import { useEffect } from 'react'
import { useAuthStore } from '@/lib/stores/auth-store'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'

export default function DashboardLayout({ children }) {
  const router = useRouter()
  const { isAuthenticated, authRequired, checkAuth } = useAuthStore()

  // Periodic session validation (every 5 minutes)
  useEffect(() => {
    if (!isAuthenticated || authRequired === false) return

    const interval = setInterval(async () => {
      console.log('Checking session validity...')
      const valid = await checkAuth()

      if (!valid) {
        toast.warning('Session expired', {
          description: 'Your session has expired. Please log in again.',
          duration: Infinity,
          action: {
            label: 'Log In',
            onClick: () => {
              // Store current path for redirect after login
              sessionStorage.setItem('redirectAfterLogin', window.location.pathname)
              router.push('/login')
            },
          },
        })
      }
    }, 5 * 60 * 1000) // Check every 5 minutes

    return () => clearInterval(interval)
  }, [isAuthenticated, authRequired, checkAuth, router])

  return <>{children}</>
}
```

**Fallback: Check on Window Focus**

If user leaves tab for extended period:

```typescript
useEffect(() => {
  if (!isAuthenticated || authRequired === false) return

  const handleVisibilityChange = async () => {
    if (document.visibilityState === 'visible') {
      console.log('Tab activated, checking session...')
      const valid = await checkAuth()

      if (!valid) {
        toast.warning('Session expired', {
          description: 'Your session expired while you were away. Please log in again.',
          duration: Infinity,
          action: {
            label: 'Log In',
            onClick: () => {
              sessionStorage.setItem('redirectAfterLogin', window.location.pathname)
              router.push('/login')
            },
          },
        })
      }
    }
  }

  document.addEventListener('visibilitychange', handleVisibilityChange)
  return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
}, [isAuthenticated, authRequired, checkAuth, router])
```

---

### 6. Network Status Check on Window Focus

**File:** `frontend/src/components/common/OfflineBanner.tsx` (already included above)

The `OfflineBanner` component listens for `visibilitychange` events and re-checks connection when the tab becomes visible.

**Additional Integration: API Client Window Focus Refetch**

For critical queries, enable `refetchOnWindowFocus`:

```typescript
// Example: Sources list (already enabled in use-sources.ts)
export function useSources(notebookId?: string) {
  return useQuery({
    queryKey: QUERY_KEYS.sources(notebookId),
    queryFn: () => api.getSources(notebookId),
    staleTime: 5000,
    refetchOnWindowFocus: true, // ← Already enabled
  })
}
```

**Apply selectively** to high-priority queries:
- Sources list (`useSources`)
- Source detail (`useSource`)
- ACM records (`useACMRecords`)
- Extraction status (`useExtractionStatus`)

Most other queries should keep `refetchOnWindowFocus: false` to avoid unnecessary API calls.

---

## File Changes

| File Path | Change Type | Description |
|-----------|-------------|-------------|
| `frontend/src/components/common/ConnectionGuard.tsx` | Modify | Add exponential backoff, online/offline listeners, periodic health check |
| `frontend/src/components/common/OfflineBanner.tsx` | Create | Persistent banner for offline state with reconnection countdown |
| `frontend/src/components/common/PageErrorFallback.tsx` | Create | Reusable error fallback component for route-level boundaries |
| `frontend/src/lib/api/query-client.ts` | Modify | Enhanced retry logic with smart failure classification |
| `frontend/src/app/(dashboard)/layout.tsx` | Modify | Add periodic session check and window focus handler |
| `frontend/src/app/(dashboard)/page.tsx` | Modify | Wrap in ErrorBoundary with PageErrorFallback |
| `frontend/src/app/(dashboard)/sources/page.tsx` | Modify | Wrap in ErrorBoundary with PageErrorFallback |
| `frontend/src/app/(dashboard)/acm/page.tsx` | Modify | Wrap in ErrorBoundary with PageErrorFallback |
| `frontend/src/app/(dashboard)/search/page.tsx` | Modify | Wrap in ErrorBoundary with PageErrorFallback |
| `frontend/src/app/(dashboard)/settings/page.tsx` | Modify | Wrap in ErrorBoundary with PageErrorFallback |
| `frontend/src/app/(dashboard)/notebooks/[id]/page.tsx` | Modify | Wrap in ErrorBoundary with PageErrorFallback |

**Optional (if using axios-retry):**
- `frontend/package.json` - Add `axios-retry` dependency
- `frontend/src/lib/api/client.ts` - Import and configure `axios-retry`

---

## Dependencies

**Required:**
- Existing `ErrorBoundary` component (`frontend/src/components/common/ErrorBoundary.tsx`)
- Existing `ConnectionGuard` component (`frontend/src/components/common/ConnectionGuard.tsx`)
- Existing `auth-store` (`frontend/src/lib/stores/auth-store.ts`)
- Existing `query-client` (`frontend/src/lib/api/query-client.ts`)
- Sonner toast library (already installed)

**Optional:**
- `axios-retry` npm package (if not using React Query retry configuration)

**No blocking dependencies** - this story can be implemented independently.

---

## Testing Strategy

### Unit Tests

**ConnectionGuard:**
```typescript
// frontend/src/components/common/__tests__/ConnectionGuard.test.tsx

import { render, screen, waitFor } from '@testing-library/react'
import { ConnectionGuard } from '../ConnectionGuard'
import { getConfig } from '@/lib/config'

jest.mock('@/lib/config')

describe('ConnectionGuard', () => {
  it('shows children when connection is successful', async () => {
    (getConfig as jest.Mock).mockResolvedValue({ dbStatus: 'online' })

    render(
      <ConnectionGuard>
        <div>App Content</div>
      </ConnectionGuard>
    )

    await waitFor(() => {
      expect(screen.getByText('App Content')).toBeInTheDocument()
    })
  })

  it('retries with exponential backoff on failure', async () => {
    (getConfig as jest.Mock)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValue({ dbStatus: 'online' })

    jest.useFakeTimers()

    render(
      <ConnectionGuard>
        <div>App Content</div>
      </ConnectionGuard>
    )

    // First retry after ~2s
    jest.advanceTimersByTime(2000)
    await waitFor(() => {
      expect(getConfig).toHaveBeenCalledTimes(2)
    })

    // Second retry after ~4s
    jest.advanceTimersByTime(4000)
    await waitFor(() => {
      expect(getConfig).toHaveBeenCalledTimes(3)
    })

    jest.useRealTimers()
  })

  it('responds to online event', async () => {
    (getConfig as jest.Mock).mockRejectedValue(new Error('Offline'))

    render(<ConnectionGuard><div>Content</div></ConnectionGuard>)

    // Trigger online event
    (getConfig as jest.Mock).mockResolvedValue({ dbStatus: 'online' })
    window.dispatchEvent(new Event('online'))

    await waitFor(() => {
      expect(screen.getByText('Content')).toBeInTheDocument()
    })
  })
})
```

**OfflineBanner:**
```typescript
// frontend/src/components/common/__tests__/OfflineBanner.test.tsx

import { render, screen, fireEvent } from '@testing-library/react'
import { OfflineBanner } from '../OfflineBanner'
import { getConfig } from '@/lib/config'

jest.mock('@/lib/config')

describe('OfflineBanner', () => {
  it('does not render when online', async () => {
    (getConfig as jest.Mock).mockResolvedValue({ dbStatus: 'online' })

    const { container } = render(<OfflineBanner />)

    await waitFor(() => {
      expect(container.firstChild).toBeNull()
    })
  })

  it('renders banner when offline', async () => {
    (getConfig as jest.Mock).mockRejectedValue(new Error('Network error'))

    render(<OfflineBanner />)

    await waitFor(() => {
      expect(screen.getByText(/Connection lost/i)).toBeInTheDocument()
    })
  })

  it('allows manual retry', async () => {
    (getConfig as jest.Mock).mockRejectedValue(new Error('Network error'))

    render(<OfflineBanner />)

    await waitFor(() => {
      expect(screen.getByText('Retry Now')).toBeInTheDocument()
    })

    (getConfig as jest.Mock).mockResolvedValue({ dbStatus: 'online' })

    fireEvent.click(screen.getByText('Retry Now'))

    await waitFor(() => {
      expect(getConfig).toHaveBeenCalledTimes(2)
    })
  })
})
```

### Integration Tests

**Session Timeout Flow:**
1. Mock `checkAuth` to return `false` after 5 minutes
2. Render dashboard layout
3. Advance timers by 5 minutes
4. Verify toast appears with "Session expired" message
5. Verify "Log In" action redirects to `/login`

**Route Error Boundary:**
1. Mock component to throw error
2. Verify `PageErrorFallback` renders
3. Click "Try Again" button
4. Verify error boundary resets and component re-renders

### Manual Testing Checklist

- [ ] Disconnect network while on dashboard → see `OfflineBanner` appear
- [ ] Reconnect network → banner disappears automatically
- [ ] Stop backend API server → `ConnectionGuard` shows error overlay
- [ ] Restart API → retry succeeds and app loads
- [ ] Leave tab inactive for >5 minutes → return to tab → session check runs
- [ ] Cause intentional error in component → route boundary catches it
- [ ] Click "Try Again" in error fallback → boundary resets
- [ ] Trigger 500 error from API → React Query retries with backoff
- [ ] Trigger 401 error → redirect to login immediately (no retry)

---

## Estimated Complexity

**Story Points:** 5

**Breakdown:**
- ConnectionGuard enhancements (exponential backoff, events): 2 points
- OfflineBanner component: 1 point
- Route-level error boundaries (7 pages): 1 point
- API retry logic: 0.5 points
- Session timeout handling: 0.5 points

**Risk Assessment:**
- **Low risk:** All changes are additive and non-breaking
- **Testing complexity:** Medium (requires timer mocking and network simulation)
- **Browser compatibility:** High (modern browser APIs only)

---

## Implementation Notes

### Error Classification Reference

| Error Type | Retry? | Reason |
|------------|--------|--------|
| Network timeout | Yes (3x) | Transient failure |
| 500 Internal Server Error | Yes (3x) | Server may recover |
| 502 Bad Gateway | Yes (3x) | Upstream may recover |
| 503 Service Unavailable | Yes (3x) | Server may be restarting |
| 429 Rate Limit | Yes (3x) | Backoff resolves |
| 401 Unauthorized | No | Auth required |
| 403 Forbidden | No | Auth required |
| 404 Not Found | No | Resource doesn't exist |
| 422 Unprocessable Entity | No | Validation error |
| Other 4xx | No | Client error |

### Browser API Support

All features use standard Web APIs with excellent browser support:
- `navigator.onLine` - All modern browsers
- `online`/`offline` events - All modern browsers
- `visibilitychange` event - All modern browsers
- Local storage persistence - Already in use

### Accessibility Considerations

- `OfflineBanner` uses semantic HTML and ARIA attributes
- Error fallbacks use `role="alert"` for screen readers
- Retry buttons are keyboard accessible
- Color is not the only indicator of state (icons + text)

### Performance Considerations

- Periodic health check (30s interval) is lightweight (single HEAD request)
- Session check (5min interval) reuses existing `checkAuth` logic
- Exponential backoff prevents thundering herd
- Retry jitter reduces server load spikes

---

## References

- **Spec Source:** `docs/state-loading-spec.md` Section 9 (Error Boundary and Recovery Patterns)
- **Related Stories:** E14-S7 (Skeleton Screens), E14-S9 (Dashboard Page), E14-S10 (Documents Page)
- **Existing Components:** `ConnectionGuard.tsx`, `ErrorBoundary.tsx`, `auth-store.ts`
- **React Query Docs:** [Error & Retry](https://tanstack.com/query/latest/docs/react/guides/query-retries)
- **MDN Reference:** [Online/Offline Events](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/onLine)

---

## Acceptance Sign-Off

**Dev Checklist:**
- [ ] Enhanced `ConnectionGuard` with exponential backoff
- [ ] `OfflineBanner` component created and integrated
- [ ] Route-level error boundaries added to all dashboard pages
- [ ] `PageErrorFallback` component created
- [ ] React Query retry logic enhanced in `query-client.ts`
- [ ] Session timeout detection added to dashboard layout
- [ ] Window focus handler checks network status
- [ ] Unit tests written for new components
- [ ] Manual testing completed per checklist
- [ ] TypeScript types are accurate
- [ ] No console errors in browser
- [ ] Build succeeds: `npm run build`

**QA Checklist:**
- [ ] Network disconnect shows banner immediately
- [ ] Network reconnect clears banner automatically
- [ ] API server restart recovers gracefully
- [ ] Session expiry prompts re-login
- [ ] Error boundaries catch component errors
- [ ] Retry buttons work as expected
- [ ] No infinite retry loops
- [ ] Toast notifications are clear and actionable

---

**Spec Status:** Ready for Implementation
**Last Updated:** 2026-02-08
