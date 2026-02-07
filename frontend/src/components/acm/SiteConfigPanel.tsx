'use client'

import { useState } from 'react'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Settings2, CheckCircle2, AlertCircle, Copy, Loader2 } from 'lucide-react'
import { SiteConfigForm } from './SiteConfigForm'
import { useSiteConfig, useSiteConfigTemplates, useApplyConfigTemplate } from '@/lib/hooks/use-site-config'
import type { SiteConfigTemplate } from '@/lib/types/acm'

interface SiteConfigPanelProps {
  sourceId: string
}

export function SiteConfigPanel({ sourceId }: SiteConfigPanelProps) {
  const [open, setOpen] = useState(false)
  const { data: config, isLoading: isLoadingConfig, refetch: refetchConfig } = useSiteConfig(sourceId)
  const { data: templates = [], isLoading: isLoadingTemplates } = useSiteConfigTemplates()
  const applyTemplate = useApplyConfigTemplate()

  const isComplete = config?.is_bar_complete ?? false
  const missingFields = config?.missing_bar_fields ?? []

  const handleApplyTemplate = async (template: SiteConfigTemplate) => {
    await applyTemplate.mutateAsync({
      sourceId,
      templateSourceId: template.source_id,
    })
  }

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <Settings2 className="h-4 w-4" />
          Site Config
          {!isLoadingConfig && (
            isComplete ? (
              <Badge variant="outline" className="ml-1 bg-green-50 text-green-700 border-green-200">
                <CheckCircle2 className="h-3 w-3 mr-1" />
                Complete
              </Badge>
            ) : (
              <Badge variant="outline" className="ml-1 bg-amber-50 text-amber-700 border-amber-200">
                <AlertCircle className="h-3 w-3 mr-1" />
                {missingFields.length} missing
              </Badge>
            )
          )}
        </Button>
      </SheetTrigger>
      <SheetContent className="w-[500px] sm:max-w-[500px]">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Settings2 className="h-5 w-5" />
            Site Configuration
          </SheetTitle>
          <SheetDescription>
            Configure site metadata required for Victorian BAR compliance exports.
          </SheetDescription>
        </SheetHeader>

        <Tabs defaultValue="config" className="mt-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="config">Configuration</TabsTrigger>
            <TabsTrigger value="templates">
              Templates
              {templates.length > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {templates.length}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="config" className="mt-4">
            <ScrollArea className="h-[calc(100vh-220px)]">
              <div className="pr-4">
                {/* Status Card */}
                {!isLoadingConfig && (
                  <Card className={`mb-4 ${isComplete ? 'border-green-200 bg-green-50' : 'border-amber-200 bg-amber-50'}`}>
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
                            <div>
                              <p className="font-medium text-amber-800">Missing Fields</p>
                              <p className="text-sm text-amber-700">
                                Complete these fields for BAR export:{' '}
                                {missingFields.join(', ')}
                              </p>
                            </div>
                          </>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Config Form */}
                <SiteConfigForm sourceId={sourceId} onSaved={() => refetchConfig()} />
              </div>
            </ScrollArea>
          </TabsContent>

          <TabsContent value="templates" className="mt-4">
            <ScrollArea className="h-[calc(100vh-220px)]">
              <div className="pr-4 space-y-3">
                {isLoadingTemplates ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin" />
                  </div>
                ) : templates.length === 0 ? (
                  <Card>
                    <CardContent className="pt-6 text-center text-muted-foreground">
                      <p>No templates available yet.</p>
                      <p className="text-sm mt-1">
                        Saved configurations will appear here as templates.
                      </p>
                    </CardContent>
                  </Card>
                ) : (
                  templates.map((template) => (
                    <TemplateCard
                      key={template.source_id}
                      template={template}
                      onApply={handleApplyTemplate}
                      isApplying={applyTemplate.isPending}
                    />
                  ))
                )}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </SheetContent>
    </Sheet>
  )
}

interface TemplateCardProps {
  template: SiteConfigTemplate
  onApply: (template: SiteConfigTemplate) => void
  isApplying: boolean
}

function TemplateCard({ template, onApply, isApplying }: TemplateCardProps) {
  return (
    <Card className="hover:border-primary/50 transition-colors">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-base">
              {template.department || 'No Department'}
              {template.agency && ` - ${template.agency}`}
            </CardTitle>
            <CardDescription className="text-xs mt-1">
              {template.source_title || template.source_id}
            </CardDescription>
          </div>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => onApply(template)}
            disabled={isApplying}
          >
            {isApplying ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="flex flex-wrap gap-1.5">
          {template.building_type && (
            <Badge variant="outline" className="text-xs">
              {template.building_type}
            </Badge>
          )}
          {template.owned_or_leased && (
            <Badge variant="outline" className="text-xs">
              {template.owned_or_leased}
            </Badge>
          )}
          {template.frequency_of_use && (
            <Badge variant="outline" className="text-xs">
              {template.frequency_of_use}
            </Badge>
          )}
          {template.public_access && (
            <Badge variant="outline" className="text-xs">
              Public: {template.public_access}
            </Badge>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
