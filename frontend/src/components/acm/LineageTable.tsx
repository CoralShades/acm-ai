'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { RawExtractionRecord } from '@/lib/types/acm'

interface LineageTableProps {
  rawExtractions: RawExtractionRecord[]
  consensusTier?: string | null
  consensusScores?: Record<string, number> | null
}

/** Map consensus tier key to a human-readable label and badge colour class */
function getConsensusTierDisplay(tier: string | null | undefined): {
  label: string
  className: string
} {
  switch (tier) {
    case 'multi_provider_agreement':
      return { label: 'Multi-Provider Agreement', className: 'bg-green-100 text-green-800 border-green-300 dark:bg-green-900/30 dark:text-green-300' }
    case 'single_provider':
      return { label: 'Single Provider', className: 'bg-blue-100 text-blue-800 border-blue-300 dark:bg-blue-900/30 dark:text-blue-300' }
    case 'multi_provider_conflict':
      return { label: 'Multi-Provider Conflict', className: 'bg-orange-100 text-orange-800 border-orange-300 dark:bg-orange-900/30 dark:text-orange-300' }
    case 'manual_override':
      return { label: 'Manual Override', className: 'bg-purple-100 text-purple-800 border-purple-300 dark:bg-purple-900/30 dark:text-purple-300' }
    default:
      return { label: tier ?? 'Unknown', className: 'bg-muted text-muted-foreground border-border' }
  }
}

/** Colour classes for confidence values */
function getConfidenceClass(confidence: number | null): string {
  if (confidence === null) return 'text-muted-foreground'
  if (confidence > 0.8) return 'text-green-700 dark:text-green-400 font-medium'
  if (confidence >= 0.5) return 'text-yellow-700 dark:text-yellow-400 font-medium'
  return 'text-red-700 dark:text-red-400 font-medium'
}

/** Expandable officer edits cell */
function OfficerEditsCell({ edits }: { edits: RawExtractionRecord['officer_edits'] }) {
  const [expanded, setExpanded] = useState(false)

  if (!edits || edits.length === 0) {
    return <span className="text-muted-foreground">0</span>
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
        aria-expanded={expanded}
      >
        {expanded ? (
          <ChevronDown className="h-3 w-3" />
        ) : (
          <ChevronRight className="h-3 w-3" />
        )}
        {edits.length} edit{edits.length !== 1 ? 's' : ''}
      </button>
      {expanded && (
        <ul className="mt-1 space-y-1 pl-4 text-xs text-muted-foreground">
          {edits.map((edit, idx) => (
            <li key={idx} className="border-l pl-2">
              <span className="font-medium text-foreground">{edit.field}:</span>{' '}
              <span className="line-through opacity-60">{String(edit.old_value)}</span>
              {' → '}
              <span>{String(edit.new_value)}</span>
              <span className="ml-1 opacity-50">({edit.user})</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

/**
 * LineageTable — displays extraction lineage for a single ACM record.
 *
 * Shows consensus tier badge at top, then a per-provider comparison table
 * with confidence scores colour-coded and officer edit history.
 *
 * Story: E33-S6 Provenance Viewer
 */
export function LineageTable({ rawExtractions, consensusTier, consensusScores }: LineageTableProps) {
  const tierDisplay = getConsensusTierDisplay(consensusTier)

  return (
    <div className="space-y-3">
      {/* Consensus tier header */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-medium text-muted-foreground">Consensus:</span>
        <Badge
          variant="outline"
          className={cn('text-xs', tierDisplay.className)}
        >
          {tierDisplay.label}
        </Badge>
        {consensusScores && Object.keys(consensusScores).length > 0 && (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {Object.entries(consensusScores).map(([provider, score]) => (
              <span key={provider} className="inline-flex items-center gap-1">
                <span className="font-medium">{provider}:</span>
                <span className={getConfidenceClass(score)}>{(score * 100).toFixed(0)}%</span>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Lineage table */}
      {rawExtractions.length === 0 ? (
        <p className="text-sm text-muted-foreground py-4 text-center">
          No extraction data available for this record
        </p>
      ) : (
        <div className="overflow-x-auto rounded-lg border">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-muted/50 border-b">
                <th className="text-left px-3 py-2 font-medium text-muted-foreground whitespace-nowrap">Provider</th>
                <th className="text-left px-3 py-2 font-medium text-muted-foreground whitespace-nowrap">Backend</th>
                <th className="text-left px-3 py-2 font-medium text-muted-foreground whitespace-nowrap">Confidence</th>
                <th className="text-left px-3 py-2 font-medium text-muted-foreground whitespace-nowrap">Has Bbox</th>
                <th className="text-left px-3 py-2 font-medium text-muted-foreground whitespace-nowrap">Edits</th>
              </tr>
            </thead>
            <tbody>
              {rawExtractions.map((extraction) => (
                <tr key={extraction.id} className="border-b last:border-0 hover:bg-muted/20">
                  <td className="px-3 py-2 font-medium capitalize">{extraction.provider_id}</td>
                  <td className="px-3 py-2 text-muted-foreground text-xs font-mono">
                    {extraction.extraction_backend}
                  </td>
                  <td className={cn('px-3 py-2', getConfidenceClass(extraction.confidence))}>
                    {extraction.confidence !== null
                      ? `${(extraction.confidence * 100).toFixed(0)}%`
                      : <span className="text-muted-foreground">—</span>}
                  </td>
                  <td className="px-3 py-2">
                    {extraction.bbox ? (
                      <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-300 dark:bg-green-900/20 dark:text-green-400">
                        Yes
                      </Badge>
                    ) : (
                      <span className="text-muted-foreground text-xs">No</span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    <OfficerEditsCell edits={extraction.officer_edits} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
