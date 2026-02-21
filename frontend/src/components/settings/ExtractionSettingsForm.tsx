'use client'

import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Separator } from '@/components/ui/separator'
import { Loader2, AlertTriangle, RotateCcw, Save } from 'lucide-react'
import { extractionSettingsApi } from '@/lib/api/extraction-settings'
import type { ExtractionSettings } from '@/lib/types/extraction-settings'

export function ExtractionSettingsForm() {
  const [settings, setSettings] = useState<ExtractionSettings | null>(null)
  const [original, setOriginal] = useState<ExtractionSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchSettings = useCallback(async () => {
    try {
      setLoading(true)
      const data = await extractionSettingsApi.get()
      setSettings(data)
      setOriginal(data)
      setError(null)
    } catch {
      setError('Failed to load extraction settings')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSettings()
  }, [fetchSettings])

  const hasChanges =
    settings && original && JSON.stringify(settings) !== JSON.stringify(original)

  const handleSave = async () => {
    if (!settings) return
    try {
      setSaving(true)
      const updated = await extractionSettingsApi.update(settings)
      setSettings(updated)
      setOriginal(updated)
      setError(null)
    } catch {
      setError('Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  const handleReset = async () => {
    try {
      setSaving(true)
      const defaults = await extractionSettingsApi.reset()
      setSettings(defaults)
      setOriginal(defaults)
      setError(null)
    } catch {
      setError('Failed to reset settings')
    } finally {
      setSaving(false)
    }
  }

  const update = (field: keyof ExtractionSettings, value: unknown) => {
    if (!settings) return
    const next = { ...settings, [field]: value }
    // Auto-disable building inventory if TOC is disabled
    if (field === 'enable_toc_extraction' && !value) {
      next.enable_building_inventory = false
    }
    setSettings(next)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!settings) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>{error || 'Failed to load settings'}</AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="space-y-6">
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Extraction Method */}
      <div className="space-y-3">
        <Label className="text-base font-medium">Extraction Method</Label>
        <p className="text-sm text-muted-foreground">
          Choose how ACM records are extracted from SAMP documents.
        </p>
        <RadioGroup
          value={settings.extraction_method}
          onValueChange={(v) => update('extraction_method', v)}
          className="space-y-2"
        >
          <div className="flex items-start space-x-3">
            <RadioGroupItem value="hybrid" id="method-hybrid" />
            <div>
              <Label htmlFor="method-hybrid" className="font-medium">Hybrid</Label>
              <p className="text-sm text-muted-foreground">
                Uses MinerU for table extraction with Docling fallback. Recommended.
              </p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <RadioGroupItem value="mineru" id="method-mineru" />
            <div>
              <Label htmlFor="method-mineru" className="font-medium">MinerU Only</Label>
              <p className="text-sm text-muted-foreground">
                ML-based table extraction with bounding box tracking.
              </p>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <RadioGroupItem value="docling" id="method-docling" />
            <div>
              <Label htmlFor="method-docling" className="font-medium">Docling Only</Label>
              <p className="text-sm text-muted-foreground">
                IBM Docling document processing engine.
              </p>
            </div>
          </div>
        </RadioGroup>
      </div>

      {/* Fallback */}
      <div className="flex items-center justify-between">
        <div>
          <Label className="text-base font-medium">Enable Fallback</Label>
          <p className="text-sm text-muted-foreground">
            Fall back to alternative method on failure.
          </p>
        </div>
        <Switch
          checked={settings.fallback_enabled}
          onCheckedChange={(v) => update('fallback_enabled', v)}
          disabled={settings.extraction_method === 'hybrid'}
        />
      </div>
      {settings.extraction_method === 'hybrid' && (
        <p className="text-xs text-muted-foreground -mt-4">
          Fallback is always enabled in Hybrid mode.
        </p>
      )}

      <Separator />

      {/* Document Intelligence Stages */}
      <div className="space-y-4">
        <div>
          <Label className="text-base font-medium">Document Intelligence Stages</Label>
          <p className="text-sm text-muted-foreground">
            Enable or disable document analysis stages that run during extraction.
          </p>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <Label>TOC Extraction</Label>
              <p className="text-xs text-muted-foreground">Extract table of contents structure</p>
            </div>
            <Switch
              checked={settings.enable_toc_extraction}
              onCheckedChange={(v) => update('enable_toc_extraction', v)}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <Label>Building Inventory</Label>
              <p className="text-xs text-muted-foreground">Compile building inventory from TOC</p>
              {!settings.enable_toc_extraction && (
                <p className="text-xs text-amber-500">Requires TOC Extraction</p>
              )}
            </div>
            <Switch
              checked={settings.enable_building_inventory}
              onCheckedChange={(v) => update('enable_building_inventory', v)}
              disabled={!settings.enable_toc_extraction}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <Label>Page Tagging</Label>
              <p className="text-xs text-muted-foreground">Tag pages with section classifications</p>
            </div>
            <Switch
              checked={settings.enable_page_tagging}
              onCheckedChange={(v) => update('enable_page_tagging', v)}
            />
          </div>

          <div className="flex items-center justify-between">
            <div>
              <Label>Metadata Enhancement</Label>
              <p className="text-xs text-muted-foreground">Enhance records with document metadata</p>
            </div>
            <Switch
              checked={settings.enable_metadata_enhancement}
              onCheckedChange={(v) => update('enable_metadata_enhancement', v)}
            />
          </div>
        </div>
      </div>

      <Separator />

      {/* Corrective RAG */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <Label className="text-base font-medium">Corrective RAG</Label>
            <p className="text-sm text-muted-foreground">
              Validate and correct extraction results using retrieval-augmented generation.
            </p>
          </div>
          <Switch
            checked={settings.enable_corrective_rag}
            onCheckedChange={(v) => update('enable_corrective_rag', v)}
          />
        </div>

        {settings.enable_corrective_rag && (
          <div className="flex items-center gap-3">
            <Label className="whitespace-nowrap">Max correction attempts:</Label>
            <input
              type="number"
              min={1}
              max={10}
              value={settings.max_correction_attempts}
              onChange={(e) => update('max_correction_attempts', parseInt(e.target.value) || 2)}
              className="w-20 rounded-md border border-input bg-background px-3 py-1 text-sm"
            />
          </div>
        )}
      </div>

      <Separator />

      {/* Actions */}
      <div className="flex items-center gap-3">
        <Button onClick={handleSave} disabled={!hasChanges || saving}>
          {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Save className="h-4 w-4 mr-2" />}
          Save Settings
        </Button>
        <Button variant="outline" onClick={handleReset} disabled={saving}>
          <RotateCcw className="h-4 w-4 mr-2" />
          Reset to Defaults
        </Button>
        {hasChanges && (
          <span className="text-sm text-amber-500">Unsaved changes</span>
        )}
      </div>
    </div>
  )
}
