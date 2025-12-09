# Tech Spec: E7-S4 - Processing Options Step

> **Story:** E7-S4
> **Epic:** Upload Wizard
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Create the processing options step where users configure how their documents should be processed.

---

## User Story

**As a** user
**I want** to configure how documents are processed
**So that** I get the right output for each type

---

## Acceptance Criteria

- [ ] ACM Documents: Enable ACM extraction toggle (default ON)
- [ ] All Documents: Embedding option
- [ ] Transformation selection (multi-select)
- [ ] Notebook assignment (multi-select)
- [ ] Processing mode: Sync vs Async

---

## Technical Design

### 1. Processing Options Store

Extend `frontend/src/stores/upload-store.ts`:

```typescript
export interface ProcessingOptions {
  enableAcmExtraction: boolean;
  enableEmbeddings: boolean;
  transformations: string[];
  notebookIds: string[];
  processingMode: 'sync' | 'async';
}

interface UploadStore {
  // ... existing fields
  options: ProcessingOptions;
  setOptions: (options: Partial<ProcessingOptions>) => void;
}

export const useUploadStore = create<UploadStore>((set) => ({
  // ... existing state
  options: {
    enableAcmExtraction: true,
    enableEmbeddings: true,
    transformations: [],
    notebookIds: [],
    processingMode: 'async',
  },

  setOptions: (updates) => {
    set((state) => ({
      options: { ...state.options, ...updates },
    }));
  },
}));
```

### 2. Processing Options Component

Create `frontend/src/components/upload/ProcessingOptionsStep.tsx`:

```tsx
'use client';

import { useUploadStore } from '@/stores/upload-store';
import { useNotebooks } from '@/hooks/use-notebooks';
import { Card } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import {
  Shield,
  Database,
  Wand2,
  FolderOpen,
  Zap,
  Clock,
} from 'lucide-react';

// Available transformations
const TRANSFORMATIONS = [
  { id: 'summary', label: 'Generate Summary', description: 'Create AI summary of document' },
  { id: 'outline', label: 'Extract Outline', description: 'Extract document structure' },
  { id: 'takeaways', label: 'Key Takeaways', description: 'Extract main points' },
];

export function ProcessingOptionsStep() {
  const { files, options, setOptions } = useUploadStore();
  const { data: notebooks } = useNotebooks();

  // Check if any files are ACM type
  const hasAcmFiles = files.some((f) => f.documentType === 'acm');

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-2">Processing Options</h2>
        <p className="text-muted-foreground">
          Configure how your documents will be processed.
        </p>
      </div>

      {/* ACM Extraction - Only show if ACM files present */}
      {hasAcmFiles && (
        <Card className="p-4">
          <div className="flex items-start gap-4">
            <Shield className="w-8 h-8 text-blue-600 mt-1" />
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="acm-extraction" className="text-base font-medium">
                    ACM Data Extraction
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    Extract structured data from ACM/SAMP registers
                  </p>
                </div>
                <Switch
                  id="acm-extraction"
                  checked={options.enableAcmExtraction}
                  onCheckedChange={(checked) =>
                    setOptions({ enableAcmExtraction: checked })
                  }
                />
              </div>
              {options.enableAcmExtraction && (
                <div className="mt-3 p-3 bg-blue-50 dark:bg-blue-950 rounded-lg text-sm">
                  <p className="font-medium text-blue-800 dark:text-blue-200">
                    ACM extraction enabled for {files.filter((f) => f.documentType === 'acm').length} file(s)
                  </p>
                  <ul className="mt-2 text-blue-700 dark:text-blue-300 list-disc list-inside">
                    <li>Building/Room hierarchy extracted</li>
                    <li>Risk status identified</li>
                    <li>Page numbers tracked for citations</li>
                  </ul>
                </div>
              )}
            </div>
          </div>
        </Card>
      )}

      {/* Embeddings */}
      <Card className="p-4">
        <div className="flex items-start gap-4">
          <Database className="w-8 h-8 text-purple-600 mt-1" />
          <div className="flex-1">
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="embeddings" className="text-base font-medium">
                  Generate Embeddings
                </Label>
                <p className="text-sm text-muted-foreground">
                  Enable semantic search across document content
                </p>
              </div>
              <Switch
                id="embeddings"
                checked={options.enableEmbeddings}
                onCheckedChange={(checked) =>
                  setOptions({ enableEmbeddings: checked })
                }
              />
            </div>
          </div>
        </div>
      </Card>

      {/* Transformations */}
      <Card className="p-4">
        <div className="flex items-start gap-4">
          <Wand2 className="w-8 h-8 text-amber-600 mt-1" />
          <div className="flex-1">
            <Label className="text-base font-medium">AI Transformations</Label>
            <p className="text-sm text-muted-foreground mb-4">
              Select AI processing to apply to documents
            </p>

            <div className="space-y-3">
              {TRANSFORMATIONS.map((transform) => (
                <div key={transform.id} className="flex items-center gap-3">
                  <Checkbox
                    id={transform.id}
                    checked={options.transformations.includes(transform.id)}
                    onCheckedChange={(checked) => {
                      const newTransforms = checked
                        ? [...options.transformations, transform.id]
                        : options.transformations.filter((t) => t !== transform.id);
                      setOptions({ transformations: newTransforms });
                    }}
                  />
                  <div>
                    <Label htmlFor={transform.id} className="font-medium">
                      {transform.label}
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      {transform.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </Card>

      {/* Notebook Assignment */}
      <Card className="p-4">
        <div className="flex items-start gap-4">
          <FolderOpen className="w-8 h-8 text-green-600 mt-1" />
          <div className="flex-1">
            <Label className="text-base font-medium">Add to Notebooks</Label>
            <p className="text-sm text-muted-foreground mb-4">
              Optionally add sources to existing notebooks
            </p>

            <div className="space-y-2 max-h-40 overflow-y-auto">
              {notebooks?.map((notebook) => (
                <div key={notebook.id} className="flex items-center gap-3">
                  <Checkbox
                    id={`notebook-${notebook.id}`}
                    checked={options.notebookIds.includes(notebook.id)}
                    onCheckedChange={(checked) => {
                      const newNotebooks = checked
                        ? [...options.notebookIds, notebook.id]
                        : options.notebookIds.filter((id) => id !== notebook.id);
                      setOptions({ notebookIds: newNotebooks });
                    }}
                  />
                  <Label htmlFor={`notebook-${notebook.id}`}>
                    {notebook.name}
                  </Label>
                </div>
              ))}
              {(!notebooks || notebooks.length === 0) && (
                <p className="text-sm text-muted-foreground italic">
                  No notebooks available
                </p>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Processing Mode */}
      <Card className="p-4">
        <Label className="text-base font-medium mb-4 block">Processing Mode</Label>
        <RadioGroup
          value={options.processingMode}
          onValueChange={(value) =>
            setOptions({ processingMode: value as 'sync' | 'async' })
          }
          className="grid grid-cols-2 gap-4"
        >
          <div className="flex items-center space-x-2 p-4 border rounded-lg">
            <RadioGroupItem value="async" id="async" />
            <div>
              <Label htmlFor="async" className="flex items-center gap-2">
                <Clock className="w-4 h-4" />
                Background (Recommended)
              </Label>
              <p className="text-xs text-muted-foreground">
                Process in background, continue using app
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2 p-4 border rounded-lg">
            <RadioGroupItem value="sync" id="sync" />
            <div>
              <Label htmlFor="sync" className="flex items-center gap-2">
                <Zap className="w-4 h-4" />
                Immediate
              </Label>
              <p className="text-xs text-muted-foreground">
                Wait for processing to complete
              </p>
            </div>
          </div>
        </RadioGroup>
      </Card>
    </div>
  );
}
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/stores/upload-store.ts` | Add processing options |
| `frontend/src/components/upload/ProcessingOptionsStep.tsx` | New component |

---

## Dependencies

- E7-S3: Document Type Step (determines which options to show)

---

## Testing

1. Upload ACM file - verify ACM extraction toggle appears
2. Toggle ACM extraction - verify state updates
3. Toggle embeddings - verify state updates
4. Select transformations - verify multi-select works
5. Select notebooks - verify multi-select works
6. Change processing mode - verify selection
7. Upload non-ACM files only - verify ACM option hidden

---

## Estimated Complexity

**Medium** - Multiple options with conditional display

---
