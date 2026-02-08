'use client'

import { useEffect, useState } from 'react'
import { WifiOff, RefreshCw } from 'lucide-react'
import { cn } from '@/lib/utils'
import { getConfig, resetConfig } from '@/lib/config'

// TODO(E14-S8): Consolidate with ConnectionGuard to avoid duplicate connection checks.
// Both OfflineBanner and ConnectionGuard independently track online/offline state.
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
    <div
      className="fixed top-0 left-0 right-0 z-50 bg-yellow-500 dark:bg-yellow-600 text-yellow-950 dark:text-yellow-50 px-4 py-2"
      role="alert"
      aria-live="assertive"
    >
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
          aria-label="Retry connection now"
        >
          <RefreshCw className={cn("h-3 w-3", isReconnecting && "animate-spin")} />
          Retry Now
        </button>
      </div>
    </div>
  )
}
