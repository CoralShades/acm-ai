# Tech Spec: E9-S3 - Document Actions and Bulk Operations

> **Story:** E9-S3
> **Epic:** Document Library Management
> **Status:** Drafted
> **Created:** 2025-12-19

---

## Overview

Implement comprehensive document actions for individual and bulk operations, including view, re-extract, delete, export, archive, and metadata editing. This enables efficient management of large document collections.

---

## User Story

**As a** user
**I want** to perform actions on documents individually and in bulk
**So that** I can efficiently manage my document collection

---

## Acceptance Criteria

- [ ] Individual document actions: View details, Open spreadsheet, Re-extract ACM, Delete
- [ ] Bulk actions: Delete selected, Re-process selected, Export selected
- [ ] Confirmation dialogs for destructive actions
- [ ] Progress feedback for bulk operations
- [ ] Undo capability for recent deletions (soft delete with grace period)
- [ ] Archive functionality (hide without delete)
- [ ] Document metadata editing (rename, add tags/notes)

---

## Technical Design

### 1. Document Actions Component

#### Location: `frontend/src/components/documents/DocumentActions.tsx`

```tsx
import { useState } from "react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import {
  Eye,
  FileSpreadsheet,
  RefreshCw,
  Trash2,
  Download,
  Archive,
  Edit,
  MoreHorizontal,
} from "lucide-react";
import { useDocumentActions } from "@/hooks/useDocumentActions";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { EditDocumentDialog } from "./EditDocumentDialog";

interface DocumentActionsProps {
  document: Document;
  onActionComplete?: () => void;
}

export function DocumentActions({ document, onActionComplete }: DocumentActionsProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showEditDialog, setShowEditDialog] = useState(false);

  const {
    viewDocument,
    openSpreadsheet,
    reExtractAcm,
    deleteDocument,
    downloadOriginal,
    archiveDocument,
    isLoading,
  } = useDocumentActions(document.id, onActionComplete);

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="sm">
            <MoreHorizontal className="w-4 h-4" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={viewDocument}>
            <Eye className="w-4 h-4 mr-2" />
            View Details
          </DropdownMenuItem>

          {document.has_acm_data && (
            <DropdownMenuItem onClick={openSpreadsheet}>
              <FileSpreadsheet className="w-4 h-4 mr-2" />
              Open Spreadsheet
            </DropdownMenuItem>
          )}

          <DropdownMenuItem onClick={() => setShowEditDialog(true)}>
            <Edit className="w-4 h-4 mr-2" />
            Edit Metadata
          </DropdownMenuItem>

          <DropdownMenuSeparator />

          <DropdownMenuItem onClick={reExtractAcm}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Re-extract ACM Data
          </DropdownMenuItem>

          <DropdownMenuItem onClick={downloadOriginal}>
            <Download className="w-4 h-4 mr-2" />
            Download Original
          </DropdownMenuItem>

          <DropdownMenuSeparator />

          <DropdownMenuItem onClick={archiveDocument}>
            <Archive className="w-4 h-4 mr-2" />
            Archive
          </DropdownMenuItem>

          <DropdownMenuItem
            onClick={() => setShowDeleteConfirm(true)}
            className="text-destructive focus:text-destructive"
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={showDeleteConfirm}
        onOpenChange={setShowDeleteConfirm}
        title="Delete Document?"
        description={`Are you sure you want to delete "${document.name}"? This will also delete all associated ACM records. This action can be undone within 30 minutes.`}
        confirmLabel="Delete"
        variant="destructive"
        onConfirm={deleteDocument}
        isLoading={isLoading}
      />

      {/* Edit Metadata Dialog */}
      <EditDocumentDialog
        open={showEditDialog}
        onOpenChange={setShowEditDialog}
        document={document}
        onSave={onActionComplete}
      />
    </>
  );
}
```

### 2. Bulk Actions Component

#### Location: `frontend/src/components/documents/BulkActions.tsx`

```tsx
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Trash2,
  RefreshCw,
  Download,
  Archive,
  X,
} from "lucide-react";
import { useBulkActions } from "@/hooks/useBulkActions";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";

interface BulkActionsProps {
  selectedCount: number;
  selectedIds: string[];
  onClearSelection: () => void;
  onActionComplete: () => void;
}

export function BulkActions({
  selectedCount,
  selectedIds,
  onClearSelection,
  onActionComplete,
}: BulkActionsProps) {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [activeOperation, setActiveOperation] = useState<string | null>(null);

  const {
    bulkDelete,
    bulkReprocess,
    bulkExport,
    bulkArchive,
    progress,
    isLoading,
  } = useBulkActions({
    onComplete: () => {
      setActiveOperation(null);
      onActionComplete();
      onClearSelection();
    },
  });

  const handleBulkDelete = async () => {
    setShowDeleteConfirm(false);
    setActiveOperation("delete");
    await bulkDelete(selectedIds);
  };

  const handleBulkReprocess = async () => {
    setActiveOperation("reprocess");
    await bulkReprocess(selectedIds);
  };

  const handleBulkExport = async () => {
    setActiveOperation("export");
    await bulkExport(selectedIds);
  };

  const handleBulkArchive = async () => {
    setActiveOperation("archive");
    await bulkArchive(selectedIds);
  };

  return (
    <div className="flex items-center gap-4 p-3 bg-muted rounded-lg">
      <Badge variant="secondary">
        {selectedCount} selected
      </Badge>

      {activeOperation && progress !== null ? (
        <div className="flex items-center gap-3 flex-1">
          <span className="text-sm text-muted-foreground capitalize">
            {activeOperation}ing...
          </span>
          <Progress value={progress} className="flex-1 h-2" />
          <span className="text-sm text-muted-foreground">{progress}%</span>
        </div>
      ) : (
        <>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleBulkReprocess}
              disabled={isLoading}
            >
              <RefreshCw className="w-4 h-4 mr-1" />
              Re-process
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleBulkExport}
              disabled={isLoading}
            >
              <Download className="w-4 h-4 mr-1" />
              Export
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={handleBulkArchive}
              disabled={isLoading}
            >
              <Archive className="w-4 h-4 mr-1" />
              Archive
            </Button>

            <Button
              variant="destructive"
              size="sm"
              onClick={() => setShowDeleteConfirm(true)}
              disabled={isLoading}
            >
              <Trash2 className="w-4 h-4 mr-1" />
              Delete
            </Button>
          </div>

          <div className="flex-1" />

          <Button variant="ghost" size="sm" onClick={onClearSelection}>
            <X className="w-4 h-4" />
          </Button>
        </>
      )}

      <ConfirmDialog
        open={showDeleteConfirm}
        onOpenChange={setShowDeleteConfirm}
        title="Delete Selected Documents?"
        description={`Are you sure you want to delete ${selectedCount} documents? This will also delete all associated ACM records. This action can be undone within 30 minutes.`}
        confirmLabel={`Delete ${selectedCount} Documents`}
        variant="destructive"
        onConfirm={handleBulkDelete}
      />
    </div>
  );
}
```

### 3. Bulk Actions Hook

#### Location: `frontend/src/hooks/useBulkActions.ts`

```tsx
import { useState, useCallback } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";

interface UseBulkActionsOptions {
  onComplete?: () => void;
}

export function useBulkActions(options: UseBulkActionsOptions = {}) {
  const [progress, setProgress] = useState<number | null>(null);

  const executeBulkOperation = useCallback(
    async (
      operation: string,
      ids: string[],
      endpoint: string
    ) => {
      setProgress(0);

      try {
        // Process in batches for progress feedback
        const batchSize = 10;
        const totalBatches = Math.ceil(ids.length / batchSize);

        for (let i = 0; i < totalBatches; i++) {
          const batch = ids.slice(i * batchSize, (i + 1) * batchSize);

          await apiClient.post(endpoint, { ids: batch });

          setProgress(Math.round(((i + 1) / totalBatches) * 100));
        }

        toast.success(`Successfully ${operation}d ${ids.length} documents`);
        options.onComplete?.();
      } catch (error) {
        toast.error(`Failed to ${operation} documents`);
        throw error;
      } finally {
        setProgress(null);
      }
    },
    [options]
  );

  const bulkDelete = useCallback(
    (ids: string[]) => executeBulkOperation("delete", ids, "/api/sources/bulk/delete"),
    [executeBulkOperation]
  );

  const bulkReprocess = useCallback(
    (ids: string[]) => executeBulkOperation("reprocess", ids, "/api/sources/bulk/reprocess"),
    [executeBulkOperation]
  );

  const bulkExport = useCallback(
    async (ids: string[]) => {
      setProgress(0);
      try {
        const response = await apiClient.post(
          "/api/sources/bulk/export",
          { ids },
          { responseType: "blob" }
        );

        // Download the file
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement("a");
        link.href = url;
        link.setAttribute("download", `acm-export-${Date.now()}.zip`);
        document.body.appendChild(link);
        link.click();
        link.remove();

        setProgress(100);
        toast.success(`Exported ${ids.length} documents`);
        options.onComplete?.();
      } catch (error) {
        toast.error("Failed to export documents");
      } finally {
        setProgress(null);
      }
    },
    [options]
  );

  const bulkArchive = useCallback(
    (ids: string[]) => executeBulkOperation("archive", ids, "/api/sources/bulk/archive"),
    [executeBulkOperation]
  );

  return {
    bulkDelete,
    bulkReprocess,
    bulkExport,
    bulkArchive,
    progress,
    isLoading: progress !== null,
  };
}
```

### 4. Backend Bulk Operations API

#### Location: `api/routers/source_bulk.py`

```python
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/sources/bulk", tags=["source-bulk"])

class BulkOperationRequest(BaseModel):
    ids: List[str]

class DeletedDocument(BaseModel):
    id: str
    deleted_at: datetime
    expires_at: datetime  # For undo functionality

# Store soft-deleted documents for undo
DELETED_DOCUMENTS: dict[str, DeletedDocument] = {}
UNDO_GRACE_PERIOD = timedelta(minutes=30)

@router.post("/delete")
async def bulk_delete(request: BulkOperationRequest, background_tasks: BackgroundTasks):
    """
    Soft-delete multiple documents with undo capability.
    Documents are permanently deleted after 30 minutes.
    """
    deleted = []
    now = datetime.utcnow()
    expires_at = now + UNDO_GRACE_PERIOD

    for source_id in request.ids:
        # Mark as deleted (soft delete)
        await db.query(f"""
            UPDATE source
            SET deleted_at = time::now(),
                status = 'deleted'
            WHERE id = '{source_id}'
        """)

        DELETED_DOCUMENTS[source_id] = DeletedDocument(
            id=source_id,
            deleted_at=now,
            expires_at=expires_at
        )
        deleted.append(source_id)

    # Schedule permanent deletion
    background_tasks.add_task(
        schedule_permanent_deletion,
        deleted,
        UNDO_GRACE_PERIOD.total_seconds()
    )

    return {"deleted": deleted, "undo_expires_at": expires_at.isoformat()}

@router.post("/undo-delete")
async def undo_delete(request: BulkOperationRequest):
    """Restore soft-deleted documents within grace period."""
    restored = []

    for source_id in request.ids:
        if source_id in DELETED_DOCUMENTS:
            doc = DELETED_DOCUMENTS[source_id]
            if datetime.utcnow() < doc.expires_at:
                await db.query(f"""
                    UPDATE source
                    SET deleted_at = null,
                        status = 'active'
                    WHERE id = '{source_id}'
                """)
                del DELETED_DOCUMENTS[source_id]
                restored.append(source_id)

    return {"restored": restored}

@router.post("/reprocess")
async def bulk_reprocess(request: BulkOperationRequest):
    """Re-process multiple documents."""
    queued = []

    for source_id in request.ids:
        # Queue for reprocessing
        await submit_command("process_source", {
            "source_id": source_id,
            "enable_acm_extraction": True,
            "force_rerun": True
        })
        queued.append(source_id)

    return {"queued": queued}

@router.post("/archive")
async def bulk_archive(request: BulkOperationRequest):
    """Archive multiple documents (hide without delete)."""
    archived = []

    for source_id in request.ids:
        await db.query(f"""
            UPDATE source
            SET archived_at = time::now(),
                status = 'archived'
            WHERE id = '{source_id}'
        """)
        archived.append(source_id)

    return {"archived": archived}

@router.post("/unarchive")
async def bulk_unarchive(request: BulkOperationRequest):
    """Restore archived documents."""
    restored = []

    for source_id in request.ids:
        await db.query(f"""
            UPDATE source
            SET archived_at = null,
                status = 'active'
            WHERE id = '{source_id}'
        """)
        restored.append(source_id)

    return {"restored": restored}

@router.post("/export")
async def bulk_export(request: BulkOperationRequest):
    """Export multiple documents as ZIP with ACM data."""
    import zipfile
    import io

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for source_id in request.ids:
            source = await Source.get(source_id)
            if not source:
                continue

            # Add original file
            if source.file_path:
                zip_file.write(source.file_path, f"{source.title}/{source.filename}")

            # Add ACM data as CSV
            acm_records = await ACMRecord.get_by_source(source_id)
            if acm_records:
                csv_content = generate_acm_csv(acm_records)
                zip_file.writestr(
                    f"{source.title}/acm_data.csv",
                    csv_content
                )

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=acm-export.zip"}
    )

async def schedule_permanent_deletion(ids: List[str], delay_seconds: float):
    """Permanently delete documents after grace period."""
    import asyncio
    await asyncio.sleep(delay_seconds)

    for source_id in ids:
        if source_id in DELETED_DOCUMENTS:
            # Permanently delete
            await db.query(f"DELETE FROM acm_record WHERE source_id = '{source_id}'")
            await db.query(f"DELETE FROM source WHERE id = '{source_id}'")
            del DELETED_DOCUMENTS[source_id]
```

### 5. Edit Document Dialog

#### Location: `frontend/src/components/documents/EditDocumentDialog.tsx`

```tsx
import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { useMutation } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { toast } from "sonner";

interface EditDocumentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  document: Document;
  onSave?: () => void;
}

export function EditDocumentDialog({
  open,
  onOpenChange,
  document,
  onSave,
}: EditDocumentDialogProps) {
  const [name, setName] = useState(document.name);
  const [notes, setNotes] = useState(document.notes || "");
  const [tags, setTags] = useState(document.tags?.join(", ") || "");

  const updateMutation = useMutation({
    mutationFn: async () => {
      await apiClient.patch(`/api/sources/${document.id}`, {
        title: name,
        notes,
        tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
      });
    },
    onSuccess: () => {
      toast.success("Document updated");
      onOpenChange(false);
      onSave?.();
    },
    onError: () => {
      toast.error("Failed to update document");
    },
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit Document</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="tags">Tags (comma-separated)</Label>
            <Input
              id="tags"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="e.g., Building A, 2024 Survey, High Priority"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Notes</Label>
            <Textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add notes about this document..."
              rows={4}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={() => updateMutation.mutate()}
            disabled={updateMutation.isPending}
          >
            Save Changes
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/components/documents/DocumentActions.tsx` | New component |
| `frontend/src/components/documents/BulkActions.tsx` | New component |
| `frontend/src/components/documents/EditDocumentDialog.tsx` | New component |
| `frontend/src/hooks/useDocumentActions.ts` | New hook |
| `frontend/src/hooks/useBulkActions.ts` | New hook |
| `api/routers/source_bulk.py` | New router |
| `api/main.py` | Register bulk router |
| `migrations/add_archive_fields.surql` | Add archive fields to source |

---

## Dependencies

- E9-S1: Document Library View (UI container)
- E1-S4: ACM API Endpoints (for delete cascade)

---

## Testing

1. Test individual actions (view, edit, delete, archive)
2. Test bulk selection and actions
3. Verify delete confirmation dialog
4. Test undo functionality within 30 minutes
5. Verify undo expires after 30 minutes
6. Test bulk export generates valid ZIP
7. Test metadata editing saves correctly
8. Test progress feedback during bulk operations

---

## Estimated Complexity

**Medium-High** - Multiple actions with undo capability

---
