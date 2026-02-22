'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Model, StageModelAssignment, ExtractionStageConfig } from '@/lib/types/models'
import { useStageModels, useUpdateStageModels, useResetStageModels } from '@/lib/hooks/use-models'
import { RotateCcw, Save } from 'lucide-react'

interface ExtractionStageModelsProps {
  models: Model[]
}

const EXTRACTION_STAGES: ExtractionStageConfig[] = [
  {
    key: 'structure_analysis',
    label: 'Structure Analysis',
    description: 'Document TOC extraction and section identification',
  },
  {
    key: 'building_inventory',
    label: 'Building Inventory',
    description: 'Compile building list from document structure',
  },
  {
    key: 'acm_extraction',
    label: 'ACM Extraction',
    description: 'Extract ACM records from tables — precision critical',
  },
  {
    key: 'page_tagging',
    label: 'Page Tagging',
    description: 'Classify pages by section type',
  },
  {
    key: 'product_classification',
    label: 'Product Classification',
    description: 'BAR taxonomy classification of ACM materials',
  },
  {
    key: 'corrective_validation',
    label: 'Corrective Validation',
    description: 'RAG-based validation and correction of extracted records',
  },
]

function getModelTier(model: Model): { label: string; variant: 'default' | 'secondary' | 'outline' } {
  const name = model.name.toLowerCase()
  if (name.includes('haiku') || name.includes('mini') || name.includes('flash') || name.includes('8b')) {
    return { label: 'Fast', variant: 'outline' }
  }
  if (name.includes('opus') || name.includes('gpt-4o') || name.includes('pro') || name.includes('72b') || name.includes('235b')) {
    return { label: 'Thorough', variant: 'default' }
  }
  return { label: 'Balanced', variant: 'secondary' }
}

export function ExtractionStageModels({ models }: ExtractionStageModelsProps) {
  const { data: stageModels, isLoading } = useStageModels()
  const updateMutation = useUpdateStageModels()
  const resetMutation = useResetStageModels()

  const [localValues, setLocalValues] = useState<StageModelAssignment>({})
  const [hasChanges, setHasChanges] = useState(false)

  useEffect(() => {
    if (stageModels) {
      setLocalValues(stageModels)
      setHasChanges(false)
    }
  }, [stageModels])

  const languageModels = models.filter((m) => m.type === 'language')

  const handleChange = (key: keyof StageModelAssignment, value: string) => {
    const newValues = { ...localValues, [key]: value || null }
    setLocalValues(newValues)
    setHasChanges(true)
  }

  const handleSave = () => {
    updateMutation.mutate(localValues)
    setHasChanges(false)
  }

  const handleReset = () => {
    resetMutation.mutate(undefined, {
      onSuccess: () => {
        setLocalValues({})
        setHasChanges(false)
      },
    })
  }

  if (isLoading) {
    return null
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Extraction Stage Models</CardTitle>
            <CardDescription>
              Assign specific models to each extraction pipeline stage. Unassigned stages use the default extraction model.
            </CardDescription>
          </div>
          {hasChanges && (
            <Badge variant="secondary">Unsaved changes</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2">
          {EXTRACTION_STAGES.map((stage) => {
            const currentValue = localValues[stage.key] || undefined

            return (
              <div key={stage.key} className="space-y-2">
                <Label>{stage.label}</Label>
                <Select
                  value={currentValue || ''}
                  onValueChange={(value) => handleChange(stage.key, value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Use default extraction model" />
                  </SelectTrigger>
                  <SelectContent>
                    {languageModels
                      .sort((a, b) => a.name.localeCompare(b.name))
                      .map((model) => {
                        const tier = getModelTier(model)
                        return (
                          <SelectItem key={model.id} value={model.id}>
                            <div className="flex items-center gap-2">
                              <span>{model.name}</span>
                              <Badge variant={tier.variant} className="text-[10px] px-1 py-0">
                                {tier.label}
                              </Badge>
                              <span className="text-xs text-muted-foreground">
                                {model.provider}
                              </span>
                            </div>
                          </SelectItem>
                        )
                      })}
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">{stage.description}</p>
              </div>
            )
          })}
        </div>

        <div className="flex items-center gap-2 pt-4 border-t">
          <Button onClick={handleSave} disabled={!hasChanges || updateMutation.isPending}>
            <Save className="h-4 w-4 mr-2" />
            {updateMutation.isPending ? 'Saving...' : 'Save Configuration'}
          </Button>
          <Button variant="outline" onClick={handleReset} disabled={resetMutation.isPending}>
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset to Defaults
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
