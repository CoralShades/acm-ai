'use client'

import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table2, FileSearch } from 'lucide-react'
import { acmApi } from '@/lib/api/acm'

interface DoclingTablesPanelProps {
  sourceId: string
  isExtracting: boolean
}

export function DoclingTablesPanel({ sourceId, isExtracting }: DoclingTablesPanelProps) {
  // Poll for raw tables during extraction
  const { data: tables, isLoading } = useQuery({
    queryKey: ['acm', 'raw-tables', sourceId],
    queryFn: () => acmApi.getRawTables(sourceId),
    enabled: !!sourceId,
    refetchInterval: isExtracting ? 5000 : false,
    staleTime: 10000,
  })

  const tableCount = tables?.length ?? 0
  const hasData = tableCount > 0

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <Table2 className="h-4 w-4" />
          Document Tables
          {hasData && (
            <span className="ml-auto text-sm font-normal text-muted-foreground">
              {tableCount} table{tableCount !== 1 ? 's' : ''} found
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading || (!hasData && isExtracting) ? (
          <div className="flex items-center gap-3 py-4 text-sm text-muted-foreground">
            <FileSearch className="h-5 w-5 animate-pulse" />
            <span>Analyzing document structure...</span>
          </div>
        ) : !hasData ? (
          <p className="text-sm text-muted-foreground py-2">No tables detected in document.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {tables?.map((table, idx) => (
              <div
                key={table.id || idx}
                className="rounded-lg border bg-muted/30 p-3 text-sm space-y-1"
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium">Table {idx + 1}</span>
                  {table.table_type && (
                    <span className="text-xs px-1.5 py-0.5 rounded bg-primary/10 text-primary">
                      {table.table_type}
                    </span>
                  )}
                </div>
                {(table.page_start != null || table.page_end != null) && (
                  <p className="text-xs text-muted-foreground">
                    {table.page_start === table.page_end
                      ? `Page ${table.page_start}`
                      : `Pages ${table.page_start}–${table.page_end}`}
                  </p>
                )}
                {table.building_name && (
                  <p className="text-xs text-muted-foreground truncate">
                    {table.building_name}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
