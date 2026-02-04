import { useState, useEffect } from 'react'

/**
 * A hook that debounces a value, delaying updates until a specified time has passed
 * since the last change. Useful for search inputs to prevent excessive re-renders.
 *
 * @param value - The value to debounce
 * @param delay - The delay in milliseconds (default: 300ms)
 * @returns The debounced value
 *
 * @example
 * ```tsx
 * const [searchText, setSearchText] = useState('')
 * const debouncedSearch = useDebouncedValue(searchText, 300)
 *
 * useEffect(() => {
 *   // This will only run 300ms after the user stops typing
 *   performSearch(debouncedSearch)
 * }, [debouncedSearch])
 * ```
 */
export function useDebouncedValue<T>(value: T, delay: number = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(timer)
    }
  }, [value, delay])

  return debouncedValue
}
