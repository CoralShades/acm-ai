'use client';

import { useUploadStore } from '@/lib/stores/upload-store';
import { useNotebooks } from '@/lib/hooks/use-notebooks';
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
  {
    id: 'summary',
    label: 'Generate Summary',
    description: 'Create AI summary of document',
  },
  {
    id: 'outline',
    label: 'Extract Outline',
    description: 'Extract document structure',
  },
  {
    id: 'takeaways',
    label: 'Key Takeaways',
    description: 'Extract main points',
  },
];

export function ProcessingOptionsStep() {
  const { files, options, setOptions } = useUploadStore();
  const { data: notebooks, isLoading: isLoadingNotebooks, isError: isNotebooksError } = useNotebooks();

  // Check if any files are ACM type
  const hasAcmFiles = files.some((f) => f.documentType === 'acm');
  const acmFileCount = files.filter((f) => f.documentType === 'acm').length;

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
            <Shield className="w-8 h-8 text-blue-600 mt-1 flex-shrink-0" />
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <div>
                  <Label
                    htmlFor="acm-extraction"
                    className="text-base font-medium"
                  >
                    ACM Data Extraction
                  </Label>
                  <p className="text-sm text-muted-foreground">
                    Extract structured data from ACM/ARA registers
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
                    ACM extraction enabled for {acmFileCount} file(s)
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
          <Database className="w-8 h-8 text-purple-600 mt-1 flex-shrink-0" />
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
          <Wand2 className="w-8 h-8 text-amber-600 mt-1 flex-shrink-0" />
          <div className="flex-1">
            <Label className="text-base font-medium">AI Transformations</Label>
            <p className="text-sm text-muted-foreground mb-4">
              Select AI processing to apply to documents
            </p>

            <div className="space-y-3">
              {TRANSFORMATIONS.map((transform) => (
                <div key={transform.id} className="flex items-start gap-3">
                  <Checkbox
                    id={transform.id}
                    checked={options.transformations.includes(transform.id)}
                    onCheckedChange={(checked) => {
                      const newTransforms = checked
                        ? [...options.transformations, transform.id]
                        : options.transformations.filter(
                            (t) => t !== transform.id
                          );
                      setOptions({ transformations: newTransforms });
                    }}
                  />
                  <div className="grid gap-0.5">
                    <Label
                      htmlFor={transform.id}
                      className="font-medium cursor-pointer"
                    >
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
          <FolderOpen className="w-8 h-8 text-green-600 mt-1 flex-shrink-0" />
          <div className="flex-1">
            <Label className="text-base font-medium">Add to Notebooks</Label>
            <p className="text-sm text-muted-foreground mb-4">
              Optionally add sources to existing notebooks
            </p>

            <div className="space-y-2 max-h-40 overflow-y-auto">
              {isLoadingNotebooks && (
                <p className="text-sm text-muted-foreground">
                  Loading notebooks...
                </p>
              )}
              {isNotebooksError && (
                <p className="text-sm text-destructive">
                  Failed to load notebooks
                </p>
              )}
              {!isLoadingNotebooks &&
                !isNotebooksError &&
                notebooks?.map((notebook) => (
                  <div key={notebook.id} className="flex items-center gap-3">
                    <Checkbox
                      id={`notebook-${notebook.id}`}
                      checked={options.notebookIds.includes(notebook.id)}
                      onCheckedChange={(checked) => {
                        const newNotebooks = checked
                          ? [...options.notebookIds, notebook.id]
                          : options.notebookIds.filter(
                              (id) => id !== notebook.id
                            );
                        setOptions({ notebookIds: newNotebooks });
                      }}
                    />
                    <Label
                      htmlFor={`notebook-${notebook.id}`}
                      className="cursor-pointer"
                    >
                      {notebook.name}
                    </Label>
                  </div>
                ))}
              {!isLoadingNotebooks &&
                !isNotebooksError &&
                (!notebooks || notebooks.length === 0) && (
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
        <Label className="text-base font-medium mb-4 block">
          Processing Mode
        </Label>
        <RadioGroup
          value={options.processingMode}
          onValueChange={(value) =>
            setOptions({ processingMode: value as 'sync' | 'async' })
          }
          className="grid grid-cols-1 sm:grid-cols-2 gap-4"
        >
          <label
            htmlFor="async"
            className="flex items-start space-x-3 p-4 border rounded-lg cursor-pointer hover:bg-muted/50 transition-colors"
          >
            <RadioGroupItem value="async" id="async" className="mt-0.5" />
            <div>
              <span className="flex items-center gap-2 font-medium">
                <Clock className="w-4 h-4" />
                Background (Recommended)
              </span>
              <p className="text-xs text-muted-foreground mt-1">
                Process in background, continue using app
              </p>
            </div>
          </label>
          <label
            htmlFor="sync"
            className="flex items-start space-x-3 p-4 border rounded-lg cursor-pointer hover:bg-muted/50 transition-colors"
          >
            <RadioGroupItem value="sync" id="sync" className="mt-0.5" />
            <div>
              <span className="flex items-center gap-2 font-medium">
                <Zap className="w-4 h-4" />
                Immediate
              </span>
              <p className="text-xs text-muted-foreground mt-1">
                Wait for processing to complete
              </p>
            </div>
          </label>
        </RadioGroup>
      </Card>
    </div>
  );
}
