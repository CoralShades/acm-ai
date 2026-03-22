'use client'

import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Check, X, Pencil } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

interface WriteApprovalPayload {
  type: 'write_approval'
  operation_id: string
  operation?: string
  record_id?: string
  field?: string
  new_value?: string
  reason?: string
  affected_count?: number
  record_ids?: string[]
}

interface HITLApprovalCardProps {
  payload: WriteApprovalPayload
  onApprove: (edits?: { new_value?: string }) => void
  onReject: () => void
}

/**
 * HITLApprovalCard — VAEA-styled write approval card for interrupt() HITL.
 *
 * Rendered by useLangGraphInterrupt when the backend's approval_node
 * calls interrupt(). Shows operation preview with amber accent,
 * inline value editing, and approve/reject buttons.
 */
export function HITLApprovalCard({ payload, onApprove, onReject }: HITLApprovalCardProps) {
  const [editing, setEditing] = useState(false)
  const [editValue, setEditValue] = useState(payload.new_value || '')
  const isBulk = (payload.affected_count ?? 0) > 1

  return (
    <motion.div
      initial={{ opacity: 0, y: 12, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ type: 'spring', stiffness: 300, damping: 22, mass: 0.8 }}
      role="alertdialog"
      aria-label={`Approve ${payload.operation || 'write'} operation`}
      className="my-2 rounded-lg border border-amber-200 dark:border-amber-800 bg-amber-50/50 dark:bg-amber-950/20 border-l-4 border-l-amber-500 overflow-hidden"
    >
      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2 border-b border-amber-200/50 dark:border-amber-800/50">
        <span className="inline-flex items-center rounded-md bg-amber-100 dark:bg-amber-900/50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-300">
          {payload.operation || 'WRITE'} Preview
        </span>
        <span className="text-[10px] font-mono text-muted-foreground">
          #{payload.operation_id}
        </span>
      </div>

      {/* Body */}
      <div className="px-3 py-2 space-y-2">
        {/* Record/field info */}
        {payload.record_id && (
          <div className="text-xs">
            <span className="text-muted-foreground">Record:</span>{' '}
            <span className="font-mono">{isBulk ? `${payload.affected_count} records` : payload.record_id}</span>
          </div>
        )}

        {payload.field && (
          <div className="text-xs">
            <span className="text-muted-foreground">Field:</span>{' '}
            <span className="font-semibold">{payload.field}</span>
          </div>
        )}

        {/* Value with inline editing */}
        {payload.new_value !== undefined && (
          <div className="text-xs">
            <span className="text-muted-foreground">New value:</span>{' '}
            {editing ? (
              <div className="mt-1 flex gap-1.5">
                <Input
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  className="h-7 text-xs"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') setEditing(false)
                    if (e.key === 'Escape') { setEditValue(payload.new_value || ''); setEditing(false) }
                  }}
                />
                <Button
                  size="sm"
                  variant="ghost"
                  className="h-7 px-2"
                  onClick={() => setEditing(false)}
                >
                  <Check className="h-3 w-3" />
                </Button>
              </div>
            ) : (
              <span className="inline-flex items-center gap-1">
                <span className="font-semibold text-green-700 dark:text-green-400">
                  {editValue || payload.new_value}
                </span>
                <button
                  type="button"
                  onClick={() => setEditing(true)}
                  className="text-muted-foreground hover:text-foreground"
                  aria-label="Edit value"
                >
                  <Pencil className="h-3 w-3" />
                </button>
              </span>
            )}
          </div>
        )}

        {/* Reason */}
        {payload.reason && (
          <p className="text-xs text-muted-foreground italic">
            {payload.reason}
          </p>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-2 px-3 py-2 border-t border-amber-200/50 dark:border-amber-800/50">
        <Button
          size="sm"
          className={cn(
            'h-7 gap-1 text-xs',
            'bg-green-600 hover:bg-green-700 text-white dark:bg-green-700 dark:hover:bg-green-600'
          )}
          onClick={() => {
            const edits = editValue !== payload.new_value ? { new_value: editValue } : undefined
            onApprove(edits)
          }}
          aria-label="Approve operation"
        >
          <Check className="h-3 w-3" />
          Approve
        </Button>
        <Button
          size="sm"
          variant="outline"
          className="h-7 gap-1 text-xs"
          onClick={onReject}
          aria-label="Reject operation"
        >
          <X className="h-3 w-3" />
          Reject
        </Button>
      </div>
    </motion.div>
  )
}
