'use client'

import { useState } from 'react'
import { CheckCircle2, XCircle, Pencil } from 'lucide-react'

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

  const { operation_id, operation, record_id, field, new_value, reason } = preview

  return (
    <div className="border border-amber-300 bg-amber-50 dark:bg-amber-950/30 dark:border-amber-700 rounded-lg p-4 my-2 shadow-sm">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xs font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-400 bg-amber-100 dark:bg-amber-900/50 px-2 py-0.5 rounded">
          {operation} — Approval Required
        </span>
        <span className="text-xs text-muted-foreground font-mono">#{operation_id}</span>
      </div>

      {field && (
        <div className="text-sm mb-2">
          <span className="font-medium">Field:</span>{' '}
          <code className="bg-white dark:bg-gray-800 px-1.5 py-0.5 rounded text-xs">{field}</code>
        </div>
      )}

      {field && new_value && !editing && (
        <div className="text-sm mb-2 flex items-center gap-2">
          <span className="font-medium">New value:</span>
          <code className="bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 px-1.5 py-0.5 rounded text-xs">
            {new_value}
          </code>
          <button
            onClick={() => setEditing(true)}
            className="text-muted-foreground hover:text-foreground transition-colors"
            title="Edit value before approving"
          >
            <Pencil className="h-3 w-3" />
          </button>
        </div>
      )}

      {editing && (
        <div className="text-sm mb-2">
          <label className="font-medium block mb-1">Edit value:</label>
          <input
            type="text"
            value={editedValue}
            onChange={(e) => setEditedValue(e.target.value)}
            className="w-full border rounded px-2 py-1 text-sm bg-white dark:bg-gray-800"
            autoFocus
          />
        </div>
      )}

      {record_id && record_id !== 'new' && (
        <div className="text-xs text-muted-foreground mb-2">Record: {record_id}</div>
      )}

      {reason && (
        <div className="text-sm text-muted-foreground mb-3 italic">{reason}</div>
      )}

      <div className="flex gap-2">
        <button
          onClick={() => {
            const edits = editing && editedValue !== new_value
              ? { new_value: editedValue }
              : undefined
            onApprove(edits)
          }}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors"
        >
          <CheckCircle2 className="h-3.5 w-3.5" />
          Approve
        </button>
        <button
          onClick={onReject}
          className="flex items-center gap-1.5 px-3 py-1.5 border text-sm rounded hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
        >
          <XCircle className="h-3.5 w-3.5" />
          Reject
        </button>
      </div>
    </div>
  )
}
