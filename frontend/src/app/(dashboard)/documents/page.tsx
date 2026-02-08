'use client'

import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { PageErrorFallback } from '@/components/common/PageErrorFallback'
import { AppShell } from '@/components/layout/AppShell'
import { DocumentLibrary } from '@/components/documents/DocumentLibrary'
import { ProcessingStatus } from '@/components/documents/ProcessingStatus'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { FileText, Activity } from 'lucide-react'

function DocumentsPageContent() {
  return (
    <AppShell>
      <div className="flex flex-col h-full w-full max-w-none px-6 py-6">
        <div className="mb-6 flex-shrink-0">
          <h1 className="text-2xl font-bold">Document Library</h1>
          <p className="text-muted-foreground">
            Manage your ACM documents and SAMP files
          </p>
        </div>
        <Tabs defaultValue="library" className="flex flex-col flex-1">
          <TabsList className="w-fit flex-shrink-0">
            <TabsTrigger value="library" className="gap-2">
              <FileText className="w-4 h-4" />
              Library
            </TabsTrigger>
            <TabsTrigger value="processing" className="gap-2">
              <Activity className="w-4 h-4" />
              Processing
            </TabsTrigger>
          </TabsList>
          <TabsContent value="library" className="flex-1 mt-4">
            <DocumentLibrary />
          </TabsContent>
          <TabsContent value="processing" className="flex-1 mt-4">
            <ProcessingStatus />
          </TabsContent>
        </Tabs>
      </div>
    </AppShell>
  )
}

export default function DocumentsPage() {
  return (
    <ErrorBoundary
      fallback={(props) => (
        <PageErrorFallback
          {...props}
          pageName="Documents"
          reloadUrl="/documents"
        />
      )}
    >
      <DocumentsPageContent />
    </ErrorBoundary>
  )
}
