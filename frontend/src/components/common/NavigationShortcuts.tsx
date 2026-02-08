'use client'

import { useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'

const navigationMap: Record<string, string> = {
  d: '/',
  s: '/sources',
  a: '/acm',
  m: '/models',
  h: '/search',
}

export function NavigationShortcuts() {
  const router = useRouter()
  const gPressedRef = useRef(false)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Skip if focus is inside editable elements
      const target = e.target as HTMLElement | null
      if (
        target &&
        (target.isContentEditable ||
          ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName))
      ) {
        return
      }

      // Skip if modifier keys are held (except shift for ?)
      if (e.metaKey || e.ctrlKey || e.altKey) {
        return
      }

      const key = e.key.toLowerCase()

      // Track G key press
      if (key === 'g' && !gPressedRef.current) {
        gPressedRef.current = true

        // Clear any existing timeout
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current)
        }

        // Reset G press after 1 second
        timeoutRef.current = setTimeout(() => {
          gPressedRef.current = false
          timeoutRef.current = null
        }, 1000)

        return
      }

      // If G was pressed, check for navigation key
      if (gPressedRef.current) {
        const href = navigationMap[key]
        if (href) {
          e.preventDefault()
          router.push(href)
        }

        // Reset G press state regardless of whether key matched
        gPressedRef.current = false
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current)
          timeoutRef.current = null
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [router])

  return null
}
