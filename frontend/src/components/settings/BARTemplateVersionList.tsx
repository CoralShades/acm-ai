'use client'

import { useState } from 'react'
import { Check, Trash2, Eye } from 'lucide-react'
import { toast } from 'sonner'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import type { BARTemplate } from '@/lib/api/bar-templates'
import { barTemplatesApi } from '@/lib/api/bar-templates'

interface BARTemplateVersionListProps {
  templates: BARTemplate[]
  onRefetch: () => void
  onPreview: (template: BARTemplate) => void
}

export function BARTemplateVersionList({
  templates,
  onRefetch,
  onPreview,
}: BARTemplateVersionListProps) {
  const [activating, setActivating] = useState<string | null>(null)
  const [deleting, setDeleting] = useState<string | null>(null)

  const handleActivate = async (template: BARTemplate) => {
    if (!template.id) return
    setActivating(template.id)
    try {
      await barTemplatesApi.activate(template.id)
      toast.success(`Activated: ${template.filename}`)
      onRefetch()
    } catch {
      toast.error('Failed to activate template')
    } finally {
      setActivating(null)
    }
  }

  const handleDelete = async (template: BARTemplate) => {
    if (!template.id) return
    setDeleting(template.id)
    try {
      await barTemplatesApi.delete(template.id)
      toast.success(`Deleted: ${template.filename}`)
      onRefetch()
    } catch {
      toast.error('Cannot delete the active template')
    } finally {
      setDeleting(null)
    }
  }

  if (templates.length === 0) {
    return (
      <p className="text-sm text-muted-foreground py-4">
        No templates uploaded yet. Upload a BAR template to get started.
      </p>
    )
  }

  return (
    <div className="border rounded-lg overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="border-b bg-muted/50">
            <th className="text-left p-3 text-sm font-medium text-muted-foreground">Filename</th>
            <th className="text-left p-3 text-sm font-medium text-muted-foreground">Columns</th>
            <th className="text-left p-3 text-sm font-medium text-muted-foreground">Uploaded</th>
            <th className="text-left p-3 text-sm font-medium text-muted-foreground">Status</th>
            <th className="w-32 p-3" />
          </tr>
        </thead>
        <tbody>
          {templates.map((t) => (
            <tr key={t.id} className="border-b last:border-b-0 hover:bg-muted/30">
              <td className="p-3 text-sm font-medium">{t.filename}</td>
              <td className="p-3 text-sm text-muted-foreground">{t.column_count}</td>
              <td className="p-3 text-sm text-muted-foreground">
                {t.uploaded_at
                  ? new Date(t.uploaded_at).toLocaleDateString(undefined, {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                    })
                  : '—'}
              </td>
              <td className="p-3">
                {t.is_active ? (
                  <Badge className="bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                    Active
                  </Badge>
                ) : (
                  <Badge variant="outline">Inactive</Badge>
                )}
              </td>
              <td className="p-3 flex items-center gap-1 justify-end">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onPreview(t)}
                  title="Preview columns"
                >
                  <Eye className="h-4 w-4" />
                </Button>
                {!t.is_active && (
                  <>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleActivate(t)}
                      disabled={activating === t.id}
                      title="Set as active"
                    >
                      <Check className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(t)}
                      disabled={deleting === t.id}
                      title="Delete"
                      className="text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
