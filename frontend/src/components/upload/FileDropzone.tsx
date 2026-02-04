'use client';

import { useCallback } from 'react';
import { useDropzone, FileRejection, ErrorCode } from 'react-dropzone';
import { Upload, X, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { useUploadStore } from '@/lib/stores/upload-store';
import { useToast } from '@/lib/hooks/use-toast';
import {
  ACCEPTED_FILE_TYPES,
  MAX_FILE_SIZE,
  MAX_FILES,
  UploadFile,
} from './types';
import { cn, formatFileSize } from '@/lib/utils';

export function FileDropzone() {
  const { files, addFiles, removeFile } = useUploadStore();
  const { toast } = useToast();

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
      // Check for duplicates before adding
      const existingNames = new Set(files.map(f => f.name));
      const uniqueFiles = acceptedFiles.filter(file => {
        if (existingNames.has(file.name)) {
          toast({
            title: 'Duplicate file',
            description: `"${file.name}" is already in the list`,
            variant: 'destructive',
          });
          return false;
        }
        return true;
      });

      // Handle accepted files
      if (uniqueFiles.length > 0) {
        addFiles(uniqueFiles);
      }

      // Handle rejected files with user-visible error messages
      if (rejectedFiles.length > 0) {
        rejectedFiles.forEach((rejection) => {
          const errorMessages = rejection.errors.map(error => {
            switch (error.code) {
              case ErrorCode.FileInvalidType:
                return 'Invalid file type';
              case ErrorCode.FileTooLarge:
                return `File too large (max ${formatFileSize(MAX_FILE_SIZE)})`;
              case ErrorCode.TooManyFiles:
                return `Too many files (max ${MAX_FILES})`;
              default:
                return error.message;
            }
          });

          toast({
            title: `"${rejection.file.name}" rejected`,
            description: errorMessages.join(', '),
            variant: 'destructive',
          });
        });
      }
    },
    [addFiles, files, toast]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: ACCEPTED_FILE_TYPES,
    maxSize: MAX_FILE_SIZE,
    maxFiles: MAX_FILES - files.length,
    disabled: files.length >= MAX_FILES,
  });

  return (
    <div className="space-y-4">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        role="button"
        aria-label={`Drop zone for file upload. ${files.length} of ${MAX_FILES} files selected. Click or drag files here.`}
        tabIndex={0}
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
          isDragActive && !isDragReject && 'border-primary bg-primary/5',
          isDragReject && 'border-destructive bg-destructive/5',
          !isDragActive && 'border-muted-foreground/25 hover:border-primary/50',
          files.length >= MAX_FILES && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input {...getInputProps()} aria-label="File input" />

        <Upload className={cn(
          'w-12 h-12 mx-auto mb-4',
          isDragActive ? 'text-primary' : 'text-muted-foreground'
        )} />

        {isDragActive ? (
          <p className="text-lg font-medium text-primary">Drop files here...</p>
        ) : (
          <>
            <p className="text-lg font-medium">
              Drag & drop files here, or click to browse
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              PDF, Word, images, audio, video up to 100MB each
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              {files.length} of {MAX_FILES} files selected
            </p>
          </>
        )}
      </div>

      {/* File List */}
      {files.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <h3 className="font-medium">Selected Files ({files.length})</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => useUploadStore.getState().clearFiles()}
            >
              Clear All
            </Button>
          </div>

          <div className="max-h-64 overflow-y-auto space-y-2">
            {files.map((file) => (
              <FilePreviewItem
                key={file.id}
                file={file}
                onRemove={() => removeFile(file.id)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function FilePreviewItem({
  file,
  onRemove,
}: {
  file: UploadFile;
  onRemove: () => void;
}) {
  const getFileIcon = (type: string) => {
    if (type.startsWith('image/')) return '🖼️';
    if (type.startsWith('audio/')) return '🎵';
    if (type.startsWith('video/')) return '🎬';
    if (type.includes('pdf')) return '📄';
    return '📁';
  };

  const isUploading = file.status === 'uploading';
  const isSuccess = file.status === 'success';
  const isError = file.status === 'error';

  return (
    <div className="flex flex-col gap-2 p-3 bg-muted/50 rounded-lg">
      <div className="flex items-center gap-3">
        <span className="text-2xl" aria-hidden="true">{getFileIcon(file.type)}</span>

        <div className="flex-1 min-w-0">
          <p className="font-medium truncate">{file.name}</p>
          <p className="text-xs text-muted-foreground">
            {formatFileSize(file.size)}
            {isUploading && ` • ${file.progress}%`}
            {isSuccess && ' • Complete'}
            {isError && file.error && ` • ${file.error}`}
          </p>
        </div>

        {isSuccess && (
          <CheckCircle2 className="w-5 h-5 text-green-500" aria-label="Upload complete" />
        )}

        {isError && (
          <AlertCircle className="w-5 h-5 text-destructive" aria-label="Upload failed" />
        )}

        <Button
          variant="ghost"
          size="sm"
          onClick={onRemove}
          className="h-8 w-8 p-0"
          aria-label={`Remove ${file.name}`}
        >
          <X className="w-4 h-4" />
        </Button>
      </div>

      {/* Progress bar for uploading files */}
      {isUploading && (
        <Progress
          value={file.progress}
          className="h-1.5"
          aria-label={`Upload progress: ${file.progress}%`}
        />
      )}
    </div>
  );
}
