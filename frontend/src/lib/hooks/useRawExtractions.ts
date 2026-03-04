import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { acmApi } from '@/lib/api/acm'
import { useToast } from '@/lib/hooks/use-toast'
import type { PatchRawExtractionRequest } from '@/lib/types/acm'

export const RAW_EXTRACTION_QUERY_KEYS = {
  bySource: (sourceId: string, provider?: string) =>
    ['raw-extractions', sourceId, provider ?? 'all'] as const,
}

/**
 * Fetch all raw extractions for a source, optionally filtered by provider.
 * provider: "docling" | "mineru" | undefined (all)
 */
export function useRawExtractions(sourceId: string, provider?: string) {
  return useQuery({
    queryKey: RAW_EXTRACTION_QUERY_KEYS.bySource(sourceId, provider),
    queryFn: () => acmApi.rawExtractions(sourceId, provider),
    enabled: !!sourceId,
    staleTime: 30 * 1000,
  })
}

/**
 * Patch a single raw extraction row with officer edits.
 * Invalidates the raw-extractions list for the source on success.
 */
export function usePatchRawExtraction(sourceId: string) {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: ({
      extractionId,
      body,
    }: {
      extractionId: string
      body: PatchRawExtractionRequest
    }) => acmApi.patchRawExtraction(sourceId, extractionId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['raw-extractions', sourceId],
      })
      toast({ title: 'Edit saved', description: 'Correction recorded to audit trail.' })
    },
    onError: () => {
      toast({
        title: 'Save failed',
        description: 'Could not save officer correction. Please try again.',
        variant: 'destructive',
      })
    },
  })
}

/**
 * Re-trigger AI extraction using officer-corrected raw data.
 * Uses existing /acm/extract with force=true to clear and rerun.
 */
export function useReprocessExtraction() {
  const { toast } = useToast()

  return useMutation({
    mutationFn: (sourceId: string) => acmApi.extract(sourceId, { force: true }),
    onSuccess: () => {
      toast({
        title: 'Re-processing started',
        description: 'AI extraction re-running with corrected data. Check the job page for progress.',
      })
    },
    onError: () => {
      toast({
        title: 'Re-process failed',
        description: 'Could not start re-extraction. Please try again.',
        variant: 'destructive',
      })
    },
  })
}
