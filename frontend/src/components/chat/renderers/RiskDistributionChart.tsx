'use client'
import { motion } from 'framer-motion'

interface RiskDistributionChartProps {
  high: number
  medium: number
  low: number
  total: number
}

export function RiskDistributionChart({ high, medium, low, total }: RiskDistributionChartProps) {
  if (total === 0) return null
  const highPct = (high / total) * 100
  const medPct = (medium / total) * 100
  const lowPct = (low / total) * 100

  return (
    <div className="space-y-1.5">
      <div className="flex h-5 w-full overflow-hidden rounded-full bg-muted">
        {highPct > 0 && (
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${highPct}%` }}
            transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1] }}
            className="bg-red-500 dark:bg-red-600"
            title={`High: ${high}`}
          />
        )}
        {medPct > 0 && (
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${medPct}%` }}
            transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1], delay: 0.1 }}
            className="bg-amber-500 dark:bg-amber-600"
            title={`Medium: ${medium}`}
          />
        )}
        {lowPct > 0 && (
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${lowPct}%` }}
            transition={{ duration: 0.6, ease: [0.25, 0.1, 0.25, 1], delay: 0.2 }}
            className="bg-green-500 dark:bg-green-600"
            title={`Low: ${low}`}
          />
        )}
      </div>
      <div className="flex gap-3 text-[10px] text-muted-foreground">
        {high > 0 && <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-red-500" />High: {high}</span>}
        {medium > 0 && <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-amber-500" />Medium: {medium}</span>}
        {low > 0 && <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-green-500" />Low: {low}</span>}
      </div>
    </div>
  )
}
