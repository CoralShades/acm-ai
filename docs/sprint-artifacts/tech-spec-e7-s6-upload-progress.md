# Tech Spec: E7-S6 - Upload Progress & Results Step

> **Story:** E7-S6
> **Epic:** Upload Wizard
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Create the final step showing upload progress and results, with options to retry failures or navigate to uploaded sources.

---

## User Story

**As a** user
**I want** to see upload progress and results
**So that** I know what succeeded and failed

---

## Acceptance Criteria

- [ ] Real-time progress per file
- [ ] Overall progress bar
- [ ] Success/failure status per file
- [ ] Error messages for failures
- [ ] Retry failed uploads option
- [ ] "View Source" link for successful uploads
- [ ] "Upload More" or "Done" actions

---

## Technical Design

### 1. Upload Service

Create `frontend/src/lib/services/upload-service.ts`:

```typescript
import { UploadFile } from '@/components/upload/types';
import { ProcessingOptions } from '@/stores/upload-store';

export interface UploadResult {
  fileId: string;
  success: boolean;
  sourceId?: string;
  error?: string;
}

export async function uploadFile(
  file: UploadFile,
  options: ProcessingOptions,
  onProgress: (progress: number) => void
): Promise<UploadResult> {
  const formData = new FormData();
  formData.append('file', file.file);
  formData.append('document_type', file.documentType || 'general');
  formData.append('options', JSON.stringify({
    enable_acm_extraction: options.enableAcmExtraction && file.documentType === 'acm',
    enable_embeddings: options.enableEmbeddings,
    transformations: options.transformations,
    notebook_ids: options.notebookIds,
    processing_mode: options.processingMode,
  }));

  try {
    const response = await fetch('/api/sources/upload', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      return {
        fileId: file.id,
        success: false,
        error: error.message || 'Upload failed',
      };
    }

    const data = await response.json();
    return {
      fileId: file.id,
      success: true,
      sourceId: data.id,
    };
  } catch (error) {
    return {
      fileId: file.id,
      success: false,
      error: error instanceof Error ? error.message : 'Network error',
    };
  }
}

export async function uploadFiles(
  files: UploadFile[],
  options: ProcessingOptions,
  onFileProgress: (fileId: string, progress: number) => void,
  onFileComplete: (result: UploadResult) => void
): Promise<UploadResult[]> {
  const results: UploadResult[] = [];

  // Upload files sequentially to avoid overwhelming the server
  for (const file of files) {
    const result = await uploadFile(
      file,
      options,
      (progress) => onFileProgress(file.id, progress)
    );
    results.push(result);
    onFileComplete(result);
  }

  return results;
}
```

### 2. Upload Progress Component

Create `frontend/src/components/upload/UploadProgressStep.tsx`:

```tsx
'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useUploadStore } from '@/stores/upload-store';
import { uploadFiles, UploadResult } from '@/lib/services/upload-service';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { formatFileSize } from '@/lib/utils/format';
import {
  CheckCircle,
  XCircle,
  Loader2,
  ExternalLink,
  RefreshCw,
  Plus,
  Home,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface FileStatus {
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  sourceId?: string;
  error?: string;
}

export function UploadProgressStep() {
  const router = useRouter();
  const { files, options, clearFiles } = useUploadStore();
  const [fileStatuses, setFileStatuses] = useState<Map<string, FileStatus>>(new Map());
  const [isUploading, setIsUploading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);

  // Initialize statuses
  useEffect(() => {
    const initial = new Map<string, FileStatus>();
    files.forEach((file) => {
      initial.set(file.id, { progress: 0, status: 'pending' });
    });
    setFileStatuses(initial);
  }, [files]);

  // Start upload on mount
  useEffect(() => {
    if (files.length === 0 || isUploading || isComplete) return;

    const startUpload = async () => {
      setIsUploading(true);

      await uploadFiles(
        files,
        options,
        // Progress callback
        (fileId, progress) => {
          setFileStatuses((prev) => {
            const updated = new Map(prev);
            updated.set(fileId, {
              ...updated.get(fileId)!,
              progress,
              status: 'uploading',
            });
            return updated;
          });
        },
        // Complete callback
        (result) => {
          setFileStatuses((prev) => {
            const updated = new Map(prev);
            updated.set(result.fileId, {
              progress: 100,
              status: result.success ? 'success' : 'error',
              sourceId: result.sourceId,
              error: result.error,
            });
            return updated;
          });
        }
      );

      setIsUploading(false);
      setIsComplete(true);
    };

    startUpload();
  }, [files, options, isUploading, isComplete]);

  // Calculate overall progress
  const overallProgress = files.length > 0
    ? Array.from(fileStatuses.values()).reduce((sum, s) => sum + s.progress, 0) / files.length
    : 0;

  const successCount = Array.from(fileStatuses.values()).filter(
    (s) => s.status === 'success'
  ).length;

  const errorCount = Array.from(fileStatuses.values()).filter(
    (s) => s.status === 'error'
  ).length;

  const retryFailed = async () => {
    const failedFiles = files.filter((f) => fileStatuses.get(f.id)?.status === 'error');

    // Reset failed files to pending
    setFileStatuses((prev) => {
      const updated = new Map(prev);
      failedFiles.forEach((f) => {
        updated.set(f.id, { progress: 0, status: 'pending' });
      });
      return updated;
    });

    setIsComplete(false);
  };

  const handleDone = () => {
    clearFiles();
    router.push('/sources');
  };

  const handleUploadMore = () => {
    clearFiles();
    router.push('/sources/new');
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-2">
          {isComplete ? 'Upload Complete' : 'Uploading Files'}
        </h2>
        <p className="text-muted-foreground">
          {isComplete
            ? `${successCount} of ${files.length} files uploaded successfully`
            : 'Please wait while your files are being uploaded...'}
        </p>
      </div>

      {/* Overall Progress */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="font-medium">Overall Progress</span>
          <span className="text-sm text-muted-foreground">
            {Math.round(overallProgress)}%
          </span>
        </div>
        <Progress value={overallProgress} className="h-3" />
        <div className="flex justify-between mt-2 text-sm text-muted-foreground">
          <span>{successCount} completed</span>
          {errorCount > 0 && (
            <span className="text-destructive">{errorCount} failed</span>
          )}
        </div>
      </Card>

      {/* File List */}
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {files.map((file) => {
          const status = fileStatuses.get(file.id);
          if (!status) return null;

          return (
            <div
              key={file.id}
              className={cn(
                'flex items-center gap-3 p-3 rounded-lg',
                status.status === 'success' && 'bg-green-50 dark:bg-green-950',
                status.status === 'error' && 'bg-red-50 dark:bg-red-950',
                status.status === 'uploading' && 'bg-blue-50 dark:bg-blue-950',
                status.status === 'pending' && 'bg-muted'
              )}
            >
              {/* Status Icon */}
              {status.status === 'success' && (
                <CheckCircle className="w-5 h-5 text-green-600" />
              )}
              {status.status === 'error' && (
                <XCircle className="w-5 h-5 text-red-600" />
              )}
              {status.status === 'uploading' && (
                <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
              )}
              {status.status === 'pending' && (
                <div className="w-5 h-5 rounded-full border-2 border-muted-foreground/30" />
              )}

              {/* File Info */}
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{file.name}</p>
                {status.status === 'uploading' && (
                  <Progress value={status.progress} className="h-1 mt-1" />
                )}
                {status.error && (
                  <p className="text-xs text-destructive mt-1">{status.error}</p>
                )}
              </div>

              {/* View Link */}
              {status.sourceId && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => router.push(`/sources/${status.sourceId}`)}
                >
                  <ExternalLink className="w-4 h-4" />
                </Button>
              )}
            </div>
          );
        })}
      </div>

      {/* Actions */}
      {isComplete && (
        <div className="flex justify-center gap-4">
          {errorCount > 0 && (
            <Button variant="outline" onClick={retryFailed}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry Failed ({errorCount})
            </Button>
          )}
          <Button variant="outline" onClick={handleUploadMore}>
            <Plus className="w-4 h-4 mr-2" />
            Upload More
          </Button>
          <Button onClick={handleDone}>
            <Home className="w-4 h-4 mr-2" />
            Done
          </Button>
        </div>
      )}
    </div>
  );
}
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/lib/services/upload-service.ts` | New - Upload logic |
| `frontend/src/components/upload/UploadProgressStep.tsx` | New component |

---

## Dependencies

- E7-S5: Review Step (triggers upload on wizard finish)
- Backend: Source upload endpoint

---

## Testing

1. Start upload - verify progress bars animate
2. Verify overall progress updates
3. Verify per-file status icons change
4. Simulate error - verify error display
5. Click Retry - verify failed files re-upload
6. Click View - verify navigation to source
7. Click Done - verify navigation to sources list
8. Click Upload More - verify wizard resets

---

## Estimated Complexity

**High** - Real-time progress tracking with error handling

---
