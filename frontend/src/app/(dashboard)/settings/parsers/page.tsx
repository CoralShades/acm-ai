'use client'

import { AppShell } from '@/components/layout/AppShell'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { FileCode } from 'lucide-react'

export default function ParsersSettingsPage() {
  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="p-6">
          <div className="max-w-4xl">
            <div className="flex items-center gap-4 mb-6">
              <h1 className="text-2xl font-bold">Parser Settings</h1>
            </div>
            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <FileCode className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <CardTitle>Document Parser Configuration</CardTitle>
                    <CardDescription>
                      Configure consultant-specific parsers and format detection rules
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="rounded-lg border border-dashed border-muted-foreground/25 p-8 text-center">
                  <p className="text-muted-foreground">
                    Parser configuration is coming in a future update.
                  </p>
                  <p className="text-sm text-muted-foreground/60 mt-2">
                    This will include consultant parser templates, column mapping rules, and format auto-detection settings.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
