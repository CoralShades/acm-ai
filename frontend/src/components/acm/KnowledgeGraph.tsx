'use client'

import { useState, useCallback, useRef } from 'react'
import {
  ReactFlow,
  Controls,
  MiniMap,
  Background,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  Panel,
  type ReactFlowInstance,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { useQuery } from '@tanstack/react-query'
import { graphNodeTypes } from './graph-nodes'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Download, RefreshCw, ZoomIn } from 'lucide-react'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import apiClient from '@/lib/api/client'

interface GraphData {
  nodes: Node[]
  edges: Edge[]
}

interface GraphStats {
  school_count: number
  building_count: number
  room_count: number
  acm_count: number
  high_risk_count: number
  medium_risk_count: number
  low_risk_count: number
}

interface KnowledgeGraphProps {
  sourceId: string
}

export function KnowledgeGraph({ sourceId }: KnowledgeGraphProps) {
  const [riskFilter, setRiskFilter] = useState<string>('')
  const reactFlowRef = useRef<ReactFlowInstance | null>(null)

  const { data: graphData, isLoading, refetch } = useQuery({
    queryKey: ['graph', 'source', sourceId, riskFilter],
    queryFn: async () => {
      const params = riskFilter ? { risk_filter: riskFilter } : {}
      const res = await apiClient.get<GraphData>(`/graph/source/${encodeURIComponent(sourceId)}`, { params })
      return res.data
    },
    enabled: !!sourceId,
    staleTime: 60 * 1000,
  })

  const { data: stats } = useQuery({
    queryKey: ['graph', 'stats', sourceId],
    queryFn: async () => {
      const res = await apiClient.get<GraphStats>(`/graph/stats/${encodeURIComponent(sourceId)}`)
      return res.data
    },
    enabled: !!sourceId,
    staleTime: 60 * 1000,
  })

  const [nodes, setNodes, onNodesChange] = useNodesState(graphData?.nodes || [])
  const [edges, setEdges, onEdgesChange] = useEdgesState(graphData?.edges || [])

  // Update nodes/edges when data changes
  const prevDataRef = useRef<GraphData | null>(null)
  if (graphData && graphData !== prevDataRef.current) {
    prevDataRef.current = graphData
    setNodes(graphData.nodes)
    setEdges(graphData.edges)
  }

  const onInit = useCallback((instance: ReactFlowInstance) => {
    reactFlowRef.current = instance
    instance.fitView({ padding: 0.2 })
  }, [])

  const handleExport = useCallback(() => {
    if (!graphData) return
    const blob = new Blob([JSON.stringify(graphData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `knowledge-graph-${sourceId}.json`
    a.click()
    URL.revokeObjectURL(url)
  }, [graphData, sourceId])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!graphData || (graphData.nodes.length === 0 && graphData.edges.length === 0)) {
    return (
      <div className="flex flex-col items-center justify-center h-full min-h-[400px] text-muted-foreground gap-2">
        <ZoomIn className="h-8 w-8" />
        <p className="text-sm">No graph data available for this source.</p>
        <p className="text-xs">ACM records need to be extracted first.</p>
      </div>
    )
  }

  return (
    <div className="h-full min-h-[500px] w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={graphNodeTypes}
        onInit={onInit}
        fitView
        minZoom={0.1}
        maxZoom={2}
        defaultEdgeOptions={{
          type: 'smoothstep',
          animated: false,
        }}
      >
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            switch (node.type) {
              case 'school': return '#3b82f6'
              case 'building': return '#f59e0b'
              case 'room': return '#a855f7'
              case 'acm': return (node.data?.risk_color as string) || '#22c55e'
              default: return '#6b7280'
            }
          }}
          className="!bg-background/80"
        />
        <Background gap={20} size={1} />

        {/* Top-right controls panel */}
        <Panel position="top-right" className="flex items-center gap-2">
          {stats && (
            <div className="flex gap-1 bg-background/90 rounded-md p-1.5 border shadow-sm">
              <Badge variant="outline" className="text-[10px]">{stats.school_count} Schools</Badge>
              <Badge variant="outline" className="text-[10px]">{stats.building_count} Buildings</Badge>
              <Badge variant="outline" className="text-[10px]">{stats.room_count} Rooms</Badge>
              <Badge variant="outline" className="text-[10px]">{stats.acm_count} ACMs</Badge>
              {stats.high_risk_count > 0 && (
                <Badge variant="destructive" className="text-[10px]">{stats.high_risk_count} High Risk</Badge>
              )}
            </div>
          )}
          <div className="flex gap-1 bg-background/90 rounded-md p-1 border shadow-sm">
            <Select value={riskFilter || 'all'} onValueChange={(v) => setRiskFilter(v === 'all' ? '' : v)}>
              <SelectTrigger className="h-7 text-xs w-[120px]">
                <SelectValue placeholder="All risks" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All risks</SelectItem>
                <SelectItem value="high">High risk</SelectItem>
                <SelectItem value="medium">Medium risk</SelectItem>
                <SelectItem value="low">Low risk</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => refetch()}>
              <RefreshCw className="h-3.5 w-3.5" />
            </Button>
            <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={handleExport}>
              <Download className="h-3.5 w-3.5" />
            </Button>
          </div>
        </Panel>
      </ReactFlow>
    </div>
  )
}
