'use client'

import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import {
  Building2,
  FileText,
  Layers,
  Brain,
  BookOpen,
} from 'lucide-react'
import type { SourceIntelligence, BuildingMeta, PageTag, Section } from '@/lib/types/intelligence'

interface SourceIntelligencePanelProps {
  data: SourceIntelligence | null | undefined
  isLoading: boolean
}

function confidenceBadge(confidence: number) {
  if (confidence >= 0.9) return <Badge variant="default" className="bg-green-600 text-xs">High</Badge>
  if (confidence >= 0.7) return <Badge variant="secondary" className="bg-yellow-500 text-black text-xs">Med</Badge>
  if (confidence >= 0.4) return <Badge variant="secondary" className="bg-orange-500 text-white text-xs">Low</Badge>
  return <Badge variant="destructive" className="text-xs">Very Low</Badge>
}

function documentTypeBadge(docType?: string | null) {
  if (!docType) return null
  const colorMap: Record<string, string> = {
    SAMP: 'bg-blue-600',
    ARA: 'bg-purple-600',
    Division_5: 'bg-teal-600',
    Unknown: 'bg-gray-500',
  }
  return (
    <Badge className={`${colorMap[docType] || 'bg-gray-500'} text-white text-xs`}>
      {docType}
    </Badge>
  )
}

// --- Document Overview ---

function DocumentOverview({ data }: { data: SourceIntelligence }) {
  const meta = data.document_meta
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold flex items-center gap-2">
        <FileText className="w-4 h-4" />
        Document Overview
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <InfoCard label="Type" value={documentTypeBadge(data.document_type) || 'Unknown'} />
        <InfoCard label="Total Pages" value={data.total_pages ?? '—'} />
        <InfoCard label="Buildings" value={data.total_buildings ?? '—'} />
        <InfoCard
          label="Register Pages"
          value={
            data.register_page_range
              ? `${data.register_page_range.start}–${data.register_page_range.end}`
              : '—'
          }
        />
      </div>
      {meta && (
        <div className="grid grid-cols-2 gap-3 mt-2">
          {meta.consultant_name && <InfoCard label="Consultant" value={meta.consultant_name} />}
          {meta.site_name && <InfoCard label="Site" value={meta.site_name} />}
          {meta.report_date && <InfoCard label="Report Date" value={meta.report_date} />}
          {meta.report_reference && <InfoCard label="Reference" value={meta.report_reference} />}
          {meta.organization && <InfoCard label="Organization" value={meta.organization} />}
          {meta.site_address && <InfoCard label="Address" value={meta.site_address} />}
        </div>
      )}
    </div>
  )
}

function InfoCard({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-md border p-3 space-y-1">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-medium">{typeof value === 'string' || typeof value === 'number' ? value : value}</p>
    </div>
  )
}

// --- Building Inventory ---

function BuildingInventorySection({ data }: { data: SourceIntelligence }) {
  const inventory = data.building_inventory
  if (!inventory?.buildings?.length) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <Building2 className="w-4 h-4" />
          Building Inventory
        </h3>
        <p className="text-sm text-muted-foreground">No buildings detected.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold flex items-center gap-2">
        <Building2 className="w-4 h-4" />
        Building Inventory ({inventory.total_buildings})
      </h3>
      <Accordion type="multiple" className="w-full">
        {inventory.buildings.map((b: BuildingMeta, i: number) => (
          <AccordionItem key={b.building_id || i} value={b.building_id || `building-${i}`}>
            <AccordionTrigger className="text-sm">
              <div className="flex items-center gap-2 text-left">
                <span className="font-medium">{b.building_id}</span>
                {b.name && <span className="text-muted-foreground">— {b.name}</span>}
                {b.year && <Badge variant="outline" className="text-xs ml-1">{b.year}</Badge>}
                <span className="text-xs text-muted-foreground ml-auto mr-2">
                  pp. {b.page_start}{b.page_end ? `–${b.page_end}` : ''}
                </span>
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <div className="space-y-2 pl-2">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-sm">
                  {b.construction && <Detail label="Construction" value={b.construction} />}
                  {b.purpose && <Detail label="Purpose" value={b.purpose} />}
                  {b.area_m2 != null && <Detail label="Area" value={`${b.area_m2} m²`} />}
                  {b.levels != null && <Detail label="Levels" value={b.levels} />}
                  <Detail label="Complexity" value={b.complexity} />
                  {b.acm_item_count_estimate != null && (
                    <Detail label="Est. ACM Items" value={b.acm_item_count_estimate} />
                  )}
                </div>
                {b.rooms.length > 0 && (
                  <div className="mt-2">
                    <p className="text-xs font-medium text-muted-foreground mb-1">
                      Rooms ({b.rooms.length})
                    </p>
                    <div className="rounded border overflow-hidden">
                      <table className="w-full text-xs">
                        <thead className="bg-muted/50">
                          <tr>
                            <th className="text-left px-2 py-1">ID</th>
                            <th className="text-left px-2 py-1">Name</th>
                            <th className="text-right px-2 py-1">Area</th>
                            <th className="text-right px-2 py-1">Page</th>
                          </tr>
                        </thead>
                        <tbody>
                          {b.rooms.map((r, ri) => (
                            <tr key={ri} className="border-t">
                              <td className="px-2 py-1">{r.room_id}</td>
                              <td className="px-2 py-1">{r.name}</td>
                              <td className="px-2 py-1 text-right">
                                {r.area_m2 != null ? `${r.area_m2}` : '—'}
                              </td>
                              <td className="px-2 py-1 text-right">{r.page ?? '—'}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  )
}

function Detail({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <span className="text-xs text-muted-foreground">{label}: </span>
      <span className="text-xs font-medium">{typeof value === 'number' ? String(value) : value}</span>
    </div>
  )
}

// --- Table of Contents ---

function TableOfContents({ data }: { data: SourceIntelligence }) {
  const structure = data.document_structure
  if (!structure?.sections?.length) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <BookOpen className="w-4 h-4" />
          Table of Contents
        </h3>
        <p className="text-sm text-muted-foreground">No sections detected.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold flex items-center gap-2">
        <BookOpen className="w-4 h-4" />
        Table of Contents
      </h3>
      <div className="space-y-1">
        {structure.sections.map((s: Section, i: number) => (
          <div key={i}>
            <div className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-muted/50">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs w-6 h-6 flex items-center justify-center p-0">
                  {s.section_id}
                </Badge>
                <span className="text-sm">{s.title}</span>
              </div>
              <span className="text-xs text-muted-foreground">
                p. {s.page_start}{s.page_end ? `–${s.page_end}` : ''}
              </span>
            </div>
            {s.subsections?.map((sub, si) => (
              <div
                key={si}
                className="flex items-center justify-between py-1 px-2 pl-10 text-muted-foreground hover:bg-muted/50 rounded"
              >
                <span className="text-xs">
                  {sub.subsection_number} {sub.title}
                </span>
                <span className="text-xs">
                  p. {sub.page_start}{sub.page_end ? `–${sub.page_end}` : ''}
                </span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

// --- Page Analysis ---

function PageAnalysis({ data }: { data: SourceIntelligence }) {
  const pageTags = data.page_tags
  if (!pageTags?.pages?.length) {
    return (
      <div className="space-y-3">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <Layers className="w-4 h-4" />
          Page Analysis
        </h3>
        <p className="text-sm text-muted-foreground">No page tags available.</p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold flex items-center gap-2">
        <Layers className="w-4 h-4" />
        Page Analysis ({pageTags.total_pages} pages)
      </h3>
      <ScrollArea className="h-[300px]">
        <div className="rounded border overflow-hidden">
          <table className="w-full text-xs">
            <thead className="bg-muted/50 sticky top-0">
              <tr>
                <th className="text-left px-2 py-1.5">Page</th>
                <th className="text-left px-2 py-1.5">Section</th>
                <th className="text-left px-2 py-1.5">Type</th>
                <th className="text-center px-2 py-1.5">Confidence</th>
                <th className="text-left px-2 py-1.5">Summary</th>
              </tr>
            </thead>
            <tbody>
              {pageTags.pages.map((p: PageTag, i: number) => (
                <tr key={i} className="border-t">
                  <td className="px-2 py-1.5 font-mono">{p.page_number}</td>
                  <td className="px-2 py-1.5">{p.section_title}</td>
                  <td className="px-2 py-1.5">
                    <Badge variant="outline" className="text-xs">
                      {p.page_type.replace('_', ' ')}
                    </Badge>
                  </td>
                  <td className="px-2 py-1.5 text-center">
                    {confidenceBadge(p.confidence)}
                  </td>
                  <td className="px-2 py-1.5 max-w-[200px] truncate text-muted-foreground">
                    {p.content_summary || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </ScrollArea>
    </div>
  )
}

// --- Loading Skeleton ---

function IntelligenceSkeleton() {
  return (
    <div className="space-y-6 p-1">
      <div className="space-y-3">
        <Skeleton className="h-5 w-40" />
        <div className="grid grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-16 rounded-md" />
          ))}
        </div>
      </div>
      <Separator />
      <div className="space-y-3">
        <Skeleton className="h-5 w-36" />
        <Skeleton className="h-10 w-full" />
        <Skeleton className="h-10 w-full" />
      </div>
      <Separator />
      <div className="space-y-3">
        <Skeleton className="h-5 w-32" />
        <Skeleton className="h-40 w-full" />
      </div>
    </div>
  )
}

// --- Empty State ---

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-3 py-12">
      <Brain className="w-10 h-10 text-muted-foreground" />
      <p className="text-sm text-muted-foreground text-center">
        No intelligence data yet.
        <br />
        Run an extraction to analyze this document.
      </p>
    </div>
  )
}

// --- Main Component ---

export function SourceIntelligencePanel({ data, isLoading }: SourceIntelligencePanelProps) {
  if (isLoading) return <IntelligenceSkeleton />
  if (!data) return <EmptyState />

  return (
    <div className="space-y-6 p-1">
      <DocumentOverview data={data} />
      <Separator />
      <BuildingInventorySection data={data} />
      <Separator />
      <TableOfContents data={data} />
      <Separator />
      <PageAnalysis data={data} />
    </div>
  )
}
