'use client'

import { AppShell } from '@/components/layout/AppShell'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { TableProperties } from 'lucide-react'
import { FieldMappingConfig } from '@/components/settings/FieldMappingConfig'

export default function FieldMappingPage() {
  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="p-6">
          <div className="max-w-4xl space-y-6">
            <h1 className="text-2xl font-bold">Export Field Mapping</h1>
            <p className="text-muted-foreground">
              Configure how ACM record fields map to BAR export columns. Each row represents a column
              in the exported BAR spreadsheet.
            </p>

            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <TableProperties className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <CardTitle>BAR Column Mapping</CardTitle>
                    <CardDescription>
                      Map ACM record fields to BAR export columns
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <FieldMappingConfig />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
