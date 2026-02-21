'use client'

import { useState, useCallback, useEffect } from 'react'
import { AppShell } from '@/components/layout/AppShell'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Activity, RefreshCw, Loader2, AlertCircle, CheckCircle2, XCircle, Clock } from 'lucide-react'
import { extractionMonitorApi, type ExtractionProgressItem } from '@/lib/api/extraction-monitor'

function StatusBadge({ status }: { status: string }) {
  switch (status) {
    case 'running':
      return <Badge variant="default" className="gap-1"><Loader2 className="h-3 w-3 animate-spin" />Running</Badge>
    case 'completed':
      return <Badge variant="secondary" className="gap-1 bg-emerald-500/15 text-emerald-600"><CheckCircle2 className="h-3 w-3" />Completed</Badge>
    case 'failed':
      return <Badge variant="destructive" className="gap-1"><XCircle className="h-3 w-3" />Failed</Badge>
    default:
      return <Badge variant="outline" className="gap-1"><Clock className="h-3 w-3" />{status}</Badge>
  }
}

function ExtractionItem({ item }: { item: ExtractionProgressItem }) {
  const stageLabel = item.state?.current_stage as string | undefined
  const recordCount = item.state?.records_created as number | undefined

  return (
    <div className="flex items-center justify-between rounded-lg border p-4">
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm">{item.command_id?.slice(0, 12) || item.id}</span>
          <StatusBadge status={item.status} />
          {item.token_limit_exceeded && (
            <Badge variant="outline" className="text-amber-500 border-amber-500/30">Token limit</Badge>
          )}
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          {item.source_id && <span>Source: {item.source_id}</span>}
          {stageLabel && <span>Stage: {stageLabel}</span>}
          {recordCount != null && <span>{recordCount} records</span>}
          {item.chunk_count && item.chunk_count > 1 && <span>{item.chunk_count} chunks</span>}
        </div>
        {item.updated_at && (
          <p className="text-xs text-muted-foreground">
            {new Date(item.updated_at).toLocaleString()}
          </p>
        )}
      </div>
    </div>
  )
}

export default function ExtractionMonitorPage() {
  const [activeTab, setActiveTab] = useState('active')
  const [items, setItems] = useState<ExtractionProgressItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchItems = useCallback(async (statusFilter?: string) => {
    try {
      setLoading(true)
      setError(null)
      const data = await extractionMonitorApi.list({
        status: statusFilter,
        limit: 100,
      })
      setItems(data.items)
    } catch {
      setError('Failed to load extraction progress')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const statusFilter = activeTab === 'active' ? 'running' : undefined
    fetchItems(statusFilter)
  }, [activeTab, fetchItems])

  // Auto-refresh active tab every 3s
  useEffect(() => {
    if (activeTab !== 'active') return
    const interval = setInterval(() => {
      fetchItems('running')
    }, 3000)
    return () => clearInterval(interval)
  }, [activeTab, fetchItems])

  const activeItems = items.filter((i) => i.status === 'running')
  const historyItems = items.filter((i) => i.status !== 'running')

  return (
    <AppShell>
      <div className="flex-1 overflow-y-auto">
        <div className="p-6">
          <div className="max-w-4xl space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold flex items-center gap-2">
                  <Activity className="h-6 w-6" />
                  Extraction Monitor
                </h1>
                <p className="text-muted-foreground mt-1">
                  Track active and historical document extractions.
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => fetchItems(activeTab === 'active' ? 'running' : undefined)}
                disabled={loading}
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Card>
              <CardHeader>
                <CardTitle>Extractions</CardTitle>
                <CardDescription>
                  {activeItems.length} active, {historyItems.length} completed
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Tabs value={activeTab} onValueChange={setActiveTab}>
                  <TabsList>
                    <TabsTrigger value="active">
                      Active
                      {activeItems.length > 0 && (
                        <Badge variant="default" className="ml-2 h-5 min-w-5 px-1">
                          {activeItems.length}
                        </Badge>
                      )}
                    </TabsTrigger>
                    <TabsTrigger value="history">History</TabsTrigger>
                  </TabsList>

                  <TabsContent value="active" className="mt-4 space-y-3">
                    {loading && items.length === 0 ? (
                      <div className="flex items-center justify-center py-8">
                        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                      </div>
                    ) : activeItems.length === 0 ? (
                      <div className="rounded-lg border border-dashed p-8 text-center">
                        <p className="text-muted-foreground">No active extractions</p>
                        <p className="text-sm text-muted-foreground/60 mt-1">
                          Start an extraction from a source document to see progress here.
                        </p>
                      </div>
                    ) : (
                      activeItems.map((item) => (
                        <ExtractionItem key={item.id || item.command_id} item={item} />
                      ))
                    )}
                  </TabsContent>

                  <TabsContent value="history" className="mt-4 space-y-3">
                    {loading && items.length === 0 ? (
                      <div className="flex items-center justify-center py-8">
                        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                      </div>
                    ) : historyItems.length === 0 ? (
                      <div className="rounded-lg border border-dashed p-8 text-center">
                        <p className="text-muted-foreground">No extraction history</p>
                        <p className="text-sm text-muted-foreground/60 mt-1">
                          Completed and failed extractions will appear here.
                        </p>
                      </div>
                    ) : (
                      historyItems.map((item) => (
                        <ExtractionItem key={item.id || item.command_id} item={item} />
                      ))
                    )}
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
