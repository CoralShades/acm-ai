'use client'

import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import { School } from 'lucide-react'

interface SchoolNodeData {
  label: string
  school_code: string
  source_id?: string
  [key: string]: unknown
}

function SchoolNodeComponent({ data }: NodeProps) {
  const d = data as SchoolNodeData
  return (
    <div className="rounded-lg border-2 border-blue-500 bg-blue-50 dark:bg-blue-950 px-4 py-3 min-w-[180px] shadow-sm">
      <div className="flex items-center gap-2 mb-1">
        <School className="h-4 w-4 text-blue-600" />
        <span className="text-xs font-medium text-blue-600 uppercase">School</span>
      </div>
      <div className="font-semibold text-sm truncate">{d.label}</div>
      <div className="text-xs text-muted-foreground">{d.school_code}</div>
      <Handle type="source" position={Position.Bottom} className="!bg-blue-500" />
    </div>
  )
}

export const SchoolNode = memo(SchoolNodeComponent)
