# Tech Spec: E7-S3 - Document Type Detection Step

> **Story:** E7-S3
> **Epic:** Upload Wizard
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Create the document type detection step that automatically classifies uploaded documents and allows manual override.

---

## User Story

**As a** user
**I want** the system to detect document types automatically
**So that** I don't have to classify them manually

---

## Acceptance Criteria

- [ ] Auto-detect document type from filename/content
- [ ] Types: SAMP/ACM Register, General Document, Media, Other
- [ ] Manual override option per file
- [ ] Batch classification (apply to all similar)
- [ ] Visual cards showing detected type with confidence

---

## Technical Design

### 1. Document Type Detection

Create `frontend/src/lib/utils/document-detection.ts`:

```typescript
import { UploadFile } from '@/components/upload/types';

export type DocumentType = 'acm' | 'general' | 'media' | 'other';

export interface DetectionResult {
  type: DocumentType;
  confidence: 'high' | 'medium' | 'low';
  reason: string;
}

// Filename patterns that indicate ACM/SAMP documents
const ACM_PATTERNS = [
  /acm/i,
  /samp/i,
  /asbestos/i,
  /register/i,
  /survey/i,
  /management\s*plan/i,
];

// File type to document type mapping
const MEDIA_TYPES = ['image/', 'audio/', 'video/'];

export function detectDocumentType(file: UploadFile): DetectionResult {
  const { name, type } = file;
  const nameLower = name.toLowerCase();

  // Check for media files first
  if (MEDIA_TYPES.some((t) => type.startsWith(t))) {
    return {
      type: 'media',
      confidence: 'high',
      reason: 'Media file detected',
    };
  }

  // Check for ACM/SAMP patterns in filename
  for (const pattern of ACM_PATTERNS) {
    if (pattern.test(nameLower)) {
      return {
        type: 'acm',
        confidence: 'high',
        reason: `Filename contains "${pattern.source.replace(/\\s\*|\\/gi, ' ')}"`,
      };
    }
  }

  // PDF files without ACM patterns
  if (type === 'application/pdf') {
    return {
      type: 'general',
      confidence: 'medium',
      reason: 'PDF document',
    };
  }

  // Word documents
  if (type.includes('word') || type.includes('document')) {
    return {
      type: 'general',
      confidence: 'medium',
      reason: 'Word document',
    };
  }

  // Default
  return {
    type: 'other',
    confidence: 'low',
    reason: 'Unknown file type',
  };
}

export function detectAllDocumentTypes(
  files: UploadFile[]
): Map<string, DetectionResult> {
  const results = new Map<string, DetectionResult>();
  files.forEach((file) => {
    results.set(file.id, detectDocumentType(file));
  });
  return results;
}
```

### 2. Document Type Step Component

Create `frontend/src/components/upload/DocumentTypeStep.tsx`:

```tsx
'use client';

import { useEffect, useMemo, useState } from 'react';
import { useUploadStore } from '@/stores/upload-store';
import { detectAllDocumentTypes, DocumentType, DetectionResult } from '@/lib/utils/document-detection';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { FileText, Image, Music, FileQuestion, Shield } from 'lucide-react';
import { cn } from '@/lib/utils';

const TYPE_CONFIG: Record<DocumentType, {
  label: string;
  icon: React.ElementType;
  description: string;
  color: string;
}> = {
  acm: {
    label: 'ACM/SAMP Document',
    icon: Shield,
    description: 'Asbestos register or management plan',
    color: 'text-blue-600 bg-blue-100',
  },
  general: {
    label: 'General Document',
    icon: FileText,
    description: 'Standard document for text extraction',
    color: 'text-gray-600 bg-gray-100',
  },
  media: {
    label: 'Media File',
    icon: Image,
    description: 'Image, audio, or video file',
    color: 'text-purple-600 bg-purple-100',
  },
  other: {
    label: 'Other',
    icon: FileQuestion,
    description: 'Unclassified file type',
    color: 'text-orange-600 bg-orange-100',
  },
};

export function DocumentTypeStep() {
  const { files, setDocumentType } = useUploadStore();
  const [detections, setDetections] = useState<Map<string, DetectionResult>>(new Map());

  // Detect types on mount
  useEffect(() => {
    const results = detectAllDocumentTypes(files);
    setDetections(results);

    // Apply detected types
    results.forEach((result, fileId) => {
      setDocumentType(fileId, result.type);
    });
  }, [files, setDocumentType]);

  // Group files by detected type
  const groupedFiles = useMemo(() => {
    const groups: Record<DocumentType, typeof files> = {
      acm: [],
      general: [],
      media: [],
      other: [],
    };

    files.forEach((file) => {
      const type = file.documentType || detections.get(file.id)?.type || 'other';
      groups[type].push(file);
    });

    return groups;
  }, [files, detections]);

  const handleTypeChange = (fileId: string, type: DocumentType) => {
    setDocumentType(fileId, type);
  };

  const applyToAll = (type: DocumentType) => {
    files.forEach((file) => {
      setDocumentType(file.id, type);
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-2">Document Classification</h2>
        <p className="text-muted-foreground">
          Review detected document types. You can change the type for any file.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Object.entries(TYPE_CONFIG).map(([type, config]) => {
          const count = groupedFiles[type as DocumentType].length;
          const Icon = config.icon;

          return (
            <Card
              key={type}
              className={cn(
                'p-4 text-center',
                count > 0 ? 'border-primary' : 'opacity-50'
              )}
            >
              <Icon className={cn('w-8 h-8 mx-auto mb-2', config.color.split(' ')[0])} />
              <p className="font-medium">{config.label}</p>
              <p className="text-2xl font-bold">{count}</p>
            </Card>
          );
        })}
      </div>

      {/* File List by Type */}
      {Object.entries(groupedFiles).map(([type, typeFiles]) => {
        if (typeFiles.length === 0) return null;
        const config = TYPE_CONFIG[type as DocumentType];

        return (
          <div key={type} className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-medium flex items-center gap-2">
                <config.icon className={cn('w-5 h-5', config.color.split(' ')[0])} />
                {config.label} ({typeFiles.length})
              </h3>
              {typeFiles.length > 1 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => applyToAll(type as DocumentType)}
                >
                  Apply to all files
                </Button>
              )}
            </div>

            <div className="space-y-2">
              {typeFiles.map((file) => {
                const detection = detections.get(file.id);

                return (
                  <div
                    key={file.id}
                    className="flex items-center gap-4 p-3 bg-muted/50 rounded-lg"
                  >
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{file.name}</p>
                      {detection && (
                        <div className="flex items-center gap-2 mt-1">
                          <Badge
                            variant="outline"
                            className={cn(
                              'text-xs',
                              detection.confidence === 'high' && 'border-green-500',
                              detection.confidence === 'medium' && 'border-yellow-500',
                              detection.confidence === 'low' && 'border-red-500'
                            )}
                          >
                            {detection.confidence} confidence
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {detection.reason}
                          </span>
                        </div>
                      )}
                    </div>

                    <Select
                      value={file.documentType || type}
                      onValueChange={(v) => handleTypeChange(file.id, v as DocumentType)}
                    >
                      <SelectTrigger className="w-48">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {Object.entries(TYPE_CONFIG).map(([t, c]) => (
                          <SelectItem key={t} value={t}>
                            <span className="flex items-center gap-2">
                              <c.icon className="w-4 h-4" />
                              {c.label}
                            </span>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}
    </div>
  );
}
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/lib/utils/document-detection.ts` | New - Detection logic |
| `frontend/src/components/upload/DocumentTypeStep.tsx` | New - Step component |

---

## Dependencies

- E7-S1: Wizard Framework
- E7-S2: File Upload Step (provides files)

---

## Testing

1. Upload file with "ACM" in name - verify detected as ACM
2. Upload file with "SAMP" in name - verify detected as ACM
3. Upload image - verify detected as Media
4. Upload generic PDF - verify detected as General
5. Change type via dropdown - verify update
6. Click "Apply to all" - verify batch update
7. Verify confidence badges display correctly

---

## Estimated Complexity

**Medium** - Pattern matching with UI for batch operations

---
