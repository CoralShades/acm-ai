'use client'

import { useState, useEffect, useCallback } from 'react'

/**
 * Hook for persisting state in sessionStorage with SSR/hydration safety.
 *
 * Prevents hydration mismatch by:
 * 1. Always starting with initialValue during SSR and first render
 * 2. Reading from sessionStorage only after hydration (in useEffect)
 *
 * @param key - The sessionStorage key
 * @param initialValue - Default value if no stored value exists
 * @returns Tuple of [storedValue, setValue]
 */
export function useSessionStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T) => void] {
  // Always start with initialValue to prevent hydration mismatch
  const [storedValue, setStoredValue] = useState<T>(initialValue)
  const [isHydrated, setIsHydrated] = useState(false)

  // Read from sessionStorage after hydration (client-side only)
  useEffect(() => {
    setIsHydrated(true)

    try {
      const item = window.sessionStorage.getItem(key)
      if (item !== null) {
        setStoredValue(JSON.parse(item) as T)
      }
    } catch (error) {
      console.warn(`Error reading sessionStorage key "${key}":`, error)
    }
  }, [key])

  // Sync to sessionStorage when value changes (after hydration)
  useEffect(() => {
    if (!isHydrated) return

    try {
      window.sessionStorage.setItem(key, JSON.stringify(storedValue))
    } catch (error) {
      console.warn(`Error writing sessionStorage key "${key}":`, error)
    }
  }, [key, storedValue, isHydrated])

  // Update function
  const setValue = useCallback((value: T) => {
    setStoredValue(value)
  }, [])

  return [storedValue, setValue]
}
