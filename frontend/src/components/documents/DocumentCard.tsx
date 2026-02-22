'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { sourcesApi } from '@/lib/api/sources'
import { SourceListResponse } from '@/lib/types/api'
import { Card, CardContent, CardFooter, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
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
  Pencil,
  Archive,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { toast } from 'sonner'
import { EditDocumentDialog } from './EditDocumentDialog'

interface DocumentCardProps {
  document: SourceListResponse
  isSelected: boolean
  onSelect: () => void
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
      return { label: 'Completed', className: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' }
    case 'running':
    case 'queued':
    case 'new':
      return { label: 'Processing', className: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' }
    case 'failed':
      return { label: 'Failed', className: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' }
    default:
      return { label: 'Pending', className: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400' }
  }
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function DocumentCard({
  document: doc,
  isSelected,
  onSelect,
  onRefetch,
}: DocumentCardProps) {
  const router = useRouter()
  const Icon = getDocumentIcon(doc)
  const statusInfo = getStatusInfo(doc)
  const docType = getDocumentType(doc)
  const [editDialogOpen, setEditDialogOpen] = useState(false)

  const handleAction = async (action: string) => {
    switch (action) {
      case 'view':
        router.push(`/sources/${doc.id}`)
        break
      case 'edit':
        setEditDialogOpen(true)
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
      case 'archive':
        try {
          await sourcesApi.bulkArchive([doc.id])
          toast.success('Document archived')
          onRefetch()
        } catch {
          toast.error('Failed to archive')
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
    <>
      <Card
        className={cn(
          'relative transition-shadow hover:shadow-md cursor-pointer',
          isSelected && 'ring-2 ring-primary'
        )}
        onClick={() => router.push(`/sources/${doc.id}`)}
      >
        {/* Selection Checkbox */}
        <div
          className="absolute top-3 left-3 z-10"
          onClick={(e) => e.stopPropagation()}
        >
          <Checkbox checked={isSelected} onCheckedChange={onSelect} />
        </div>

        <CardHeader className="pt-10 pb-2">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2 min-w-0">
              <Icon className="w-5 h-5 text-muted-foreground flex-shrink-0" />
              <div className="min-w-0">
                <h3 className="font-medium line-clamp-1">{doc.title || 'Untitled'}</h3>
                <p className="text-sm text-muted-foreground">
                  {formatDate(doc.created)}
                </p>
              </div>
            </div>
            <div onClick={(e) => e.stopPropagation()}>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => handleAction('view')}>
                    <Eye className="w-4 h-4 mr-2" /> View
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleAction('edit')}>
                    <Pencil className="w-4 h-4 mr-2" /> Edit
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleAction('reprocess')}>
                    <RefreshCw className="w-4 h-4 mr-2" /> Re-process
                  </DropdownMenuItem>
                  {doc.asset?.file_path && (
                    <DropdownMenuItem onClick={() => handleAction('download')}>
                      <Download className="w-4 h-4 mr-2" /> Download
                    </DropdownMenuItem>
                  )}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => handleAction('archive')}>
                    <Archive className="w-4 h-4 mr-2" /> Archive
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => handleAction('delete')}
                    className="text-destructive"
                  >
                    <Trash2 className="w-4 h-4 mr-2" /> Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </CardHeader>

        <CardContent className="pb-2">
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline">{docType}</Badge>
            <Badge className={statusInfo.className}>{statusInfo.label}</Badge>
          </div>
        </CardContent>

        <CardFooter className="text-sm text-muted-foreground pt-0">
          <div className="flex items-center gap-4">
            {doc.embedded && (
              <span>{doc.embedded_chunks} chunks</span>
            )}
            {doc.insights_count > 0 && (
              <span>{doc.insights_count} insights</span>
            )}
            {!doc.embedded && doc.insights_count === 0 && (
              <span>No data extracted</span>
            )}
          </div>
        </CardFooter>
      </Card>

      <EditDocumentDialog
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        sourceId={doc.id}
        currentTitle={doc.title || ''}
        currentTopics={doc.topics || []}
        onSaved={onRefetch}
      />
    </>
  )
}
