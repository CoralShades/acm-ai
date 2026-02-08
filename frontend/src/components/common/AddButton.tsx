'use client'

import { useState } from 'react'
import { Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { AddSourceDialog } from '@/components/sources/AddSourceDialog'

interface AddButtonProps {
  variant?: 'default' | 'outline' | 'ghost'
  size?: 'sm' | 'default' | 'lg'
  className?: string
  iconOnly?: boolean
}

export function AddButton({
  variant = 'default',
  size = 'default',
  className,
  iconOnly = false
}: AddButtonProps) {
  const [sourceDialogOpen, setSourceDialogOpen] = useState(false)

  const handleAddSource = () => {
    setSourceDialogOpen(true)
  }

  return (
    <>
      <Button
        variant={variant}
        size={size}
        className={className}
        onClick={handleAddSource}
      >
        <Plus className="h-4 w-4" />
        {!iconOnly && <span className="ml-2">Add Source</span>}
      </Button>

      <AddSourceDialog
        open={sourceDialogOpen}
        onOpenChange={setSourceDialogOpen}
      />
    </>
  )
}