import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { acmApi } from '@/lib/api/acm'
import type { ACMRecordUpdateRequest } from '@/lib/types/acm'

export const ACM_ITEMS_QUERY_KEYS = {
  byBuilding: (sourceId: string, buildingId: string | null) =>
    ['acm', 'items', sourceId, buildingId] as const,
  fieldSchema: () => ['acm', 'field-schema'] as const,
  validationSummary: (sourceId: string) => ['acm', 'validation-summary', sourceId] as const,
}

export function useACMItems(sourceId: string, buildingId: string | null) {
  return useQuery({
    queryKey: ACM_ITEMS_QUERY_KEYS.byBuilding(sourceId, buildingId),
    queryFn: () =>
      acmApi.list({ source_id: sourceId, building_record_id: buildingId ?? undefined, limit: 500 }),
    enabled: !!sourceId && !!buildingId,
    staleTime: 30 * 1000,
  })
}

export function useFieldSchema() {
  return useQuery({
    queryKey: ACM_ITEMS_QUERY_KEYS.fieldSchema(),
    queryFn: () => acmApi.getFieldSchema(),
    staleTime: Infinity, // schema is session-stable
  })
}

/**
 * Query hook for per-building validation error counts (E33-S4).
 */
export function useValidationSummary(sourceId: string) {
  return useQuery({
    queryKey: ACM_ITEMS_QUERY_KEYS.validationSummary(sourceId),
    queryFn: () => acmApi.getValidationSummary(sourceId),
    enabled: !!sourceId,
    staleTime: 30 * 1000,
    // Limit retries to avoid console error noise for sources with no buildings (E35-S8)
    retry: 1,
  })
}

/**
 * Mutation hook for updating a single ACM record (E33-S4).
 * Invalidates all ACM queries on success.
 */
export function useUpdateACMRecord() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ recordId, data }: { recordId: string; data: ACMRecordUpdateRequest }) =>
      acmApi.update(recordId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['acm'] })
    },
  })
}

/**
 * Mutation hook for bulk-fixing auto-correctable validation issues (E33-S4).
 * Invalidates all ACM queries on success.
 */
export function useBulkFix() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ sourceId, buildingId }: { sourceId: string; buildingId?: string }) =>
      acmApi.bulkFix(sourceId, buildingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['acm'] })
    },
  })
}

/**
 * Mutation hook for bulk-editing a single field across multiple ACM records (E34-S2).
 * Publishes SSE progress events via PipelineEventBus.
 */
export function useBulkEdit() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (args: {
      sourceId: string
      body: { record_ids: string[]; field: string; value: unknown; operation_id: string }
    }) => {
      const res = await fetch(
        `/api/acm/bulk-edit?source_id=${encodeURIComponent(args.sourceId)}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(args.body),
        }
      )
      if (!res.ok) throw new Error(await res.text())
      return res.json() as Promise<{ updated_count: number; operation_id: string }>
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['acm', 'items'] })
    },
  })
}

/**
 * Mutation hook for re-running SF validation on selected ACM records (E34-S2).
 */
export function useBulkValidate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (body: { record_ids: string[] }) => {
      const res = await fetch('/api/acm/bulk-validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error(await res.text())
      return res.json() as Promise<{ fixed_count: number; remaining_errors: number }>
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['acm', 'items'] })
      queryClient.invalidateQueries({ queryKey: ['acm', 'validation-summary'] })
    },
  })
}
