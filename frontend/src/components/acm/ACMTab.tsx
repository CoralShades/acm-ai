'use client'

import { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import dynamic from 'next/dynamic'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { FileWarning, AlertCircle } from 'lucide-react'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { ACMGrid, type ACMGridRef, type CellSelectionDetails } from './ACMGrid'
import { ACMRecordDialog } from './ACMRecordDialog'
import { ACMRecordDetailPanel } from './ACMRecordDetailPanel'
import { ACMExtractionBanner } from './ACMExtractionBanner'
import { ACMStatsCards } from './ACMStatsCards'
import { OnboardingHint } from '@/components/common/OnboardingHint'
import { ACMToolbar } from './ACMToolbar'
import { BuildingTabs } from './BuildingTabs'
import { SiteConfigPanel } from './SiteConfigPanel'
import {
  useACMRecords,
  useACMStats,
  useDeleteACMRecord,
  useExtractACM,
  useExportACMCsv,
  useExportACMExcel,
} from '@/lib/hooks/use-acm'
import { useExtractionStatus } from '@/lib/hooks/use-extraction-status'
import { useExtractionAgent } from '@/lib/hooks/use-extraction-agent'
import { useSource } from '@/lib/hooks/use-sources'
import { useDebouncedValue } from '@/lib/hooks/use-debounced-value'
import { useSessionStorage } from '@/lib/hooks/use-session-storage'
import type { ACMRecord } from '@/lib/types/acm'

interface ACMTabProps {
  sourceId: string
}

const ACMCellViewer = dynamic(
  () => import('./ACMCellViewer').then((module) => module.ACMCellViewer),
  { ssr: false }
)

export function ACMTab({ sourceId }: ACMTabProps) {
  // Hooks
  const router = useRouter()

  // Refs
  const gridRef = useRef<ACMGridRef>(null)

  // State
  const [gridApi, setGridApiState] = useState<import('ag-grid-community').GridApi | null>(null)
  const [riskFilter, setRiskFilter] = useState<string | undefined>(undefined)
  const [searchText, setSearchText] = useState('')
  const [visibleCount, setVisibleCount] = useState<number | undefined>(undefined)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create')
  const [selectedRecord, setSelectedRecord] = useState<ACMRecord | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [recordToDelete, setRecordToDelete] = useState<ACMRecord | null>(null)
  // Cell citation viewer state
  const [selectedCell, setSelectedCell] = useState<CellSelectionDetails | null>(null)
  // Detail panel state (slide-out, replaces modal dialog)
  const [panelOpen, setPanelOpen] = useState(false)
  const [panelRecordId, setPanelRecordId] = useState<string | null>(null)

  // Building tab state - persisted per source in session storage
  const [selectedBuilding, setSelectedBuilding] = useSessionStorage<string | null>(
    `acm-building-${sourceId}`,
    null
  )

  // Debounce search text for better performance
  const debouncedSearchText = useDebouncedValue(searchText, 300)

  // Reset search and building selection when risk filter changes to avoid confusion
  // Skip initial mount by checking if searchText has content
  useEffect(() => {
    if (searchText) {
      setSearchText('')
    }
    // Reset building selection when risk filter changes
    if (selectedBuilding !== null) {
      setSelectedBuilding(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [riskFilter])

  // Queries
  const {
    data: recordsData,
    isLoading: isLoadingRecords,
    refetch: refetchRecords,
  } = useACMRecords({
    source_id: sourceId,
    risk_status: riskFilter,
    limit: 500,
  })

  const { data: stats, isLoading: isLoadingStats } = useACMStats(sourceId)

  // Fetch source data to get PDF URL for citation viewer
  const { data: sourceData } = useSource(sourceId)

  // Create PDF download URL if source has an asset
  const pdfUrl = useMemo(() => {
    // Check if source has a file asset (PDF)
    if (sourceData?.asset?.file_path) {
      // Use the download endpoint to get the PDF
      return `/api/sources/${sourceId}/download`
    }
    return null
  }, [sourceData?.asset?.file_path, sourceId])

  // Extraction status tracking
  const extractionStatus = useExtractionStatus(sourceId)

  // AG-UI incremental record streaming (E17-S2)
  const extractionAgent = useExtractionAgent(sourceId)

  // Mutations
  const deleteRecord = useDeleteACMRecord()
  const extractACM = useExtractACM(extractionStatus.startTracking)
  const exportCsv = useExportACMCsv()
  const exportExcel = useExportACMExcel()

  // Handlers
  const handleAddNew = useCallback(() => {
    setSelectedRecord(null)
    setDialogMode('create')
    setDialogOpen(true)
  }, [])

  const handleEdit = useCallback((record: ACMRecord) => {
    setSelectedRecord(record)
    setDialogMode('edit')
    setDialogOpen(true)
  }, [])

  const handleDelete = useCallback((record: ACMRecord) => {
    setRecordToDelete(record)
    setDeleteDialogOpen(true)
  }, [])

  const confirmDelete = useCallback(async () => {
    if (recordToDelete) {
      await deleteRecord.mutateAsync({
        recordId: recordToDelete.id,
        sourceId: sourceId,
      })
      setDeleteDialogOpen(false)
      setRecordToDelete(null)
    }
  }, [recordToDelete, deleteRecord, sourceId])

  const handleExtract = useCallback(() => {
    extractACM.mutate(sourceId)
  }, [extractACM, sourceId])

  const handleExportCsv = useCallback(() => {
    exportCsv.mutate(sourceId)
  }, [exportCsv, sourceId])

  const handleExportExcel = useCallback(() => {
    exportExcel.mutate(sourceId)
  }, [exportExcel, sourceId])

  const handleRefresh = useCallback(() => {
    refetchRecords()
  }, [refetchRecords])

  const handleExpandAll = useCallback(() => {
    gridRef.current?.expandAll()
  }, [])

  const handleCollapseAll = useCallback(() => {
    gridRef.current?.collapseAll()
  }, [])

  const handleVisibleCountChange = useCallback((count: number) => {
    setVisibleCount(count)
  }, [])

  const handleResetColumns = useCallback(() => {
    gridRef.current?.resetColumns()
  }, [])

  // Capture gridApi from the grid ref once it's available
  useEffect(() => {
    const checkApi = () => {
      const api = gridRef.current?.getGridApi()
      if (api && api !== gridApi) {
        setGridApiState(api)
      }
    }
    // Check immediately and after a short delay (grid may init async)
    checkApi()
    const timer = setTimeout(checkApi, 500)
    return () => clearTimeout(timer)
  }, [isLoadingRecords, gridApi])

  // Listen for acm-command custom events from Command Palette
  useEffect(() => {
    const handleACMCommand = (e: Event) => {
      const customEvent = e as CustomEvent<{ action: string }>
      const action = customEvent.detail?.action
      if (!action) return

      switch (action) {
        case 'extract':
          handleExtract()
          break
        case 'export-csv':
          handleExportCsv()
          break
        case 'export-excel':
          handleExportExcel()
          break
        case 'add-record':
          handleAddNew()
          break
        case 'upload':
          router.push('/sources?action=upload')
          break
      }
    }

    window.addEventListener('acm-command', handleACMCommand)
    return () => window.removeEventListener('acm-command', handleACMCommand)
  }, [handleExtract, handleExportCsv, handleExportExcel, handleAddNew, router])

  // Row click handler — toggles slide-out detail panel
  const handleRowClick = useCallback((record: ACMRecord) => {
    if (panelOpen && panelRecordId === record.id) {
      // Same row clicked again → close panel
      setPanelOpen(false)
      setPanelRecordId(null)
    } else {
      setPanelRecordId(record.id)
      setPanelOpen(true)
    }
  }, [panelOpen, panelRecordId])

  const handlePanelClose = useCallback(() => {
    setPanelOpen(false)
    setPanelRecordId(null)
  }, [])

  // Cell citation viewer handler
  const handleCellSelect = useCallback((details: CellSelectionDetails) => {
    setSelectedCell(details)
  }, [])

  const handleCellViewerClose = useCallback(() => {
    setSelectedCell(null)
  }, [])

  // Building change handler
  const handleBuildingChange = useCallback((buildingId: string | null) => {
    setSelectedBuilding(buildingId)
  }, [setSelectedBuilding])

  // All records from API (full dataset for building tabs)
  const allRecords = useMemo(() => recordsData?.records || [], [recordsData?.records])

  // Reset building selection if selected building no longer exists in data
  useEffect(() => {
    if (selectedBuilding && allRecords.length > 0) {
      const buildingExists = allRecords.some((r) => r.building_id === selectedBuilding)
      if (!buildingExists) {
        setSelectedBuilding(null)
      }
    }
  }, [allRecords, selectedBuilding, setSelectedBuilding])

  // Filter records by selected building
  const records = useMemo(() => {
    if (!selectedBuilding) return allRecords
    return allRecords.filter((r) => r.building_id === selectedBuilding)
  }, [allRecords, selectedBuilding])

  // Panel navigation — must be after records/allRecords are defined
  const panelIndex = useMemo(() => {
    if (!panelRecordId) return -1
    return records.findIndex((r) => r.id === panelRecordId)
  }, [records, panelRecordId])

  const handlePanelNavigatePrev = useCallback(() => {
    if (panelIndex > 0) {
      setPanelRecordId(records[panelIndex - 1].id)
    }
  }, [panelIndex, records])

  const handlePanelNavigateNext = useCallback(() => {
    if (panelIndex < records.length - 1) {
      setPanelRecordId(records[panelIndex + 1].id)
    }
  }, [panelIndex, records])

  const handlePanelViewInPDF = useCallback((pageNumber: number) => {
    const record = allRecords.find((r) => r.id === panelRecordId)
    if (!record) return
    setSelectedCell({
      recordId: record.id,
      field: 'page_number',
      value: pageNumber,
      pageNumber: pageNumber,
      record: record,
    })
  }, [panelRecordId, allRecords])

  const totalCount = allRecords.length
  const filteredCount = records.length
  const hasRecords = totalCount > 0

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <ACMStatsCards stats={stats} isLoading={isLoadingStats} />

      {/* ACM Records Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileWarning className="h-5 w-5" />
                ACM Records
              </CardTitle>
              <CardDescription>
                Asbestos Containing Material records extracted from this source document
              </CardDescription>
            </div>
            <SiteConfigPanel sourceId={sourceId} />
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Building Tabs */}
          {hasRecords && (
            <BuildingTabs
              records={allRecords}
              selectedBuilding={selectedBuilding}
              onBuildingChange={handleBuildingChange}
            />
          )}

          {/* Onboarding Hint — only when records exist */}
          {hasRecords && (
            <OnboardingHint
              id="acm-register"
              message="Use the Columns button to show/hide fields. Click any row for full record details."
            />
          )}

          {/* Toolbar */}
          <ACMToolbar
            onAddNew={handleAddNew}
            onExtract={handleExtract}
            onExportCsv={handleExportCsv}
            onExportExcel={handleExportExcel}
            onRefresh={handleRefresh}
            onExpandAll={handleExpandAll}
            onCollapseAll={handleCollapseAll}
            onResetColumns={handleResetColumns}
            gridApi={gridApi}
            riskFilter={riskFilter}
            onRiskFilterChange={setRiskFilter}
            isExtracting={extractACM.isPending || extractionStatus.phase === 'extracting'}
            isExportingCsv={exportCsv.isPending}
            isExportingExcel={exportExcel.isPending}
            disabled={isLoadingRecords}
            showGroupingControls={hasRecords}
            searchText={searchText}
            onSearchChange={setSearchText}
            visibleCount={visibleCount}
            totalCount={filteredCount}
          />

          {/* Extraction Progress Banner */}
          <ACMExtractionBanner
            phase={extractionStatus.phase}
            recordsCreated={extractionStatus.recordsCreated}
            errorMessage={extractionStatus.errorMessage}
            onDismiss={extractionStatus.dismiss}
          />

          {/* AG-UI Chunk Progress (E17-S2) */}
          {extractionStatus.phase === 'extracting' && extractionAgent.chunksTotal > 0 && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
              </span>
              Chunk {extractionAgent.chunksProcessed} / {extractionAgent.chunksTotal}
              {extractionAgent.previewRecords.length > 0 && (
                <span className="font-medium">
                  — {extractionAgent.previewRecords.length} record{extractionAgent.previewRecords.length !== 1 ? 's' : ''} streaming
                </span>
              )}
            </div>
          )}

          {/* No Records Alert */}
          {!isLoadingRecords && !hasRecords && extractionStatus.phase !== 'extracting' && (
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>No ACM Records Found</AlertTitle>
              <AlertDescription>
                This source doesn&apos;t have any ACM records yet. Click &quot;Extract ACM&quot; to
                automatically extract records from the document, or &quot;Add Record&quot; to
                manually add entries.
              </AlertDescription>
            </Alert>
          )}

          {/* AG Grid */}
          {(hasRecords || isLoadingRecords) && (
            <ACMGrid
              ref={gridRef}
              records={records}
              previewRecords={
                extractionStatus.phase === 'extracting'
                  ? (extractionAgent.previewRecords as unknown as ACMRecord[])
                  : undefined
              }
              isLoading={isLoadingRecords}
              onEdit={handleEdit}
              onDelete={handleDelete}
              quickFilterText={debouncedSearchText}
              onVisibleCountChange={handleVisibleCountChange}
              onCellSelect={handleCellSelect}
              onRowClick={handleRowClick}
              selectedRecordId={panelRecordId}
            />
          )}
        </CardContent>
      </Card>

      {/* Record Detail Panel (slide-out) */}
      <ACMRecordDetailPanel
        recordId={panelRecordId}
        open={panelOpen}
        sourceId={sourceId}
        onClose={handlePanelClose}
        onViewInPDF={handlePanelViewInPDF}
        onNavigatePrev={handlePanelNavigatePrev}
        onNavigateNext={handlePanelNavigateNext}
        hasPrev={panelIndex > 0}
        hasNext={panelIndex < records.length - 1 && panelIndex >= 0}
      />

      {/* Create/Edit Dialog */}
      <ACMRecordDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        sourceId={sourceId}
        record={selectedRecord}
        mode={dialogMode}
      />

      {/* Delete Confirmation Dialog */}
      <ConfirmDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        title="Delete ACM Record"
        description={`Are you sure you want to delete this ACM record? This action cannot be undone.`}
        confirmText="Delete"
        confirmVariant="destructive"
        onConfirm={confirmDelete}
        isLoading={deleteRecord.isPending}
      />

      {/* Cell Citation Viewer */}
      {selectedCell && (
        <ACMCellViewer
          sourceId={sourceId}
          selection={selectedCell}
          pdfUrl={pdfUrl}
          onClose={handleCellViewerClose}
        />
      )}
    </div>
  )
}
