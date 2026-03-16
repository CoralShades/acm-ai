'use client'

import { useState, useEffect } from 'react'
import { Check, X, Pencil } from 'lucide-react'

interface WritePreview {
  type: string
  operation_id: string
  operation: string
  record_id?: string
  field?: string
  new_value?: string
  reason?: string
}

interface HITLApprovalDialogProps {
  preview: WritePreview
  onApprove: (edits?: Record<string, string>) => void
  onReject: () => void
}

export function HITLApprovalDialog({
  preview,
  onApprove,
  onReject,
}: HITLApprovalDialogProps) {
  const [editing, setEditing] = useState(false)
  const [editedValue, setEditedValue] = useState(preview.new_value || '')
  const [submitting, setSubmitting] = useState(false)

  // Reset submitting state after 10s timeout (fallback if dialog isn't replaced)
  useEffect(() => {
    if (submitting) {
      const t = setTimeout(() => setSubmitting(false), 10000)
      return () => clearTimeout(t)
    }
  }, [submitting])

  const { operation_id, operation, record_id, field, new_value, reason } = preview

  return (
    <div className="border rounded-lg p-3 my-2 text-sm bg-background">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-amber-600 dark:text-amber-400">
            {operation}
          </span>
          <span className="text-xs text-muted-foreground font-mono">
            #{operation_id}
          </span>
        </div>
      </div>

      {field && (
        <div className="mb-1.5">
          <span className="text-muted-foreground">Field:</span>{' '}
          <code className="bg-muted px-1 py-0.5 rounded text-xs">{field}</code>
        </div>
      )}

      {field && new_value && !editing && (
        <div className="mb-1.5 flex items-center gap-2">
          <span className="text-muted-foreground">Value:</span>
          <code className="text-xs px-1 py-0.5 rounded bg-muted">
            {new_value}
          </code>
          <button
            type="button"
            onClick={() => setEditing(true)}
            className="text-muted-foreground hover:text-foreground cursor-pointer"
            title="Edit value"
            aria-label="Edit value before approving"
          >
            <Pencil className="h-3 w-3" />
          </button>
        </div>
      )}

      {editing && (
        <div className="mb-2">
          <label htmlFor={`edit-${operation_id}`} className="text-xs text-muted-foreground block mb-1">
            Edit value:
          </label>
          <input
            id={`edit-${operation_id}`}
            type="text"
            value={editedValue}
            onChange={(e) => setEditedValue(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Escape') setEditing(false) }}
            className="w-full border rounded px-2 py-1 text-sm bg-background focus:outline-none focus:ring-1 focus:ring-ring"
            autoFocus
          />
        </div>
      )}

      {record_id && record_id !== 'new' && (
        <div className="text-xs text-muted-foreground mb-1.5 font-mono">{record_id}</div>
      )}

      {reason && (
        <div className="text-xs text-muted-foreground mb-2">{reason}</div>
      )}

      <div className="flex gap-2 pt-1">
        <button
          disabled={submitting}
          onClick={() => {
            setSubmitting(true)
            const edits = editing && editedValue !== new_value
              ? { new_value: editedValue }
              : undefined
            onApprove(edits)
          }}
          className="flex items-center gap-1 px-2.5 py-1 bg-foreground text-background text-xs rounded-md cursor-pointer hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Check className="h-3 w-3" />
          {submitting ? 'Applying...' : 'Approve'}
        </button>
        <button
          disabled={submitting}
          onClick={() => {
            setSubmitting(true)
            onReject()
          }}
          className="flex items-center gap-1 px-2.5 py-1 border text-xs rounded-md cursor-pointer hover:bg-muted transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <X className="h-3 w-3" />
          Reject
        </button>
      </div>
    </div>
  )
}
