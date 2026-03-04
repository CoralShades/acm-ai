'use client'

import { use } from 'react'
import Link from 'next/link'
import { AppShell } from '@/components/layout/AppShell'
import { BuildingDetailForm } from '@/components/acm/BuildingDetailForm'
import { useBuildingDetail, useUpdateBuilding } from '@/lib/hooks/useBuildingDetail'
import { useFieldSchema } from '@/lib/hooks/useACMItems'
import { Button } from '@/components/ui/button'
import { ArrowLeft, LayoutGrid } from 'lucide-react'
import type { BuildingRecord } from '@/lib/types/building'

function BuildingDetailContent({
  sourceId,
  buildingId,
}: {
  sourceId: string
  buildingId: string
}) {
  const { data: building, isLoading, isError } = useBuildingDetail(buildingId)
  const { data: schema } = useFieldSchema()
  const updateBuilding = useUpdateBuilding()

  const handleSave = (data: Partial<BuildingRecord>) => {
    if (!building) return
    updateBuilding.mutate({ buildingId: building.id, data })
  }

  if (isLoading) {
    return (
      <AppShell>
        <div className="flex flex-col h-full overflow-hidden">
          <div className="flex items-center gap-3 px-4 py-2 border-b bg-background shrink-0">
            <div className="h-8 w-32 rounded bg-muted animate-pulse" />
            <div className="h-6 w-48 rounded bg-muted animate-pulse" />
          </div>
          <div className="flex-1 p-6 space-y-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="space-y-4">
                <div className="h-4 w-24 rounded bg-muted animate-pulse" />
                <div className="grid grid-cols-2 gap-4">
                  {Array.from({ length: 4 }).map((_, j) => (
                    <div key={j} className="h-16 rounded bg-muted animate-pulse" />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </AppShell>
    )
  }

  if (isError || !building) {
    return (
      <AppShell>
        <div className="flex flex-col h-full overflow-hidden">
          <div className="flex items-center gap-3 px-4 py-2 border-b bg-background shrink-0">
            <Button variant="ghost" size="sm" asChild>
              <Link href={`/source/${sourceId}`}>
                <ArrowLeft className="h-4 w-4 mr-1" />
                Back to Register
              </Link>
            </Button>
          </div>
          <div className="flex-1 flex items-center justify-center">
            <p className="text-sm text-destructive">Failed to load building details.</p>
          </div>
        </div>
      </AppShell>
    )
  }

  const buildingTitle =
    building.building_name ??
    building.building_code ??
    building.internal_id

  return (
    <AppShell>
      <div className="flex flex-col h-full overflow-hidden">
        {/* Top bar */}
        <div className="flex items-center gap-3 px-4 py-2 border-b bg-background shrink-0">
          <Button variant="ghost" size="sm" asChild>
            <Link href={`/source/${sourceId}`}>
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back to Register
            </Link>
          </Button>
          <h1 className="text-lg font-semibold truncate flex-1">{buildingTitle}</h1>
          <span className="text-sm text-muted-foreground font-mono">
            {building.internal_id}
          </span>
          <Button variant="outline" size="sm" asChild>
            <Link href={`/source/${sourceId}?building=${encodeURIComponent(building.id)}`}>
              <LayoutGrid className="h-4 w-4 mr-1" />
              View Items
            </Link>
          </Button>
        </div>

        {/* Form body */}
        <div className="flex-1 overflow-hidden min-h-0">
          <BuildingDetailForm
            building={building}
            sourceId={sourceId}
            schema={schema ?? null}
            onSave={handleSave}
            isSaving={updateBuilding.isPending}
          />
        </div>
      </div>
    </AppShell>
  )
}

/**
 * BuildingDetailPage — Dedicated route for viewing and editing a single building record.
 *
 * URL: /source/[id]/building/[buildingId]
 * Story: E33-S7 Building Detail Page
 */
export default function BuildingDetailPage({
  params,
}: {
  params: Promise<{ id: string; buildingId: string }>
}) {
  const { id: rawSourceId, buildingId: rawBuildingId } = use(params)
  const sourceId = decodeURIComponent(rawSourceId)
  const buildingId = decodeURIComponent(rawBuildingId)

  return <BuildingDetailContent sourceId={sourceId} buildingId={buildingId} />
}
