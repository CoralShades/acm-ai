/**
 * ACM (Asbestos Containing Material) React Query Hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { acmApi } from '@/lib/api/acm'
import { useToast } from '@/lib/hooks/use-toast'
import type {
  ACMListParams,
  ACMRecordCreateRequest,
  ACMRecordUpdateRequest,
} from '@/lib/types/acm'

// Query keys for ACM
export const ACM_QUERY_KEYS = {
  records: (sourceId: string, params?: Partial<Omit<ACMListParams, 'source_id'>>) =>
    ['acm', 'records', sourceId, params] as const,
  record: (recordId: string) => ['acm', 'records', 'detail', recordId] as const,
  stats: (sourceId?: string) => ['acm', 'stats', sourceId] as const,
}

/**
 * Hook to fetch ACM records for a source
 */
export function useACMRecords(params: ACMListParams) {
  return useQuery({
    queryKey: ACM_QUERY_KEYS.records(params.source_id, {
      building_id: params.building_id,
      room_id: params.room_id,
      risk_status: params.risk_status,
      page: params.page,
      limit: params.limit,
    }),
    queryFn: () => acmApi.list(params),
    enabled: !!params.source_id,
    staleTime: 30 * 1000, // 30 seconds
  })
}

/**
 * Hook to fetch a single ACM record
 */
export function useACMRecord(recordId: string) {
  return useQuery({
    queryKey: ACM_QUERY_KEYS.record(recordId),
    queryFn: () => acmApi.get(recordId),
    enabled: !!recordId,
  })
}

/**
 * Hook to fetch ACM statistics
 */
export function useACMStats(sourceId?: string) {
  return useQuery({
    queryKey: ACM_QUERY_KEYS.stats(sourceId),
    queryFn: () => acmApi.stats(sourceId),
    staleTime: 60 * 1000, // 1 minute
  })
}

/**
 * Hook to create a new ACM record
 */
export function useCreateACMRecord() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (data: ACMRecordCreateRequest) => acmApi.create(data),
    onSuccess: (_, variables) => {
      // Invalidate records list for the source
      queryClient.invalidateQueries({
        queryKey: ['acm', 'records', variables.source_id],
      })
      // Invalidate stats
      queryClient.invalidateQueries({
        queryKey: ACM_QUERY_KEYS.stats(variables.source_id),
      })
      toast({
        title: 'Success',
        description: 'ACM record created successfully',
      })
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to create ACM record',
        variant: 'destructive',
      })
    },
  })
}

/**
 * Hook to update an ACM record
 */
export function useUpdateACMRecord() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: ({
      recordId,
      sourceId,
      data,
    }: {
      recordId: string
      sourceId: string
      data: ACMRecordUpdateRequest
    }) => acmApi.update(recordId, data),
    onSuccess: (_, { recordId, sourceId }) => {
      // Invalidate the specific record
      queryClient.invalidateQueries({
        queryKey: ACM_QUERY_KEYS.record(recordId),
      })
      // Invalidate records list for the source
      queryClient.invalidateQueries({
        queryKey: ['acm', 'records', sourceId],
      })
      // Invalidate stats
      queryClient.invalidateQueries({
        queryKey: ACM_QUERY_KEYS.stats(sourceId),
      })
      toast({
        title: 'Success',
        description: 'ACM record updated successfully',
      })
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to update ACM record',
        variant: 'destructive',
      })
    },
  })
}

/**
 * Hook to delete an ACM record
 */
export function useDeleteACMRecord() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: ({ recordId }: { recordId: string; sourceId: string }) =>
      acmApi.delete(recordId),
    onSuccess: (_, { sourceId }) => {
      // Invalidate records list for the source
      queryClient.invalidateQueries({
        queryKey: ['acm', 'records', sourceId],
      })
      // Invalidate stats
      queryClient.invalidateQueries({
        queryKey: ACM_QUERY_KEYS.stats(sourceId),
      })
      toast({
        title: 'Success',
        description: 'ACM record deleted successfully',
      })
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to delete ACM record',
        variant: 'destructive',
      })
    },
  })
}

/**
 * Hook to trigger ACM extraction
 */
export function useExtractACM() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (sourceId: string) => acmApi.extract(sourceId),
    onSuccess: (result, sourceId) => {
      toast({
        title: 'Extraction Started',
        description: result.message,
      })
      // Invalidate after a delay to allow processing
      setTimeout(() => {
        queryClient.invalidateQueries({
          queryKey: ['acm', 'records', sourceId],
        })
        queryClient.invalidateQueries({
          queryKey: ACM_QUERY_KEYS.stats(sourceId),
        })
      }, 2000)
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to start ACM extraction',
        variant: 'destructive',
      })
    },
  })
}

/**
 * Hook to export ACM records as CSV
 */
export function useExportACMCsv() {
  const { toast } = useToast()

  return useMutation({
    mutationFn: async (sourceId: string) => {
      const blob = await acmApi.exportCsv(sourceId)
      // Create download link
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `acm_export_${sourceId}.csv`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    },
    onSuccess: () => {
      toast({
        title: 'Success',
        description: 'CSV exported successfully',
      })
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to export CSV',
        variant: 'destructive',
      })
    },
  })
}
