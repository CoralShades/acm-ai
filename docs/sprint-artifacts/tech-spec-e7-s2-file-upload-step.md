# Tech Spec: E7-S2 - File Upload Step with Drag & Drop

> **Story:** E7-S2
> **Epic:** Upload Wizard
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Create the first step of the upload wizard with a drag-and-drop file upload zone supporting batch uploads.

---

## User Story

**As a** user
**I want** to drag and drop files or click to browse
**So that** uploading is intuitive

---

## Acceptance Criteria

- [ ] Large drop zone with visual feedback
- [ ] Click to browse fallback
- [ ] File type validation with clear error messages
- [ ] File size validation
- [ ] Preview of selected files with remove option
- [ ] Batch support: up to 50 files
- [ ] Progress indicator per file

---

## Technical Design

### 1. Install react-dropzone

```bash
cd frontend
npm install react-dropzone
```

### 2. File Upload Types

Create `frontend/src/components/upload/types.ts`:

```typescript
export interface UploadFile {
  id: string;
  file: File;
  name: string;
  size: number;
  type: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
  documentType?: 'acm' | 'general' | 'media' | 'other';
}

export const ACCEPTED_FILE_TYPES = {
  'application/pdf': ['.pdf'],
  'application/msword': ['.doc'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
  'audio/*': ['.mp3', '.wav', '.m4a'],
  'video/*': ['.mp4', '.webm', '.mov'],
};

export const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB
export const MAX_FILES = 50;
```

### 3. File Upload Store

Create `frontend/src/stores/upload-store.ts`:

```typescript
import { create } from 'zustand';
import { UploadFile } from '@/components/upload/types';
import { nanoid } from 'nanoid';

interface UploadStore {
  files: UploadFile[];
  addFiles: (files: File[]) => void;
  removeFile: (id: string) => void;
  updateFile: (id: string, updates: Partial<UploadFile>) => void;
  clearFiles: () => void;
  setDocumentType: (id: string, type: UploadFile['documentType']) => void;
}

export const useUploadStore = create<UploadStore>((set) => ({
  files: [],

  addFiles: (newFiles) => {
    const uploadFiles: UploadFile[] = newFiles.map((file) => ({
      id: nanoid(),
      file,
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'pending',
      progress: 0,
    }));

    set((state) => ({
      files: [...state.files, ...uploadFiles].slice(0, MAX_FILES),
    }));
  },

  removeFile: (id) => {
    set((state) => ({
      files: state.files.filter((f) => f.id !== id),
    }));
  },

  updateFile: (id, updates) => {
    set((state) => ({
      files: state.files.map((f) =>
        f.id === id ? { ...f, ...updates } : f
      ),
    }));
  },

  clearFiles: () => set({ files: [] }),

  setDocumentType: (id, type) => {
    set((state) => ({
      files: state.files.map((f) =>
        f.id === id ? { ...f, documentType: type } : f
      ),
    }));
  },
}));
```

### 4. Dropzone Component

Create `frontend/src/components/upload/FileDropzone.tsx`:

```tsx
'use client';

import { useCallback } from 'react';
import { useDropzone, FileRejection } from 'react-dropzone';
import { Upload, FileText, X, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useUploadStore } from '@/stores/upload-store';
import {
  ACCEPTED_FILE_TYPES,
  MAX_FILE_SIZE,
  MAX_FILES,
  UploadFile,
} from './types';
import { cn } from '@/lib/utils';
import { formatFileSize } from '@/lib/utils/format';

export function FileDropzone() {
  const { files, addFiles, removeFile } = useUploadStore();

  const onDrop = useCallback(
    (acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
      // Handle accepted files
      addFiles(acceptedFiles);

      // Handle rejected files - show toast or error
      if (rejectedFiles.length > 0) {
        rejectedFiles.forEach((rejection) => {
          console.error(`File rejected: ${rejection.file.name}`, rejection.errors);
        });
      }
    },
    [addFiles]
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
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
          isDragActive && !isDragReject && 'border-primary bg-primary/5',
          isDragReject && 'border-destructive bg-destructive/5',
          !isDragActive && 'border-muted-foreground/25 hover:border-primary/50',
          files.length >= MAX_FILES && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input {...getInputProps()} />

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

  return (
    <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
      <span className="text-2xl">{getFileIcon(file.type)}</span>

      <div className="flex-1 min-w-0">
        <p className="font-medium truncate">{file.name}</p>
        <p className="text-xs text-muted-foreground">
          {formatFileSize(file.size)}
        </p>
      </div>

      {file.status === 'error' && (
        <AlertCircle className="w-5 h-5 text-destructive" />
      )}

      <Button
        variant="ghost"
        size="sm"
        onClick={onRemove}
        className="h-8 w-8 p-0"
      >
        <X className="w-4 h-4" />
      </Button>
    </div>
  );
}
```

### 5. Format Utility

Create `frontend/src/lib/utils/format.ts`:

```typescript
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/package.json` | Add react-dropzone |
| `frontend/src/components/upload/types.ts` | New - Type definitions |
| `frontend/src/stores/upload-store.ts` | New - Upload state |
| `frontend/src/components/upload/FileDropzone.tsx` | New - Dropzone component |
| `frontend/src/lib/utils/format.ts` | New - Format utilities |

---

## Dependencies

- E7-S1: Wizard Framework (integration)

---

## Testing

1. Drag files onto dropzone - verify visual feedback
2. Drop files - verify they appear in list
3. Click dropzone - verify file browser opens
4. Add invalid file type - verify rejection message
5. Add file over size limit - verify rejection
6. Add 50+ files - verify limit enforced
7. Remove file from list - verify removal
8. Clear all - verify list empties

---

## Estimated Complexity

**Medium** - Third-party integration with state management

---
