'use client'

import { useState } from 'react'
import { sourcesApi } from '@/lib/api/sources'
import { Button } from '@/components/ui/button'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { Trash2, X } from 'lucide-react'
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

  const handleBulkDelete = async () => {
    const results = await Promise.allSettled(
      selectedIds.map((id) =>
        sourcesApi
          .delete(id)
          .then(() => ({ id, success: true }))
          .catch(() => ({ id, success: false }))
      )
    )

    const successful = results.filter(
      (r): r is PromiseFulfilledResult<{ id: string; success: boolean }> =>
        r.status === 'fulfilled' && r.value.success
    ).length

    const failed = selectedCount - successful

    if (failed === 0) {
      toast.success(`${selectedCount} documents deleted`)
    } else if (successful > 0) {
      toast.warning(`${successful} deleted, ${failed} failed`)
    } else {
      toast.error('Failed to delete documents')
    }

    setDeleteDialogOpen(false)
    onActionComplete()
  }

  return (
    <>
      <div className="flex items-center gap-3 px-4 py-2 bg-muted rounded-lg">
        <span className="text-sm font-medium">
          {selectedCount} selected
        </span>
        <Button variant="outline" size="sm" onClick={onClearSelection}>
          <X className="w-4 h-4 mr-1" />
          Clear
        </Button>
        <Button
          variant="destructive"
          size="sm"
          onClick={() => setDeleteDialogOpen(true)}
        >
          <Trash2 className="w-4 h-4 mr-1" />
          Delete
        </Button>
      </div>

      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete Documents"
        description={`Are you sure you want to delete ${selectedCount} selected documents? This action cannot be undone.`}
        confirmText="Delete"
        confirmVariant="destructive"
        onConfirm={handleBulkDelete}
      />
    </>
  )
}
