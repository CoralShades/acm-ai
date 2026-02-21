'use client'

import { useState, useCallback, useEffect } from 'react'
import { AppShell } from '@/components/layout/AppShell'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertTriangle } from 'lucide-react'
import { BARTemplateUploader } from '@/components/settings/BARTemplateUploader'
import { BARTemplateVersionList } from '@/components/settings/BARTemplateVersionList'
import { BARTemplateColumnPreview } from '@/components/settings/BARTemplateColumnPreview'
import { barTemplatesApi, type BARTemplate } from '@/lib/api/bar-templates'

export default function BARTemplatesPage() {
  const [templates, setTemplates] = useState<BARTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [previewTemplate, setPreviewTemplate] = useState<BARTemplate | null>(null)

  const fetchTemplates = useCallback(async () => {
    try {
      const data = await barTemplatesApi.list()
      setTemplates(data)
    } catch {
      // Silently fail — list will be empty
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchTemplates()
  }, [fetchTemplates])

  const hasActive = templates.some((t) => t.is_active)

  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="p-6">
          <div className="max-w-4xl space-y-6">
            <h1 className="text-2xl font-bold">BAR Templates</h1>
            <p className="text-muted-foreground">
              Upload and manage Victorian Government BAR (Building Asbestos Register) Excel templates.
              The active template determines the column structure used for exports.
            </p>

            {/* Warning if no active template */}
            {!loading && !hasActive && templates.length > 0 && (
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  No active template set. Exports will use the default column order.
                  Activate a template to ensure BAR compliance.
                </AlertDescription>
              </Alert>
            )}

            {/* Upload */}
            <Card>
              <CardHeader>
                <CardTitle>Upload Template</CardTitle>
                <CardDescription>
                  Upload an official BAR Excel template to extract its column structure.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <BARTemplateUploader onUploaded={fetchTemplates} />
              </CardContent>
            </Card>

            {/* Version List */}
            <Card>
              <CardHeader>
                <CardTitle>Template Versions</CardTitle>
                <CardDescription>
                  {templates.length} template{templates.length !== 1 ? 's' : ''} uploaded
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <p className="text-sm text-muted-foreground py-4">Loading...</p>
                ) : (
                  <BARTemplateVersionList
                    templates={templates}
                    onRefetch={fetchTemplates}
                    onPreview={setPreviewTemplate}
                  />
                )}
              </CardContent>
            </Card>

            {/* Column Preview */}
            {previewTemplate && (
              <Card>
                <CardHeader>
                  <CardTitle>Column Preview</CardTitle>
                </CardHeader>
                <CardContent>
                  <BARTemplateColumnPreview template={previewTemplate} />
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  )
}
