'use client'

import { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { FileWarning, AlertCircle } from 'lucide-react'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { ACMGrid, type ACMGridRef, type CellSelectionDetails } from './ACMGrid'
import { ACMCellViewer } from './ACMCellViewer'
import { ACMRecordDialog } from './ACMRecordDialog'
import { ACMStatsCards } from './ACMStatsCards'
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
import { useSource } from '@/lib/hooks/use-sources'
import { useDebouncedValue } from '@/lib/hooks/use-debounced-value'
import { useSessionStorage } from '@/lib/hooks/use-session-storage'
import type { ACMRecord } from '@/lib/types/acm'

interface ACMTabProps {
  sourceId: string
}

export function ACMTab({ sourceId }: ACMTabProps) {
  // Refs
  const gridRef = useRef<ACMGridRef>(null)

  // State
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

  // Mutations
  const deleteRecord = useDeleteACMRecord()
  const extractACM = useExtractACM()
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

          {/* Toolbar */}
          <ACMToolbar
            onAddNew={handleAddNew}
            onExtract={handleExtract}
            onExportCsv={handleExportCsv}
            onExportExcel={handleExportExcel}
            onRefresh={handleRefresh}
            onExpandAll={handleExpandAll}
            onCollapseAll={handleCollapseAll}
            riskFilter={riskFilter}
            onRiskFilterChange={setRiskFilter}
            isExtracting={extractACM.isPending}
            isExportingCsv={exportCsv.isPending}
            isExportingExcel={exportExcel.isPending}
            disabled={isLoadingRecords}
            showGroupingControls={hasRecords}
            searchText={searchText}
            onSearchChange={setSearchText}
            visibleCount={visibleCount}
            totalCount={filteredCount}
          />

          {/* No Records Alert */}
          {!isLoadingRecords && !hasRecords && (
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
              isLoading={isLoadingRecords}
              onEdit={handleEdit}
              onDelete={handleDelete}
              quickFilterText={debouncedSearchText}
              onVisibleCountChange={handleVisibleCountChange}
              onCellSelect={handleCellSelect}
            />
          )}
        </CardContent>
      </Card>

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
      <ACMCellViewer
        sourceId={sourceId}
        selection={selectedCell}
        pdfUrl={pdfUrl}
        onClose={handleCellViewerClose}
      />
    </div>
  )
}
