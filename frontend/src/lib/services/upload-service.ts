/**
 * Upload Service
 * Handles file uploads with real progress tracking and cancellation support
 */

import { UploadFile } from '@/components/upload/types';
import { ProcessingOptions } from '@/lib/stores/upload-store';
import apiClient from '@/lib/api/client';
import { acmApi } from '@/lib/api/acm';
import type { SourceResponse } from '@/lib/types/api';

export interface UploadResult {
  fileId: string;
  success: boolean;
  sourceId?: string;
  error?: string;
  cancelled?: boolean;
}

/**
 * Upload a single file with real progress tracking
 */
export async function uploadFile(
  file: UploadFile,
  options: ProcessingOptions,
  onProgress: (progress: number) => void,
  abortSignal?: AbortSignal
): Promise<UploadResult> {
  // Check if already cancelled
  if (abortSignal?.aborted) {
    return {
      fileId: file.id,
      success: false,
      error: 'Upload cancelled',
      cancelled: true,
    };
  }

  try {
    // Build FormData
    const formData = new FormData();
    formData.append('type', 'upload');
    formData.append('file', file.file);
    formData.append('title', file.title || file.name);
    formData.append('notebooks', JSON.stringify(options.notebookIds));
    formData.append('transformations', JSON.stringify(options.transformations));
    formData.append('embed', String(options.enableEmbeddings));
    formData.append('async_processing', String(options.processingMode === 'async'));
    formData.append('delete_source', 'false');

    // Upload with real progress tracking
    const response = await apiClient.post<SourceResponse>('/sources', formData, {
      signal: abortSignal,
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          // Calculate real progress (0-90% for upload, 90-100% for processing)
          const uploadProgress = Math.round((progressEvent.loaded / progressEvent.total) * 90);
          onProgress(uploadProgress);
        }
      },
    });

    onProgress(95); // Upload complete, now doing post-processing

    // Trigger ACM extraction if enabled and file is ACM type
    if (options.enableAcmExtraction && file.documentType === 'acm' && response.data?.id) {
      try {
        await acmApi.extract(response.data.id);
      } catch (acmError) {
        // Log but don't fail - ACM extraction is secondary
        console.warn('ACM extraction queued but may have issues:', acmError);
      }
    }

    onProgress(100);

    return {
      fileId: file.id,
      success: true,
      sourceId: response.data?.id,
    };
  } catch (error) {
    // Check if this was a cancellation
    if (abortSignal?.aborted || (error instanceof Error && error.name === 'CanceledError')) {
      return {
        fileId: file.id,
        success: false,
        error: 'Upload cancelled',
        cancelled: true,
      };
    }

    onProgress(100);

    let errorMessage = 'Upload failed';
    if (error instanceof Error) {
      errorMessage = error.message;
    } else if (typeof error === 'object' && error !== null) {
      const axiosError = error as { response?: { data?: { detail?: string; message?: string } } };
      errorMessage = axiosError.response?.data?.detail ||
                     axiosError.response?.data?.message ||
                     'Upload failed';
    }

    return {
      fileId: file.id,
      success: false,
      error: errorMessage,
    };
  }
}

/**
 * Upload multiple files sequentially with progress callbacks
 * Returns an abort function to cancel all pending uploads
 */
export function createUploadSession(
  files: UploadFile[],
  options: ProcessingOptions,
  onFileProgress: (fileId: string, progress: number) => void,
  onFileComplete: (result: UploadResult) => void,
  onAllComplete: (results: UploadResult[]) => void
): { start: () => Promise<void>; cancel: () => void } {
  const abortController = new AbortController();
  let isCancelled = false;

  const start = async () => {
    const results: UploadResult[] = [];

    // Upload files sequentially to avoid overwhelming the server
    for (const file of files) {
      // Check if cancelled before starting each file
      if (isCancelled) {
        // Mark remaining files as cancelled
        results.push({
          fileId: file.id,
          success: false,
          error: 'Upload cancelled',
          cancelled: true,
        });
        onFileComplete(results[results.length - 1]);
        continue;
      }

      // Mark file as uploading
      onFileProgress(file.id, 0);

      const result = await uploadFile(
        file,
        options,
        (progress) => onFileProgress(file.id, progress),
        abortController.signal
      );

      results.push(result);
      onFileComplete(result);
    }

    onAllComplete(results);
  };

  const cancel = () => {
    isCancelled = true;
    abortController.abort();
  };

  return { start, cancel };
}

/**
 * Simple upload function for backwards compatibility
 */
export async function uploadFiles(
  files: UploadFile[],
  options: ProcessingOptions,
  onFileProgress: (fileId: string, progress: number) => void,
  onFileComplete: (result: UploadResult) => void
): Promise<UploadResult[]> {
  const results: UploadResult[] = [];

  for (const file of files) {
    onFileProgress(file.id, 0);

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
