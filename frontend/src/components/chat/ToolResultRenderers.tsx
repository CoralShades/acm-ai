'use client'

import { useCopilotAction } from '@copilotkit/react-core'
import { ACMTableResult } from './renderers/ACMTableResult'
import { ACMStatsResult } from './renderers/ACMStatsResult'
import { SearchResult } from './renderers/SearchResult'
import { AgentActivityIndicator } from './renderers/AgentActivityIndicator'

function safeParseJSON(str: string): Record<string, unknown> | null {
  try {
    return JSON.parse(str)
  } catch {
    return null
  }
}

/**
 * Registers CopilotKit action renderers for all 9 backend tools.
 * Must be rendered inside a CopilotKit provider.
 */
export function ToolResultRenderers() {
  // ACM tools - render as structured table/cards
  useCopilotAction({
    name: 'search_acm_by_risk',
    description: 'Search ACM records by risk status',
    parameters: [],
    available: 'disabled',
    render: ({ status, result }) => {
      if (status === 'executing')
        return <AgentActivityIndicator tool="search_acm_by_risk" status="executing" />
      const data = typeof result === 'string' ? safeParseJSON(result) : result
      if (!data) return <></>
      return <ACMTableResult data={data} queryType="Risk Status" />
    },
  })

  useCopilotAction({
    name: 'search_acm_by_building',
    description: 'Search ACM records by building',
    parameters: [],
    available: 'disabled',
    render: ({ status, result }) => {
      if (status === 'executing')
        return <AgentActivityIndicator tool="search_acm_by_building" status="executing" />
      const data = typeof result === 'string' ? safeParseJSON(result) : result
      if (!data) return <></>
      return <ACMTableResult data={data} queryType="Building" />
    },
  })

  useCopilotAction({
    name: 'search_acm_by_room',
    description: 'Search ACM records by room',
    parameters: [],
    available: 'disabled',
    render: ({ status, result }) => {
      if (status === 'executing')
        return <AgentActivityIndicator tool="search_acm_by_room" status="executing" />
      const data = typeof result === 'string' ? safeParseJSON(result) : result
      if (!data) return <></>
      return <ACMTableResult data={data} queryType="Room" />
    },
  })

  useCopilotAction({
    name: 'search_acm_by_product',
    description: 'Search ACM records by product/material',
    parameters: [],
    available: 'disabled',
    render: ({ status, result }) => {
      if (status === 'executing')
        return <AgentActivityIndicator tool="search_acm_by_product" status="executing" />
      const data = typeof result === 'string' ? safeParseJSON(result) : result
      if (!data) return <></>
      return <ACMTableResult data={data} queryType="Product" />
    },
  })

  useCopilotAction({
    name: 'get_acm_stats',
    description: 'Get ACM statistics summary',
    parameters: [],
    available: 'disabled',
    render: ({ status, result }) => {
      if (status === 'executing')
        return <AgentActivityIndicator tool="get_acm_stats" status="executing" />
      const data = typeof result === 'string' ? safeParseJSON(result) : result
      if (!data) return <></>
      return <ACMStatsResult data={data} />
    },
  })

  useCopilotAction({
    name: 'get_acm_record_detail',
    description: 'Get detailed ACM record',
    parameters: [],
    available: 'disabled',
    render: ({ status, result }) => {
      if (status === 'executing')
        return <AgentActivityIndicator tool="get_acm_record_detail" status="executing" />
      const data = typeof result === 'string' ? safeParseJSON(result) : result
      if (!data) return <></>
      return <ACMTableResult data={{ records: [data], total: 1 }} queryType="Detail" />
    },
  })

  useCopilotAction({
    name: 'list_acm_buildings',
    description: 'List buildings with ACM data',
    parameters: [],
    available: 'disabled',
    render: ({ status, result }) => {
      if (status === 'executing')
        return <AgentActivityIndicator tool="list_acm_buildings" status="executing" />
      const data = typeof result === 'string' ? safeParseJSON(result) : result
      if (!data) return <></>
      return <ACMStatsResult data={data} />
    },
  })

  // Document search tools
  useCopilotAction({
    name: 'search_documents_vector',
    description: 'Search documents using vector similarity',
    parameters: [],
    available: 'disabled',
    render: ({ status, result }) => {
      if (status === 'executing')
        return <AgentActivityIndicator tool="search_documents_vector" status="executing" />
      const data = typeof result === 'string' ? safeParseJSON(result) : result
      if (!data) return <></>
      return <SearchResult data={data} searchType="Vector" />
    },
  })

  useCopilotAction({
    name: 'search_documents_text',
    description: 'Search documents using full-text search',
    parameters: [],
    available: 'disabled',
    render: ({ status, result }) => {
      if (status === 'executing')
        return <AgentActivityIndicator tool="search_documents_text" status="executing" />
      const data = typeof result === 'string' ? safeParseJSON(result) : result
      if (!data) return <></>
      return <SearchResult data={data} searchType="Text" />
    },
  })

  return null
}
