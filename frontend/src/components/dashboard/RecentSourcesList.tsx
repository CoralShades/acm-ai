import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import { FileText } from 'lucide-react';

interface Source {
  id: string;
  title: string;
  created?: string | null;
}

interface RecentSourcesListProps {
  sources: Source[];
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
      {sources.map((source) => (
        <Link
          key={source.id}
          href={`/sources/${source.id}`}
          className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted transition-colors"
        >
          <FileText className="w-4 h-4 text-muted-foreground flex-shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="font-medium truncate">{source.title}</p>
            {source.created && (
              <p className="text-xs text-muted-foreground">
                {formatDistanceToNow(new Date(source.created), { addSuffix: true })}
              </p>
            )}
          </div>
        </Link>
      ))}
    </div>
  );
}
