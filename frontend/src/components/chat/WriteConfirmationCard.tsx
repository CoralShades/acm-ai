'use client'

interface WritePreview {
  type: 'preview_write'
  operation_id: string
  operation: string
  record_id?: string
  field?: string
  new_value?: string
  reason?: string
  instruction?: string
}

interface WriteConfirmationCardProps {
  content: string
  onConfirm: (operationId: string) => void
  onCancel: (operationId: string) => void
}

/**
 * WriteConfirmationCard — renders a confirmation UI when the CRUD agent
 * proposes a write operation (preview_write JSON in tool result content).
 *
 * Returns null for any content that is not a preview_write JSON object,
 * so it is safe to render speculatively for any tool result string.
 *
 * Story: E19-S8 Conversational CRUD Chat
 */
export function WriteConfirmationCard({
  content,
  onConfirm,
  onCancel,
}: WriteConfirmationCardProps) {
  let preview: WritePreview | null = null
  try {
    const parsed = JSON.parse(content)
    if (parsed?.type === 'preview_write') {
      preview = parsed as WritePreview
    }
  } catch {
    return null
  }

  if (!preview) return null

  const { operation_id, operation, record_id, field, new_value, reason } = preview

  return (
    <div className="border border-amber-200 bg-amber-50 rounded-lg p-4 my-2">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xs font-semibold uppercase tracking-wide text-amber-700 bg-amber-100 px-2 py-0.5 rounded">
          {operation} Preview
        </span>
        <span className="text-xs text-muted-foreground font-mono">#{operation_id}</span>
      </div>

      {field && (
        <div className="text-sm mb-2">
          <span className="font-medium">Field:</span>{' '}
          <code className="bg-white px-1 rounded">{field}</code>
          {' → '}
          <code className="bg-white px-1 rounded text-green-700">{new_value}</code>
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
          onClick={() => onConfirm(operation_id)}
          className="px-3 py-1.5 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors"
        >
          Confirm
        </button>
        <button
          onClick={() => onCancel(operation_id)}
          className="px-3 py-1.5 border text-sm rounded hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
