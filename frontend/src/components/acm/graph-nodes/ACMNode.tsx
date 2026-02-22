'use client'

import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import { AlertTriangle, ShieldCheck, ShieldAlert } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

interface ACMNodeData {
  label: string
  material?: string
  result?: string
  risk_status?: string | null
  friable?: string | null
  condition?: string | null
  risk_color?: string
  [key: string]: unknown
}

function ACMNodeComponent({ data }: NodeProps) {
  const d = data as ACMNodeData
  const risk = (d.risk_status || '').toLowerCase()
  const borderColor =
    risk === 'high' ? 'border-red-500' :
    risk === 'medium' ? 'border-yellow-500' :
    'border-green-500'
  const bgColor =
    risk === 'high' ? 'bg-red-50 dark:bg-red-950' :
    risk === 'medium' ? 'bg-yellow-50 dark:bg-yellow-950' :
    'bg-green-50 dark:bg-green-950'

  const RiskIcon = risk === 'high' ? ShieldAlert : risk === 'medium' ? AlertTriangle : ShieldCheck
  const iconColor = risk === 'high' ? 'text-red-600' : risk === 'medium' ? 'text-yellow-600' : 'text-green-600'

  return (
    <div className={`rounded-lg border-2 ${borderColor} ${bgColor} px-3 py-2 min-w-[150px] shadow-sm`}>
      <Handle type="target" position={Position.Top} style={{ background: d.risk_color || '#22c55e' }} />
      <div className="flex items-center gap-1.5 mb-1">
        <RiskIcon className={`h-3.5 w-3.5 ${iconColor}`} />
        <span className="text-xs font-medium uppercase" style={{ color: d.risk_color }}>ACM</span>
      </div>
      <div className="font-semibold text-xs truncate">{d.label}</div>
      {d.result && (
        <div className="text-[10px] text-muted-foreground truncate">{d.result}</div>
      )}
      <div className="flex gap-1 mt-1 flex-wrap">
        {d.risk_status && (
          <Badge
            variant={risk === 'high' ? 'destructive' : 'outline'}
            className="text-[9px] px-1 py-0"
          >
            {d.risk_status}
          </Badge>
        )}
        {d.friable && d.friable.toLowerCase() === 'yes' && (
          <Badge variant="secondary" className="text-[9px] px-1 py-0">Friable</Badge>
        )}
      </div>
    </div>
  )
}

export const ACMNode = memo(ACMNodeComponent)
