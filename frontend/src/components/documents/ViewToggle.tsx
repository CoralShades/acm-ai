'use client'

import { LayoutGrid, List, Table } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ViewToggleProps {
  view: 'grid' | 'list' | 'table'
  onChange: (view: 'grid' | 'list' | 'table') => void
}

export function ViewToggle({ view, onChange }: ViewToggleProps) {
  return (
    <div className="flex items-center border rounded-lg p-1">
      <Button
        variant={view === 'grid' ? 'secondary' : 'ghost'}
        size="sm"
        onClick={() => onChange('grid')}
        className="px-2"
        aria-label="Grid view"
      >
        <LayoutGrid className="w-4 h-4" />
      </Button>
      <Button
        variant={view === 'list' ? 'secondary' : 'ghost'}
        size="sm"
        onClick={() => onChange('list')}
        className="px-2"
        aria-label="List view"
      >
        <List className="w-4 h-4" />
      </Button>
      <Button
        variant={view === 'table' ? 'secondary' : 'ghost'}
        size="sm"
        onClick={() => onChange('table')}
        className="px-2"
        aria-label="Table view"
      >
        <Table className="w-4 h-4" />
      </Button>
    </div>
  )
}
