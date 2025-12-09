# Tech Spec: E7-S5 - Review & Confirm Step

> **Story:** E7-S5
> **Epic:** Upload Wizard
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Create the review step where users can see a summary of all their selections before starting the upload.

---

## User Story

**As a** user
**I want** to review my selections before uploading
**So that** I can catch mistakes

---

## Acceptance Criteria

- [ ] Summary table of all files
- [ ] Document type, notebooks, transformations per file
- [ ] Edit button to go back to specific step
- [ ] Total count and estimated processing time
- [ ] "Start Upload" button with confirmation

---

## Technical Design

### 1. Review Step Component

Create `frontend/src/components/upload/ReviewStep.tsx`:

```tsx
'use client';

import { useMemo } from 'react';
import { useUploadStore } from '@/stores/upload-store';
import { useNotebooks } from '@/hooks/use-notebooks';
import { useWizard } from '@/components/ui/wizard';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatFileSize } from '@/lib/utils/format';
import {
  FileText,
  Shield,
  Image,
  FileQuestion,
  Edit2,
  Clock,
  Folder,
  Wand2,
} from 'lucide-react';

const TYPE_ICONS = {
  acm: Shield,
  general: FileText,
  media: Image,
  other: FileQuestion,
};

export function ReviewStep() {
  const { files, options } = useUploadStore();
  const { data: notebooks } = useNotebooks();
  const { goToStep } = useWizard();

  // Calculate summary stats
  const summary = useMemo(() => {
    const totalSize = files.reduce((sum, f) => sum + f.size, 0);
    const acmCount = files.filter((f) => f.documentType === 'acm').length;

    // Rough time estimate (very approximate)
    let estimatedMinutes = Math.ceil(files.length * 0.5);
    if (options.enableAcmExtraction && acmCount > 0) {
      estimatedMinutes += acmCount * 2;
    }
    if (options.transformations.length > 0) {
      estimatedMinutes += files.length * options.transformations.length * 0.5;
    }

    return {
      totalFiles: files.length,
      totalSize,
      acmCount,
      estimatedMinutes,
    };
  }, [files, options]);

  // Get notebook names
  const selectedNotebooks = notebooks?.filter((n) =>
    options.notebookIds.includes(n.id)
  ) || [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-2">Review & Confirm</h2>
        <p className="text-muted-foreground">
          Review your upload settings before proceeding.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4 text-center">
          <p className="text-3xl font-bold">{summary.totalFiles}</p>
          <p className="text-sm text-muted-foreground">Files</p>
        </Card>
        <Card className="p-4 text-center">
          <p className="text-3xl font-bold">{formatFileSize(summary.totalSize)}</p>
          <p className="text-sm text-muted-foreground">Total Size</p>
        </Card>
        <Card className="p-4 text-center">
          <p className="text-3xl font-bold">{summary.acmCount}</p>
          <p className="text-sm text-muted-foreground">ACM Documents</p>
        </Card>
        <Card className="p-4 text-center">
          <p className="text-3xl font-bold">~{summary.estimatedMinutes}</p>
          <p className="text-sm text-muted-foreground">Est. Minutes</p>
        </Card>
      </div>

      {/* Processing Options Summary */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">Processing Options</h3>
          <Button variant="ghost" size="sm" onClick={() => goToStep(2)}>
            <Edit2 className="w-4 h-4 mr-1" />
            Edit
          </Button>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          {/* ACM Extraction */}
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-blue-600" />
            <span>ACM Extraction:</span>
            <Badge variant={options.enableAcmExtraction ? 'default' : 'secondary'}>
              {options.enableAcmExtraction ? 'Enabled' : 'Disabled'}
            </Badge>
          </div>

          {/* Embeddings */}
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-purple-600" />
            <span>Embeddings:</span>
            <Badge variant={options.enableEmbeddings ? 'default' : 'secondary'}>
              {options.enableEmbeddings ? 'Enabled' : 'Disabled'}
            </Badge>
          </div>

          {/* Transformations */}
          <div className="flex items-start gap-2">
            <Wand2 className="w-5 h-5 text-amber-600 mt-0.5" />
            <span>Transformations:</span>
            <div className="flex flex-wrap gap-1">
              {options.transformations.length > 0 ? (
                options.transformations.map((t) => (
                  <Badge key={t} variant="outline">{t}</Badge>
                ))
              ) : (
                <span className="text-muted-foreground">None</span>
              )}
            </div>
          </div>

          {/* Notebooks */}
          <div className="flex items-start gap-2">
            <Folder className="w-5 h-5 text-green-600 mt-0.5" />
            <span>Notebooks:</span>
            <div className="flex flex-wrap gap-1">
              {selectedNotebooks.length > 0 ? (
                selectedNotebooks.map((n) => (
                  <Badge key={n.id} variant="outline">{n.name}</Badge>
                ))
              ) : (
                <span className="text-muted-foreground">None</span>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Files Table */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">Files ({files.length})</h3>
          <Button variant="ghost" size="sm" onClick={() => goToStep(0)}>
            <Edit2 className="w-4 h-4 mr-1" />
            Edit
          </Button>
        </div>

        <div className="max-h-64 overflow-y-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>File</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Size</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {files.map((file) => {
                const TypeIcon = TYPE_ICONS[file.documentType || 'other'];
                return (
                  <TableRow key={file.id}>
                    <TableCell className="font-medium max-w-xs truncate">
                      {file.name}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-1">
                        <TypeIcon className="w-4 h-4" />
                        <span className="capitalize">{file.documentType || 'other'}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      {formatFileSize(file.size)}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </Card>

      {/* Confirmation Notice */}
      <div className="p-4 bg-muted rounded-lg text-center">
        <p className="text-sm text-muted-foreground">
          Click <strong>Finish</strong> to start uploading {files.length} file(s).
          {options.processingMode === 'async' && (
            <span> Processing will continue in the background.</span>
          )}
        </p>
      </div>
    </div>
  );
}
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/components/upload/ReviewStep.tsx` | New component |

---

## Dependencies

- E7-S2: File Upload Step (file data)
- E7-S3: Document Type Step (type assignments)
- E7-S4: Processing Options Step (options)

---

## Testing

1. Complete previous steps - verify summary shows
2. Verify file count matches
3. Verify total size calculation
4. Verify ACM count for ACM files only
5. Click Edit buttons - verify navigation to correct step
6. Verify all selected options shown
7. Verify files table is scrollable for many files

---

## Estimated Complexity

**Low** - Display component aggregating previous step data

---
