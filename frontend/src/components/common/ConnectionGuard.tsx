'use client'

import { useEffect, useState, useCallback } from 'react'
import { ConnectionError } from '@/lib/types/config'
import { ConnectionErrorOverlay } from '@/components/errors/ConnectionErrorOverlay'
import { getConfig, resetConfig } from '@/lib/config'
import { BRANDING } from '@/config/branding'

interface ConnectionGuardProps {
  children: React.ReactNode
}

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

export function ConnectionGuard({ children }: ConnectionGuardProps) {
  const [error, setError] = useState<ConnectionError | null>(null)
  const [isChecking, setIsChecking] = useState(true)
  const [retryState, setRetryState] = useState<RetryState>({
    attempt: 0,
    nextRetryMs: INITIAL_RETRY_DELAY,
    maxRetries: MAX_RETRIES
  })

  const checkConnection = useCallback(async () => {
    setIsChecking(true)
    setError(null)

    // Reset config cache to force a fresh fetch
    resetConfig()

    try {
      const config = await getConfig()

      // Check if database is offline
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
      // API is unreachable
      const errorMessage =
        err instanceof Error ? err.message : 'Unknown error occurred'
      const attemptedUrl =
        typeof window !== 'undefined'
          ? `${window.location.origin}/api/config`
          : undefined

      setError({
        type: 'api-unreachable',
        details: {
          message: `The ${BRANDING.name} API server could not be reached`,
          technicalMessage: errorMessage,
          stack: err instanceof Error ? err.stack : undefined,
          attemptedUrl,
        },
      })
      setIsChecking(false)
    }
  }, [])

  // Check connection on mount
  useEffect(() => {
    checkConnection()
  }, [checkConnection])

  // Exponential backoff retry
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
  }, [error, retryState, checkConnection])

  // Online/Offline event listeners
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

  // Periodic health check (every 30 seconds) - only when no error
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

  // Add keyboard shortcut for retry (R key)
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (error && (e.key === 'r' || e.key === 'R')) {
        e.preventDefault()
        checkConnection()
      }
    }

    window.addEventListener('keydown', handleKeyPress)
    return () => window.removeEventListener('keydown', handleKeyPress)
  }, [error, checkConnection])

  // Show overlay if there's an error
  if (error) {
    return <ConnectionErrorOverlay error={error} onRetry={checkConnection} />
  }

  // Show nothing while checking (prevents flash of content)
  if (isChecking) {
    return null
  }

  // Render children if connection is good
  return <>{children}</>
}
