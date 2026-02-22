'use client'

import { useState } from 'react'
import { sourcesApi } from '@/lib/api/sources'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { Trash2, X, Archive, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'

interface BulkActionsProps {
  selectedCount: number
  selectedIds: string[]
  onClearSelection: () => void
  onActionComplete: () => void
}

export function BulkActions({
  selectedCount,
  selectedIds,
  onClearSelection,
  onActionComplete,
}: BulkActionsProps) {
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [archiveDialogOpen, setArchiveDialogOpen] = useState(false)
  const [reprocessDialogOpen, setReprocessDialogOpen] = useState(false)
  const [loading, setLoading] = useState(false)

  const handleBulkDelete = async () => {
    setLoading(true)
    try {
      const result = await sourcesApi.bulkDelete(selectedIds)
      if (result.failed.length === 0) {
        toast.success(`${selectedCount} documents deleted`, {
          action: {
            label: 'Undo',
            onClick: async () => {
              try {
                await sourcesApi.bulkUndoDelete(selectedIds)
                toast.success('Documents restored')
                onActionComplete()
              } catch {
                toast.error('Failed to undo delete')
              }
            },
          },
        })
      } else if (result.success.length > 0) {
        toast.warning(`${result.success.length} deleted, ${result.failed.length} failed`)
      } else {
        toast.error('Failed to delete documents')
      }
    } catch {
      toast.error('Failed to delete documents')
    } finally {
      setLoading(false)
      setDeleteDialogOpen(false)
      onActionComplete()
    }
  }

  const handleBulkArchive = async () => {
    setLoading(true)
    try {
      const result = await sourcesApi.bulkArchive(selectedIds)
      if (result.failed.length === 0) {
        toast.success(`${selectedCount} documents archived`)
      } else {
        toast.warning(`${result.success.length} archived, ${result.failed.length} failed`)
      }
    } catch {
      toast.error('Failed to archive documents')
    } finally {
      setLoading(false)
      setArchiveDialogOpen(false)
      onActionComplete()
    }
  }

  const handleBulkReprocess = async () => {
    setLoading(true)
    try {
      const result = await sourcesApi.bulkReprocess(selectedIds)
      if (result.failed.length === 0) {
        toast.success(`${selectedCount} documents queued for re-processing`)
      } else {
        toast.warning(`${result.success.length} queued, ${result.failed.length} failed`)
      }
    } catch {
      toast.error('Failed to re-process documents')
    } finally {
      setLoading(false)
      setReprocessDialogOpen(false)
      onActionComplete()
    }
  }

  return (
    <>
      <div className="flex items-center gap-3 px-4 py-2 bg-muted rounded-lg">
        <span className="text-sm font-medium">
          {selectedCount} selected
        </span>
        <Button variant="outline" size="sm" onClick={onClearSelection} disabled={loading}>
          <X className="w-4 h-4 mr-1" />
          Clear
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setReprocessDialogOpen(true)}
          disabled={loading}
        >
          <RefreshCw className="w-4 h-4 mr-1" />
          Re-process
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setArchiveDialogOpen(true)}
          disabled={loading}
        >
          <Archive className="w-4 h-4 mr-1" />
          Archive
        </Button>
        <Button
          variant="destructive"
          size="sm"
          onClick={() => setDeleteDialogOpen(true)}
          disabled={loading}
        >
          <Trash2 className="w-4 h-4 mr-1" />
          Delete
        </Button>
      </div>

      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete Documents"
        description={`Are you sure you want to delete ${selectedCount} selected documents? You can undo this within 30 minutes.`}
        confirmText="Delete"
        confirmVariant="destructive"
        onConfirm={handleBulkDelete}
      />

      <ConfirmDialog
        open={archiveDialogOpen}
        onOpenChange={setArchiveDialogOpen}
        title="Archive Documents"
        description={`Archive ${selectedCount} selected documents? Archived documents are hidden but not deleted.`}
        confirmText="Archive"
        onConfirm={handleBulkArchive}
      />

      <ConfirmDialog
        open={reprocessDialogOpen}
        onOpenChange={setReprocessDialogOpen}
        title="Re-process Documents"
        description={`Re-process ${selectedCount} selected documents? This will re-extract ACM data.`}
        confirmText="Re-process"
        onConfirm={handleBulkReprocess}
      />
    </>
  )
}
