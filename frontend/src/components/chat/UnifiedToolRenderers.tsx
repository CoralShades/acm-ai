'use client'

import React, { useCallback, useRef } from 'react'
import {
  useRenderToolCall,
  useDefaultTool,
  useCopilotChat,
} from '@copilotkit/react-core'
import { TextMessage, Role } from '@copilotkit/runtime-client-gql'
import { ACMTableResult } from './renderers/ACMTableResult'
import { ACMStatsResult } from './renderers/ACMStatsResult'
import { SearchResult } from './renderers/SearchResult'
import { RiskDistributionChart } from './renderers/RiskDistributionChart'
import { ToolErrorCard } from './renderers/ToolErrorCard'
import { ToolStepItem } from './renderers/ToolStepItem'
import { ItemDetailCard } from './renderers/ItemDetailCard'
import { BuildingSummaryCard } from './renderers/BuildingSummaryCard'
import { isErrorResult } from '@/lib/utils/tool-result'
import { ChatMiniGrid } from '@/components/jobs/ChatMiniGrid'
import { ChatChoiceCard } from '@/components/jobs/ChatChoiceCard'

function safeParseJSON(val: unknown): Record<string, unknown> | null {
  if (!val) return null
  if (typeof val === 'object') return val as Record<string, unknown>
  if (typeof val === 'string') {
    try {
      const parsed = JSON.parse(val)
      return typeof parsed === 'object' ? parsed : null
    } catch {
      return null
    }
  }
  return null
}

function parseResult(result: unknown): Record<string, unknown> | null {
  if (!result) return null
  const parsed = safeParseJSON(result)
  if (!parsed) return null
  // Don't swallow errors — let individual renderers decide how to display them.
  // Previously returned null here, which caused empty renders for any tool error.
  return parsed
}

// --- Centralized render helpers ---

/** Render an ACM table tool result (risk, building, room, product, detail) */
function renderACMTable(toolName: string, queryType: string, status: string, result: unknown) {
  if (status === 'inProgress' || status === 'executing') return <ToolStepItem toolName={toolName} status="executing" />
  if (isErrorResult(result)) return <ToolStepItem toolName={toolName} status="error"><ToolErrorCard tool={toolName} /></ToolStepItem>
  const data = parseResult(result)
  if (!data) return <></>
  return <ToolStepItem toolName={toolName} status="complete"><ACMTableResult data={data} queryType={queryType} /></ToolStepItem>
}

/** Render a search tool result (vector or text) */
function renderSearch(toolName: string, searchType: 'Vector' | 'Text', status: string, result: unknown) {
  if (status === 'inProgress' || status === 'executing') return <ToolStepItem toolName={toolName} status="executing" />
  if (isErrorResult(result)) return <ToolStepItem toolName={toolName} status="error"><ToolErrorCard tool={toolName} /></ToolStepItem>
  const data = parseResult(result)
  if (!data) return <></>
  return <ToolStepItem toolName={toolName} status="complete"><SearchResult data={data} searchType={searchType} /></ToolStepItem>
}

/** Schema info card */
function SchemaInfoCard({ data }: { data: Record<string, unknown> }) {
  const tables = data.tables as Record<string, { updatable_fields: string[]; enum_values: Record<string, string[]> }> | undefined
  const error = data.error as string | undefined
  if (error) return <div className="border border-red-200 dark:border-red-900 rounded-lg p-3 my-2 text-sm"><p className="text-red-600 dark:text-red-400 text-xs">{error}</p></div>
  if (!tables) return null
  return (
    <div className="border rounded-lg p-3 my-2 text-sm bg-background space-y-3">
      <div className="text-xs font-medium text-muted-foreground">Schema Information</div>
      {Object.entries(tables).map(([tableName, schema]) => (
        <div key={tableName}>
          <div className="text-xs font-semibold mb-1.5">{tableName}</div>
          <div className="flex flex-wrap gap-1 mb-2">
            {schema.updatable_fields.map((field) => (
              <span key={field} className="inline-block px-1.5 py-0.5 text-[10px] bg-muted rounded-md text-muted-foreground">{field}</span>
            ))}
          </div>
          {Object.keys(schema.enum_values || {}).length > 0 && (
            <div className="space-y-1">
              {Object.entries(schema.enum_values).map(([field, values]) => (
                <div key={field} className="text-xs">
                  <span className="text-muted-foreground">{field}:</span>{' '}
                  <span className="flex flex-wrap gap-1 mt-0.5 inline">
                    {values.map((v) => (
                      <span key={v} className="inline-block px-1.5 py-0.5 text-[10px] bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 rounded-full">{v}</span>
                    ))}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

/** Compact query results table */
function QueryResultsTable({ data }: { data: Record<string, unknown> }) {
  const results = (data.results as Record<string, unknown>[]) || []
  const totalResults = (data.total_results as number) || 0
  const warnings = (data.warnings as string[]) || []
  const generatedSql = data.generated_sql as string | undefined
  const error = data.error as string | undefined
  if (error) return <div className="border border-red-200 dark:border-red-900 rounded-lg p-3 my-2 text-sm"><div className="text-xs text-red-500 font-medium mb-1">Query Error</div><p className="text-red-600 dark:text-red-400">{error}</p>{generatedSql && <pre className="text-xs text-muted-foreground mt-2 p-2 bg-muted rounded">{generatedSql}</pre>}</div>
  if (results.length === 0) return <div className="border rounded-lg p-3 my-2 text-sm bg-background"><p className="text-muted-foreground">No results found.</p></div>
  const visibleCols = Object.keys(results[0]).filter((k) => !['id', 'source_id', 'embedding', 'embedding_text', 'embedding_model'].includes(k))
  return (
    <div className="border rounded-lg my-2 text-sm bg-background overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b bg-muted/50">
        <span className="text-xs font-medium text-muted-foreground">Query Results ({totalResults} total{results.length < totalResults ? `, showing ${results.length}` : ''})</span>
        {generatedSql && <details className="text-xs"><summary className="cursor-pointer text-muted-foreground hover:text-foreground">SQL</summary><pre className="mt-1 p-2 bg-muted rounded text-xs max-w-md overflow-auto">{generatedSql}</pre></details>}
      </div>
      {warnings.length > 0 && <div className="px-3 py-1 text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/30 border-b">{warnings.join('; ')}</div>}
      <div className="overflow-auto max-h-80">
        <table className="w-full text-xs">
          <thead><tr className="border-b bg-muted/30">{visibleCols.map((col) => <th key={col} className="px-3 py-1.5 text-left font-medium text-muted-foreground whitespace-nowrap">{col.replace(/_/g, ' ')}</th>)}</tr></thead>
          <tbody>{results.map((row, i) => <tr key={i} className="border-b last:border-0 hover:bg-muted/20">{visibleCols.map((col) => <td key={col} className="px-3 py-1.5 whitespace-nowrap max-w-[200px] truncate">{row[col] == null ? '—' : typeof row[col] === 'boolean' ? (row[col] ? 'Yes' : 'No') : String(row[col])}</td>)}</tr>)}</tbody>
        </table>
      </div>
    </div>
  )
}

/**
 * UnifiedToolRenderers — all tool renderers in one component.
 *
 * Uses centralized render helpers to eliminate copy-paste.
 * HITL approval is handled by useLangGraphInterrupt in UnifiedChatPanel,
 * NOT by text-message generation here.
 *
 * Must be rendered inside a CopilotKit provider.
 */
export function UnifiedToolRenderers() {
  const { appendMessage } = useCopilotChat()
  const appendRef = useRef(appendMessage)
  appendRef.current = appendMessage
  const stableAppend = useCallback(
    (...args: Parameters<typeof appendMessage>) => appendRef.current(...args),
    []
  )

  // ── ACM Search Tools (centralized via renderACMTable) ──

  useRenderToolCall({ name: 'search_acm_by_risk', render: ({ status, result }) => renderACMTable('search_acm_by_risk', 'Risk Status', status, result) })
  useRenderToolCall({ name: 'search_acm_by_building', render: ({ status, result }) => renderACMTable('search_acm_by_building', 'Building', status, result) })
  useRenderToolCall({ name: 'search_acm_by_room', render: ({ status, result }) => renderACMTable('search_acm_by_room', 'Room', status, result) })
  useRenderToolCall({ name: 'search_acm_by_material', render: ({ status, result }) => renderACMTable('search_acm_by_material', 'Product', status, result) })
  useRenderToolCall({ name: 'get_acm_record_detail', render: ({ status, result }) => {
    if (status === 'inProgress' || status === 'executing') return <ToolStepItem toolName="get_acm_record_detail" status="executing" />
    if (isErrorResult(result)) return <ToolStepItem toolName="get_acm_record_detail" status="error"><ToolErrorCard tool="get_acm_record_detail" /></ToolStepItem>
    const data = parseResult(result)
    if (!data) return <></>
    const record = (data.record as Record<string, unknown>) || data
    return <ToolStepItem toolName="get_acm_record_detail" status="complete"><ItemDetailCard data={record as Parameters<typeof ItemDetailCard>[0]['data']} /></ToolStepItem>
  }})
  useRenderToolCall({ name: 'list_acm_buildings', render: ({ status, result }) => {
    if (status === 'inProgress' || status === 'executing') return <ToolStepItem toolName="list_acm_buildings" status="executing" />
    if (isErrorResult(result)) return <ToolStepItem toolName="list_acm_buildings" status="error"><ToolErrorCard tool="list_acm_buildings" /></ToolStepItem>
    const data = parseResult(result)
    if (!data) return <></>
    const buildings = (data.buildings as Array<Record<string, unknown>>) || []
    if (buildings.length === 0) return <ToolStepItem toolName="list_acm_buildings" status="complete"><div className="text-xs text-muted-foreground p-3">No buildings found.</div></ToolStepItem>
    return (
      <ToolStepItem toolName="list_acm_buildings" status="complete">
        <div className="space-y-1">
          {buildings.map((b, i) => (
            <BuildingSummaryCard key={i} data={{
              building_name: String(b.building_name || 'Unknown'),
              building_id: b.internal_id ? String(b.internal_id) : undefined,
              record_count: (b.record_count as number) || 0,
              high_risk_count: (b.high_risk_count as number) || 0,
              address: b.address ? String(b.address) : undefined,
            }} />
          ))}
          <div className="text-xs text-muted-foreground px-1">{String(data.total_buildings)} building{Number(data.total_buildings) !== 1 ? 's' : ''} total</div>
        </div>
      </ToolStepItem>
    )
  }})

  // ── Stats with RiskDistributionChart ──

  useRenderToolCall({ name: 'get_acm_stats', render: ({ status, result }) => {
    if (status === 'inProgress' || status === 'executing') return <ToolStepItem toolName="get_acm_stats" status="executing" />
    if (isErrorResult(result)) return <ToolStepItem toolName="get_acm_stats" status="error"><ToolErrorCard tool="get_acm_stats" /></ToolStepItem>
    const data = parseResult(result)
    if (!data) return <></>
    const high = (data.high_risk as number) || 0
    const medium = (data.medium_risk as number) || 0
    const low = (data.low_risk as number) || 0
    const total = high + medium + low
    return (
      <ToolStepItem toolName="get_acm_stats" status="complete">
        <ACMStatsResult data={data} />
        {total > 0 && <div className="mt-2"><RiskDistributionChart high={high} medium={medium} low={low} total={total} /></div>}
      </ToolStepItem>
    )
  }})

  // ── Document Search Tools (FIXED: names match backend) ──

  useRenderToolCall({ name: 'search_documents', render: ({ status, result }) => renderSearch('search_documents', 'Vector', status, result) })
  useRenderToolCall({ name: 'text_search_documents', render: ({ status, result }) => renderSearch('text_search_documents', 'Text', status, result) })

  // ── Semantic ACM Search ──

  useRenderToolCall({ name: 'semantic_search_acm', render: ({ status, result }) => renderACMTable('semantic_search_acm', 'Semantic', status, result) })

  // ── Source Metadata ──

  useRenderToolCall({ name: 'get_source_metadata', render: ({ status, result }) => {
    if (status === 'inProgress' || status === 'executing') return <ToolStepItem toolName="get_source_metadata" status="executing" />
    if (isErrorResult(result)) return <ToolStepItem toolName="get_source_metadata" status="error"><ToolErrorCard tool="get_source_metadata" /></ToolStepItem>
    const data = parseResult(result)
    if (!data) return <></>
    const source = (data.source as Record<string, unknown>) || {}
    const intel = (data.intelligence as Record<string, unknown>) || {}
    const stats = (data.extraction_stats as Record<string, unknown>) || {}
    return (
      <ToolStepItem toolName="get_source_metadata" status="complete">
        <div className="border rounded-lg p-3 my-2 text-sm bg-background space-y-2">
          <div className="text-xs font-medium text-muted-foreground">Document Information</div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
            {source.name ? <div><span className="text-muted-foreground">Name:</span> {String(source.name)}</div> : null}
            {source.page_count ? <div><span className="text-muted-foreground">Pages:</span> {String(source.page_count)}</div> : null}
            {source.state ? <div><span className="text-muted-foreground">Status:</span> {String(source.state)}</div> : null}
            {intel.consultant ? <div><span className="text-muted-foreground">Consultant:</span> {String(intel.consultant)}</div> : null}
            {intel.site_name ? <div><span className="text-muted-foreground">Site:</span> {String(intel.site_name)}</div> : null}
            {intel.site_address ? <div><span className="text-muted-foreground">Address:</span> {String(intel.site_address)}</div> : null}
            {intel.document_type ? <div><span className="text-muted-foreground">Type:</span> {String(intel.document_type)}</div> : null}
            {stats.total_records != null ? <div><span className="text-muted-foreground">Records:</span> {String(stats.total_records)}</div> : null}
            {stats.total_buildings != null ? <div><span className="text-muted-foreground">Buildings:</span> {String(stats.total_buildings)}</div> : null}
          </div>
          {Array.isArray(intel.building_names) && (intel.building_names as string[]).length > 0 ? (
            <div className="text-xs">
              <span className="text-muted-foreground">Buildings:</span>{' '}
              {(intel.building_names as string[]).join(', ')}
            </div>
          ) : null}
        </div>
      </ToolStepItem>
    )
  }})

  // ── CRUD Tools ──

  useRenderToolCall({
    name: 'surreal_query',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') return <ToolStepItem toolName="surreal_query" status="executing" />
      if (isErrorResult(result)) return <ToolStepItem toolName="surreal_query" status="error"><ToolErrorCard tool="surreal_query" /></ToolStepItem>
      if (!result) return <></>
      const parsed = safeParseJSON(result)
      if (parsed?.type === 'surreal_query') {
        const results = (parsed.results as Record<string, unknown>[]) || []
        if (results.length > 5 && Object.keys(results[0] || {}).length > 2) {
          return (
            <ToolStepItem toolName="surreal_query" status="complete">
              <ChatMiniGrid
                data={results}
                onEditRecord={(id, row) => stableAppend(new TextMessage({ role: Role.User, content: `Edit record ${id}: ${JSON.stringify(row)}` }))}
                onViewRecord={(id) => stableAppend(new TextMessage({ role: Role.User, content: `Show details for record ${id}` }))}
              />
            </ToolStepItem>
          )
        }
        return <ToolStepItem toolName="surreal_query" status="complete"><QueryResultsTable data={parsed} /></ToolStepItem>
      }
      return <ToolStepItem toolName="surreal_query" status="complete"><pre className="text-xs p-2 bg-muted rounded max-h-40 overflow-auto">{typeof result === 'string' ? result : JSON.stringify(result, null, 2)}</pre></ToolStepItem>
    },
  })

  // Write tools: show read-only preview indicator.
  // Actual approval is handled by useLangGraphInterrupt in UnifiedChatPanel.

  useRenderToolCall({
    name: 'preview_write',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') return <ToolStepItem toolName="preview_write" status="executing" />
      if (isErrorResult(result)) return <ToolStepItem toolName="preview_write" status="error"><ToolErrorCard tool="preview_write" /></ToolStepItem>
      if (!result) return <></>
      const parsed = safeParseJSON(result)
      if (parsed?.error) return <ToolStepItem toolName="preview_write" status="error"><div className="text-xs text-red-500 px-3 py-2">{String(parsed.error)}</div></ToolStepItem>
      if (!parsed || parsed.type !== 'preview_write') return <></>
      return (
        <ToolStepItem toolName="preview_write" status="complete" defaultExpanded>
          <div className="border border-amber-200 dark:border-amber-800 rounded-lg p-3 my-1 text-xs space-y-1">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center rounded-md bg-amber-100 dark:bg-amber-900/50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-300">{String(parsed.operation)} Preview</span>
              <span className="text-[10px] font-mono text-muted-foreground">#{String(parsed.operation_id)}</span>
            </div>
            {!!parsed.record_id && <div><span className="text-muted-foreground">Record:</span> <span className="font-mono">{String(parsed.record_id)}</span></div>}
            {!!parsed.field && <div><span className="text-muted-foreground">Field:</span> <span className="font-semibold">{String(parsed.field)}</span> → <span className="text-green-700 dark:text-green-400 font-semibold">{String(parsed.new_value)}</span></div>}
            {!!parsed.reason && <p className="text-muted-foreground italic">{String(parsed.reason)}</p>}
            <p className="text-amber-600 dark:text-amber-400 text-[10px]">Awaiting approval via interrupt dialog...</p>
          </div>
        </ToolStepItem>
      )
    },
  })

  useRenderToolCall({
    name: 'preview_bulk_write',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') return <ToolStepItem toolName="preview_bulk_write" status="executing" />
      if (isErrorResult(result)) return <ToolStepItem toolName="preview_bulk_write" status="error"><ToolErrorCard tool="preview_bulk_write" /></ToolStepItem>
      if (!result) return <></>
      const parsed = safeParseJSON(result)
      if (parsed?.error) return <ToolStepItem toolName="preview_bulk_write" status="error"><div className="text-xs text-red-500 px-3 py-2">{String(parsed.error)}</div></ToolStepItem>
      if (!parsed || parsed.type !== 'preview_bulk_write') return <></>
      return (
        <ToolStepItem toolName="preview_bulk_write" status="complete" defaultExpanded>
          <div className="border border-amber-200 dark:border-amber-800 rounded-lg p-3 my-1 text-xs space-y-1">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center rounded-md bg-amber-100 dark:bg-amber-900/50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-700 dark:text-amber-300">BULK {String(parsed.operation)} Preview</span>
              <span className="text-[10px] font-mono text-muted-foreground">#{String(parsed.operation_id)}</span>
            </div>
            <div><span className="text-muted-foreground">Affected:</span> <span className="font-semibold">{String(parsed.affected_count)} records</span></div>
            {!!parsed.field && <div><span className="text-muted-foreground">Field:</span> <span className="font-semibold">{String(parsed.field)}</span> → <span className="text-green-700 dark:text-green-400 font-semibold">{String(parsed.new_value)}</span></div>}
            {!!parsed.reason && <p className="text-muted-foreground italic">{String(parsed.reason)}</p>}
            <p className="text-amber-600 dark:text-amber-400 text-[10px]">Awaiting approval via interrupt dialog...</p>
          </div>
        </ToolStepItem>
      )
    },
  })

  useRenderToolCall({
    name: 'execute_pending_write',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') return <ToolStepItem toolName="execute_pending_write" status="executing" />
      if (isErrorResult(result)) return <ToolStepItem toolName="execute_pending_write" status="error"><ToolErrorCard tool="execute_pending_write" /></ToolStepItem>
      if (!result) return <></>
      const parsed = safeParseJSON(result)
      const msg = parsed?.message ? String(parsed.message) : typeof result === 'string' ? result : JSON.stringify(result)
      return (
        <ToolStepItem toolName="execute_pending_write" status="complete">
          <div className="text-xs border border-green-200 dark:border-green-900 rounded-lg px-3 py-2 text-green-700 dark:text-green-400">{msg}</div>
        </ToolStepItem>
      )
    },
  })

  useRenderToolCall({
    name: 'get_schema_info',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') return <ToolStepItem toolName="get_schema_info" status="executing" />
      if (isErrorResult(result)) return <ToolStepItem toolName="get_schema_info" status="error"><ToolErrorCard tool="get_schema_info" /></ToolStepItem>
      if (!result) return <></>
      const parsed = safeParseJSON(result)
      if (parsed?.type === 'schema_info') return <ToolStepItem toolName="get_schema_info" status="complete"><SchemaInfoCard data={parsed} /></ToolStepItem>
      return <></>
    },
  })

  useRenderToolCall({
    name: 'ask_user_choice',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') return <ToolStepItem toolName="ask_user_choice" status="executing" />
      if (isErrorResult(result)) return <ToolStepItem toolName="ask_user_choice" status="error"><ToolErrorCard tool="ask_user_choice" /></ToolStepItem>
      if (!result) return <></>
      const parsed = safeParseJSON(result)
      if (parsed?.type === 'ask_user_choice' && parsed?.options) {
        return (
          <ToolStepItem toolName="ask_user_choice" status="complete" defaultExpanded>
            <ChatChoiceCard
              question={parsed.question as string}
              options={parsed.options as { label: string; value: string }[]}
              choiceId={parsed.choice_id as string}
              onSelect={(value) => { stableAppend(new TextMessage({ role: Role.User, content: `Selected: ${value} for choice #${parsed.choice_id}` })) }}
            />
          </ToolStepItem>
        )
      }
      return <></>
    },
  })

  useRenderToolCall({
    name: 'undo_last_write',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') return <ToolStepItem toolName="undo_last_write" status="executing" />
      if (isErrorResult(result)) return <ToolStepItem toolName="undo_last_write" status="error"><ToolErrorCard tool="undo_last_write" /></ToolStepItem>
      if (!result) return <></>
      const parsed = safeParseJSON(result)
      if (parsed?.type === 'undo_error') {
        return <ToolStepItem toolName="undo_last_write" status="error"><div className="text-xs text-amber-700 dark:text-amber-400 px-3 py-2">{String(parsed.error)}</div></ToolStepItem>
      }
      if (parsed?.type === 'preview_write') {
        return (
          <ToolStepItem toolName="undo_last_write" status="complete" defaultExpanded>
            <div className="border border-amber-200 dark:border-amber-800 rounded-lg p-3 my-1 text-xs space-y-1">
              <div className="text-muted-foreground">Undo: restoring <span className="font-semibold">{String(parsed.field)}</span> to <span className="text-green-700 dark:text-green-400 font-semibold">{String(parsed.new_value)}</span></div>
              <p className="text-amber-600 dark:text-amber-400 text-[10px]">Awaiting approval via interrupt dialog...</p>
            </div>
          </ToolStepItem>
        )
      }
      return <></>
    },
  })

  // ── Fallback ──

  useDefaultTool({
    render: ({ name, status, result }): React.ReactElement => {
      if (status === 'inProgress' || status === 'executing') return <ToolStepItem toolName={name} status="executing" />
      if (isErrorResult(result)) return <ToolStepItem toolName={name} status="error"><ToolErrorCard tool={name} /></ToolStepItem>
      if (!result) return <></>
      return (
        <ToolStepItem toolName={name} status="complete">
          <div className="border rounded-lg p-3 text-sm bg-muted/30">
            <pre className="text-xs whitespace-pre-wrap overflow-auto max-h-40">{typeof result === 'string' ? result : JSON.stringify(result, null, 2)}</pre>
          </div>
        </ToolStepItem>
      )
    },
  })

  return null
}
