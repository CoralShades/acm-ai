/**
 * Site Configuration React Query Hooks
 * For Victorian BAR compliance data entry
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { acmApi } from '@/lib/api/acm'
import { useToast } from '@/lib/hooks/use-toast'
import type { SiteConfigRequest } from '@/lib/types/acm'

// Query keys for site config
export const SITE_CONFIG_QUERY_KEYS = {
  config: (sourceId: string) => ['site-config', sourceId] as const,
  templates: (limit?: number) => ['site-config', 'templates', limit] as const,
  agencies: (department?: string) => ['site-config', 'agencies', department] as const,
}

/**
 * Hook to fetch site configuration for a source
 */
export function useSiteConfig(sourceId: string) {
  return useQuery({
    queryKey: SITE_CONFIG_QUERY_KEYS.config(sourceId),
    queryFn: () => acmApi.getConfig(sourceId),
    enabled: !!sourceId,
    staleTime: 60 * 1000, // 1 minute
  })
}

/**
 * Hook to fetch site configuration templates
 */
export function useSiteConfigTemplates(limit: number = 20) {
  return useQuery({
    queryKey: SITE_CONFIG_QUERY_KEYS.templates(limit),
    queryFn: () => acmApi.getConfigTemplates(limit),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

/**
 * Hook to fetch agencies for autocomplete
 */
export function useAgencies(department?: string) {
  return useQuery({
    queryKey: SITE_CONFIG_QUERY_KEYS.agencies(department),
    queryFn: () => acmApi.getAgencies(department),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

/**
 * Hook to save site configuration
 */
export function useSaveSiteConfig() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: (data: SiteConfigRequest) => acmApi.saveConfig(data),
    onSuccess: (_, variables) => {
      // Invalidate the config for this source
      queryClient.invalidateQueries({
        queryKey: SITE_CONFIG_QUERY_KEYS.config(variables.source_id),
      })
      // Invalidate templates as this may create a new one
      queryClient.invalidateQueries({
        queryKey: ['site-config', 'templates'],
      })
      // Invalidate agencies list if agency was set
      if (variables.agency) {
        queryClient.invalidateQueries({
          queryKey: ['site-config', 'agencies'],
        })
      }
      toast({
        title: 'Success',
        description: 'Site configuration saved successfully',
      })
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to save site configuration',
        variant: 'destructive',
      })
    },
  })
}

/**
 * Hook to apply a template to a source's configuration
 */
export function useApplyConfigTemplate() {
  const queryClient = useQueryClient()
  const { toast } = useToast()

  return useMutation({
    mutationFn: ({ sourceId, templateSourceId }: { sourceId: string; templateSourceId: string }) =>
      acmApi.applyConfigTemplate(sourceId, templateSourceId),
    onSuccess: (_, { sourceId }) => {
      // Invalidate the config for this source
      queryClient.invalidateQueries({
        queryKey: SITE_CONFIG_QUERY_KEYS.config(sourceId),
      })
      toast({
        title: 'Success',
        description: 'Template applied successfully',
      })
    },
    onError: () => {
      toast({
        title: 'Error',
        description: 'Failed to apply template',
        variant: 'destructive',
      })
    },
  })
}
