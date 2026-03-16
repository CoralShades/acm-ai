'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'

interface ACMItemData {
  id?: string
  building_name?: string
  room_name?: string
  product?: string
  material_description?: string
  risk_status?: string
  friable?: string
  sample_result?: string
  material_condition?: string
  location?: string
  [key: string]: unknown
}

interface ItemDetailCardProps {
  data: ACMItemData
}

const RISK_COLORS: Record<string, string> = {
  High: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  Medium: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  Low: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
}

export function ItemDetailCard({ data }: ItemDetailCardProps) {
  const [expanded, setExpanded] = useState(false)

  const riskColor =
    RISK_COLORS[data.risk_status || ''] ||
    'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400'

  const primaryFields = ['building_name', 'room_name', 'product', 'risk_status', 'friable', 'sample_result']
  const extraFields = Object.entries(data).filter(
    ([key, val]) => !primaryFields.includes(key) && key !== 'id' && val != null && val !== ''
  )

  return (
    <div className="border rounded-lg p-3 my-1 text-sm">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="font-medium truncate">
            {data.product || 'Unknown product'}
          </div>
          <div className="text-xs text-muted-foreground">
            {data.building_name || '?'} / {data.room_name || '?'}
          </div>
        </div>
        {data.risk_status && (
          <span className={`text-xs font-medium px-2 py-0.5 rounded shrink-0 ${riskColor}`}>
            {data.risk_status}
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-1 mt-2 text-xs">
        {data.friable && (
          <div>
            <span className="text-muted-foreground">Friable:</span>{' '}
            <span className={data.friable === 'Friable' ? 'text-red-600 dark:text-red-400' : ''}>
              {data.friable}
            </span>
          </div>
        )}
        {data.sample_result && (
          <div>
            <span className="text-muted-foreground">Sample:</span>{' '}
            <span className={data.sample_result === 'Positive' ? 'text-red-600 dark:text-red-400' : ''}>
              {data.sample_result}
            </span>
          </div>
        )}
        {data.material_condition && (
          <div>
            <span className="text-muted-foreground">Condition:</span> {data.material_condition}
          </div>
        )}
        {data.location && (
          <div>
            <span className="text-muted-foreground">Location:</span> {data.location}
          </div>
        )}
      </div>

      {extraFields.length > 0 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground mt-2 transition-colors"
        >
          {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
          {extraFields.length} more fields
        </button>
      )}

      {expanded && (
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 mt-1 text-xs border-t pt-1">
          {extraFields.map(([key, val]) => (
            <div key={key}>
              <span className="text-muted-foreground">{key}:</span>{' '}
              {String(val)}
            </div>
          ))}
        </div>
      )}

      {data.id && (
        <div className="text-xs text-muted-foreground mt-2 font-mono">{data.id}</div>
      )}
    </div>
  )
}
