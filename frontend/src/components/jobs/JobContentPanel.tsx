'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { Download, FileText } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useSource } from '@/lib/hooks/use-sources'
import { sourcesApi } from '@/lib/api/sources'

interface JobContentPanelProps {
  sourceId: string
}

/**
 * Renders extracted source markdown content for the Job Detail Content tab.
 */
export function JobContentPanel({ sourceId }: JobContentPanelProps) {
  const { data: source, isLoading } = useSource(sourceId)
  const [isDownloading, setIsDownloading] = useState(false)

  const handleDownloadPdf = async () => {
    if (!source?.asset?.file_path || isDownloading) return

    try {
      setIsDownloading(true)
      const response = await sourcesApi.downloadFile(source.id)
      const filename =
        source.asset.file_path.split(/[/\\]/).pop() || `source-${source.id}.pdf`

      const blobUrl = window.URL.createObjectURL(response.data)
      const link = document.createElement('a')
      link.href = blobUrl
      link.download = filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(blobUrl)
    } catch {
      toast.error('Failed to download PDF')
    } finally {
      setIsDownloading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
        Loading content...
      </div>
    )
  }

  if (!source) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
        Source content unavailable
      </div>
    )
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border bg-muted/30 px-4 py-3">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <FileText className="h-4 w-4" />
          {source.asset?.file_path
            ? 'Original PDF available'
            : 'No uploaded PDF available'}
        </div>
        {source.asset?.file_path && (
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" asChild>
              <a
                href={`/api/sources/${encodeURIComponent(source.id)}/download`}
                target="_blank"
                rel="noopener noreferrer"
              >
                Open PDF
              </a>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleDownloadPdf}
              disabled={isDownloading}
            >
              <Download className="mr-2 h-4 w-4" />
              {isDownloading ? 'Downloading...' : 'Download PDF'}
            </Button>
          </div>
        )}
      </div>

      <ScrollArea className="mt-4 flex-1 min-h-0">
        <div className="prose prose-sm prose-neutral dark:prose-invert max-w-none pr-4 prose-headings:font-semibold prose-a:text-blue-600 prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-p:mb-4 prose-p:leading-7 prose-li:mb-2">
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
            {source.full_text || 'No extracted content available yet.'}
          </ReactMarkdown>
        </div>
      </ScrollArea>
    </div>
  )
}
