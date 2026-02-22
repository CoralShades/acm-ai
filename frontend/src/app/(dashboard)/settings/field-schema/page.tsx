'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AppShell } from '@/components/layout/AppShell'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { Save, RotateCcw, Download, Pencil } from 'lucide-react'
import { toast } from 'sonner'
import apiClient from '@/lib/api/client'

interface FieldDef {
  internal_name: string
  display_name: string
  excel_column: string
  col_index: number
  field_type: string
  required: boolean
  active: boolean
  enum_name: string | null
  group: string | null
}

interface BusinessRule {
  rule_id: string
  description: string
  enabled: boolean
}

interface FieldSchemaConfig {
  fields: FieldDef[]
  enums: Record<string, string[]>
  business_rules: BusinessRule[]
  version: string
  source_template: string | null
}

function FieldSchemaContent() {
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['acm', 'field-config'],
    queryFn: async () => {
      const res = await apiClient.get<FieldSchemaConfig>('/acm/field-config')
      return res.data
    },
  })

  const updateMutation = useMutation({
    mutationFn: async (config: FieldSchemaConfig) => {
      const res = await apiClient.put<FieldSchemaConfig>('/acm/field-config', config)
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['acm', 'field-config'] })
      toast.success('Field schema saved')
      setHasChanges(false)
    },
    onError: () => {
      toast.error('Failed to save field schema')
    },
  })

  const resetMutation = useMutation({
    mutationFn: async () => {
      const res = await apiClient.post<FieldSchemaConfig>('/acm/field-config/reset')
      return res.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['acm', 'field-config'] })
      toast.success('Field schema reset to defaults')
      setHasChanges(false)
    },
  })

  const [config, setConfig] = useState<FieldSchemaConfig | null>(null)
  const [hasChanges, setHasChanges] = useState(false)
  const [editField, setEditField] = useState<FieldDef | null>(null)
  const [editDisplayName, setEditDisplayName] = useState('')

  useEffect(() => {
    if (data) {
      setConfig(data)
      setHasChanges(false)
    }
  }, [data])

  const toggleFieldActive = (internalName: string) => {
    if (!config) return
    setConfig({
      ...config,
      fields: config.fields.map((f) =>
        f.internal_name === internalName ? { ...f, active: !f.active } : f
      ),
    })
    setHasChanges(true)
  }

  const toggleRule = (ruleId: string) => {
    if (!config) return
    setConfig({
      ...config,
      business_rules: config.business_rules.map((r) =>
        r.rule_id === ruleId ? { ...r, enabled: !r.enabled } : r
      ),
    })
    setHasChanges(true)
  }

  const openEditField = (field: FieldDef) => {
    setEditField(field)
    setEditDisplayName(field.display_name)
  }

  const saveFieldEdit = () => {
    if (!config || !editField) return
    setConfig({
      ...config,
      fields: config.fields.map((f) =>
        f.internal_name === editField.internal_name
          ? { ...f, display_name: editDisplayName }
          : f
      ),
    })
    setHasChanges(true)
    setEditField(null)
  }

  const handleExport = () => {
    if (!config) return
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'field-schema-config.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  if (isLoading || !config) {
    return (
      <AppShell>
        <div className="flex items-center justify-center min-h-[60vh]">
          <LoadingSpinner size="lg" />
        </div>
      </AppShell>
    )
  }

  const activeCount = config.fields.filter((f) => f.active).length
  const requiredCount = config.fields.filter((f) => f.required).length

  // Group fields
  const groups = new Map<string, FieldDef[]>()
  for (const field of config.fields) {
    const group = field.group || 'Other'
    if (!groups.has(group)) groups.set(group, [])
    groups.get(group)!.push(field)
  }

  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="p-6 max-w-5xl space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">BAR Field Schema</h1>
              <p className="text-muted-foreground mt-1">
                Configure the {config.fields.length} BAR fields used for extraction and export
              </p>
            </div>
            <div className="flex items-center gap-2">
              {hasChanges && <Badge variant="secondary">Unsaved changes</Badge>}
              <Badge variant="outline">{activeCount} active / {config.fields.length} total</Badge>
              <Badge variant="outline">{requiredCount} required</Badge>
            </div>
          </div>

          {/* Field Groups */}
          {Array.from(groups.entries()).map(([groupName, fields]) => (
            <Card key={groupName}>
              <CardHeader>
                <CardTitle className="text-lg">{groupName}</CardTitle>
                <CardDescription>{fields.length} fields</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-1">
                  <div className="grid grid-cols-[60px_1fr_120px_80px_80px_80px_40px] gap-2 px-2 py-1 text-xs font-medium text-muted-foreground border-b">
                    <span>Column</span>
                    <span>Field</span>
                    <span>Key</span>
                    <span>Type</span>
                    <span>Required</span>
                    <span>Active</span>
                    <span></span>
                  </div>
                  {fields
                    .sort((a, b) => a.col_index - b.col_index)
                    .map((field) => (
                      <div
                        key={field.internal_name}
                        className="grid grid-cols-[60px_1fr_120px_80px_80px_80px_40px] gap-2 px-2 py-2 items-center hover:bg-muted/50 rounded text-sm"
                      >
                        <span className="font-mono text-xs text-muted-foreground">
                          {field.excel_column}
                        </span>
                        <span className={!field.active ? 'text-muted-foreground line-through' : ''}>
                          {field.display_name}
                        </span>
                        <span className="font-mono text-xs text-muted-foreground truncate">
                          {field.internal_name}
                        </span>
                        <Badge variant="outline" className="text-[10px] w-fit">
                          {field.field_type}
                          {field.enum_name ? ` (${field.enum_name})` : ''}
                        </Badge>
                        <span>
                          {field.required && (
                            <Badge variant="destructive" className="text-[10px]">Required</Badge>
                          )}
                        </span>
                        <Switch
                          checked={field.active}
                          onCheckedChange={() => toggleFieldActive(field.internal_name)}
                          disabled={field.required}
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-7 w-7 p-0"
                          onClick={() => openEditField(field)}
                        >
                          <Pencil className="h-3 w-3" />
                        </Button>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          ))}

          {/* Business Rules */}
          {config.business_rules.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Business Rules</CardTitle>
                <CardDescription>BAR compliance validation rules</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {config.business_rules.map((rule) => (
                  <div key={rule.rule_id} className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium">{rule.rule_id}</p>
                      <p className="text-xs text-muted-foreground">{rule.description}</p>
                    </div>
                    <Switch
                      checked={rule.enabled}
                      onCheckedChange={() => toggleRule(rule.rule_id)}
                    />
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Actions */}
          <div className="flex items-center gap-2">
            <Button
              onClick={() => updateMutation.mutate(config)}
              disabled={!hasChanges || updateMutation.isPending}
            >
              <Save className="h-4 w-4 mr-2" />
              {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
            </Button>
            <Button variant="outline" onClick={handleExport}>
              <Download className="h-4 w-4 mr-2" />
              Export JSON
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

      {/* Edit Field Dialog */}
      <Dialog open={!!editField} onOpenChange={(open) => !open && setEditField(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Field: {editField?.internal_name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Display Name</Label>
              <Input
                value={editDisplayName}
                onChange={(e) => setEditDisplayName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Internal Key</Label>
              <Input value={editField?.internal_name || ''} disabled />
            </div>
            <div className="space-y-2">
              <Label>Excel Column</Label>
              <Input value={editField?.excel_column || ''} disabled />
            </div>
            <div className="space-y-2">
              <Label>Type</Label>
              <Input value={editField?.field_type || ''} disabled />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditField(null)}>Cancel</Button>
            <Button onClick={saveFieldEdit}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppShell>
  )
}

export default function FieldSchemaPage() {
  return (
    <ErrorBoundary
      fallback={(props) => (
        <PageErrorFallback
          {...props}
          pageName="BAR Field Schema"
          reloadUrl="/settings/field-schema"
        />
      )}
    >
      <FieldSchemaContent />
    </ErrorBoundary>
  )
}
