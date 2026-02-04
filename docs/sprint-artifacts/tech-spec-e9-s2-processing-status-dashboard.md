# Tech Spec: E9-S2 - Document Processing Status Dashboard

> **Story:** E9-S2
> **Epic:** Document Library Management
> **Status:** Drafted
> **Created:** 2025-12-19

---

## Overview

Create a real-time processing status dashboard that shows the status of all documents being processed, including pending, in-progress, completed, and failed states. This provides visibility into the document processing pipeline and enables users to monitor progress and handle failures.

---

## User Story

**As a** user
**I want** to see real-time processing status for all documents
**So that** I know what's being processed and can identify failures

---

## Acceptance Criteria

- [ ] Processing queue visualization (pending, in-progress, completed, failed)
- [ ] Real-time status updates via polling or WebSocket
- [ ] Progress percentage for documents being processed
- [ ] Estimated time remaining for large documents
- [ ] Error details with actionable messages for failures
- [ ] Retry button for failed documents
- [ ] Cancel button for in-progress documents
- [ ] Processing history log

---

## Technical Design

### 1. Processing Status Component

#### Location: `frontend/src/components/documents/ProcessingStatus.tsx`

```tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useProcessingStatus } from "@/hooks/useProcessingStatus";
import { RefreshCw, X, AlertCircle, CheckCircle, Clock, Loader2 } from "lucide-react";

export function ProcessingStatus() {
  const { jobs, isLoading, retry, cancel, refetch } = useProcessingStatus();

  const statusGroups = {
    inProgress: jobs.filter((j) => j.status === "processing"),
    pending: jobs.filter((j) => j.status === "pending"),
    completed: jobs.filter((j) => j.status === "completed"),
    failed: jobs.filter((j) => j.status === "failed"),
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <StatusCard
          title="In Progress"
          count={statusGroups.inProgress.length}
          icon={<Loader2 className="animate-spin" />}
          color="blue"
        />
        <StatusCard
          title="Pending"
          count={statusGroups.pending.length}
          icon={<Clock />}
          color="gray"
        />
        <StatusCard
          title="Completed"
          count={statusGroups.completed.length}
          icon={<CheckCircle />}
          color="green"
        />
        <StatusCard
          title="Failed"
          count={statusGroups.failed.length}
          icon={<AlertCircle />}
          color="red"
        />
      </div>

      {/* In Progress Queue */}
      {statusGroups.inProgress.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Loader2 className="w-5 h-5 animate-spin text-blue-500" />
              Processing ({statusGroups.inProgress.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {statusGroups.inProgress.map((job) => (
              <ProcessingJobCard
                key={job.id}
                job={job}
                onCancel={() => cancel(job.id)}
              />
            ))}
          </CardContent>
        </Card>
      )}

      {/* Failed Queue */}
      {statusGroups.failed.length > 0 && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <AlertCircle className="w-5 h-5" />
              Failed ({statusGroups.failed.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {statusGroups.failed.map((job) => (
              <FailedJobCard
                key={job.id}
                job={job}
                onRetry={() => retry(job.id)}
              />
            ))}
          </CardContent>
        </Card>
      )}

      {/* Pending Queue */}
      {statusGroups.pending.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-muted-foreground" />
              Pending ({statusGroups.pending.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <PendingJobsList jobs={statusGroups.pending} />
          </CardContent>
        </Card>
      )}

      {/* Recent Completed */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            Recently Completed
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ProcessingHistoryTable jobs={statusGroups.completed.slice(0, 10)} />
        </CardContent>
      </Card>
    </div>
  );
}
```

### 2. Processing Job Card (In Progress)

```tsx
interface ProcessingJobCardProps {
  job: ProcessingJob;
  onCancel: () => void;
}

function ProcessingJobCard({ job, onCancel }: ProcessingJobCardProps) {
  return (
    <div className="flex items-center gap-4 p-4 bg-muted/50 rounded-lg">
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-2">
          <span className="font-medium">{job.document_name}</span>
          <Badge variant="outline">{job.document_type}</Badge>
        </div>
        <div className="space-y-2">
          <Progress value={job.progress} className="h-2" />
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>{job.current_step}</span>
            <span>{job.progress}%</span>
          </div>
          {job.estimated_remaining && (
            <p className="text-xs text-muted-foreground">
              Est. {formatDuration(job.estimated_remaining)} remaining
            </p>
          )}
        </div>
      </div>
      <Button variant="ghost" size="sm" onClick={onCancel}>
        <X className="w-4 h-4" />
      </Button>
    </div>
  );
}
```

### 3. Failed Job Card

```tsx
interface FailedJobCardProps {
  job: ProcessingJob;
  onRetry: () => void;
}

function FailedJobCard({ job, onRetry }: FailedJobCardProps) {
  return (
    <div className="flex items-start gap-4 p-4 bg-destructive/10 rounded-lg border border-destructive/20">
      <AlertCircle className="w-5 h-5 text-destructive mt-0.5" />
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-medium">{job.document_name}</span>
          <Badge variant="destructive">Failed</Badge>
        </div>
        <p className="text-sm text-muted-foreground mb-2">
          {job.error_message}
        </p>
        {job.error_details && (
          <details className="text-xs text-muted-foreground">
            <summary className="cursor-pointer">Show details</summary>
            <pre className="mt-2 p-2 bg-muted rounded overflow-x-auto">
              {job.error_details}
            </pre>
          </details>
        )}
      </div>
      <Button variant="outline" size="sm" onClick={onRetry}>
        <RefreshCw className="w-4 h-4 mr-1" />
        Retry
      </Button>
    </div>
  );
}
```

### 4. Processing Status Hook with Polling

#### Location: `frontend/src/hooks/useProcessingStatus.ts`

```tsx
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";

interface ProcessingJob {
  id: string;
  source_id: string;
  document_name: string;
  document_type: string;
  status: "pending" | "processing" | "completed" | "failed";
  progress: number;
  current_step: string;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  error_details: string | null;
  estimated_remaining: number | null;
}

export function useProcessingStatus() {
  const queryClient = useQueryClient();

  // Poll every 2 seconds for active jobs, 10 seconds otherwise
  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ["processing-status"],
    queryFn: async () => {
      const response = await apiClient.get("/api/processing/status");
      return response.data as ProcessingJob[];
    },
    refetchInterval: (data) => {
      const hasActiveJobs = data?.some(
        (j) => j.status === "processing" || j.status === "pending"
      );
      return hasActiveJobs ? 2000 : 10000;
    },
  });

  const retryMutation = useMutation({
    mutationFn: async (jobId: string) => {
      await apiClient.post(`/api/processing/${jobId}/retry`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["processing-status"] });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: async (jobId: string) => {
      await apiClient.post(`/api/processing/${jobId}/cancel`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["processing-status"] });
    },
  });

  return {
    jobs,
    isLoading,
    retry: retryMutation.mutate,
    cancel: cancelMutation.mutate,
    refetch: () => queryClient.invalidateQueries({ queryKey: ["processing-status"] }),
  };
}
```

### 5. Backend Processing Status API

#### Location: `api/routers/processing.py`

```python
from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/api/processing", tags=["processing"])

class ProcessingJobResponse(BaseModel):
    id: str
    source_id: str
    document_name: str
    document_type: str
    status: str
    progress: int
    current_step: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    error_details: Optional[str]
    estimated_remaining: Optional[int]  # seconds

@router.get("/status")
async def get_processing_status() -> List[ProcessingJobResponse]:
    """Get all processing jobs with their current status."""
    # Get from command queue/status table
    jobs = await db.query("""
        SELECT
            c.id,
            c.source_id,
            s.title as document_name,
            s.document_type,
            c.status,
            c.progress,
            c.current_step,
            c.started_at,
            c.completed_at,
            c.error_message,
            c.error_details
        FROM command_status c
        JOIN source s ON s.id = c.source_id
        WHERE c.command_type = 'process_source'
        ORDER BY c.created_at DESC
        LIMIT 100
    """)

    # Calculate estimated remaining for in-progress jobs
    for job in jobs:
        if job["status"] == "processing" and job["progress"] > 0:
            elapsed = (datetime.utcnow() - job["started_at"]).total_seconds()
            estimated_total = elapsed / (job["progress"] / 100)
            job["estimated_remaining"] = int(estimated_total - elapsed)

    return jobs

@router.post("/{job_id}/retry")
async def retry_job(job_id: str):
    """Retry a failed processing job."""
    job = await db.query(f"SELECT * FROM command_status WHERE id = '{job_id}'")
    if not job:
        raise HTTPException(404, "Job not found")

    if job[0]["status"] != "failed":
        raise HTTPException(400, "Only failed jobs can be retried")

    # Reset status and re-queue
    await db.query(f"""
        UPDATE command_status
        SET status = 'pending', progress = 0, error_message = null, error_details = null
        WHERE id = '{job_id}'
    """)

    # Re-submit to command queue
    await submit_command(job[0]["command_type"], job[0]["payload"])

    return {"status": "queued"}

@router.post("/{job_id}/cancel")
async def cancel_job(job_id: str):
    """Cancel a pending or in-progress job."""
    job = await db.query(f"SELECT * FROM command_status WHERE id = '{job_id}'")
    if not job:
        raise HTTPException(404, "Job not found")

    if job[0]["status"] not in ("pending", "processing"):
        raise HTTPException(400, "Only pending or processing jobs can be cancelled")

    await db.query(f"""
        UPDATE command_status
        SET status = 'cancelled', completed_at = time::now()
        WHERE id = '{job_id}'
    """)

    # Signal cancellation to worker (if in progress)
    await signal_job_cancellation(job_id)

    return {"status": "cancelled"}
```

### 6. Processing Progress Updates in Worker

#### Update: `commands/source_commands.py`

```python
async def handle_process_source(cmd: ProcessSourceCommand):
    job_id = cmd.job_id

    async def update_progress(progress: int, step: str):
        await db.query(f"""
            UPDATE command_status
            SET progress = {progress}, current_step = '{step}'
            WHERE id = '{job_id}'
        """)

    try:
        await update_progress(0, "Starting processing...")

        # Step 1: Parse document
        await update_progress(10, "Parsing document...")
        content = await parse_document(cmd.source_id)

        # Step 2: Extract text
        await update_progress(30, "Extracting text...")
        text = await extract_text(content)

        # Step 3: Run transformations
        await update_progress(50, "Running transformations...")
        for i, transform in enumerate(cmd.transformations):
            progress = 50 + (i / len(cmd.transformations)) * 30
            await update_progress(int(progress), f"Running {transform}...")
            await run_transformation(cmd.source_id, transform)

        # Step 4: ACM extraction (if enabled)
        if cmd.enable_acm_extraction:
            await update_progress(80, "Extracting ACM data...")
            await run_acm_extraction(cmd.source_id)

        # Step 5: Generate embeddings
        await update_progress(90, "Generating embeddings...")
        await generate_embeddings(cmd.source_id)

        await update_progress(100, "Completed")

    except Exception as e:
        await db.query(f"""
            UPDATE command_status
            SET status = 'failed',
                error_message = '{str(e)[:500]}',
                error_details = '{traceback.format_exc()[:2000]}'
            WHERE id = '{job_id}'
        """)
        raise
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/components/documents/ProcessingStatus.tsx` | New component |
| `frontend/src/hooks/useProcessingStatus.ts` | New hook |
| `api/routers/processing.py` | New router |
| `api/main.py` | Register processing router |
| `commands/source_commands.py` | Add progress updates |
| `migrations/add_processing_status.surql` | Add command_status table |

---

## Dependencies

- E1-S5: Source Processing Integration
- E7-S6: Upload Progress & Results (complements this story)

---

## Testing

1. Upload a document and verify status appears
2. Verify progress updates in real-time
3. Test cancel functionality on in-progress job
4. Force a failure and verify error display
5. Test retry on failed job
6. Verify history log shows recent completions
7. Test polling frequency (fast for active, slow for idle)

---

## Estimated Complexity

**Medium-High** - Requires backend progress tracking integration

---
