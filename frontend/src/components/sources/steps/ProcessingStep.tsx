"use client"

import { Control, Controller } from "react-hook-form"
import { FormSection } from "@/components/ui/form-section"
import { CheckboxList } from "@/components/ui/checkbox-list"
import { Checkbox } from "@/components/ui/checkbox"
import { Transformation } from "@/lib/types/transformations"
import { SettingsResponse } from "@/lib/types/api"
import { Shield } from "lucide-react"

interface CreateSourceFormData {
  type: 'link' | 'upload' | 'text'
  title?: string
  url?: string
  content?: string
  file?: FileList | File
  notebooks?: string[]
  transformations?: string[]
  embed: boolean
  async_processing: boolean
  enable_acm_extraction?: boolean
}

interface ProcessingStepProps {
  control: Control<CreateSourceFormData>
  transformations: Transformation[]
  selectedTransformations: string[]
  onToggleTransformation: (transformationId: string) => void
  loading?: boolean
  settings?: SettingsResponse
}

export function ProcessingStep({
  control,
  transformations,
  selectedTransformations,
  onToggleTransformation,
  loading = false,
  settings
}: ProcessingStepProps) {
  const transformationItems = transformations.map((transformation) => ({
    id: transformation.id,
    title: transformation.title,
    description: transformation.description
  }))

  return (
    <div className="space-y-8">
      {/* ACM Extraction Section */}
      <FormSection
        title="ACM Register Extraction"
        description="Extract asbestos containing material data from SAMP documents."
      >
        <Controller
          control={control}
          name="enable_acm_extraction"
          render={({ field }) => (
            <label className="flex items-start gap-3 cursor-pointer p-4 rounded-lg border border-primary/30 bg-primary/5 hover:bg-primary/10 transition-colors">
              <Checkbox
                checked={field.value}
                onCheckedChange={field.onChange}
                className="mt-0.5"
              />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <Shield className="h-4 w-4 text-primary" />
                  <span className="text-sm font-medium">Enable ACM extraction</span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  Automatically extract ACM register data from your SAMP/asbestos documents.
                  Extracted data will appear in the ACM Register view.
                </p>
              </div>
            </label>
          )}
        />
      </FormSection>

      <FormSection
        title="Transformations (optional)"
        description="Apply AI transformations to analyze and extract insights from your content."
      >
        <CheckboxList
          items={transformationItems}
          selectedIds={selectedTransformations}
          onToggle={onToggleTransformation}
          loading={loading}
          emptyMessage="No transformations found."
        />
      </FormSection>

      <FormSection
        title="Processing Settings"
        description="Configure how your source will be processed and stored."
      >
        <div className="space-y-4">
          {settings?.default_embedding_option === 'ask' && (
            <Controller
              control={control}
              name="embed"
              render={({ field }) => (
                <label className="flex items-start gap-3 cursor-pointer p-3 rounded-md hover:bg-muted">
                  <Checkbox
                    checked={field.value}
                    onCheckedChange={field.onChange}
                    className="mt-0.5"
                  />
                  <div className="flex-1">
                    <span className="text-sm font-medium block">Enable embedding for search</span>
                    <p className="text-xs text-muted-foreground mt-1">
                      Allows this source to be found in vector searches and AI queries
                    </p>
                  </div>
                </label>
              )}
            />
          )}

          {settings?.default_embedding_option === 'always' && (
            <div className="p-3 rounded-md bg-primary/10 border border-primary/30">
              <div className="flex items-start gap-3">
                <div className="w-4 h-4 bg-primary rounded-full mt-0.5 flex-shrink-0"></div>
                <div className="flex-1">
                  <span className="text-sm font-medium block text-primary">Embedding enabled automatically</span>
                  <p className="text-xs text-primary mt-1">
                    Your settings are configured to always embed content for vector search.
                    You can change this in <span className="font-medium">Settings</span>.
                  </p>
                </div>
              </div>
            </div>
          )}

          {settings?.default_embedding_option === 'never' && (
            <div className="p-3 rounded-md bg-muted border border-border">
              <div className="flex items-start gap-3">
                <div className="w-4 h-4 bg-muted-foreground rounded-full mt-0.5 flex-shrink-0"></div>
                <div className="flex-1">
                  <span className="text-sm font-medium block text-foreground">Embedding disabled</span>
                  <p className="text-xs text-muted-foreground mt-1">
                    Your settings are configured to skip embedding. Vector search won&apos;t be available for this source.
                    You can change this in <span className="font-medium">Settings</span>.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </FormSection>
    </div>
  )
}
