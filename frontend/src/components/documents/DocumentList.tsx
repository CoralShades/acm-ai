'use client'

import { useRouter } from 'next/navigation'
import { sourcesApi } from '@/lib/api/sources'
import { SourceListResponse } from '@/lib/types/api'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  MoreVertical,
  Eye,
  RefreshCw,
  Trash2,
  Download,
  FileText,
  ExternalLink,
  Upload,
} from 'lucide-react'
import { toast } from 'sonner'

interface DocumentListProps {
  documents: SourceListResponse[]
  selectedIds: Set<string>
  onSelect: (id: string) => void
  onSelectAll: () => void
  onRefetch: () => void
}

function getDocumentType(doc: SourceListResponse) {
  if (doc.asset?.file_path) return 'File'
  if (doc.asset?.url) return 'Link'
  return 'Text'
}

function getDocumentIcon(doc: SourceListResponse) {
  if (doc.asset?.file_path) return Upload
  if (doc.asset?.url) return ExternalLink
  return FileText
}

function getStatusInfo(doc: SourceListResponse) {
  const status = doc.status || (doc.embedded ? 'completed' : 'pending')
  switch (status) {
    case 'completed':
      return {
        label: 'Completed',
        className:
          'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      }
    case 'running':
    case 'queued':
    case 'new':
      return {
        label: 'Processing',
        className:
          'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
      }
    case 'failed':
      return {
        label: 'Failed',
        className:
          'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
      }
    default:
      return {
        label: 'Pending',
        className:
          'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400',
      }
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function DocumentList({
  documents,
  selectedIds,
  onSelect,
  onSelectAll,
  onRefetch,
}: DocumentListProps) {
  const router = useRouter()

  const handleAction = async (action: string, doc: SourceListResponse) => {
    switch (action) {
      case 'view':
        router.push(`/sources/${doc.id}`)
        break
      case 'reprocess':
        try {
          await sourcesApi.retry(doc.id)
          toast.success('Re-processing started')
          onRefetch()
        } catch {
          toast.error('Failed to re-process')
        }
        break
      case 'download':
        try {
          const response = await sourcesApi.downloadFile(doc.id)
          const url = window.URL.createObjectURL(new Blob([response.data]))
          const a = window.document.createElement('a')
          a.href = url
          a.download = doc.title || 'document'
          a.click()
          window.URL.revokeObjectURL(url)
        } catch {
          toast.error('Failed to download')
        }
        break
      case 'delete':
        try {
          await sourcesApi.delete(doc.id)
          toast.success('Document deleted')
          onRefetch()
        } catch {
          toast.error('Failed to delete')
        }
        break
    }
  }

  return (
    <div className="border rounded-lg overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b bg-muted/50">
            <th className="w-10 p-3">
              <Checkbox
                checked={
                  selectedIds.size === documents.length && documents.length > 0
                }
                onCheckedChange={onSelectAll}
              />
            </th>
            <th className="text-left p-3 text-sm font-medium text-muted-foreground">
              Name
            </th>
            <th className="text-left p-3 text-sm font-medium text-muted-foreground hidden md:table-cell">
              Type
            </th>
            <th className="text-left p-3 text-sm font-medium text-muted-foreground hidden sm:table-cell">
              Date
            </th>
            <th className="text-left p-3 text-sm font-medium text-muted-foreground">
              Status
            </th>
            <th className="text-left p-3 text-sm font-medium text-muted-foreground hidden lg:table-cell">
              Insights
            </th>
            <th className="w-10 p-3" />
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => {
            const Icon = getDocumentIcon(doc)
            const statusInfo = getStatusInfo(doc)
            const docType = getDocumentType(doc)

            return (
              <tr
                key={doc.id}
                className="border-b last:border-b-0 hover:bg-muted/30 cursor-pointer transition-colors"
                onClick={() => router.push(`/sources/${doc.id}`)}
              >
                <td
                  className="p-3"
                  onClick={(e) => e.stopPropagation()}
                >
                  <Checkbox
                    checked={selectedIds.has(doc.id)}
                    onCheckedChange={() => onSelect(doc.id)}
                  />
                </td>
                <td className="p-3">
                  <div className="flex items-center gap-2 min-w-0">
                    <Icon className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                    <span className="font-medium truncate">
                      {doc.title || 'Untitled'}
                    </span>
                  </div>
                </td>
                <td className="p-3 hidden md:table-cell">
                  <Badge variant="outline" className="text-xs">
                    {docType}
                  </Badge>
                </td>
                <td className="p-3 text-sm text-muted-foreground hidden sm:table-cell">
                  {formatDate(doc.created)}
                </td>
                <td className="p-3">
                  <Badge className={statusInfo.className}>
                    {statusInfo.label}
                  </Badge>
                </td>
                <td className="p-3 text-sm text-muted-foreground hidden lg:table-cell">
                  {doc.insights_count > 0
                    ? `${doc.insights_count} insights`
                    : doc.embedded
                      ? `${doc.embedded_chunks} chunks`
                      : '—'}
                </td>
                <td
                  className="p-3"
                  onClick={(e) => e.stopPropagation()}
                >
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={() => handleAction('view', doc)}
                      >
                        <Eye className="w-4 h-4 mr-2" /> View
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => handleAction('reprocess', doc)}
                      >
                        <RefreshCw className="w-4 h-4 mr-2" /> Re-process
                      </DropdownMenuItem>
                      {doc.asset?.file_path && (
                        <DropdownMenuItem
                          onClick={() => handleAction('download', doc)}
                        >
                          <Download className="w-4 h-4 mr-2" /> Download
                        </DropdownMenuItem>
                      )}
                      <DropdownMenuItem
                        onClick={() => handleAction('delete', doc)}
                        className="text-destructive"
                      >
                        <Trash2 className="w-4 h-4 mr-2" /> Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
