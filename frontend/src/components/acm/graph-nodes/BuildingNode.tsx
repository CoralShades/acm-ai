'use client'

import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import { Building2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

interface BuildingNodeData {
  label: string
  building_code: string
  year?: string | null
  construction?: string | null
  [key: string]: unknown
}

function BuildingNodeComponent({ data }: NodeProps) {
  const d = data as BuildingNodeData
  return (
    <div className="rounded-lg border-2 border-amber-500 bg-amber-50 dark:bg-amber-950 px-4 py-3 min-w-[180px] shadow-sm">
      <Handle type="target" position={Position.Top} className="!bg-amber-500" />
      <div className="flex items-center gap-2 mb-1">
        <Building2 className="h-4 w-4 text-amber-600" />
        <span className="text-xs font-medium text-amber-600 uppercase">Building</span>
      </div>
      <div className="font-semibold text-sm truncate">{d.label}</div>
      <div className="flex items-center gap-1 mt-1 flex-wrap">
        {d.year && (
          <Badge variant="outline" className="text-[10px]">{d.year}</Badge>
        )}
        {d.construction && (
          <Badge variant="outline" className="text-[10px]">{d.construction}</Badge>
        )}
      </div>
      <Handle type="source" position={Position.Bottom} className="!bg-amber-500" />
    </div>
  )
}

export const BuildingNode = memo(BuildingNodeComponent)
