'use client'

import { usePathname, useSearchParams } from 'next/navigation'
import { useCallback, useEffect, useRef, useState } from 'react'

const MIN_VISIBLE_MS = 250
const MAX_VISIBLE_MS = 12000

export function NavigationProgress() {
  const pathname = usePathname()
  const searchParams = useSearchParams()
  const searchKey = searchParams.toString()
  const [loading, setLoading] = useState(false)
  const startedAtRef = useRef<number | null>(null)
  const hideTimerRef = useRef<number | null>(null)
  const safetyTimerRef = useRef<number | null>(null)

  const clearTimers = useCallback(() => {
    if (hideTimerRef.current) {
      window.clearTimeout(hideTimerRef.current)
      hideTimerRef.current = null
    }
    if (safetyTimerRef.current) {
      window.clearTimeout(safetyTimerRef.current)
      safetyTimerRef.current = null
    }
  }, [])

  const startLoading = useCallback(() => {
    clearTimers()
    if (!startedAtRef.current) {
      startedAtRef.current = Date.now()
    }
    setLoading(true)

    safetyTimerRef.current = window.setTimeout(() => {
      startedAtRef.current = null
      setLoading(false)
    }, MAX_VISIBLE_MS)
  }, [clearTimers])

  const finishLoading = useCallback((delayMs: number = 0) => {
    clearTimers()
    hideTimerRef.current = window.setTimeout(() => {
      startedAtRef.current = null
      setLoading(false)
      clearTimers()
    }, delayMs)
  }, [clearTimers])

  useEffect(() => {
    const handleClickCapture = (event: MouseEvent) => {
      if (event.defaultPrevented || event.button !== 0) return
      if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return

      const target = event.target as HTMLElement | null
      const anchor = target?.closest('a[href]') as HTMLAnchorElement | null
      if (!anchor) return

      const href = anchor.getAttribute('href')
      if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:')) {
        return
      }

      if (anchor.hasAttribute('download')) return
      if (anchor.target && anchor.target !== '_self') return

      const destination = new URL(anchor.href, window.location.href)
      if (destination.origin !== window.location.origin) return

      const currentPath = `${window.location.pathname}${window.location.search}`
      const nextPath = `${destination.pathname}${destination.search}`

      if (nextPath === currentPath) return

      startLoading()
    }

    window.addEventListener('click', handleClickCapture, true)

    return () => {
      window.removeEventListener('click', handleClickCapture, true)
      clearTimers()
    }
  }, [clearTimers, startLoading])

  useEffect(() => {
    if (!loading) return

    const startedAt = startedAtRef.current ?? Date.now()
    const elapsed = Date.now() - startedAt
    const remaining = Math.max(MIN_VISIBLE_MS - elapsed, 0)
    finishLoading(remaining)
  }, [finishLoading, loading, pathname, searchKey])

  if (!loading) return null

  return (
    <>
      <div className="pointer-events-none fixed inset-x-0 top-0 z-[100] h-0.5 bg-primary/20">
        <div className="h-full w-[65%] bg-primary shadow-[0_0_10px_hsl(var(--primary))] animate-[navigation-progress_1.1s_ease-in-out_infinite]" />
      </div>
      <style jsx global>{`
        @keyframes navigation-progress {
          0% {
            transform: translateX(-100%);
            width: 35%;
          }
          50% {
            transform: translateX(40%);
            width: 70%;
          }
          100% {
            transform: translateX(130%);
            width: 40%;
          }
        }
      `}</style>
    </>
  )
}
