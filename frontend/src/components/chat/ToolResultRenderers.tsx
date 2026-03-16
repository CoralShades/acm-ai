'use client'

import React from 'react'
import { useRenderToolCall, useDefaultTool } from '@copilotkit/react-core'
import { ACMTableResult } from './renderers/ACMTableResult'
import { ACMStatsResult } from './renderers/ACMStatsResult'
import { SearchResult } from './renderers/SearchResult'
import { AgentActivityIndicator } from './renderers/AgentActivityIndicator'
import { ToolErrorCard } from './renderers/ToolErrorCard'
import { isErrorResult } from '@/lib/utils/tool-result'

function safeParseJSON(str: string): Record<string, unknown> | null {
  try {
    return JSON.parse(str)
  } catch {
    return null
  }
}

/** Parse a tool result into a record, returning null for error/empty results. */
function parseResult(result: unknown): Record<string, unknown> | null {
  if (!result) return null
  if (typeof result === 'string') {
    // Check if the string is an error message (not JSON)
    const parsed = safeParseJSON(result)
    if (!parsed) return null
    // Check for error shape in parsed result
    if ('error' in parsed) return null
    return parsed
  }
  if (typeof result === 'object' && result !== null && 'error' in result) return null
  return result as Record<string, unknown>
}

/**
 * Registers CopilotKit tool-call renderers for all 9 backend tools.
 *
 * Uses useRenderToolCall (the correct hook for rendering backend-emitted
 * tool calls) instead of useCopilotAction with available:'disabled'.
 *
 * Must be rendered inside a CopilotKit provider.
 */
export function ToolResultRenderers() {
  // ACM tools - render as structured table/cards
  useRenderToolCall({
    name: 'search_acm_by_risk',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing')
        return <AgentActivityIndicator tool="search_acm_by_risk" status="executing" />
      if (isErrorResult(result))
        return <ToolErrorCard tool="search_acm_by_risk" />
      const data = parseResult(result)
      if (!data) return <></>
      return <ACMTableResult data={data} queryType="Risk Status" />
    },
  })

  useRenderToolCall({
    name: 'search_acm_by_building',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing')
        return <AgentActivityIndicator tool="search_acm_by_building" status="executing" />
      if (isErrorResult(result))
        return <ToolErrorCard tool="search_acm_by_building" />
      const data = parseResult(result)
      if (!data) return <></>
      return <ACMTableResult data={data} queryType="Building" />
    },
  })

  useRenderToolCall({
    name: 'search_acm_by_room',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing')
        return <AgentActivityIndicator tool="search_acm_by_room" status="executing" />
      if (isErrorResult(result))
        return <ToolErrorCard tool="search_acm_by_room" />
      const data = parseResult(result)
      if (!data) return <></>
      return <ACMTableResult data={data} queryType="Room" />
    },
  })

  useRenderToolCall({
    name: 'search_acm_by_product',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing')
        return <AgentActivityIndicator tool="search_acm_by_product" status="executing" />
      if (isErrorResult(result))
        return <ToolErrorCard tool="search_acm_by_product" />
      const data = parseResult(result)
      if (!data) return <></>
      return <ACMTableResult data={data} queryType="Product" />
    },
  })

  useRenderToolCall({
    name: 'get_acm_stats',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing')
        return <AgentActivityIndicator tool="get_acm_stats" status="executing" />
      if (isErrorResult(result))
        return <ToolErrorCard tool="get_acm_stats" />
      const data = parseResult(result)
      if (!data) return <></>
      return <ACMStatsResult data={data} />
    },
  })

  useRenderToolCall({
    name: 'get_acm_record_detail',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing')
        return <AgentActivityIndicator tool="get_acm_record_detail" status="executing" />
      if (isErrorResult(result))
        return <ToolErrorCard tool="get_acm_record_detail" />
      const data = parseResult(result)
      if (!data) return <></>
      return <ACMTableResult data={{ records: [data], total: 1 }} queryType="Detail" />
    },
  })

  useRenderToolCall({
    name: 'list_acm_buildings',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing')
        return <AgentActivityIndicator tool="list_acm_buildings" status="executing" />
      if (isErrorResult(result))
        return <ToolErrorCard tool="list_acm_buildings" />
      const data = parseResult(result)
      if (!data) return <></>
      return <ACMStatsResult data={data} />
    },
  })

  // Document search tools
  useRenderToolCall({
    name: 'search_documents_vector',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing')
        return <AgentActivityIndicator tool="search_documents_vector" status="executing" />
      if (isErrorResult(result))
        return <ToolErrorCard tool="search_documents_vector" />
      const data = parseResult(result)
      if (!data) return <></>
      return <SearchResult data={data} searchType="Vector" />
    },
  })

  useRenderToolCall({
    name: 'search_documents_text',
    render: ({ status, result }) => {
      if (status === 'inProgress' || status === 'executing')
        return <AgentActivityIndicator tool="search_documents_text" status="executing" />
      if (isErrorResult(result))
        return <ToolErrorCard tool="search_documents_text" />
      const data = parseResult(result)
      if (!data) return <></>
      return <SearchResult data={data} searchType="Text" />
    },
  })

  // Fallback renderer for any tool not explicitly handled above
  useDefaultTool({
    render: ({ name, status, result }): React.ReactElement => {
      if (status === 'inProgress' || status === 'executing') {
        return <AgentActivityIndicator tool={name} status="executing" />
      }
      if (isErrorResult(result)) return <ToolErrorCard tool={name} />
      if (!result) return <></>
      return (
        <div className="border rounded-lg p-3 my-1 text-sm bg-muted/30">
          <div className="text-xs font-medium text-muted-foreground mb-1">{name}</div>
          <pre className="text-xs whitespace-pre-wrap overflow-auto max-h-40">
            {typeof result === 'string' ? result : JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )
    },
  })

  return null
}
