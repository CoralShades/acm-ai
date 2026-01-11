'use client'

import { useState, useEffect } from 'react'

/**
 * Hook to detect if viewport matches a media query.
 * Returns false during SSR to avoid hydration mismatches.
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false)

  useEffect(() => {
    const mediaQuery = window.matchMedia(query)
    setMatches(mediaQuery.matches)

    const handler = (event: MediaQueryListEvent) => {
      setMatches(event.matches)
    }

    mediaQuery.addEventListener('change', handler)
    return () => mediaQuery.removeEventListener('change', handler)
  }, [query])

  return matches
}

/**
 * Returns true if viewport is >= 1024px (Tailwind's 'lg' breakpoint)
 */
export function useIsDesktop(): boolean {
  return useMediaQuery('(min-width: 1024px)')
}

/**
 * Returns the number of columns for a responsive grid based on viewport width.
 * - < 768px: 1 column
 * - 768px+: 2 columns
 * - 1024px+: 3 columns
 * - 1280px+: 4 columns
 */
export function useGridColumns(): number {
  const isXl = useMediaQuery('(min-width: 1280px)')
  const isLg = useMediaQuery('(min-width: 1024px)')
  const isMd = useMediaQuery('(min-width: 768px)')

  if (isXl) return 4
  if (isLg) return 3
  if (isMd) return 2
  return 1
}
