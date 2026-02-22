'use client'

import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import { DoorOpen } from 'lucide-react'

interface RoomNodeData {
  label: string
  room_id?: string
  area?: string | null
  floor_level?: string | null
  [key: string]: unknown
}

function RoomNodeComponent({ data }: NodeProps) {
  const d = data as RoomNodeData
  return (
    <div className="rounded-lg border-2 border-purple-500 bg-purple-50 dark:bg-purple-950 px-4 py-3 min-w-[160px] shadow-sm">
      <Handle type="target" position={Position.Top} className="!bg-purple-500" />
      <div className="flex items-center gap-2 mb-1">
        <DoorOpen className="h-4 w-4 text-purple-600" />
        <span className="text-xs font-medium text-purple-600 uppercase">Room</span>
      </div>
      <div className="font-semibold text-sm truncate">{d.label}</div>
      {d.floor_level && (
        <div className="text-xs text-muted-foreground">Floor: {d.floor_level}</div>
      )}
      <Handle type="source" position={Position.Bottom} className="!bg-purple-500" />
    </div>
  )
}

export const RoomNode = memo(RoomNodeComponent)
