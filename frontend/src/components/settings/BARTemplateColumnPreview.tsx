'use client'

import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import type { BARTemplate } from '@/lib/api/bar-templates'

interface BARTemplateColumnPreviewProps {
  template: BARTemplate | null
}

export function BARTemplateColumnPreview({ template }: BARTemplateColumnPreviewProps) {
  if (!template) {
    return (
      <p className="text-sm text-muted-foreground py-4">
        Select a template to preview its column structure.
      </p>
    )
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold">
        {template.filename} — {template.column_count} columns
      </h3>
      <ScrollArea className="h-[400px] border rounded-lg">
        <table className="w-full">
          <thead className="sticky top-0 bg-background">
            <tr className="border-b">
              <th className="text-left p-2 text-xs font-medium text-muted-foreground w-16">Col</th>
              <th className="text-left p-2 text-xs font-medium text-muted-foreground">Name</th>
              <th className="text-left p-2 text-xs font-medium text-muted-foreground w-24">Required</th>
            </tr>
          </thead>
          <tbody>
            {template.columns.map((col) => (
              <tr key={col.column_letter} className="border-b last:border-b-0">
                <td className="p-2 text-sm font-mono text-muted-foreground">{col.column_letter}</td>
                <td className="p-2 text-sm">{col.column_name}</td>
                <td className="p-2">
                  {col.is_required ? (
                    <Badge variant="default" className="text-xs">Required</Badge>
                  ) : (
                    <Badge variant="outline" className="text-xs">Optional</Badge>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </ScrollArea>
    </div>
  )
}
