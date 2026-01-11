'use client';

import { useMemo, useState } from 'react';
import { useUploadStore } from '@/lib/stores/upload-store';
import { useNotebooks } from '@/lib/hooks/use-notebooks';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { formatFileSize } from '@/lib/utils';
import {
  FileText,
  Shield,
  Image,
  FileQuestion,
  Edit2,
  Clock,
  FolderOpen,
  Wand2,
  Database,
  AlertCircle,
  FileUp,
} from 'lucide-react';
import type { DocumentType } from './types';

const TYPE_ICONS: Record<DocumentType | 'other', typeof FileText> = {
  acm: Shield,
  general: FileText,
  media: Image,
  other: FileQuestion,
};

const TYPE_COLORS: Record<DocumentType | 'other', string> = {
  acm: 'text-blue-600',
  general: 'text-gray-600',
  media: 'text-purple-600',
  other: 'text-gray-400',
};

interface ReviewStepProps {
  onGoToStep?: (step: number) => void;
  onConfirmChange?: (confirmed: boolean) => void;
}

export function ReviewStep({ onGoToStep, onConfirmChange }: ReviewStepProps) {
  const { files, options } = useUploadStore();
  const { data: notebooks, isLoading: isLoadingNotebooks } = useNotebooks();
  const [confirmed, setConfirmed] = useState(false);

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
      estimatedMinutes: Math.ceil(estimatedMinutes),
    };
  }, [files, options]);

  // Get notebook names for selected notebooks
  const selectedNotebooks = useMemo(() => {
    if (!notebooks) return [];
    return notebooks.filter((n) => options.notebookIds.includes(n.id));
  }, [notebooks, options.notebookIds]);

  // Handler for edit buttons - navigates to specific step
  const handleEdit = (step: number) => {
    if (onGoToStep) {
      onGoToStep(step);
    }
  };

  // Handler for confirmation checkbox
  const handleConfirmChange = (checked: boolean) => {
    setConfirmed(checked);
    if (onConfirmChange) {
      onConfirmChange(checked);
    }
  };

  // Empty state - no files selected
  if (files.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold mb-2">Review & Confirm</h2>
          <p className="text-muted-foreground">
            Review your upload settings before proceeding.
          </p>
        </div>

        <Card className="p-8 text-center">
          <AlertCircle className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Files Selected</h3>
          <p className="text-muted-foreground mb-4">
            You haven&apos;t added any files to upload yet.
          </p>
          <Button onClick={() => handleEdit(1)}>
            <FileUp className="w-4 h-4 mr-2" />
            Add Files
          </Button>
        </Card>
      </div>
    );
  }

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
          <Button variant="ghost" size="sm" onClick={() => handleEdit(3)}>
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
            <Database className="w-5 h-5 text-purple-600" />
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
                  <Badge key={t} variant="outline" className="capitalize">
                    {t}
                  </Badge>
                ))
              ) : (
                <span className="text-muted-foreground">None</span>
              )}
            </div>
          </div>

          {/* Notebooks */}
          <div className="flex items-start gap-2">
            <FolderOpen className="w-5 h-5 text-green-600 mt-0.5" />
            <span>Notebooks:</span>
            <div className="flex flex-wrap gap-1">
              {isLoadingNotebooks ? (
                <span className="text-muted-foreground">Loading...</span>
              ) : selectedNotebooks.length > 0 ? (
                selectedNotebooks.map((n) => (
                  <Badge key={n.id} variant="outline">
                    {n.name}
                  </Badge>
                ))
              ) : (
                <span className="text-muted-foreground">None</span>
              )}
            </div>
          </div>

          {/* Processing Mode */}
          <div className="flex items-center gap-2 md:col-span-2">
            <Clock className="w-5 h-5 text-gray-600" />
            <span>Processing Mode:</span>
            <Badge variant="outline">
              {options.processingMode === 'async' ? 'Background' : 'Immediate'}
            </Badge>
          </div>
        </div>
      </Card>

      {/* Files Table */}
      <Card className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">Files ({files.length})</h3>
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={() => handleEdit(2)}>
              <Edit2 className="w-4 h-4 mr-1" />
              Edit Types
            </Button>
            <Button variant="ghost" size="sm" onClick={() => handleEdit(1)}>
              <Edit2 className="w-4 h-4 mr-1" />
              Edit Files
            </Button>
          </div>
        </div>

        <div className="max-h-64 overflow-y-auto border rounded-lg">
          {/* Table Header */}
          <div className="grid grid-cols-[1fr_auto_auto] gap-4 px-4 py-2 bg-muted font-medium text-sm border-b">
            <div>File</div>
            <div>Type</div>
            <div className="text-right">Size</div>
          </div>

          {/* Table Body */}
          <div className="divide-y">
            {files.map((file) => {
              const docType = file.documentType || 'other';
              const TypeIcon = TYPE_ICONS[docType];
              const iconColor = TYPE_COLORS[docType];

              return (
                <div
                  key={file.id}
                  className="grid grid-cols-[1fr_auto_auto] gap-4 px-4 py-2 text-sm items-center hover:bg-muted/50"
                >
                  <div className="font-medium truncate" title={file.name}>
                    {file.name}
                  </div>
                  <div className="flex items-center gap-1">
                    <TypeIcon className={`w-4 h-4 ${iconColor}`} />
                    <span className="capitalize">{docType}</span>
                  </div>
                  <div className="text-right text-muted-foreground">
                    {formatFileSize(file.size)}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </Card>

      {/* Confirmation Notice */}
      <Card className="p-4 border-primary/20 bg-primary/5">
        <div className="flex items-start gap-3">
          <Checkbox
            id="confirm-upload"
            checked={confirmed}
            onCheckedChange={(checked) => handleConfirmChange(checked === true)}
            className="mt-0.5"
          />
          <div className="flex-1">
            <Label
              htmlFor="confirm-upload"
              className="text-sm font-medium cursor-pointer"
            >
              I have reviewed my selections and am ready to upload
            </Label>
            <p className="text-sm text-muted-foreground mt-1">
              Click <strong>Finish</strong> to start uploading {files.length} file(s).
              {options.processingMode === 'async' && (
                <span> Processing will continue in the background.</span>
              )}
            </p>
          </div>
        </div>
      </Card>
    </div>
  );
}
