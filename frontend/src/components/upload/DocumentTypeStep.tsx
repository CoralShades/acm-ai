'use client';

import { useEffect, useMemo, useState, useRef } from 'react';
import { useUploadStore } from '@/lib/stores/upload-store';
import {
  detectAllDocumentTypes,
  DocumentType,
  DetectionResult,
  DOCUMENT_TYPE_CONFIG,
} from '@/lib/utils/document-detection';
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
import { FileText, Image, FileQuestion, Shield } from 'lucide-react';
import { cn } from '@/lib/utils';

const TYPE_ICONS: Record<DocumentType, React.ElementType> = {
  acm: Shield,
  general: FileText,
  media: Image,
  other: FileQuestion,
};

export function DocumentTypeStep() {
  const { files, setDocumentType } = useUploadStore();
  const [detections, setDetections] = useState<Map<string, DetectionResult>>(
    new Map()
  );
  // Track which files have been processed to prevent infinite loops
  const processedFileIds = useRef<Set<string>>(new Set());

  // Detect types on mount and when new files are added
  useEffect(() => {
    // Find files that haven't been processed yet
    const unprocessedFiles = files.filter(
      (f) => !processedFileIds.current.has(f.id)
    );

    if (unprocessedFiles.length === 0) return;

    const results = detectAllDocumentTypes(files);
    setDetections(results);

    // Apply detected types only to unprocessed files
    unprocessedFiles.forEach((file) => {
      const result = results.get(file.id);
      if (result) {
        setDocumentType(file.id, result.type);
        processedFileIds.current.add(file.id);
      }
    });

    // Clean up processed IDs for removed files
    const currentFileIds = new Set(files.map((f) => f.id));
    processedFileIds.current.forEach((id) => {
      if (!currentFileIds.has(id)) {
        processedFileIds.current.delete(id);
      }
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
      const type =
        file.documentType || detections.get(file.id)?.type || 'other';
      groups[type].push(file);
    });

    return groups;
  }, [files, detections]);

  const handleTypeChange = (fileId: string, type: DocumentType) => {
    setDocumentType(fileId, type);
  };

  const applyTypeToAll = (type: DocumentType) => {
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
        {(Object.entries(DOCUMENT_TYPE_CONFIG) as [DocumentType, typeof DOCUMENT_TYPE_CONFIG.acm][]).map(
          ([type, config]) => {
            const count = groupedFiles[type].length;
            const Icon = TYPE_ICONS[type];

            return (
              <Card
                key={type}
                className={cn(
                  'p-4 text-center',
                  count > 0 ? 'border-primary' : 'opacity-50'
                )}
              >
                <Icon
                  className={cn('w-8 h-8 mx-auto mb-2', config.color)}
                />
                <p className="font-medium text-sm">{config.label}</p>
                <p className="text-2xl font-bold">{count}</p>
              </Card>
            );
          }
        )}
      </div>

      {/* File List by Type */}
      {(Object.entries(groupedFiles) as [DocumentType, typeof files][]).map(
        ([type, typeFiles]) => {
          if (typeFiles.length === 0) return null;
          const config = DOCUMENT_TYPE_CONFIG[type];
          const Icon = TYPE_ICONS[type];

          return (
            <div key={type} className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="font-medium flex items-center gap-2">
                  <Icon className={cn('w-5 h-5', config.color)} />
                  {config.label} ({typeFiles.length})
                </h3>
                {typeFiles.length > 1 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => applyTypeToAll(type)}
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
                                detection.confidence === 'high' &&
                                  'border-green-500 text-green-600',
                                detection.confidence === 'medium' &&
                                  'border-yellow-500 text-yellow-600',
                                detection.confidence === 'low' &&
                                  'border-red-500 text-red-600'
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
                        onValueChange={(v) =>
                          handleTypeChange(file.id, v as DocumentType)
                        }
                      >
                        <SelectTrigger className="w-48">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {(Object.entries(DOCUMENT_TYPE_CONFIG) as [DocumentType, typeof DOCUMENT_TYPE_CONFIG.acm][]).map(
                            ([t, c]) => {
                              const TypeIcon = TYPE_ICONS[t];
                              return (
                                <SelectItem key={t} value={t}>
                                  <span className="flex items-center gap-2">
                                    <TypeIcon className="w-4 h-4" />
                                    {c.label}
                                  </span>
                                </SelectItem>
                              );
                            }
                          )}
                        </SelectContent>
                      </Select>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        }
      )}

      {files.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          No files selected. Go back to upload files.
        </div>
      )}
    </div>
  );
}
