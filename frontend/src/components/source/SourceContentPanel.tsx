'use client';

import { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import { ExternalLink } from 'lucide-react';
import { SourceDetailResponse } from '@/lib/types/api';
import { ScrollArea } from '@/components/ui/scroll-area';

interface SourceContentPanelProps {
  source: SourceDetailResponse;
}

/**
 * Panel component displaying source content (text, markdown, or YouTube embed)
 * Used in the source detail page's Content tab
 */
export function SourceContentPanel({ source }: SourceContentPanelProps) {
  // Check for YouTube URL
  const youTubeVideoId = useMemo(() => {
    if (!source?.asset?.url) return null;
    const patterns = [
      /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)/,
      /youtube\.com\/watch\?.*v=([^&\n?#]+)/,
    ];
    for (const pattern of patterns) {
      const match = source.asset.url.match(pattern);
      if (match) return match[1];
    }
    return null;
  }, [source?.asset?.url]);

  const isYouTube = !!youTubeVideoId;

  return (
    <ScrollArea className="h-full">
      <div className="space-y-4">
        {/* YouTube Embed */}
        {isYouTube && (
          <div className="space-y-2">
            <div className="aspect-video rounded-lg overflow-hidden bg-black">
              <iframe
                src={`https://www.youtube.com/embed/${youTubeVideoId}`}
                title="YouTube video"
                className="w-full h-full"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
            {source.asset?.url && (
              <a
                href={source.asset.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-muted-foreground hover:underline inline-flex items-center gap-1"
              >
                <ExternalLink className="h-3 w-3" />
                Open on YouTube
              </a>
            )}
          </div>
        )}

        {/* Text Content */}
        <div className="prose prose-sm prose-neutral dark:prose-invert max-w-none prose-headings:font-semibold prose-a:text-blue-600 prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-p:mb-4 prose-p:leading-7 prose-li:mb-2">
          <ReactMarkdown
            components={{
              p: ({ children }) => <p className="mb-4">{children}</p>,
              h1: ({ children }) => (
                <h1 className="text-2xl font-bold mt-6 mb-4">{children}</h1>
              ),
              h2: ({ children }) => (
                <h2 className="text-xl font-bold mt-5 mb-3">{children}</h2>
              ),
              h3: ({ children }) => (
                <h3 className="text-lg font-semibold mt-4 mb-2">{children}</h3>
              ),
              ul: ({ children }) => (
                <ul className="mb-4 list-disc pl-6">{children}</ul>
              ),
              ol: ({ children }) => (
                <ol className="mb-4 list-decimal pl-6">{children}</ol>
              ),
              li: ({ children }) => <li className="mb-1">{children}</li>,
            }}
          >
            {source.full_text || 'No content available'}
          </ReactMarkdown>
        </div>
      </div>
    </ScrollArea>
  );
}
