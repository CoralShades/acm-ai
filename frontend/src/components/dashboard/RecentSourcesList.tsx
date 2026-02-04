import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import { FileText } from 'lucide-react';

interface Source {
  id: string;
  title: string | null;
  created?: string | null;
}

interface RecentSourcesListProps {
  sources: Source[];
}

function formatCreatedDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    // Check for invalid date
    if (isNaN(date.getTime())) {
      return '';
    }
    return formatDistanceToNow(date, { addSuffix: true });
  } catch {
    return '';
  }
}

export function RecentSourcesList({ sources }: RecentSourcesListProps) {
  if (sources.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-4">
        No sources yet
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {sources.map((source) => {
        const formattedDate = source.created ? formatCreatedDate(source.created) : '';

        return (
          <Link
            key={source.id}
            href={`/sources/${source.id}`}
            className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted transition-colors"
          >
            <FileText className="w-4 h-4 text-muted-foreground flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="font-medium truncate">{source.title || 'Untitled'}</p>
              {formattedDate && (
                <p className="text-xs text-muted-foreground">{formattedDate}</p>
              )}
            </div>
          </Link>
        );
      })}
    </div>
  );
}
