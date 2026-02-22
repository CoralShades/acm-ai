'use client'

import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { sourcesApi } from '@/lib/api/sources'
import { toast } from 'sonner'

interface EditDocumentDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  sourceId: string
  currentTitle: string
  currentTopics: string[]
  onSaved: () => void
}

export function EditDocumentDialog({
  open,
  onOpenChange,
  sourceId,
  currentTitle,
  currentTopics,
  onSaved,
}: EditDocumentDialogProps) {
  const [title, setTitle] = useState(currentTitle)
  const [topics, setTopics] = useState(currentTopics.join(', '))
  const [saving, setSaving] = useState(false)

  // Sync state when props change (dialog reused for different documents)
  useEffect(() => {
    setTitle(currentTitle)
    setTopics(currentTopics.join(', '))
  }, [currentTitle, currentTopics])

  const handleSave = async () => {
    setSaving(true)
    try {
      await sourcesApi.update(sourceId, {
        title,
        topics: topics
          .split(',')
          .map((t) => t.trim())
          .filter(Boolean),
      })
      toast.success('Document updated')
      onSaved()
      onOpenChange(false)
    } catch {
      toast.error('Failed to update document')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit Document</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="topics">Tags (comma-separated)</Label>
            <Input
              id="topics"
              value={topics}
              onChange={(e) => setTopics(e.target.value)}
              placeholder="e.g., school, asbestos, report"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
