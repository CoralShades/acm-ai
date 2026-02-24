'use client'

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import type { ACMRecord } from '@/lib/types/acm'

interface RecordMergeModalProps {
  open: boolean
  onClose: () => void
  record1: ACMRecord | null
  record2: ACMRecord | null
  onMerge: (keepId: string, deleteId: string) => void
}

interface RecordCardProps {
  record: ACMRecord
  onKeep: () => void
}

function RecordCard({ record, onKeep }: RecordCardProps) {
  return (
    <div className="border rounded-lg p-4 space-y-2 flex-1">
      <dl className="space-y-1 text-sm">
        <div className="flex gap-2">
          <dt className="text-muted-foreground font-medium w-28 shrink-0">Building:</dt>
          <dd className="truncate">{record.building_id || '—'}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="text-muted-foreground font-medium w-28 shrink-0">Room/Area:</dt>
          <dd className="truncate">{record.room_name || '—'}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="text-muted-foreground font-medium w-28 shrink-0">ACM Name:</dt>
          <dd className="truncate">{record.product || '—'}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="text-muted-foreground font-medium w-28 shrink-0">Description:</dt>
          <dd className="truncate">{record.material_description || '—'}</dd>
        </div>
      </dl>
      <Button
        size="sm"
        variant="default"
        className="w-full mt-3"
        onClick={onKeep}
      >
        Keep this one
      </Button>
    </div>
  )
}

/**
 * RecordMergeModal — simple modal for merging duplicate ACM records.
 *
 * Shows two records side-by-side with their key fields. The user clicks
 * "Keep this one" to select which record to retain; the other is deleted.
 *
 * Story: E19-S6 ACM Schema Mapping Wizard — Step 2 (Frontend)
 */
export function RecordMergeModal({
  open,
  onClose,
  record1,
  record2,
  onMerge,
}: RecordMergeModalProps) {
  if (!record1 || !record2) return null

  const handleKeep = (keepId: string, deleteId: string) => {
    onMerge(keepId, deleteId)
    onClose()
  }

  return (
    <Dialog open={open} onOpenChange={(isOpen) => { if (!isOpen) onClose() }}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Merge Duplicate Records</DialogTitle>
          <DialogDescription>
            These two records appear to be duplicates. Select which record to
            keep. The other record will be permanently deleted.
          </DialogDescription>
        </DialogHeader>

        <div className="flex gap-4">
          <RecordCard
            record={record1}
            onKeep={() => handleKeep(record1.id, record2.id)}
          />
          <RecordCard
            record={record2}
            onKeep={() => handleKeep(record2.id, record1.id)}
          />
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
