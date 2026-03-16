'use client'

import React, { useCallback, useRef } from 'react'
import {
  useRenderToolCall,
  useDefaultTool,
  useCopilotChat,
} from '@copilotkit/react-core'
import { TextMessage, Role } from '@copilotkit/runtime-client-gql'
import { AgentActivityIndicator } from '@/components/chat/renderers/AgentActivityIndicator'
import { HITLApprovalDialog } from '@/components/chat/renderers/HITLApprovalDialog'
import { ToolErrorCard } from '@/components/chat/renderers/ToolErrorCard'
import { isErrorResult } from '@/lib/utils/tool-result'
import { ChatMiniGrid } from './ChatMiniGrid'
import { ChatChoiceCard } from './ChatChoiceCard'

/**
 * Parse a value that may be a JSON string or an already-parsed object.
 */
function parseJsonSafe(val: unknown): Record<string, unknown> | null {
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

/**
 * Render a schema info card with field badges and enum value chips.
 */
function SchemaInfoCard({ data }: { data: Record<string, unknown> }) {
  const tables = data.tables as Record<string, { updatable_fields: string[]; enum_values: Record<string, string[]> }> | undefined
  const error = data.error as string | undefined

  if (error) {
    return (
      <div className="border border-red-200 dark:border-red-900 rounded-lg p-3 my-2 text-sm">
        <p className="text-red-600 dark:text-red-400 text-xs">{error}</p>
      </div>
    )
  }

  if (!tables) return null

  return (
    <div className="border rounded-lg p-3 my-2 text-sm bg-background space-y-3">
      <div className="text-xs font-medium text-muted-foreground">Schema Information</div>
      {Object.entries(tables).map(([tableName, schema]) => (
        <div key={tableName}>
          <div className="text-xs font-semibold mb-1.5">{tableName}</div>
          <div className="flex flex-wrap gap-1 mb-2">
            {schema.updatable_fields.map((field) => (
              <span
                key={field}
                className="inline-block px-1.5 py-0.5 text-[10px] bg-muted rounded-md text-muted-foreground"
              >
                {field}
              </span>
            ))}
          </div>
          {Object.keys(schema.enum_values || {}).length > 0 && (
            <div className="space-y-1">
              {Object.entries(schema.enum_values).map(([field, values]) => (
                <div key={field} className="text-xs">
                  <span className="text-muted-foreground">{field}:</span>{' '}
                  <span className="flex flex-wrap gap-1 mt-0.5 inline">
                    {values.map((v) => (
                      <span
                        key={v}
                        className="inline-block px-1.5 py-0.5 text-[10px] bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 rounded-full"
                      >
                        {v}
                      </span>
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

/**
 * Render a table of results from a surreal_query tool call.
 */
function QueryResultsTable({ data }: { data: Record<string, unknown> }) {
  const results = (data.results as Record<string, unknown>[]) || []
  const totalResults = (data.total_results as number) || 0
  const warnings = (data.warnings as string[]) || []
  const generatedSql = data.generated_sql as string | undefined
  const error = data.error as string | undefined

  if (error) {
    return (
      <div className="border border-red-200 dark:border-red-900 rounded-lg p-3 my-2 text-sm">
        <div className="text-xs text-red-500 font-medium mb-1">Query Error</div>
        <p className="text-red-600 dark:text-red-400">{error}</p>
        {generatedSql && (
          <pre className="text-xs text-muted-foreground mt-2 p-2 bg-muted rounded">
            {generatedSql}
          </pre>
        )}
      </div>
    )
  }

  if (results.length === 0) {
    return (
      <div className="border rounded-lg p-3 my-2 text-sm bg-background">
        <div className="text-xs text-muted-foreground mb-1">Query Results</div>
        <p className="text-muted-foreground">No results found.</p>
      </div>
    )
  }

  return (
    <div className="border rounded-lg my-2 text-sm bg-background overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b bg-muted/50">
        <span className="text-xs font-medium text-muted-foreground">
          Query Results ({totalResults} total{results.length < totalResults ? `, showing ${results.length}` : ''})
        </span>
        {generatedSql && (
          <details className="text-xs">
            <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
              SQL
            </summary>
            <pre className="mt-1 p-2 bg-muted rounded text-xs max-w-md overflow-auto">
              {generatedSql}
            </pre>
          </details>
        )}
      </div>
      {warnings.length > 0 && (
        <div className="px-3 py-1 text-xs text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/30 border-b">
          {warnings.join('; ')}
        </div>
      )}
      {/* Use compact HTML table for small result sets, AG Grid for larger ones */}
      <div className="overflow-auto max-h-80">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b bg-muted/30">
              {Object.keys(results[0])
                .filter((k) => !['id', 'source_id', 'embedding', 'embedding_text', 'embedding_model'].includes(k))
                .map((col) => (
                  <th key={col} className="px-3 py-1.5 text-left font-medium text-muted-foreground whitespace-nowrap">
                    {col.replace(/_/g, ' ')}
                  </th>
                ))}
            </tr>
          </thead>
          <tbody>
            {results.map((row, i) => (
              <tr key={i} className="border-b last:border-0 hover:bg-muted/20">
                {Object.keys(results[0])
                  .filter((k) => !['id', 'source_id', 'embedding', 'embedding_text', 'embedding_model'].includes(k))
                  .map((col) => (
                    <td key={col} className="px-3 py-1.5 whitespace-nowrap max-w-[200px] truncate">
                      {row[col] === null || row[col] === undefined
                        ? '—'
                        : typeof row[col] === 'boolean'
                          ? row[col] ? 'Yes' : 'No'
                          : String(row[col])}
                    </td>
                  ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

/**
 * Registers CopilotKit tool-call renderers for CRUD operations.
 *
 * Handles:
 * - surreal_query: renders structured table results (mini grid for multi-row, table for counts)
 * - preview_write: renders HITL approval dialog
 * - preview_bulk_write: renders HITL approval dialog with affected count
 * - execute_pending_write: renders write confirmation
 * - get_schema_info: renders schema card with field badges and enum chips
 * - ask_user_choice: renders choice card with clickable options
 * - undo_last_write: renders "preparing undo" indicator (result triggers preview_write renderer)
 *
 * Must be rendered inside a CopilotKit provider configured with /copilot-crud.
 */
export function CrudToolRenderers() {
  const { appendMessage } = useCopilotChat()

  // Stabilize appendMessage in a ref so render callbacks passed to
  // useRenderToolCall always use the latest version without changing
  // their own reference. This prevents dependency-loop re-renders when
  // the CopilotKit hook returns a new appendMessage reference each render.
  const appendMessageRef = useRef(appendMessage)
  appendMessageRef.current = appendMessage

  const stableAppendMessage = useCallback(
    (...args: Parameters<typeof appendMessage>) => appendMessageRef.current(...args),
    []
  )

  // --- surreal_query: structured table results with mini AG Grid ---
  useRenderToolCall({
    name: 'surreal_query',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') {
        return <AgentActivityIndicator tool="surreal_query" status="executing" />
      }
      if (isErrorResult(result)) return <ToolErrorCard tool="surreal_query" />
      if (!result) return <></>

      const parsed = parseJsonSafe(result)
      if (parsed && parsed.type === 'surreal_query') {
        const results = (parsed.results as Record<string, unknown>[]) || []
        const totalResults = (parsed.total_results as number) || 0
        const generatedSql = parsed.generated_sql as string | undefined
        // Use ChatMiniGrid for multi-column results with >5 rows
        if (results.length > 5 && Object.keys(results[0] || {}).length > 2) {
          return (
            <div className="my-2">
              <div className="flex items-center justify-between px-1 mb-1">
                <span className="text-xs font-medium text-muted-foreground">
                  Query Results ({totalResults} total)
                </span>
                {generatedSql && (
                  <details className="text-xs">
                    <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                      SQL
                    </summary>
                    <pre className="mt-1 p-2 bg-muted rounded text-xs max-w-md overflow-auto">
                      {generatedSql}
                    </pre>
                  </details>
                )}
              </div>
              <ChatMiniGrid
                data={results}
                onEditRecord={(id, row) => {
                  stableAppendMessage(
                    new TextMessage({
                      role: Role.User,
                      content: `Edit record ${id}: ${JSON.stringify(row)}`,
                    })
                  )
                }}
                onViewRecord={(id) => {
                  stableAppendMessage(
                    new TextMessage({
                      role: Role.User,
                      content: `Show details for record ${id}`,
                    })
                  )
                }}
              />
            </div>
          )
        }
        return <QueryResultsTable data={parsed} />
      }

      // Fallback: render as plain text
      return (
        <div className="border rounded-lg p-3 my-2 text-sm bg-background">
          <div className="text-xs text-muted-foreground mb-1">Query Results</div>
          <pre className="text-xs whitespace-pre-wrap overflow-auto max-h-60 leading-relaxed">
            {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )
    },
  })

  // Legacy: keep query_job_records renderer for backward compatibility
  useRenderToolCall({
    name: 'query_job_records',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') {
        return <AgentActivityIndicator tool="query_job_records" status="executing" />
      }
      if (isErrorResult(result)) return <ToolErrorCard tool="query_job_records" />
      if (!result) return <></>
      return (
        <div className="border rounded-lg p-3 my-2 text-sm bg-background">
          <div className="text-xs text-muted-foreground mb-1">Query Results</div>
          <pre className="text-xs whitespace-pre-wrap overflow-auto max-h-60 leading-relaxed">
            {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )
    },
  })

  // --- preview_write: HITL approval dialog ---
  useRenderToolCall({
    name: 'preview_write',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') {
        return <AgentActivityIndicator tool="preview_write" status="executing" />
      }
      if (isErrorResult(result)) return <ToolErrorCard tool="preview_write" />
      if (!result) return <></>

      const parsed = parseJsonSafe(result)
      if (!parsed || parsed.type !== 'preview_write') {
        if (parsed?.error) {
          return (
            <div className="border border-red-200 dark:border-red-900 rounded-lg px-3 py-2 my-1 text-xs text-red-600 dark:text-red-400">
              {String(parsed.error)}
            </div>
          )
        }
        return <></>
      }

      return (
        <HITLApprovalDialog
          preview={parsed as never}
          onApprove={(edits) => {
            const opId = parsed.operation_id as string
            const editStr = edits ? ` with edits: ${JSON.stringify(edits)}` : ''
            stableAppendMessage(
              new TextMessage({
                role: Role.User,
                content: `Approved. Execute operation #${opId}${editStr}`,
              })
            )
          }}
          onReject={() => {
            const opId = parsed.operation_id as string
            stableAppendMessage(
              new TextMessage({
                role: Role.User,
                content: `Rejected. Cancel operation #${opId}`,
              })
            )
          }}
        />
      )
    },
  })

  // --- preview_bulk_write: HITL approval with affected count ---
  useRenderToolCall({
    name: 'preview_bulk_write',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') {
        return <AgentActivityIndicator tool="preview_bulk_write" status="executing" />
      }
      if (isErrorResult(result)) return <ToolErrorCard tool="preview_bulk_write" />
      if (!result) return <></>

      const parsed = parseJsonSafe(result)
      if (!parsed || parsed.type !== 'preview_bulk_write') {
        if (parsed?.error) {
          return (
            <div className="border border-red-200 dark:border-red-900 rounded-lg px-3 py-2 my-1 text-xs text-red-600 dark:text-red-400">
              {String(parsed.error)}
            </div>
          )
        }
        return <></>
      }

      const affectedCount = parsed.affected_count as number
      const bulkPreview = {
        type: 'preview_write',
        operation_id: parsed.operation_id,
        operation: `BULK ${parsed.operation}`,
        record_id: `${affectedCount} records`,
        field: parsed.field as string,
        new_value: parsed.new_value as string,
        reason: parsed.reason as string,
      }

      return (
        <HITLApprovalDialog
          preview={bulkPreview as never}
          onApprove={(edits) => {
            const opId = parsed.operation_id as string
            const editStr = edits ? ` with edits: ${JSON.stringify(edits)}` : ''
            stableAppendMessage(
              new TextMessage({
                role: Role.User,
                content: `Approved. Execute operation #${opId}${editStr}`,
              })
            )
          }}
          onReject={() => {
            const opId = parsed.operation_id as string
            stableAppendMessage(
              new TextMessage({
                role: Role.User,
                content: `Rejected. Cancel operation #${opId}`,
              })
            )
          }}
        />
      )
    },
  })

  // --- execute_pending_write: write confirmation ---
  useRenderToolCall({
    name: 'execute_pending_write',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') {
        return <AgentActivityIndicator tool="execute_pending_write" status="executing" />
      }
      if (isErrorResult(result)) return <ToolErrorCard tool="execute_pending_write" />
      if (!result) return <></>

      const parsed = parseJsonSafe(result)
      if (parsed?.type === 'write_result' && parsed?.success) {
        return (
          <div className="text-xs border border-green-200 dark:border-green-900 rounded-lg px-3 py-2 my-1 text-green-700 dark:text-green-400">
            {String(parsed.message)}
          </div>
        )
      }

      const content = typeof result === 'string' ? result : JSON.stringify(result)
      return (
        <div className="text-xs border border-green-200 dark:border-green-900 rounded-lg px-3 py-2 my-1 text-green-700 dark:text-green-400">
          {content}
        </div>
      )
    },
  })

  // --- get_schema_info: schema card with field badges ---
  useRenderToolCall({
    name: 'get_schema_info',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') {
        return <AgentActivityIndicator tool="get_schema_info" status="executing" />
      }
      if (isErrorResult(result)) return <ToolErrorCard tool="get_schema_info" />
      if (!result) return <></>

      const parsed = parseJsonSafe(result)
      if (parsed?.type === 'schema_info') {
        return <SchemaInfoCard data={parsed} />
      }

      return (
        <div className="border rounded-lg p-3 my-2 text-sm bg-background">
          <pre className="text-xs whitespace-pre-wrap overflow-auto max-h-40">
            {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )
    },
  })

  // --- ask_user_choice: choice card with clickable options ---
  useRenderToolCall({
    name: 'ask_user_choice',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') {
        return <AgentActivityIndicator tool="ask_user_choice" status="executing" />
      }
      if (isErrorResult(result)) return <ToolErrorCard tool="ask_user_choice" />
      if (!result) return <></>

      const parsed = parseJsonSafe(result)
      if (parsed?.type === 'ask_user_choice' && parsed?.options) {
        return (
          <ChatChoiceCard
            question={parsed.question as string}
            options={parsed.options as { label: string; value: string }[]}
            choiceId={parsed.choice_id as string}
            onSelect={(value) => {
              const choiceId = parsed.choice_id as string
              stableAppendMessage(
                new TextMessage({
                  role: Role.User,
                  content: `Selected: ${value} for choice #${choiceId}`,
                })
              )
            }}
          />
        )
      }

      if (parsed?.error) {
        return (
          <div className="border border-red-200 dark:border-red-900 rounded-lg px-3 py-2 my-1 text-xs text-red-600 dark:text-red-400">
            {String(parsed.error)}
          </div>
        )
      }

      return <></>
    },
  })

  // --- undo_last_write: preparing indicator (result triggers preview_write renderer) ---
  useRenderToolCall({
    name: 'undo_last_write',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing') {
        return <AgentActivityIndicator tool="undo_last_write" status="executing" />
      }
      if (isErrorResult(result)) return <ToolErrorCard tool="undo_last_write" />
      if (!result) return <></>

      const parsed = parseJsonSafe(result)

      // Undo error
      if (parsed?.type === 'undo_error') {
        return (
          <div className="border border-amber-200 dark:border-amber-900 rounded-lg px-3 py-2 my-1 text-xs text-amber-700 dark:text-amber-400">
            {String(parsed.error)}
          </div>
        )
      }

      // Successful undo generates a preview_write — which will be rendered by
      // the preview_write renderer above. But the undo tool itself returns the
      // preview_write JSON, so render it here too.
      if (parsed?.type === 'preview_write') {
        return (
          <HITLApprovalDialog
            preview={parsed as never}
            onApprove={(edits) => {
              const opId = parsed.operation_id as string
              const editStr = edits ? ` with edits: ${JSON.stringify(edits)}` : ''
              stableAppendMessage(
                new TextMessage({
                  role: Role.User,
                  content: `Approved. Execute operation #${opId}${editStr}`,
                })
              )
            }}
            onReject={() => {
              const opId = parsed.operation_id as string
              stableAppendMessage(
                new TextMessage({
                  role: Role.User,
                  content: `Rejected. Cancel operation #${opId}`,
                })
              )
            }}
          />
        )
      }

      return <></>
    },
  })

  // Fallback for any unregistered tools
  useDefaultTool({
    render: ({ name, status, result }): React.ReactElement => {
      if (status === 'inProgress' || status === 'executing') {
        return <AgentActivityIndicator tool={name} status="executing" />
      }
      if (isErrorResult(result)) return <ToolErrorCard tool={name} />
      if (!result) return <></>
      return (
        <div className="border rounded-lg p-3 my-1 text-sm bg-background">
          <div className="text-xs text-muted-foreground mb-1">{name}</div>
          <pre className="text-xs whitespace-pre-wrap overflow-auto max-h-40">
            {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )
    },
  })

  return null
}
