'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AppShell } from '@/components/layout/AppShell'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { Save, RotateCcw, Zap, Scale, Shield, Info } from 'lucide-react'
import { toast } from 'sonner'
import apiClient from '@/lib/api/client'

interface ProcessingConfig {
  chunk_size: number
  confidence_threshold: number
  max_correction_attempts: number
  batch_size: number
  per_page_timeout: number
  total_document_timeout: number
  store_raw_json: boolean
  auto_classify: boolean
  auto_normalize: boolean
}

const DEFAULTS: ProcessingConfig = {
  chunk_size: 4000,
  confidence_threshold: 0.7,
  max_correction_attempts: 3,
  batch_size: 3,
  per_page_timeout: 60,
  total_document_timeout: 15,
  store_raw_json: true,
  auto_classify: true,
  auto_normalize: true,
}

const PRESETS: Record<string, { label: string; icon: React.ElementType; config: ProcessingConfig }> = {
  fast: {
    label: 'Fast',
    icon: Zap,
    config: {
      chunk_size: 6000,
      confidence_threshold: 0.5,
      max_correction_attempts: 1,
      batch_size: 5,
      per_page_timeout: 30,
      total_document_timeout: 10,
      store_raw_json: false,
      auto_classify: true,
      auto_normalize: true,
    },
  },
  balanced: {
    label: 'Balanced',
    icon: Scale,
    config: { ...DEFAULTS },
  },
  thorough: {
    label: 'Thorough',
    icon: Shield,
    config: {
      chunk_size: 3000,
      confidence_threshold: 0.85,
      max_correction_attempts: 5,
      batch_size: 2,
      per_page_timeout: 90,
      total_document_timeout: 25,
      store_raw_json: true,
      auto_classify: true,
      auto_normalize: true,
    },
  },
}

function getActivePreset(config: ProcessingConfig): string | null {
  for (const [key, preset] of Object.entries(PRESETS)) {
    if (JSON.stringify(preset.config) === JSON.stringify(config)) return key
  }
  return null
}

function ProcessingContent() {
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['settings', 'processing'],
    queryFn: async () => {
      const res = await apiClient.get<ProcessingConfig>('/settings/processing')
      return res.data
    },
  })

  const updateMutation = useMutation({
    mutationFn: async (config: ProcessingConfig) => {
      const res = await apiClient.put<ProcessingConfig>('/settings/processing', config)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'processing'] })
      toast.success('Processing configuration saved')
      setHasChanges(false)
    },
    onError: () => {
      toast.error('Failed to save configuration')
    },
  })

  const resetMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post<ProcessingConfig>('/settings/processing/reset')
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings', 'processing'] })
      toast.success('Configuration reset to defaults')
      setHasChanges(false)
    },
  })

  const [config, setConfig] = useState<ProcessingConfig>(DEFAULTS)
  const [hasChanges, setHasChanges] = useState(false)

  useEffect(() => {
    if (data) {
      setConfig(data)
      setHasChanges(false)
    }
  }, [data])

  const updateField = <K extends keyof ProcessingConfig>(key: K, value: ProcessingConfig[K]) => {
    setConfig((prev) => ({ ...prev, [key]: value }))
    setHasChanges(true)
  }

  const applyPreset = (presetKey: string) => {
    setConfig(PRESETS[presetKey].config)
    setHasChanges(true)
  }

  const activePreset = getActivePreset(config)

  if (isLoading) {
    return (
      <AppShell>
        <div className="flex items-center justify-center min-h-[60vh]">
          <LoadingSpinner size="lg" />
        </div>
      </AppShell>
    )
  }

  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 max-w-4xl space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Processing Settings</h1>
              <p className="text-muted-foreground mt-1">
                Configure extraction pipeline behavior and performance tuning
              </p>
            </div>
            {hasChanges && <Badge variant="secondary">Unsaved changes</Badge>}
          </div>

          <Alert>
            <Info className="h-4 w-4" />
            <AlertDescription>
              Changes take effect on the next extraction run. In-progress extractions use their original settings.
            </AlertDescription>
          </Alert>

          {/* Presets */}
          <Card>
            <CardHeader>
              <CardTitle>Presets</CardTitle>
              <CardDescription>Quick configurations for common use cases</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-3">
                {Object.entries(PRESETS).map(([key, preset]) => {
                  const Icon = preset.icon
                  return (
                    <Button
                      key={key}
                      variant={activePreset === key ? 'default' : 'outline'}
                      onClick={() => applyPreset(key)}
                      className="flex items-center gap-2"
                    >
                      <Icon className="h-4 w-4" />
                      {preset.label}
                      {activePreset === key && <Badge variant="secondary" className="ml-1 text-[10px]">Active</Badge>}
                    </Button>
                  )
                })}
              </div>
            </CardContent>
          </Card>

          {/* Processing Parameters */}
          <Card>
            <CardHeader>
              <CardTitle>Processing Parameters</CardTitle>
              <CardDescription>Fine-tune extraction behavior</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Chunk Size (2000-8000)</Label>
                  <Input
                    type="number"
                    min={2000}
                    max={8000}
                    value={config.chunk_size}
                    onChange={(e) => updateField('chunk_size', parseInt(e.target.value) || 4000)}
                  />
                  <p className="text-xs text-muted-foreground">Characters per extraction chunk</p>
                </div>
                <div className="space-y-2">
                  <Label>Confidence Threshold (0.0-1.0)</Label>
                  <Input
                    type="number"
                    min={0}
                    max={1}
                    step={0.05}
                    value={config.confidence_threshold}
                    onChange={(e) => updateField('confidence_threshold', parseFloat(e.target.value) || 0.7)}
                  />
                  <p className="text-xs text-muted-foreground">Minimum confidence for extracted records</p>
                </div>
                <div className="space-y-2">
                  <Label>Max Correction Attempts (1-5)</Label>
                  <Input
                    type="number"
                    min={1}
                    max={5}
                    value={config.max_correction_attempts}
                    onChange={(e) => updateField('max_correction_attempts', parseInt(e.target.value) || 3)}
                  />
                  <p className="text-xs text-muted-foreground">Corrective RAG retry limit per chunk</p>
                </div>
                <div className="space-y-2">
                  <Label>Batch Size (1-10)</Label>
                  <Input
                    type="number"
                    min={1}
                    max={10}
                    value={config.batch_size}
                    onChange={(e) => updateField('batch_size', parseInt(e.target.value) || 3)}
                  />
                  <p className="text-xs text-muted-foreground">Pages processed concurrently</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Timeout Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Timeout Settings</CardTitle>
              <CardDescription>Control maximum processing duration</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Per-Page Timeout (10-120 seconds)</Label>
                  <Input
                    type="number"
                    min={10}
                    max={120}
                    value={config.per_page_timeout}
                    onChange={(e) => updateField('per_page_timeout', parseInt(e.target.value) || 60)}
                  />
                  <p className="text-xs text-muted-foreground">Maximum time per page extraction</p>
                </div>
                <div className="space-y-2">
                  <Label>Total Document Timeout (1-30 minutes)</Label>
                  <Input
                    type="number"
                    min={1}
                    max={30}
                    value={config.total_document_timeout}
                    onChange={(e) => updateField('total_document_timeout', parseInt(e.target.value) || 15)}
                  />
                  <p className="text-xs text-muted-foreground">Maximum time for entire document</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Output Preferences */}
          <Card>
            <CardHeader>
              <CardTitle>Output Preferences</CardTitle>
              <CardDescription>Control extraction output behavior</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Store Raw JSON</Label>
                  <p className="text-xs text-muted-foreground">Keep raw LLM response JSON for debugging</p>
                </div>
                <Switch
                  checked={config.store_raw_json}
                  onCheckedChange={(checked) => updateField('store_raw_json', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Auto-Classify</Label>
                  <p className="text-xs text-muted-foreground">Automatically classify materials into BAR taxonomy</p>
                </div>
                <Switch
                  checked={config.auto_classify}
                  onCheckedChange={(checked) => updateField('auto_classify', checked)}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Auto-Normalize</Label>
                  <p className="text-xs text-muted-foreground">Automatically normalize consultant recommendations</p>
                </div>
                <Switch
                  checked={config.auto_normalize}
                  onCheckedChange={(checked) => updateField('auto_normalize', checked)}
                />
              </div>
            </CardContent>
          </Card>

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            <Button
              onClick={() => updateMutation.mutate(config)}
              disabled={!hasChanges || updateMutation.isPending}
            >
              <Save className="h-4 w-4 mr-2" />
              {updateMutation.isPending ? 'Saving...' : 'Save Configuration'}
            </Button>
            <Button
              variant="outline"
              onClick={() => resetMutation.mutate()}
              disabled={resetMutation.isPending}
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Reset to Defaults
            </Button>
          </div>
        </div>
      </div>
    </AppShell>
  )
}

export default function ProcessingSettingsPage() {
  return (
    <ErrorBoundary
      fallback={(props) => (
        <PageErrorFallback
          {...props}
          pageName="Processing Settings"
          reloadUrl="/settings/processing"
        />
      )}
    >
      <ProcessingContent />
    </ErrorBoundary>
  )
}
