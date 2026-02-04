'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { insightsApi, SourceInsightResponse } from '@/lib/api/insights';
import { transformationsApi } from '@/lib/api/transformations';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Sparkles, Plus, Lightbulb, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { SourceInsightDialog } from '@/components/source/SourceInsightDialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Alert, AlertDescription } from '@/components/ui/alert';

interface SourceInsightsPanelProps {
  sourceId: string;
}

/** Maximum characters to show in insight preview */
const INSIGHT_PREVIEW_LENGTH = 180;

/**
 * Panel component displaying AI-generated insights for a source
 * Used in the source detail page's Insights tab
 */
export function SourceInsightsPanel({ sourceId }: SourceInsightsPanelProps) {
  const queryClient = useQueryClient();
  const [selectedTransformation, setSelectedTransformation] = useState<string>('');
  const [selectedInsight, setSelectedInsight] = useState<SourceInsightResponse | null>(null);

  // Fetch insights using React Query
  const {
    data: insights = [],
    isLoading: loadingInsights,
    error: insightsError,
  } = useQuery({
    queryKey: ['insights', 'source', sourceId],
    queryFn: () => insightsApi.listForSource(sourceId),
    enabled: !!sourceId,
    staleTime: 30 * 1000,
  });

  // Fetch transformations using React Query
  const {
    data: transformations = [],
    error: transformationsError,
  } = useQuery({
    queryKey: ['transformations'],
    queryFn: () => transformationsApi.list(),
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
  });

  // Create insight mutation
  const createInsightMutation = useMutation({
    mutationFn: () =>
      insightsApi.create(sourceId, {
        transformation_id: selectedTransformation,
      }),
    onSuccess: () => {
      toast.success('Insight created successfully');
      setSelectedTransformation('');
      // Invalidate insights query to refetch
      queryClient.invalidateQueries({ queryKey: ['insights', 'source', sourceId] });
    },
    onError: (err) => {
      console.error('Failed to create insight:', err);
      toast.error('Failed to create insight');
    },
  });

  const handleCreateInsight = () => {
    if (!selectedTransformation) {
      toast.error('Please select a transformation');
      return;
    }
    createInsightMutation.mutate();
  };

  // Show error state if both queries failed
  const hasError = insightsError || transformationsError;

  return (
    <>
      <ScrollArea className="h-full">
        <div className="space-y-4">
          {/* Error Alert */}
          {hasError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                {insightsError
                  ? 'Failed to load insights. Please try refreshing.'
                  : 'Failed to load transformations. Insight creation unavailable.'}
              </AlertDescription>
            </Alert>
          )}

          {/* Create New Insight */}
          <div className="rounded-lg border bg-muted/30 p-4">
            <h3 className="mb-3 text-sm font-semibold flex items-center gap-2">
              <Sparkles className="h-4 w-4" />
              Generate New Insight
            </h3>
            <div className="flex gap-2">
              <Select
                value={selectedTransformation}
                onValueChange={setSelectedTransformation}
                disabled={createInsightMutation.isPending || !!transformationsError}
              >
                <SelectTrigger className="flex-1">
                  <SelectValue placeholder="Select a transformation..." />
                </SelectTrigger>
                <SelectContent>
                  {transformations.map((trans) => (
                    <SelectItem key={trans.id} value={trans.id}>
                      {trans.title || trans.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                size="sm"
                onClick={handleCreateInsight}
                disabled={!selectedTransformation || createInsightMutation.isPending}
              >
                {createInsightMutation.isPending ? (
                  <>
                    <LoadingSpinner className="mr-2 h-3 w-3" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Plus className="mr-2 h-4 w-4" />
                    Create
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Insights List */}
          {loadingInsights ? (
            <div className="flex items-center justify-center py-8">
              <LoadingSpinner />
            </div>
          ) : insights.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Lightbulb className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">No insights yet</p>
              <p className="text-xs mt-1">
                Create your first insight using a transformation above
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {insights.map((insight) => (
                <div
                  key={insight.id}
                  className="rounded-lg border bg-background p-4"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs uppercase">
                        {insight.insight_type}
                      </Badge>
                    </div>
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">
                    {insight.content.slice(0, INSIGHT_PREVIEW_LENGTH)}
                    {insight.content.length > INSIGHT_PREVIEW_LENGTH ? '…' : ''}
                  </p>
                  <div className="mt-3 flex justify-end">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setSelectedInsight(insight)}
                    >
                      View Insight
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </ScrollArea>

      <SourceInsightDialog
        open={Boolean(selectedInsight)}
        onOpenChange={(open) => {
          if (!open) {
            setSelectedInsight(null);
          }
        }}
        insight={selectedInsight ?? undefined}
      />
    </>
  );
}
