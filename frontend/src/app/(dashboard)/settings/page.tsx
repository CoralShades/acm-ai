'use client'

import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { AppShell } from '@/components/layout/AppShell'
import { SettingsForm } from './components/SettingsForm'
import { useSettings } from '@/lib/hooks/use-settings'
import { Button } from '@/components/ui/button'
import { RefreshCw } from 'lucide-react'

function SettingsPageContent() {
  const { refetch } = useSettings()

  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="p-6">
          <div className="max-w-4xl">
            <div className="flex items-center gap-4 mb-6">
              <h1 className="text-2xl font-bold">Settings</h1>
              <Button variant="outline" size="sm" onClick={() => refetch()}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
            <SettingsForm />
          </div>
        </div>
      </div>
    </AppShell>
  )
}

export default function SettingsPage() {
  return (
    <ErrorBoundary
      fallback={(props) => (
        <PageErrorFallback
          {...props}
          pageName="Settings"
          reloadUrl="/settings"
        />
      )}
    >
      <SettingsPageContent />
    </ErrorBoundary>
  )
}
