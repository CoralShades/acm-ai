'use client'

import { useState, useMemo } from 'react'
import { useRouter } from 'next/navigation'
import { AppShell } from '@/components/layout/AppShell'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { EmptyState } from '@/components/common/EmptyState'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { FileWarning, AlertCircle } from 'lucide-react'
import { ACMGrid } from '@/components/acm/ACMGrid'
import { ACMRecordDialog } from '@/components/acm/ACMRecordDialog'
import { ACMStatsCards } from '@/components/acm/ACMStatsCards'
import { ACMToolbar } from '@/components/acm/ACMToolbar'
import {
  useACMRecords,
  useACMStats,
  useDeleteACMRecord,
  useExtractACM,
  useExportACMCsv,
} from '@/lib/hooks/use-acm'
import { useSources } from '@/lib/hooks/use-sources'
import type { ACMRecord } from '@/lib/types/acm'

export default function ACMPage() {
  const router = useRouter()

  // State
  const [selectedSourceId, setSelectedSourceId] = useState<string | undefined>(undefined)
  const [riskFilter, setRiskFilter] = useState<string | undefined>(undefined)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [dialogMode, setDialogMode] = useState<'create' | 'edit'>('create')
  const [selectedRecord, setSelectedRecord] = useState<ACMRecord | null>(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [recordToDelete, setRecordToDelete] = useState<ACMRecord | null>(null)

  // Fetch sources for selector (we'll use all sources without notebook filter)
  const { data: sources, isLoading: isLoadingSources } = useSources('')

  // Queries - only fetch when source is selected
  const {
    data: recordsData,
    isLoading: isLoadingRecords,
    refetch: refetchRecords,
  } = useACMRecords({
    source_id: selectedSourceId || '',
    risk_status: riskFilter,
    limit: 500,
  })

  const { data: stats, isLoading: isLoadingStats } = useACMStats(selectedSourceId)

  // Mutations
  const deleteRecord = useDeleteACMRecord()
  const extractACM = useExtractACM()
  const exportCsv = useExportACMCsv()

  // Compute records
  const records = useMemo(() => recordsData?.records || [], [recordsData])
  const hasRecords = records.length > 0

  // Handlers
  const handleSourceChange = (sourceId: string) => {
    setSelectedSourceId(sourceId === 'none' ? undefined : sourceId)
  }

  const handleAddNew = () => {
    if (!selectedSourceId) return
    setSelectedRecord(null)
    setDialogMode('create')
    setDialogOpen(true)
  }

  const handleEdit = (record: ACMRecord) => {
    setSelectedRecord(record)
    setDialogMode('edit')
    setDialogOpen(true)
  }

  const handleDelete = (record: ACMRecord) => {
    setRecordToDelete(record)
    setDeleteDialogOpen(true)
  }

  const confirmDelete = async () => {
    if (recordToDelete && selectedSourceId) {
      await deleteRecord.mutateAsync({
        recordId: recordToDelete.id,
        sourceId: selectedSourceId,
      })
      setDeleteDialogOpen(false)
      setRecordToDelete(null)
    }
  }

  const handleExtract = () => {
    if (selectedSourceId) {
      extractACM.mutate(selectedSourceId)
    }
  }

  const handleExport = () => {
    if (selectedSourceId) {
      exportCsv.mutate(selectedSourceId)
    }
  }

  const handleRefresh = () => {
    refetchRecords()
  }

  // Navigate to source detail page
  const handleViewSource = () => {
    if (selectedSourceId) {
      router.push(`/sources/${selectedSourceId}`)
    }
  }

  return (
    <AppShell>
      <div className="flex flex-col h-full w-full max-w-none px-6 py-6">
        {/* Header */}
        <div className="mb-6 flex-shrink-0">
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <FileWarning className="h-8 w-8" />
            ACM Register
          </h1>
          <p className="mt-2 text-muted-foreground">
            View and manage Asbestos Containing Material records extracted from source documents.
          </p>
        </div>

        {/* Source Selector */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Select Source Document</CardTitle>
            <CardDescription>
              Choose a source document to view its ACM records
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Select
              value={selectedSourceId || 'none'}
              onValueChange={handleSourceChange}
              disabled={isLoadingSources}
            >
              <SelectTrigger className="w-full max-w-md">
                <SelectValue placeholder="Select a source document..." />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">-- Select a source --</SelectItem>
                {sources?.map((source) => (
                  <SelectItem key={source.id} value={source.id}>
                    {source.title || `Source ${source.id}`}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </CardContent>
        </Card>

        {/* No Source Selected */}
        {!selectedSourceId && (
          <EmptyState
            icon={FileWarning}
            title="No Source Selected"
            description="Select a source document above to view its ACM records"
          />
        )}

        {/* Source Selected - Show Stats and Grid */}
        {selectedSourceId && (
          <div className="space-y-6 flex-1">
            {/* Stats Cards */}
            <ACMStatsCards stats={stats} isLoading={isLoadingStats} />

            {/* ACM Records Card */}
            <Card className="flex-1">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileWarning className="h-5 w-5" />
                  ACM Records
                </CardTitle>
                <CardDescription>
                  Asbestos Containing Material records for the selected source
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Toolbar */}
                <ACMToolbar
                  onAddNew={handleAddNew}
                  onExtract={handleExtract}
                  onExport={handleExport}
                  onRefresh={handleRefresh}
                  riskFilter={riskFilter}
                  onRiskFilterChange={setRiskFilter}
                  isExtracting={extractACM.isPending}
                  isExporting={exportCsv.isPending}
                  disabled={isLoadingRecords}
                />

                {/* Loading State */}
                {isLoadingRecords && (
                  <div className="flex items-center justify-center py-8">
                    <LoadingSpinner />
                  </div>
                )}

                {/* No Records Alert */}
                {!isLoadingRecords && !hasRecords && (
                  <Alert>
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>No ACM Records Found</AlertTitle>
                    <AlertDescription>
                      This source doesn&apos;t have any ACM records yet. Click &quot;Extract
                      ACM&quot; to automatically extract records from the document, or &quot;Add
                      Record&quot; to manually add entries.
                    </AlertDescription>
                  </Alert>
                )}

                {/* AG Grid */}
                {!isLoadingRecords && hasRecords && (
                  <ACMGrid
                    records={records}
                    isLoading={isLoadingRecords}
                    onEdit={handleEdit}
                    onDelete={handleDelete}
                  />
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Create/Edit Dialog */}
        {selectedSourceId && (
          <ACMRecordDialog
            open={dialogOpen}
            onOpenChange={setDialogOpen}
            sourceId={selectedSourceId}
            record={selectedRecord}
            mode={dialogMode}
          />
        )}

        {/* Delete Confirmation Dialog */}
        <ConfirmDialog
          open={deleteDialogOpen}
          onOpenChange={setDeleteDialogOpen}
          title="Delete ACM Record"
          description="Are you sure you want to delete this ACM record? This action cannot be undone."
          confirmText="Delete"
          confirmVariant="destructive"
          onConfirm={confirmDelete}
          isLoading={deleteRecord.isPending}
        />
      </div>
    </AppShell>
  )
}
