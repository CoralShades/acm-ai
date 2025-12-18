'use client'

import { useState, useCallback, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { FileWarning, AlertCircle } from 'lucide-react'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { ACMGrid, type ACMGridRef } from './ACMGrid'
import { ACMRecordDialog } from './ACMRecordDialog'
import { ACMStatsCards } from './ACMStatsCards'
import { ACMToolbar } from './ACMToolbar'
import {
  useACMRecords,
  useACMStats,
  useDeleteACMRecord,
  useExtractACM,
  useExportACMCsv,
} from '@/lib/hooks/use-acm'
import type { ACMRecord } from '@/lib/types/acm'

interface ACMTabProps {
  sourceId: string
}

export function ACMTab({ sourceId }: ACMTabProps) {
  // Refs
  const gridRef = useRef<ACMGridRef>(null)

  // State
  const [riskFilter, setRiskFilter] = useState<string | undefined>(undefined)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create')
  const [selectedRecord, setSelectedRecord] = useState<ACMRecord | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [recordToDelete, setRecordToDelete] = useState<ACMRecord | null>(null)

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

  // Mutations
  const deleteRecord = useDeleteACMRecord()
  const extractACM = useExtractACM()
  const exportCsv = useExportACMCsv()

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

  const handleExport = useCallback(() => {
    exportCsv.mutate(sourceId)
  }, [exportCsv, sourceId])

  const handleRefresh = useCallback(() => {
    refetchRecords()
  }, [refetchRecords])

  const handleExpandAll = useCallback(() => {
    gridRef.current?.expandAll()
  }, [])

  const handleCollapseAll = useCallback(() => {
    gridRef.current?.collapseAll()
  }, [])

  const records = recordsData?.records || []
  const hasRecords = records.length > 0

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <ACMStatsCards stats={stats} isLoading={isLoadingStats} />

      {/* ACM Records Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileWarning className="h-5 w-5" />
            ACM Records
          </CardTitle>
          <CardDescription>
            Asbestos Containing Material records extracted from this source document
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Toolbar */}
          <ACMToolbar
            onAddNew={handleAddNew}
            onExtract={handleExtract}
            onExport={handleExport}
            onRefresh={handleRefresh}
            onExpandAll={handleExpandAll}
            onCollapseAll={handleCollapseAll}
            riskFilter={riskFilter}
            onRiskFilterChange={setRiskFilter}
            isExtracting={extractACM.isPending}
            isExporting={exportCsv.isPending}
            disabled={isLoadingRecords}
            showGroupingControls={hasRecords}
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
    </div>
  )
}
