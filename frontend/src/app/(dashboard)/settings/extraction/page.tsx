'use client'

import { AppShell } from '@/components/layout/AppShell'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { FlaskConical } from 'lucide-react'
import { ExtractionSettingsForm } from '@/components/settings/ExtractionSettingsForm'

export default function ExtractionSettingsPage() {
  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="p-6">
          <div className="max-w-4xl">
            <div className="flex items-center gap-4 mb-6">
              <h1 className="text-2xl font-bold">Extraction Settings</h1>
            </div>
            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <FlaskConical className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <CardTitle>ACM Extraction Configuration</CardTitle>
                    <CardDescription>
                      Configure how ACM registers are extracted from SAMP documents
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <ExtractionSettingsForm />
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
