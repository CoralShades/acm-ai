import { formatDistanceToNow } from 'date-fns';

/**
 * Safely formats a date string to relative time (e.g., "2 days ago").
 * Returns empty string if date is invalid.
 */
export function formatCreatedDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      return '';
    }
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return '';
  }
}
