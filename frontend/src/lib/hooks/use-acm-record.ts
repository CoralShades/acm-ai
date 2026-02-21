/**
 * Hook for ACM Record Detail Panel -- single record fetch and inline edit.
 */

import { useState, useCallback } from 'react'
import { useACMRecord, useUpdateACMRecord } from './use-acm'
import type { ACMRecord, ACMRecordUpdateRequest } from '@/lib/types/acm'

export interface UseACMRecordDetailResult {
  record: ACMRecord | undefined
  isLoading: boolean
  isEditing: boolean
  isSaving: boolean
  setIsEditing: (value: boolean) => void
  saveRecord: (data: ACMRecordUpdateRequest, sourceId: string) => Promise<void>
}

export function useACMRecordDetail(recordId: string | null): UseACMRecordDetailResult {
  const [isEditing, setIsEditing] = useState(false)

  const { data: record, isLoading } = useACMRecord(recordId ?? '')
  const updateMutation = useUpdateACMRecord()

  const saveRecord = useCallback(
    async (data: ACMRecordUpdateRequest, sourceId: string) => {
      if (!recordId) return
      await updateMutation.mutateAsync({ recordId, sourceId, data })
      setIsEditing(false)
    },
    [recordId, updateMutation]
  )

  return {
    record,
    isLoading,
    isEditing,
    isSaving: updateMutation.isPending,
    setIsEditing,
    saveRecord,
  }
}
