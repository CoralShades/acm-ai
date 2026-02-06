'use client'

import { useState } from 'react'
import { FormSection } from '@/components/ui/form-section'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  CheckCircle2,
  AlertCircle,
  Clock,
  FileStack,
  Copy,
  Loader2,
} from 'lucide-react'
import {
  DEPARTMENTS,
  BUILDING_TYPES,
  OWNERSHIP_OPTIONS,
  FREQUENCY_OPTIONS,
  PUBLIC_ACCESS_OPTIONS,
  SiteConfigTemplate,
} from '@/lib/types/acm'
import { useSiteConfigTemplates, useAgencies } from '@/lib/hooks/use-site-config'

export interface SiteConfigFormData {
  department?: string
  agency?: string
  building_type?: string
  owned_or_leased?: string
  frequency_of_use?: string
  public_access?: string
  building_unique_id?: string
}

interface SiteConfigStepProps {
  siteConfig: SiteConfigFormData
  onSiteConfigChange: (config: SiteConfigFormData) => void
  isBatchMode: boolean
  fileCount: number
  applyToAll: boolean
  onApplyToAllChange: (apply: boolean) => void
  skipConfig: boolean
  onSkipConfigChange: (skip: boolean) => void
  fileNames?: string[]
}

// Calculate missing BAR fields
function getMissingFields(config: SiteConfigFormData): string[] {
  const requiredFields: (keyof SiteConfigFormData)[] = [
    'department',
    'agency',
    'building_type',
    'owned_or_leased',
    'frequency_of_use',
    'public_access',
  ]
  return requiredFields.filter(field => !config[field])
}

// Format field name for display
function formatFieldName(field: string): string {
  return field.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

export function SiteConfigStep({
  siteConfig,
  onSiteConfigChange,
  isBatchMode,
  fileCount,
  applyToAll,
  onApplyToAllChange,
  skipConfig,
  onSkipConfigChange,
  fileNames = [],
}: SiteConfigStepProps) {
  const [showTemplates, setShowTemplates] = useState(false)
  const { data: templates = [], isLoading: isLoadingTemplates } = useSiteConfigTemplates()
  const { data: agencies = [] } = useAgencies(siteConfig.department || undefined)

  const missingFields = getMissingFields(siteConfig)
  const isComplete = missingFields.length === 0

  // Update a single field
  const updateField = (field: keyof SiteConfigFormData, value: string) => {
    onSiteConfigChange({
      ...siteConfig,
      [field]: value || undefined,
    })
    // Clear skip flag when user starts configuring
    if (skipConfig) {
      onSkipConfigChange(false)
    }
  }

  // Apply template values
  const applyTemplate = (template: SiteConfigTemplate) => {
    onSiteConfigChange({
      department: template.department || undefined,
      agency: template.agency || undefined,
      building_type: template.building_type || undefined,
      owned_or_leased: template.owned_or_leased || undefined,
      frequency_of_use: template.frequency_of_use || undefined,
      public_access: template.public_access || undefined,
    })
    onSkipConfigChange(false)
    setShowTemplates(false)
  }

  // Handle configure later
  const handleConfigureLater = () => {
    onSkipConfigChange(true)
    onSiteConfigChange({})
  }

  // If user chose to skip config, show minimal UI
  if (skipConfig) {
    return (
      <div className="space-y-6">
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <Clock className="h-5 w-5 text-amber-600 mt-0.5" />
              <div className="flex-1">
                <p className="font-medium text-amber-800">Configuration Deferred</p>
                <p className="text-sm text-amber-700 mt-1">
                  Site configuration will be skipped for now. You can configure it later from the source detail page.
                </p>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="mt-3"
                  onClick={() => onSkipConfigChange(false)}
                >
                  Configure Now Instead
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Status Card */}
      <Card className={isComplete ? 'border-green-200 bg-green-50' : 'border-amber-200 bg-amber-50'}>
        <CardContent className="pt-4">
          <div className="flex items-start gap-3">
            {isComplete ? (
              <>
                <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
                <div>
                  <p className="font-medium text-green-800">BAR Export Ready</p>
                  <p className="text-sm text-green-700">
                    All required fields are configured.
                  </p>
                </div>
              </>
            ) : (
              <>
                <AlertCircle className="h-5 w-5 text-amber-600 mt-0.5" />
                <div className="flex-1">
                  <p className="font-medium text-amber-800">Missing Fields (Optional)</p>
                  <p className="text-sm text-amber-700">
                    Complete these for BAR export: {missingFields.map(formatFieldName).join(', ')}
                  </p>
                </div>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Batch Mode Card */}
      {isBatchMode && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileStack className="h-4 w-4 text-muted-foreground" />
                <CardTitle className="text-base">Batch Upload: {fileCount} files</CardTitle>
              </div>
              <Badge variant="secondary">{fileCount} files</Badge>
            </div>
            <CardDescription>
              Configure site metadata for all uploaded files at once.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-0">
            <label className="flex items-center gap-3 cursor-pointer p-3 rounded-lg border bg-muted/50 hover:bg-muted transition-colors">
              <Checkbox
                checked={applyToAll}
                onCheckedChange={(checked) => onApplyToAllChange(checked === true)}
              />
              <div>
                <span className="text-sm font-medium">Apply configuration to all {fileCount} files</span>
                <p className="text-xs text-muted-foreground mt-0.5">
                  All files will receive the same site metadata
                </p>
              </div>
            </label>

            {/* Show file list if apply to all is checked */}
            {applyToAll && fileNames.length > 0 && (
              <div className="mt-3 p-2 bg-muted rounded-md">
                <p className="text-xs text-muted-foreground mb-2">Files to configure:</p>
                <ScrollArea className="h-20">
                  <ul className="text-xs space-y-1">
                    {fileNames.map((name) => (
                      <li key={name} className="truncate text-muted-foreground">
                        {name}
                      </li>
                    ))}
                  </ul>
                </ScrollArea>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Template Selection */}
      <FormSection
        title="Quick Start"
        description="Apply settings from a previous configuration."
      >
        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setShowTemplates(!showTemplates)}
            disabled={templates.length === 0}
          >
            <Copy className="h-4 w-4 mr-2" />
            {templates.length > 0 ? `Use Template (${templates.length})` : 'No Templates'}
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleConfigureLater}
          >
            <Clock className="h-4 w-4 mr-2" />
            Configure Later
          </Button>
        </div>

        {showTemplates && (
          <div className="mt-4 space-y-2">
            {isLoadingTemplates ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-5 w-5 animate-spin" />
              </div>
            ) : (
              templates.slice(0, 5).map((template) => (
                <Card
                  key={template.source_id}
                  className="cursor-pointer hover:border-primary/50 transition-colors"
                  onClick={() => applyTemplate(template)}
                >
                  <CardContent className="py-3 px-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium">
                          {template.department || 'No Department'}
                          {template.agency && ` - ${template.agency}`}
                        </p>
                        <p className="text-xs text-muted-foreground truncate max-w-[300px]">
                          {template.source_title || template.source_id}
                        </p>
                      </div>
                      <div className="flex gap-1">
                        {template.building_type && (
                          <Badge variant="outline" className="text-xs">
                            {template.building_type}
                          </Badge>
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        )}
      </FormSection>

      {/* Configuration Form */}
      <FormSection
        title="Site Configuration"
        description="Configure site metadata for Victorian BAR compliance."
      >
        <div className="space-y-4">
          {/* Department */}
          <div className="space-y-2">
            <Label htmlFor="department">Department</Label>
            <Select
              value={siteConfig.department || ''}
              onValueChange={(value) => updateField('department', value)}
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
              value={siteConfig.agency || ''}
              onChange={(e) => updateField('agency', e.target.value)}
              placeholder="e.g., Victoria Police, District Health"
              list="agency-suggestions-wizard"
            />
            {agencies.length > 0 && (
              <datalist id="agency-suggestions-wizard">
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
              value={siteConfig.building_type || ''}
              onValueChange={(value) => updateField('building_type', value)}
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
              value={siteConfig.owned_or_leased || ''}
              onValueChange={(value) => updateField('owned_or_leased', value)}
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
              value={siteConfig.frequency_of_use || ''}
              onValueChange={(value) => updateField('frequency_of_use', value)}
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
              value={siteConfig.public_access || ''}
              onValueChange={(value) => updateField('public_access', value)}
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
            <Label htmlFor="building_unique_id">Building Unique ID (Optional)</Label>
            <Input
              id="building_unique_id"
              value={siteConfig.building_unique_id || ''}
              onChange={(e) => updateField('building_unique_id', e.target.value)}
              placeholder="Optional unique identifier"
            />
          </div>
        </div>
      </FormSection>
    </div>
  )
}
