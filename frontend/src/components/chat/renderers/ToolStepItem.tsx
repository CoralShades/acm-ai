'use client'

import React, { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Loader2, Check, XCircle, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

/** Human-readable labels for tool names */
const TOOL_LABELS: Record<string, string> = {
  search_acm_by_risk: 'Searching by risk level',
  search_acm_by_building: 'Searching buildings',
  search_acm_by_room: 'Searching rooms',
  search_acm_by_material: 'Searching materials',
  search_acm_by_product: 'Searching materials',
  get_acm_stats: 'Analyzing statistics',
  get_acm_record_detail: 'Loading record details',
  list_acm_buildings: 'Loading buildings',
  semantic_search_acm: 'Semantic search',
  search_documents: 'Searching documents',
  search_documents_vector: 'Searching documents',
  search_documents_text: 'Text search',
  text_search_documents: 'Text search',
  surreal_query: 'Running database query',
  query_job_records: 'Querying records',
  preview_write: 'Preparing update',
  preview_bulk_write: 'Preparing bulk update',
  execute_pending_write: 'Executing write',
  get_schema_info: 'Loading field schema',
  ask_user_choice: 'Asking for your input',
  undo_last_write: 'Reversing last change',
}

interface ToolStepItemProps {
  toolName: string
  status: 'executing' | 'complete' | 'error'
  children?: React.ReactNode
  defaultExpanded?: boolean
}

/**
 * ToolStepItem — ChatGPT-style collapsible step indicator.
 *
 * Shows spinner → checkmark transition with tool label.
 * When complete, children (result card) collapse behind a chevron.
 * Adjacent ToolStepItems visually stack with shared border styling.
 */
export function ToolStepItem({
  toolName,
  status,
  children,
  defaultExpanded,
}: ToolStepItemProps) {
  const [expanded, setExpanded] = useState(defaultExpanded ?? status !== 'complete')
  const label = TOOL_LABELS[toolName] || toolName.replace(/_/g, ' ')

  // Auto-collapse completed steps after a delay (but not HITL or error steps)
  useEffect(() => {
    if (status === 'complete' && !defaultExpanded && children) {
      const timer = setTimeout(() => setExpanded(false), 1200)
      return () => clearTimeout(timer)
    }
  }, [status, defaultExpanded, children])

  return (
    <motion.div
      data-tool-step
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
      className="my-1"
    >
      {/* Step header row */}
      <button
        type="button"
        onClick={() => children && setExpanded(!expanded)}
        disabled={!children}
        aria-expanded={children ? expanded : undefined}
        className={cn(
          'flex w-full items-center gap-2 rounded-lg border px-3 py-1.5 text-left text-xs transition-colors',
          status === 'error'
            ? 'border-red-200 dark:border-red-900 bg-red-50/50 dark:bg-red-950/20'
            : 'border-border bg-muted/30 hover:bg-muted/50',
          !children && 'cursor-default'
        )}
      >
        {/* Status icon */}
        <span className="flex-shrink-0">
          {status === 'executing' && (
            <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
          )}
          {status === 'complete' && (
            <motion.span
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: 'spring', stiffness: 500, damping: 25 }}
            >
              <Check className="h-3.5 w-3.5 text-green-600 dark:text-green-400" />
            </motion.span>
          )}
          {status === 'error' && (
            <XCircle className="h-3.5 w-3.5 text-red-500" />
          )}
        </span>

        {/* Label */}
        <span className="flex-1 truncate text-muted-foreground">
          {label}
        </span>

        {/* Expand chevron (only when there are children) */}
        {children && (
          <ChevronDown
            className={cn(
              'h-3 w-3 text-muted-foreground/50 transition-transform duration-150',
              expanded && 'rotate-180'
            )}
          />
        )}
      </button>

      {/* Expandable content */}
      <AnimatePresence initial={false}>
        {expanded && children && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="overflow-hidden"
          >
            <div className="pt-1">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
