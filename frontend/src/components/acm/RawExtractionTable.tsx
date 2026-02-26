'use client'

import { useCallback, useEffect, useMemo, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AgGridReact } from 'ag-grid-react'
import type { ColDef } from 'ag-grid-community'
import { AllCommunityModule, ModuleRegistry } from 'ag-grid-community'
import { PreviewRecordBadge } from './PreviewRecordBadge'
import type { ExtractionPhase } from '@/lib/hooks/use-extraction-progress'
import type { PipelineRunState, StageId } from '@/lib/types/pipeline'

// Register AG Grid modules (safe to call multiple times)
ModuleRegistry.registerModules([AllCommunityModule])

/**
 * Raw record type — loosely typed to accommodate streaming ExtractionAgentState records.
 * Fields come from `ExtractionAgentState.records` which has [key: string]: unknown
 * in addition to the core typed fields.
 */
type RawRecord = {
  building_id?: string
  building_name?: string | null
  room_name?: string | null
  product?: string
  result?: string
  page_number?: number | null
  location?: string | null
  friable?: string | null
  sample_result?: string | null
  no_access?: boolean | null
  material_condition?: string | null
  nata_sample_number?: string | null
  extraction_confidence?: string | number | null
  [key: string]: unknown
}

interface RawExtractionTableProps {
  sourceId: string
  phase: ExtractionPhase
  pipelineState: PipelineRunState | null
  onComplete?: () => void
}

const STAGE_ORDER: StageId[] = [
  'STRUCTURE',
  'PREFLIGHT',
  'ORCHESTRATOR',
  'EXTRACT',
  'VALIDATE',
  'CORRECT',
  'STORE',
]

async function fetchRawRecords(sourceId: string): Promise<RawRecord[]> {
  const response = await fetch(
    `/api/acm/records?source_id=${encodeURIComponent(sourceId)}&limit=500`
  )
  if (!response.ok) {
    throw new Error(`Failed to fetch raw records: ${response.statusText}`)
  }
  const data = await response.json()
  return Array.isArray(data) ? data : (data.records ?? [])
}

/**
 * RawExtractionTable — live-updating AG Grid that shows raw extracted records
 * as each chunk is processed via the E17 AG-UI StateDelta streaming mechanism.
 *
 * Story: E19-S4 Raw Extraction Table — Live Records During Extraction
 */
export function RawExtractionTable({
  sourceId,
  phase,
  pipelineState,
  onComplete,
}: RawExtractionTableProps) {
  const { data: previewRecords = [] } = useQuery({
    queryKey: ['raw-extraction-records', sourceId],
    queryFn: () => fetchRawRecords(sourceId),
    enabled: !!sourceId,
    staleTime: 0,
    refetchInterval: phase === 'extracting' ? 2000 : false,
  })

  const isStreaming = phase === 'extracting'
  const previousPhaseRef = useRef<ExtractionPhase>(phase)
  const onCompleteCalledRef = useRef(false)

  const stageIndex = useMemo(() => {
    if (!pipelineState) return 1
    const runningStage = STAGE_ORDER.find(
      (stageId) => pipelineState.stages[stageId]?.status === 'running'
    )
    if (runningStage) {
      return STAGE_ORDER.indexOf(runningStage) + 1
    }
    const completedStages = STAGE_ORDER.filter(
      (stageId) => pipelineState.stages[stageId]?.status === 'complete'
    )
    if (completedStages.length > 0) {
      return Math.min(completedStages.length + 1, STAGE_ORDER.length)
    }
    return 1
  }, [pipelineState])

  const stageTotal = STAGE_ORDER.length

  // Call onComplete once when streaming finishes and records exist
  useEffect(() => {
    const previousPhase = previousPhaseRef.current
    previousPhaseRef.current = phase

    if (
      previousPhase === 'extracting' &&
      (phase === 'completed' || phase === 'failed') &&
      previewRecords.length > 0 &&
      !onCompleteCalledRef.current
    ) {
      onCompleteCalledRef.current = true
      onComplete?.()
    }
  }, [onComplete, phase, previewRecords.length])

  const columnDefs = useMemo<ColDef<RawRecord>[]>(
    () => [
      {
        field: 'building_name',
        headerName: 'Building',
        flex: 1,
        minWidth: 120,
        sortable: true,
        filter: true,
        valueGetter: (params) =>
          params.data?.building_name || params.data?.building_id || '',
      },
      {
        field: 'room_name',
        headerName: 'Room/Area',
        flex: 1,
        minWidth: 120,
        sortable: true,
        filter: true,
      },
      {
        field: 'location',
        headerName: 'Location',
        flex: 1,
        minWidth: 120,
        sortable: true,
        filter: true,
      },
      {
        field: 'product',
        headerName: 'ACM Product',
        flex: 1.5,
        minWidth: 150,
        sortable: true,
        filter: true,
      },
      {
        field: 'friable',
        headerName: 'Friable',
        width: 120,
        sortable: true,
        filter: true,
        cellRenderer: (params: { value: unknown }) => {
          if (!params.value) return <span className="text-muted-foreground">-</span>
          const isFriable =
            String(params.value).toLowerCase() === 'friable' || params.value === true
          return isFriable ? (
            <span className="text-amber-600 font-medium">Friable</span>
          ) : (
            <span>Non-friable</span>
          )
        },
      },
      {
        field: 'sample_result',
        headerName: 'Sample Result',
        width: 130,
        sortable: true,
        filter: true,
      },
      {
        field: 'no_access',
        headerName: 'No Access',
        width: 100,
        sortable: true,
        filter: true,
        cellRenderer: (params: { value: unknown }) => {
          if (!params.value) return <span />
          return <span className="text-amber-600 font-medium">No Access</span>
        },
      },
      {
        field: 'material_condition',
        headerName: 'Condition',
        width: 110,
        sortable: true,
        filter: true,
      },
      {
        field: 'nata_sample_number',
        headerName: 'Sample No.',
        width: 110,
        sortable: true,
        filter: true,
      },
      {
        field: 'extraction_confidence',
        headerName: 'Confidence',
        width: 110,
        sortable: true,
        filter: true,
        cellRenderer: (params: { value: unknown }) => {
          if (params.value == null) return <span className="text-muted-foreground">-</span>
          const val = String(params.value)
          const isLow = val.toLowerCase() === 'low'
          const isMedium = val.toLowerCase() === 'medium'
          return (
            <span
              className={
                isLow
                  ? 'text-amber-600 font-medium'
                  : isMedium
                    ? 'text-yellow-600'
                    : 'text-green-600'
              }
            >
              {val}
            </span>
          )
        },
      },
      {
        field: 'page_number',
        headerName: 'Page',
        width: 70,
        sortable: true,
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

  const getRowClass = useCallback(
    () => {
      // All rows in this view are streaming/preview during extraction
      if (isStreaming) {
        return 'acm-row-preview'
      }
      return undefined
    },
    [isStreaming]
  )

  const onGridReady = useCallback(() => {
    // No special initialization needed for this lightweight table
  }, [])

  const recordCount = previewRecords.length

  return (
    <div className="space-y-2">
      {/* Streaming indicator header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium text-foreground">
            Raw Extracted Records
          </span>
          {isStreaming && <PreviewRecordBadge />}
        </div>
        <div className="text-sm text-muted-foreground">
          {isStreaming ? (
            <span>Extracting... Stage {stageIndex} of {stageTotal}</span>
          ) : recordCount > 0 ? (
            <span className="font-medium text-foreground">
              {recordCount} record{recordCount !== 1 ? 's' : ''} extracted
            </span>
          ) : null}
        </div>
      </div>

      {/* AG Grid */}
      <div
        className="ag-theme-alpine w-full"
        style={{ height: '400px' }}
        role="region"
        aria-label="Raw Extracted ACM Records"
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
          .ag-theme-alpine .acm-row-preview {
            font-style: italic;
            opacity: 0.85;
            border-left: 3px solid hsl(var(--primary) / 0.5) !important;
            animation: acm-preview-pulse 2s ease-in-out infinite;
          }
          @keyframes acm-preview-pulse {
            0%, 100% { border-left-color: hsl(var(--primary) / 0.3); }
            50% { border-left-color: hsl(var(--primary)); }
          }
        `}</style>
        <AgGridReact<RawRecord>
          rowData={previewRecords as RawRecord[]}
          columnDefs={columnDefs}
          defaultColDef={defaultColDef}
          onGridReady={onGridReady}
          getRowClass={getRowClass}
          animateRows={true}
          pagination={true}
          paginationPageSize={50}
          paginationPageSizeSelector={[20, 50, 100]}
          domLayout="normal"
          alwaysShowHorizontalScroll={true}
          // Use legacy theming for ag-theme-alpine CSS compatibility (matches ACMGrid.tsx)
          theme="legacy"
          overlayNoRowsTemplate={
            isStreaming
              ? '<span class="text-muted-foreground text-sm">Waiting for records...</span>'
              : '<span class="text-muted-foreground text-sm">No records extracted yet.</span>'
          }
        />
      </div>

      {/* Summary bar */}
      {!isStreaming && recordCount > 0 && (
        <p className="text-sm text-muted-foreground text-right">
          {recordCount} record{recordCount !== 1 ? 's' : ''} extracted
        </p>
      )}
    </div>
  )
}
