'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { AlertTriangle, Building2, DoorOpen, FileWarning } from 'lucide-react'
import type { ACMStats } from '@/lib/types/acm'

interface ACMStatsCardsProps {
  stats: ACMStats | undefined
  isLoading?: boolean
}

export function ACMStatsCards({ stats, isLoading }: ACMStatsCardsProps) {
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Loading...</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-8 bg-muted animate-pulse rounded" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (!stats) {
    return null
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {/* Total Records */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Records</CardTitle>
          <FileWarning className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.total_records}</div>
          <p className="text-xs text-muted-foreground">ACM items identified</p>
        </CardContent>
      </Card>

      {/* Risk Breakdown */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Risk Status</CardTitle>
          <AlertTriangle className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 flex-wrap">
            <Badge variant="destructive" className="text-xs">
              High: {stats.high_risk_count}
            </Badge>
            <Badge variant="secondary" className="text-xs bg-yellow-100 text-yellow-800 hover:bg-yellow-200">
              Medium: {stats.medium_risk_count}
            </Badge>
            <Badge variant="secondary" className="text-xs bg-green-100 text-green-800 hover:bg-green-200">
              Low: {stats.low_risk_count}
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* Buildings */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Buildings</CardTitle>
          <Building2 className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.building_count}</div>
          <p className="text-xs text-muted-foreground">Unique buildings</p>
        </CardContent>
      </Card>

      {/* Rooms */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Rooms</CardTitle>
          <DoorOpen className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.room_count}</div>
          <p className="text-xs text-muted-foreground">Unique rooms</p>
        </CardContent>
      </Card>
    </div>
  )
}
