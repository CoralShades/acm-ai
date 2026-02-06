'use client'

import { AppShell } from '@/components/layout/AppShell'
import { DocumentLibrary } from '@/components/documents/DocumentLibrary'

export default function DocumentsPage() {
  return (
    <AppShell>
      <div className="flex flex-col h-full w-full max-w-none px-6 py-6">
        <div className="mb-6 flex-shrink-0">
          <h1 className="text-2xl font-bold">Document Library</h1>
          <p className="text-muted-foreground">
            Manage your ACM documents and SAMP files
          </p>
        </div>
        <DocumentLibrary />
      </div>
    </AppShell>
  )
}
