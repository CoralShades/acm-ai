'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { Loader2, Square, RefreshCw } from 'lucide-react'
import { toast } from 'sonner'

interface JobControlsProps {
  sourceId: string
  reviewStatus?: string
  onStatusChange?: () => void
}

async function cancelExtraction(sourceId: string): Promise<{ cancelled: boolean; command_id: string }> {
  const res = await fetch(`/api/jobs/${encodeURIComponent(sourceId)}/cancel`, { method: 'POST' })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: 'Cancel failed' }))
    throw new Error(body.detail || `Cancel failed (${res.status})`)
  }
  return res.json()
}

async function restartExtraction(sourceId: string): Promise<{ command_id: string; restarted: boolean }> {
  const res = await fetch(`/api/jobs/${encodeURIComponent(sourceId)}/restart`, { method: 'POST' })
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: 'Restart failed' }))
    throw new Error(body.detail || `Restart failed (${res.status})`)
  }
  return res.json()
}

async function canExtract(sourceId: string): Promise<{ can_extract: boolean; reason: string }> {
  const res = await fetch(`/api/jobs/${encodeURIComponent(sourceId)}/can-extract`)
  if (!res.ok) return { can_extract: true, reason: '' }
  return res.json()
}

export function JobControls({ sourceId, reviewStatus, onStatusChange }: JobControlsProps) {
  const queryClient = useQueryClient()
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false)

  const isExtracting = reviewStatus === 'extracting'

  const invalidateQueries = () => {
    void queryClient.invalidateQueries({ queryKey: ['sources', sourceId] })
    void queryClient.invalidateQueries({ queryKey: ['sources'] })
    void queryClient.invalidateQueries({ queryKey: ['acm-records', sourceId] })
    onStatusChange?.()
  }

  const cancelMutation = useMutation({
    mutationFn: () => cancelExtraction(sourceId),
    onSuccess: () => {
      toast.success('Extraction cancelled')
      invalidateQueries()
    },
    onError: (err: Error) => {
      toast.error(err.message)
    },
  })

  const restartMutation = useMutation({
    mutationFn: async () => {
      const check = await canExtract(sourceId)
      if (!check.can_extract) {
        throw new Error(check.reason || 'Cannot start extraction — one is already running')
      }
      return restartExtraction(sourceId)
    },
    onSuccess: () => {
      toast.success('Extraction restarted')
      invalidateQueries()
    },
    onError: (err: Error) => {
      toast.error(err.message)
    },
  })

  if (isExtracting) {
    return (
      <>
        <Button
          variant="destructive"
          size="sm"
          onClick={() => setCancelDialogOpen(true)}
          disabled={cancelMutation.isPending}
        >
          {cancelMutation.isPending ? (
            <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />
          ) : (
            <Square className="h-3.5 w-3.5 mr-1.5" />
          )}
          Cancel Extraction
        </Button>

        <AlertDialog open={cancelDialogOpen} onOpenChange={setCancelDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Cancel extraction?</AlertDialogTitle>
              <AlertDialogDescription>
                This will stop the current extraction. Any partially extracted records
                may be incomplete. You can restart the extraction later.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Keep Running</AlertDialogCancel>
              <AlertDialogAction
                onClick={() => cancelMutation.mutate()}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                Cancel Extraction
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </>
    )
  }

  // Show restart for failed or completed jobs
  if (reviewStatus === 'failed' || reviewStatus === 'published' || reviewStatus === 'pending_review') {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={() => restartMutation.mutate()}
        disabled={restartMutation.isPending}
      >
        {restartMutation.isPending ? (
          <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />
        ) : (
          <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
        )}
        Re-Extract
      </Button>
    )
  }

  return null
}
