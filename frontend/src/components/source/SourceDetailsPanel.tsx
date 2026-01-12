'use client';

import { useState, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  Copy,
  CheckCircle,
  ExternalLink,
  Database,
  AlertCircle,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { toast } from 'sonner';
import { SourceDetailResponse } from '@/lib/types/api';
import { NotebookAssociations } from '@/components/source/NotebookAssociations';
import { ScrollArea } from '@/components/ui/scroll-area';

interface SourceDetailsPanelProps {
  source: SourceDetailResponse;
  onEmbedContent: () => void;
  isEmbedding: boolean;
  onRefetch: () => void;
}

/**
 * Panel component displaying source metadata and details
 * Used in the source detail page's Details tab
 */
export function SourceDetailsPanel({
  source,
  onEmbedContent,
  isEmbedding,
  onRefetch,
}: SourceDetailsPanelProps) {
  const [copied, setCopied] = useState(false);

  const handleCopyUrl = useCallback(() => {
    if (source?.asset?.url) {
      navigator.clipboard.writeText(source.asset.url);
      setCopied(true);
      toast.success('URL copied to clipboard');
      setTimeout(() => setCopied(false), 2000);
    }
  }, [source]);

  const handleOpenExternal = useCallback(() => {
    if (source?.asset?.url) {
      window.open(source.asset.url, '_blank');
    }
  }, [source]);

  return (
    <ScrollArea className="h-full">
      <div className="space-y-6">
        {/* Embedding Alert */}
        {!source.embedded && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Content Not Embedded</AlertTitle>
            <AlertDescription>
              This content hasn&apos;t been embedded for vector search. Embedding
              enables advanced search capabilities and better content discovery.
              <div className="mt-3">
                <Button onClick={onEmbedContent} disabled={isEmbedding} size="sm">
                  <Database className="mr-2 h-4 w-4" />
                  {isEmbedding ? 'Embedding...' : 'Embed Content'}
                </Button>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Source Information */}
        <div className="space-y-4">
          {source.asset?.url && (
            <div>
              <h3 className="mb-2 text-sm font-semibold">URL</h3>
              <div className="flex items-center gap-2">
                <code className="flex-1 rounded bg-muted px-2 py-1 text-sm truncate">
                  {source.asset.url}
                </code>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleCopyUrl}
                  aria-label={copied ? 'URL copied' : 'Copy URL to clipboard'}
                >
                  {copied ? (
                    <CheckCircle className="h-4 w-4" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleOpenExternal}
                  aria-label="Open URL in new tab"
                >
                  <ExternalLink className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}

          {source.asset?.file_path && (
            <div>
              <h3 className="mb-2 text-sm font-semibold">Uploaded File</h3>
              <code className="rounded bg-muted px-2 py-1 text-sm break-all">
                {source.asset.file_path.split(/[/\\]/).pop()}
              </code>
              <p className="mt-1 text-xs text-muted-foreground">
                Use the Download button in the header to download this file.
              </p>
            </div>
          )}

          {source.topics && source.topics.length > 0 && (
            <div>
              <h3 className="mb-2 text-sm font-semibold">Topics</h3>
              <div className="flex flex-wrap gap-2">
                {source.topics.map((topic, idx) => (
                  <Badge key={idx} variant="outline">
                    {topic}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Metadata */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold">Metadata</h3>
            <div className="flex items-center gap-2">
              <Database className="h-3.5 w-3.5 text-muted-foreground" />
              <Badge
                variant={source.embedded ? 'default' : 'secondary'}
                className="text-xs"
              >
                {source.embedded ? 'Embedded' : 'Not Embedded'}
              </Badge>
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <p className="text-xs font-medium text-muted-foreground">Created</p>
              <p className="text-sm">
                {formatDistanceToNow(new Date(source.created), { addSuffix: true })}
              </p>
              <p className="text-xs text-muted-foreground">
                {new Date(source.created).toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs font-medium text-muted-foreground">Updated</p>
              <p className="text-sm">
                {formatDistanceToNow(new Date(source.updated), { addSuffix: true })}
              </p>
              <p className="text-xs text-muted-foreground">
                {new Date(source.updated).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        {/* Source ID */}
        <div>
          <h3 className="mb-2 text-sm font-semibold">Source ID</h3>
          <code className="rounded bg-muted px-2 py-1 text-xs break-all">
            {source.id}
          </code>
        </div>

        {/* Notebook Associations */}
        <NotebookAssociations
          sourceId={source.id}
          currentNotebookIds={source.notebooks || []}
          onSave={onRefetch}
        />
      </div>
    </ScrollArea>
  );
}
