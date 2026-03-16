/**
 * Shared utility for checking whether a tool result represents a backend error.
 *
 * Handles three shapes:
 *  - falsy (null / undefined / empty string) → false
 *  - JSON string that parses to an object with an "error" key → true
 *  - plain object with an "error" key → true
 */
export function isErrorResult(result: unknown): boolean {
  if (!result) return false
  if (typeof result === 'string') {
    try {
      const parsed = JSON.parse(result)
      return typeof parsed === 'object' && parsed !== null && 'error' in parsed
    } catch {
      return false
    }
  }
  return typeof result === 'object' && result !== null && 'error' in result
}
