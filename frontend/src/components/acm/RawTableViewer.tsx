'use client'

import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { acmApi } from '@/lib/api/acm'
import type { ACMRawTable } from '@/lib/types/acm'

interface RawTableViewerProps {
  sourceId: string
}

function getTableTypeMeta(tableType?: string | null): {
  label: string
  className: string
} {
  const normalized = (tableType ?? '').toLowerCase()

  if (normalized.includes('register')) {
    return {
      label: 'Register Table',
      className: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    }
  }

  if (normalized.includes('metadata')) {
    return {
      label: 'Metadata Table',
      className: 'border-blue-200 bg-blue-50 text-blue-700',
    }
  }

  if (normalized.includes('lab')) {
    return {
      label: 'Lab Report Table',
      className: 'border-amber-200 bg-amber-50 text-amber-700',
    }
  }

  if (normalized.includes('docling')) {
    return {
      label: 'Docling Markdown',
      className: 'border-slate-200 bg-slate-50 text-slate-700',
    }
  }

  return {
    label: 'MinerU Table',
    className: 'border-cyan-200 bg-cyan-50 text-cyan-700',
  }
}

function hasMergedCells(rawHtml?: string | null): boolean {
  if (!rawHtml) {
    return false
  }

  return /(colspan|rowspan)\s*=\s*['\"]?[2-9]\d*['\"]?/i.test(rawHtml)
}

function formatPageRange(table: ACMRawTable): string {
  if (table.page_start === table.page_end) {
    return `Page ${table.page_start}`
  }
  return `Pages ${table.page_start}-${table.page_end}`
}

function getTableMarkup(rawHtml: string): string {
  return `<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <style>
      :root { color-scheme: light; }
      body {
        font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        margin: 0;
        padding: 8px;
        color: #0f172a;
        background: #ffffff;
      }
      table {
        width: 100%;
        border-collapse: collapse;
        table-layout: auto;
        font-size: 12px;
      }
      th,
      td {
        border: 1px solid #d1d5db;
        padding: 6px;
        text-align: left;
        vertical-align: top;
      }
      th {
        background: #f8fafc;
      }
    </style>
  </head>
  <body>
    ${rawHtml}
  </body>
</html>`
}

export function RawTableViewer({ sourceId }: RawTableViewerProps) {
  const {
    data: tables = [],
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['acm-raw-tables', sourceId],
    queryFn: () => acmApi.getRawTables(sourceId),
    enabled: !!sourceId,
    staleTime: 60_000,
  })

  const summary = useMemo(() => {
    return tables.reduce(
      (acc, table) => {
        const normalizedType = (table.table_type ?? '').toLowerCase()

        if (normalizedType.includes('register')) {
          acc.register += 1
        }
        if (normalizedType.includes('metadata')) {
          acc.metadata += 1
        }
        if (hasMergedCells(table.raw_html)) {
          acc.merged += 1
        }

        return acc
      },
      { register: 0, metadata: 0, merged: 0 }
    )
  }, [tables])

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-72" />
        <Skeleton className="h-56 w-full" />
        <Skeleton className="h-56 w-full" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
        Failed to load raw tables: {error instanceof Error ? error.message : 'Unknown error'}
      </div>
    )
  }

  if (tables.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-8 text-center text-sm text-muted-foreground">
        No raw table sections are available for this job yet.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2 text-sm">
        <Badge variant="outline">{tables.length} table section(s)</Badge>
        <Badge variant="outline">Register: {summary.register}</Badge>
        <Badge variant="outline">Metadata: {summary.metadata}</Badge>
        <Badge variant="outline">Merged cells: {summary.merged}</Badge>
      </div>

      <div className="space-y-4">
        {tables.map((table, index) => {
          const typeMeta = getTableTypeMeta(table.table_type)
          const merged = hasMergedCells(table.raw_html)

          return (
            <Card key={table.id || `${table.page_start}-${table.page_end}-${index}`}>
              <CardHeader className="pb-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <CardTitle className="text-sm font-semibold">
                    Table {index + 1} - {formatPageRange(table)}
                  </CardTitle>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="outline" className={typeMeta.className}>
                      {typeMeta.label}
                    </Badge>
                    <Badge
                      variant="outline"
                      className={
                        merged
                          ? 'border-orange-200 bg-orange-50 text-orange-700'
                          : 'border-slate-200 bg-slate-50 text-slate-700'
                      }
                    >
                      {merged ? 'Merged cells detected' : 'No merged cells'}
                    </Badge>
                  </div>
                </div>
                {table.building_name ? (
                  <p className="text-xs text-muted-foreground">{table.building_name}</p>
                ) : null}
              </CardHeader>
              <CardContent>
                {table.raw_html ? (
                  <iframe
                    title={`Raw table ${index + 1}`}
                    sandbox=""
                    srcDoc={getTableMarkup(table.raw_html)}
                    className="h-80 w-full rounded-md border"
                  />
                ) : (
                  <pre className="max-h-80 overflow-auto rounded-md border bg-muted/30 p-3 text-xs leading-relaxed whitespace-pre-wrap">
                    {table.raw_text || 'No raw content available'}
                  </pre>
                )}
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
