'use client'

import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Loader2 } from 'lucide-react'
import { useSiteConfig, useSaveSiteConfig, useAgencies } from '@/lib/hooks/use-site-config'
import {
  DEPARTMENTS,
  BUILDING_TYPES,
  OWNERSHIP_OPTIONS,
  FREQUENCY_OPTIONS,
  PUBLIC_ACCESS_OPTIONS,
} from '@/lib/types/acm'

// Zod validation schema for site configuration
const siteConfigSchema = z.object({
  source_id: z.string().min(1, 'Source ID is required'),
  department: z.string().optional(),
  agency: z.string().optional(),
  building_type: z.string().optional(),
  owned_or_leased: z.string().optional(),
  frequency_of_use: z.string().optional(),
  public_access: z.string().optional(),
  building_unique_id: z.string().optional(),
})

type SiteConfigFormData = z.infer<typeof siteConfigSchema>

interface SiteConfigFormProps {
  sourceId: string
  onSaved?: () => void
}

export function SiteConfigForm({ sourceId, onSaved }: SiteConfigFormProps) {
  const { data: config, isLoading } = useSiteConfig(sourceId)
  const saveConfig = useSaveSiteConfig()

  const { register, handleSubmit, watch, setValue, reset } = useForm<SiteConfigFormData>({
    resolver: zodResolver(siteConfigSchema),
    defaultValues: {
      source_id: sourceId,
      department: '',
      agency: '',
      building_type: '',
      owned_or_leased: '',
      frequency_of_use: '',
      public_access: '',
      building_unique_id: '',
    },
  })

  // Watch department for agency filtering
  const department = watch('department')

  // Fetch agencies based on selected department
  const { data: agencies = [] } = useAgencies(department || undefined)

  // Reset form when config loads
  useEffect(() => {
    if (config) {
      reset({
        source_id: sourceId,
        department: config.department || '',
        agency: config.agency || '',
        building_type: config.building_type || '',
        owned_or_leased: config.owned_or_leased || '',
        frequency_of_use: config.frequency_of_use || '',
        public_access: config.public_access || '',
        building_unique_id: config.building_unique_id || '',
      })
    }
  }, [config, reset, sourceId])

  const onSubmit = async (data: SiteConfigFormData) => {
    try {
      await saveConfig.mutateAsync(data)
      onSaved?.()
    } catch {
      // Error is handled by the mutation's onError callback (shows toast)
      // Form state remains unchanged so user can retry
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* Department */}
      <div className="space-y-2">
        <Label htmlFor="department">Department</Label>
        <Select
          value={watch('department') || ''}
          onValueChange={(value) => setValue('department', value)}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Select department" />
          </SelectTrigger>
          <SelectContent>
            {DEPARTMENTS.map((dept) => (
              <SelectItem key={dept} value={dept}>
                {dept}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Agency */}
      <div className="space-y-2">
        <Label htmlFor="agency">Agency</Label>
        <Input
          id="agency"
          {...register('agency')}
          placeholder="e.g., Victoria Police, District Health"
          list="agency-suggestions"
        />
        {agencies.length > 0 && (
          <datalist id="agency-suggestions">
            {agencies.map((agency) => (
              <option key={agency} value={agency} />
            ))}
          </datalist>
        )}
      </div>

      {/* Building Type */}
      <div className="space-y-2">
        <Label htmlFor="building_type">Building Type</Label>
        <Select
          value={watch('building_type') || ''}
          onValueChange={(value) => setValue('building_type', value)}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Select building type" />
          </SelectTrigger>
          <SelectContent>
            {BUILDING_TYPES.map((type) => (
              <SelectItem key={type} value={type}>
                {type}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Owned or Leased */}
      <div className="space-y-2">
        <Label htmlFor="owned_or_leased">Ownership</Label>
        <Select
          value={watch('owned_or_leased') || ''}
          onValueChange={(value) => setValue('owned_or_leased', value)}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Select ownership" />
          </SelectTrigger>
          <SelectContent>
            {OWNERSHIP_OPTIONS.map((opt) => (
              <SelectItem key={opt} value={opt}>
                {opt}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Frequency of Use */}
      <div className="space-y-2">
        <Label htmlFor="frequency_of_use">Frequency of Use</Label>
        <Select
          value={watch('frequency_of_use') || ''}
          onValueChange={(value) => setValue('frequency_of_use', value)}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Select frequency" />
          </SelectTrigger>
          <SelectContent>
            {FREQUENCY_OPTIONS.map((freq) => (
              <SelectItem key={freq} value={freq}>
                {freq}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Public Access */}
      <div className="space-y-2">
        <Label htmlFor="public_access">Public Access</Label>
        <Select
          value={watch('public_access') || ''}
          onValueChange={(value) => setValue('public_access', value)}
        >
          <SelectTrigger className="w-full">
            <SelectValue placeholder="Select public access" />
          </SelectTrigger>
          <SelectContent>
            {PUBLIC_ACCESS_OPTIONS.map((opt) => (
              <SelectItem key={opt} value={opt}>
                {opt}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Building Unique ID */}
      <div className="space-y-2">
        <Label htmlFor="building_unique_id">Building Unique ID</Label>
        <Input
          id="building_unique_id"
          {...register('building_unique_id')}
          placeholder="Optional unique identifier"
        />
      </div>

      {/* Submit Button */}
      <div className="flex justify-end pt-4">
        <Button type="submit" disabled={saveConfig.isPending}>
          {saveConfig.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Save Configuration
        </Button>
      </div>
    </form>
  )
}
