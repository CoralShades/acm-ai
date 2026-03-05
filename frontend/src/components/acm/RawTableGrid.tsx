'use client'

import { useMemo, useState } from 'react'
import Link from 'next/link'
import { AgGridReact } from 'ag-grid-react'
import type { ColDef, ValueGetterParams } from 'ag-grid-community'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { ArrowLeft, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { useRawExtractions, usePatchRawExtraction, useReprocessExtraction } from '@/lib/hooks/useRawExtractions'
import { useAuthStore } from '@/lib/stores/auth-store'
import type { RawExtractionRecord, OfficerEdit, StructuredJsonContent } from '@/lib/types/acm'

// Register AG Grid modules once (idempotent)
ModuleRegistry.registerModules([AllCommunityModule])

type ProviderTab = 'all' | 'docling' | 'mineru' | 'consensus'

interface RawTableGridProps {
  sourceId: string
}

function ProviderBadge({ value }: { value: string | null | undefined }) {
  if (!value) return <span className="text-muted-foreground">-</span>

  const colorMap: Record<string, string> = {
    docling: 'text-blue-700 bg-blue-50 border-blue-200',
    mineru: 'text-purple-700 bg-purple-50 border-purple-200',
  }
  const classes = colorMap[value.toLowerCase()] ?? 'text-muted-foreground bg-muted'

  return (
    <span
      className={`inline-flex items-center rounded px-2 py-0.5 text-xs font-medium border ${classes}`}
    >
      {value}
    </span>
  )
}

function parseStructuredJson(raw: string | null): StructuredJsonContent | null {
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw)
    if (typeof parsed === 'object' && parsed !== null) {
      return {
        headers: Array.isArray(parsed.headers) ? parsed.headers : [],
        rows: Array.isArray(parsed.rows) ? parsed.rows : [],
      }
    }
    return null
  } catch {
    return null
  }
}

function diffStructuredJson(
  original: StructuredJsonContent,
  updated: StructuredJsonContent,
  currentUser: string
): OfficerEdit[] {
  const edits: OfficerEdit[] = []
  updated.rows.forEach((row, rowIdx) => {
    row.forEach((cell, colIdx) => {
      const oldCell = original.rows[rowIdx]?.[colIdx] ?? ''
      if (cell !== oldCell) {
        const header = updated.headers[colIdx] ?? `col_${colIdx}`
        edits.push({
          field: `row[${rowIdx}].${header}`,
          old_value: oldCell,
          new_value: cell,
          user: currentUser,
          timestamp: new Date().toISOString(),
        })
      }
    })
  })
  return edits
}

export function RawTableGrid({ sourceId }: RawTableGridProps) {
  const [activeProvider, setActiveProvider] = useState<ProviderTab>('all')
  const [editRow, setEditRow] = useState<RawExtractionRecord | null>(null)
  const [editJsonText, setEditJsonText] = useState('')
  const [editHistoryRow, setEditHistoryRow] = useState<RawExtractionRecord | null>(null)
  const [reprocessConfirmOpen, setReprocessConfirmOpen] = useState(false)
  const [jsonError, setJsonError] = useState<string | null>(null)

  const providerParam =
    activeProvider === 'all' || activeProvider === 'consensus' ? undefined : activeProvider

  const { data, isLoading } = useRawExtractions(sourceId, providerParam)
  const patchMutation = usePatchRawExtraction(sourceId)
  const reprocessMutation = useReprocessExtraction()

  // Get current user from auth store for officer edit attribution
  const token = useAuthStore((s) => s.token)
  const currentUser = token ? 'officer' : 'unknown'

  const total = data?.total ?? 0
  const extractions = data?.extractions ?? []

  const columnDefs = useMemo<ColDef<RawExtractionRecord>[]>(
    () => [
      {
        field: 'page_number',
        headerName: 'Page',
        width: 80,
        pinned: 'left' as const,
        sortable: true,
      },
      {
        field: 'provider_id',
        headerName: 'Provider',
        width: 110,
        pinned: 'left' as const,
        cellRenderer: ({ value }: { value: string | null | undefined }) => (
          <ProviderBadge value={value} />
        ),
        sortable: true,
      },
      {
        field: 'confidence',
        headerName: 'Confidence',
        width: 110,
        valueFormatter: ({ value }: { value: number | null | undefined }) => {
          if (value == null) return '-'
          return `${Math.round(value * 100)}%`
        },
        sortable: true,
      },
      {
        headerName: 'Rows',
        width: 80,
        sortable: false,
        valueGetter: (params: ValueGetterParams<RawExtractionRecord>) => {
          if (!params.data?.structured_json) return 0
          const parsed = parseStructuredJson(params.data.structured_json)
          return parsed ? parsed.rows.length : '?'
        },
      },
      {
        headerName: 'Cols',
        width: 80,
        sortable: false,
        valueGetter: (params: ValueGetterParams<RawExtractionRecord>) => {
          if (!params.data?.structured_json) return 0
          const parsed = parseStructuredJson(params.data.structured_json)
          return parsed ? parsed.headers.length : '?'
        },
      },
      {
        field: 'structured_json',
        headerName: 'Preview',
        flex: 1,
        minWidth: 200,
        sortable: false,
        cellRenderer: ({ data: row }: { data: RawExtractionRecord | undefined }) => {
          if (!row) return null
          const parsed = parseStructuredJson(row.structured_json)
          const preview = parsed
            ? parsed.rows[0]?.join(' | ') ?? '(empty)'
            : row.structured_json
              ? 'Unparseable JSON'
              : '(no data)'
          const truncated = preview.length > 80 ? preview.slice(0, 80) + '…' : preview
          return (
            <button
              className="text-left text-xs text-blue-600 hover:underline truncate w-full cursor-pointer"
              onClick={() => {
                setEditRow(row)
                setJsonError(null)
                setEditJsonText(
                  row.structured_json
                    ? (() => { try { return JSON.stringify(JSON.parse(row.structured_json), null, 2) } catch { return row.structured_json } })()
                    : ''
                )
              }}
              title="Click to edit structured JSON"
            >
              {truncated || '(click to edit)'}
            </button>
          )
        },
      },
      {
        headerName: 'Edits',
        width: 80,
        sortable: false,
        valueGetter: (params: ValueGetterParams<RawExtractionRecord>) =>
          params.data?.officer_edits?.length ?? 0,
        cellRenderer: ({ data: row, value }: { data: RawExtractionRecord | undefined; value: number }) => {
          if (!row) return null
          return (
            <button
              className="text-xs text-blue-600 hover:underline cursor-pointer"
              onClick={() => setEditHistoryRow(row)}
              title="View edit history"
            >
              {value}
            </button>
          )
        },
      },
    ],
    []
  )

  const defaultColDef = useMemo<ColDef>(
    () => ({
      resizable: true,
      suppressMenu: true,
    }),
    []
  )

  function handleSaveEdit() {
    if (!editRow) return
    let parsedUpdated: StructuredJsonContent | null = null
    try {
      parsedUpdated = JSON.parse(editJsonText)
    } catch {
      setJsonError('Invalid JSON — please fix before saving.')
      return
    }
    setJsonError(null)

    const originalParsed = parseStructuredJson(editRow.structured_json)
    const edits: OfficerEdit[] =
      parsedUpdated && originalParsed
        ? diffStructuredJson(originalParsed, parsedUpdated, currentUser)
        : []

    patchMutation.mutate(
      {
        extractionId: editRow.id,
        body: {
          structured_json: editJsonText,
          edits,
        },
      },
      {
        onSuccess: () => setEditRow(null),
      }
    )
  }

  function handleReprocess() {
    setReprocessConfirmOpen(false)
    reprocessMutation.mutate(sourceId)
  }

  const tabLabels: { key: ProviderTab; label: string }[] = [
    { key: 'all', label: 'All Providers' },
    { key: 'docling', label: 'Docling' },
    { key: 'mineru', label: 'MinerU' },
    { key: 'consensus', label: 'Consensus' },
  ]

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Top bar */}
      <div className="flex items-center gap-3 px-4 py-2 border-b bg-background shrink-0">
        <Button variant="ghost" size="sm" asChild>
          <Link href={`/source/${sourceId}`}>
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Register
          </Link>
        </Button>
        <h1 className="text-lg font-semibold">Raw Table Review</h1>
        <Badge variant="outline" className="text-amber-600 border-amber-300 bg-amber-50">
          Opt-In
        </Badge>
        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs text-muted-foreground">{total} raw extraction row{total !== 1 ? 's' : ''}</span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setReprocessConfirmOpen(true)}
            disabled={patchMutation.isPending || reprocessMutation.isPending}
          >
            <RefreshCw className="h-4 w-4 mr-1" />
            Re-process
          </Button>
        </div>
      </div>

      {/* Provider tabs */}
      <div className="flex gap-1 px-4 py-2 border-b bg-muted/30 shrink-0">
        {tabLabels.map(({ key, label }) => (
          <Button
            key={key}
            variant={activeProvider === key ? 'default' : 'ghost'}
            size="sm"
            onClick={() => setActiveProvider(key)}
          >
            {label}
          </Button>
        ))}
      </div>

      {/* Consensus placeholder */}
      {activeProvider === 'consensus' ? (
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center space-y-3">
            <p className="text-muted-foreground text-sm">
              Consensus view is available on the Register page.
            </p>
            <Button variant="outline" size="sm" asChild>
              <Link href={`/source/${sourceId}`}>View ACM Register</Link>
            </Button>
          </div>
        </div>
      ) : total === 0 && !isLoading ? (
        /* Empty state */
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center space-y-3">
            <p className="text-muted-foreground text-sm">
              No raw extraction data found. Run extraction first to populate raw tables.
            </p>
            <Button variant="outline" size="sm" asChild>
              <Link href={`/jobs/${sourceId}`}>Go to Job</Link>
            </Button>
          </div>
        </div>
      ) : (
        /* AG Grid */
        <div className="flex-1 min-h-0 overflow-hidden p-4">
          <div
            className="ag-theme-alpine h-full w-full"
            style={{ height: '100%' }}
            role="region"
            aria-label="Raw Extractions Data Grid"
          >
            <style jsx global>{`
              .ag-theme-alpine {
                --ag-header-background-color: hsl(var(--muted));
                --ag-odd-row-background-color: hsl(var(--muted) / 0.3);
                --ag-row-hover-color: hsl(var(--muted));
                --ag-border-color: hsl(var(--border));
                --ag-header-foreground-color: hsl(var(--foreground));
                --ag-foreground-color: hsl(var(--foreground));
                --ag-background-color: hsl(var(--background));
              }
              .dark .ag-theme-alpine {
                --ag-header-background-color: hsl(var(--muted));
                --ag-odd-row-background-color: hsl(var(--muted) / 0.3);
                --ag-row-hover-color: hsl(var(--muted));
              }
            `}</style>
            <AgGridReact<RawExtractionRecord>
              rowData={extractions}
              columnDefs={columnDefs}
              defaultColDef={defaultColDef}
              loading={isLoading}
              animateRows={true}
              rowSelection="single"
              suppressRowClickSelection={true}
              pagination={true}
              paginationPageSize={50}
              paginationPageSizeSelector={[25, 50, 100]}
              domLayout="normal"
              alwaysShowHorizontalScroll={true}
              theme="legacy"
            />
          </div>
        </div>
      )}

      {/* Edit JSON modal */}
      <Dialog open={!!editRow} onOpenChange={(open) => { if (!open) setEditRow(null) }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              Edit Structured JSON — Page {editRow?.page_number}, {editRow?.provider_id}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground">
              Edit the JSON below. Expected shape: <code>{'{ "headers": [...], "rows": [[...], ...] }'}</code>.
              Changes will be recorded to the audit trail.
            </p>
            <textarea
              className="w-full h-64 font-mono text-xs border rounded p-2 bg-muted/20 resize-y focus:outline-none focus:ring-1 focus:ring-ring"
              value={editJsonText}
              onChange={(e) => setEditJsonText(e.target.value)}
              spellCheck={false}
            />
          </div>
          {jsonError && (
            <p className="text-xs text-destructive px-1 pb-1">{jsonError}</p>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditRow(null)}>
              Cancel
            </Button>
            <Button onClick={handleSaveEdit} disabled={patchMutation.isPending}>
              {patchMutation.isPending ? 'Saving…' : 'Save'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit history drawer */}
      <Sheet open={!!editHistoryRow} onOpenChange={(open) => { if (!open) setEditHistoryRow(null) }}>
        <SheetContent side="right" className="w-[420px] overflow-y-auto">
          <SheetHeader>
            <SheetTitle>
              Edit History — Page {editHistoryRow?.page_number}, {editHistoryRow?.provider_id}
            </SheetTitle>
          </SheetHeader>
          <div className="mt-4 space-y-3">
            {editHistoryRow?.officer_edits?.length === 0 ? (
              <p className="text-sm text-muted-foreground">No edits recorded for this row.</p>
            ) : (
              editHistoryRow?.officer_edits?.map((edit, idx) => (
                <div key={idx} className="border rounded p-3 text-xs space-y-1 bg-muted/20">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-foreground">{edit.field}</span>
                    <span className="text-muted-foreground">{edit.user}</span>
                  </div>
                  <div className="text-muted-foreground">{new Date(edit.timestamp).toLocaleString()}</div>
                  <div className="grid grid-cols-2 gap-2 mt-1">
                    <div>
                      <div className="text-muted-foreground mb-0.5">Old</div>
                      <div className="bg-red-50 dark:bg-red-950/30 text-red-700 dark:text-red-300 rounded px-2 py-1 break-all">
                        {edit.old_value || '(empty)'}
                      </div>
                    </div>
                    <div>
                      <div className="text-muted-foreground mb-0.5">New</div>
                      <div className="bg-green-50 dark:bg-green-950/30 text-green-700 dark:text-green-300 rounded px-2 py-1 break-all">
                        {edit.new_value || '(empty)'}
                      </div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </SheetContent>
      </Sheet>

      {/* Re-process confirm dialog */}
      <Dialog open={reprocessConfirmOpen} onOpenChange={setReprocessConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Re-run AI Extraction?</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            Re-run AI extraction (pipeline will re-process the source document; officer edits to raw
            data are stored for future pipeline integration). Existing ACM records for this source
            will be cleared.
          </p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setReprocessConfirmOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleReprocess} disabled={reprocessMutation.isPending}>
              {reprocessMutation.isPending ? 'Starting…' : 'Confirm Re-process'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
