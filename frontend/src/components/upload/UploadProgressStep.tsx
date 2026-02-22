'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useUploadStore } from '@/lib/stores/upload-store';
import { createUploadSession, UploadResult } from '@/lib/services/upload-service';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { formatFileSize } from '@/lib/utils';
import {
  CheckCircle,
  XCircle,
  Loader2,
  ExternalLink,
  RefreshCw,
  Plus,
  FolderOpen,
  AlertCircle,
  StopCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface FileStatus {
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error' | 'cancelled';
  sourceId?: string;
  error?: string;
}

interface UploadProgressStepProps {
  onReset?: () => void;
}

export function UploadProgressStep({ onReset }: UploadProgressStepProps) {
  const router = useRouter();
  const { files, options, clearFiles, resetOptions } = useUploadStore();
  const [fileStatuses, setFileStatuses] = useState<Map<string, FileStatus>>(new Map());
  const [isUploading, setIsUploading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);
  const uploadStarted = useRef(false);
  const cancelUpload = useRef<(() => void) | null>(null);

  // Initialize statuses
  useEffect(() => {
    const initial = new Map<string, FileStatus>();
    files.forEach((file) => {
      initial.set(file.id, { progress: 0, status: 'pending' });
    });
    setFileStatuses(initial);
  }, [files]);

  // Progress callback - wrapped in useCallback for stability
  const handleFileProgress = useCallback((fileId: string, progress: number) => {
    setFileStatuses((prev) => {
      const updated = new Map(prev);
      const current = updated.get(fileId);
      if (current) {
        updated.set(fileId, {
          ...current,
          progress,
          status: progress < 100 ? 'uploading' : current.status,
        });
      }
      return updated;
    });
  }, []);

  // Complete callback - wrapped in useCallback for stability
  const handleFileComplete = useCallback((result: UploadResult) => {
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
  }, []);

  // Start upload on mount (only once)
  useEffect(() => {
    if (files.length === 0 || uploadStarted.current) return;

    uploadStarted.current = true;
    setIsUploading(true);

    const session = createUploadSession(
      files,
      options,
      handleFileProgress,
      handleFileComplete,
      () => {
        setIsUploading(false);
        setIsComplete(true);
        cancelUpload.current = null;
      }
    );

    cancelUpload.current = session.cancel;
    session.start();

    // Cleanup on unmount - cancel any in-progress uploads
    return () => {
      if (cancelUpload.current) {
        cancelUpload.current();
        cancelUpload.current = null;
      }
    };
  }, [files, options, handleFileProgress, handleFileComplete]);

  // Calculate overall progress
  const overallProgress = files.length > 0
    ? Array.from(fileStatuses.values()).reduce((sum, s) => sum + s.progress, 0) / files.length
    : 0;

  const successCount = Array.from(fileStatuses.values()).filter(
    (s) => s.status === 'success'
  ).length;

  const errorCount = Array.from(fileStatuses.values()).filter(
    (s) => s.status === 'error' || s.status === 'cancelled'
  ).length;

  const pendingCount = Array.from(fileStatuses.values()).filter(
    (s) => s.status === 'pending' || s.status === 'uploading'
  ).length;

  // Cancel ongoing uploads
  const handleCancel = () => {
    if (cancelUpload.current) {
      cancelUpload.current();
      // Mark uploading files as cancelled
      setFileStatuses((prev) => {
        const updated = new Map(prev);
        prev.forEach((status, fileId) => {
          if (status.status === 'uploading' || status.status === 'pending') {
            updated.set(fileId, {
              ...status,
              status: 'cancelled',
              error: 'Upload cancelled',
            });
          }
        });
        return updated;
      });
      setIsUploading(false);
      setIsComplete(true);
      cancelUpload.current = null;
    }
  };

  // Retry failed uploads with race condition guard
  const retryFailed = async () => {
    // Guard against double-clicks and concurrent retries
    if (isRetrying || isUploading) return;

    const failedFiles = files.filter((f) => {
      const status = fileStatuses.get(f.id)?.status;
      return status === 'error' || status === 'cancelled';
    });

    if (failedFiles.length === 0) return;

    setIsRetrying(true);

    // Reset failed files to pending
    setFileStatuses((prev) => {
      const updated = new Map(prev);
      failedFiles.forEach((f) => {
        updated.set(f.id, { progress: 0, status: 'pending' });
      });
      return updated;
    });

    setIsComplete(false);
    setIsUploading(true);

    // Create new session for retry
    const session = createUploadSession(
      failedFiles,
      options,
      handleFileProgress,
      handleFileComplete,
      () => {
        setIsUploading(false);
        setIsComplete(true);
        setIsRetrying(false);
        cancelUpload.current = null;
      }
    );

    cancelUpload.current = session.cancel;
    await session.start();
  };

  // Navigate to source detail (if single file) or sources list (if batch)
  const handleDone = useCallback(() => {
    // If only one file was uploaded successfully, navigate to its detail page
    const successEntries = Array.from(fileStatuses.entries()).filter(
      ([, s]) => s.status === 'success' && s.sourceId
    );
    const targetPath = successEntries.length === 1
      ? `/sources/${successEntries[0][1].sourceId}`
      : '/sources';

    clearFiles();
    resetOptions();
    router.push(targetPath);
  }, [fileStatuses, clearFiles, resetOptions, router]);

  // Auto-redirect after successful completion (2s delay)
  const [autoRedirectCountdown, setAutoRedirectCountdown] = useState<number | null>(null);
  useEffect(() => {
    if (!isComplete || errorCount > 0) return;
    setAutoRedirectCountdown(3);
    const interval = setInterval(() => {
      setAutoRedirectCountdown((prev) => {
        if (prev === null || prev <= 1) {
          clearInterval(interval);
          handleDone();
          return null;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [isComplete, errorCount, handleDone]);

  // Reset wizard for more uploads
  const handleUploadMore = () => {
    clearFiles();
    resetOptions();
    if (onReset) {
      onReset();
    } else {
      router.push('/sources');
    }
  };

  // Empty state - no files to upload
  if (files.length === 0 && !isComplete) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold mb-2">Upload Progress</h2>
          <p className="text-muted-foreground">
            No files to upload.
          </p>
        </div>

        <Card className="p-8 text-center">
          <AlertCircle className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Files Selected</h3>
          <p className="text-muted-foreground mb-4">
            Please go back and add files to upload.
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-2">
          {isComplete ? 'Upload Complete' : 'Uploading Files'}
        </h2>
        <p className="text-muted-foreground">
          {isComplete
            ? `${successCount} of ${files.length} file${files.length !== 1 ? 's' : ''} uploaded successfully`
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
          <span className="flex items-center gap-1">
            <CheckCircle className="w-4 h-4 text-green-600" />
            {successCount} completed
          </span>
          {pendingCount > 0 && (
            <span className="flex items-center gap-1">
              <Loader2 className="w-4 h-4 animate-spin" />
              {pendingCount} pending
            </span>
          )}
          {errorCount > 0 && (
            <span className="flex items-center gap-1 text-destructive">
              <XCircle className="w-4 h-4" />
              {errorCount} failed
            </span>
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
                'flex items-center gap-3 p-3 rounded-lg border transition-colors',
                status.status === 'success' && 'bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800',
                status.status === 'error' && 'bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800',
                status.status === 'cancelled' && 'bg-orange-50 dark:bg-orange-950/30 border-orange-200 dark:border-orange-800',
                status.status === 'uploading' && 'bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800',
                status.status === 'pending' && 'bg-muted border-border'
              )}
            >
              {/* Status Icon */}
              <div className="flex-shrink-0">
                {status.status === 'success' && (
                  <CheckCircle className="w-5 h-5 text-green-600" />
                )}
                {status.status === 'error' && (
                  <XCircle className="w-5 h-5 text-red-600" />
                )}
                {status.status === 'cancelled' && (
                  <StopCircle className="w-5 h-5 text-orange-600" />
                )}
                {status.status === 'uploading' && (
                  <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                )}
                {status.status === 'pending' && (
                  <div className="w-5 h-5 rounded-full border-2 border-muted-foreground/30" />
                )}
              </div>

              {/* File Info */}
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate" title={file.name}>
                  {file.name}
                </p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>{formatFileSize(file.size)}</span>
                  {file.documentType && (
                    <>
                      <span>•</span>
                      <span className="capitalize">{file.documentType}</span>
                    </>
                  )}
                </div>
                {status.status === 'uploading' && (
                  <Progress value={status.progress} className="h-1 mt-2" />
                )}
                {status.error && (
                  <p className="text-xs text-destructive mt-1">{status.error}</p>
                )}
              </div>

              {/* View Link for successful uploads */}
              {status.sourceId && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => router.push(`/sources/${status.sourceId}`)}
                  title="View Source"
                >
                  <ExternalLink className="w-4 h-4" />
                </Button>
              )}
            </div>
          );
        })}
      </div>

      {/* Auto-redirect notice */}
      {autoRedirectCountdown !== null && (
        <Card className="p-4 bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800">
          <p className="text-sm text-green-700 dark:text-green-300 text-center">
            Redirecting in {autoRedirectCountdown}s...
          </p>
        </Card>
      )}

      {/* Actions */}
      {isComplete && (
        <Card className="p-4">
          <div className="flex flex-wrap justify-center gap-3">
            {errorCount > 0 && (
              <Button
                variant="outline"
                onClick={retryFailed}
                disabled={isRetrying}
              >
                {isRetrying ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4 mr-2" />
                )}
                {isRetrying ? 'Retrying...' : `Retry Failed (${errorCount})`}
              </Button>
            )}
            <Button variant="outline" onClick={handleUploadMore} disabled={isRetrying}>
              <Plus className="w-4 h-4 mr-2" />
              Upload More
            </Button>
            <Button onClick={handleDone} disabled={isRetrying}>
              <FolderOpen className="w-4 h-4 mr-2" />
              View Sources
            </Button>
          </div>
        </Card>
      )}

      {/* Uploading indicator with Cancel button */}
      {isUploading && (
        <Card className="p-4 bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800">
          <div className="flex items-center justify-between">
            <p className="text-sm text-blue-700 dark:text-blue-300 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              Uploading files... Please don&apos;t close this page.
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={handleCancel}
              className="text-red-600 border-red-300 hover:bg-red-50 dark:hover:bg-red-950/30"
            >
              <StopCircle className="w-4 h-4 mr-1" />
              Cancel
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}
