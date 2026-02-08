'use client';

import { useRouter, useParams } from 'next/navigation';
import { useState, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { SourceDetailSkeleton } from '@/components/skeletons/SourceDetailSkeleton';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { BentoGrid } from '@/components/ui/bento-grid';
import {
  BentoCard,
  BentoCardHeader,
  BentoCardTitle,
  BentoCardContent,
  BentoCardActions,
  BentoCardDescription,
} from '@/components/ui/bento-card';
import {
  ArrowLeft,
  FileText,
  MessageSquare,
  Lightbulb,
  TableProperties,
  Download,
  Trash2,
  MoreVertical,
  ChevronDown,
  ChevronUp,
  Link as LinkIcon,
  Upload,
  AlignLeft,
  Database,
  ExternalLink,
  Youtube,
  Info,
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useSourceChat } from '@/lib/hooks/useSourceChat';
import { ChatPanel } from '@/components/source/ChatPanel';
import { useNavigation } from '@/lib/hooks/use-navigation';
import { Breadcrumbs } from '@/components/common/Breadcrumbs';
import { acmApi } from '@/lib/api/acm';
import { useSource } from '@/lib/hooks/use-sources';
import { useACMStats } from '@/lib/hooks/use-acm';
import { ACMTab } from '@/components/acm/ACMTab';
import { SourceContentPanel } from '@/components/source/SourceContentPanel';
import { SourceInsightsPanel } from '@/components/source/SourceInsightsPanel';
import { SourceDetailsPanel } from '@/components/source/SourceDetailsPanel';
import { formatDistanceToNow } from 'date-fns';
import { toast } from 'sonner';
import { sourcesApi } from '@/lib/api/sources';
import { embeddingApi } from '@/lib/api/embedding';
import { insightsApi } from '@/lib/api/insights';
import { cn } from '@/lib/utils';
import { InlineEdit } from '@/components/common/InlineEdit';

export default function SourceDetailPage() {
  const router = useRouter();
  const params = useParams();
  const sourceId = decodeURIComponent(params.id as string);
  const navigation = useNavigation();

  // State
  const [chatExpanded, setChatExpanded] = useState(true);
  const [activeTab, setActiveTab] = useState<string>('content');
  const [isEmbedding, setIsEmbedding] = useState(false);
  const [isDownloadingFile, setIsDownloadingFile] = useState(false);

  // Initialize source chat
  const chat = useSourceChat(sourceId);

  // Fetch source data
  const {
    data: source,
    isLoading: isLoadingSource,
    refetch: refetchSource,
  } = useSource(sourceId);

  // Check if source has ACM data
  const { data: hasAcmData = false, isError: acmCheckError } = useQuery({
    queryKey: ['acm-has-records', sourceId],
    queryFn: () => acmApi.hasRecords(sourceId),
    enabled: !!sourceId,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  // ACM Stats for badge
  const { data: acmStats } = useACMStats(sourceId);

  // Insights count for badge
  const { data: insightsData } = useQuery({
    queryKey: ['insights', 'source', sourceId],
    queryFn: () => insightsApi.listForSource(sourceId),
    enabled: !!sourceId,
    staleTime: 30 * 1000,
  });
  const insightsCount = insightsData?.length || 0;

  // If ACM check failed, show toggle anyway (fail-open for better UX)
  const showAcmToggle = acmCheckError ? true : hasAcmData;

  // Get source icon and type
  const sourceIcon = useMemo(() => {
    if (!source) return null;
    if (source.asset?.url) return <LinkIcon className="h-5 w-5" />;
    if (source.asset?.file_path) return <Upload className="h-5 w-5" />;
    return <AlignLeft className="h-5 w-5" />;
  }, [source]);

  const sourceType = useMemo(() => {
    if (!source) return 'Document';
    if (source.asset?.url) return 'Link';
    if (source.asset?.file_path) return 'File';
    return 'Text';
  }, [source]);

  const isYouTubeUrl = useMemo(() => {
    if (!source?.asset?.url) return false;
    return /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)/.test(
      source.asset.url
    );
  }, [source?.asset?.url]);

  const handleBack = useCallback(() => {
    const returnPath = navigation.getReturnPath();
    router.push(returnPath);
    navigation.clearReturnTo();
  }, [navigation, router]);

  const handleEmbedContent = async () => {
    if (!source) return;
    try {
      setIsEmbedding(true);
      const response = await embeddingApi.embedContent(sourceId, 'source');
      toast.success(response.message);
      refetchSource();
    } catch (err) {
      console.error('Failed to embed content:', err);
      toast.error('Failed to embed content');
    } finally {
      setIsEmbedding(false);
    }
  };

  const handleDownloadFile = async () => {
    if (!source?.asset?.file_path || isDownloadingFile) return;
    try {
      setIsDownloadingFile(true);
      const response = await sourcesApi.downloadFile(source.id);
      const filename =
        source.asset.file_path.split(/[/\\]/).pop() || `source-${source.id}`;
      const blobUrl = window.URL.createObjectURL(response.data);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
      toast.success('Download started');
    } catch (err) {
      console.error('Failed to download file:', err);
      toast.error('Failed to download file');
    } finally {
      setIsDownloadingFile(false);
    }
  };

  const handleDelete = async () => {
    if (!source) return;
    if (confirm('Are you sure you want to delete this source?')) {
      try {
        await sourcesApi.delete(source.id);
        toast.success('Source deleted successfully');
        handleBack();
      } catch (error) {
        console.error('Failed to delete source:', error);
        toast.error('Failed to delete source');
      }
    }
  };

  const handleUpdateTitle = async (newTitle: string) => {
    if (!source || newTitle === source.title) return;
    try {
      await sourcesApi.update(sourceId, { title: newTitle });
      toast.success('Source title updated');
      refetchSource();
    } catch (err) {
      console.error('Failed to update source title:', err);
      toast.error('Failed to update source title');
    }
  };

  if (isLoadingSource) {
    return <SourceDetailSkeleton />;
  }

  if (!source) {
    return <SourceNotFound onBack={handleBack} />;
  }

  const formattedDate = source.created
    ? formatDistanceToNow(new Date(source.created), { addSuffix: true })
    : '';

  return (
    <div className="flex flex-col h-screen">
      {/* Back button + Breadcrumbs */}
      <div className="pt-4 pb-2 px-6 flex-shrink-0 space-y-2">
        <Button variant="ghost" size="sm" onClick={handleBack}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          {navigation.getReturnLabel()}
        </Button>
        <Breadcrumbs
          items={[
            { label: 'Home', href: '/' },
            { label: 'Documents', href: '/documents' },
            { label: source.title || 'Untitled Source' },
          ]}
        />
      </div>

      {/* Main Bento Grid Layout */}
      <div className="flex-1 overflow-auto px-6 pb-6">
        <BentoGrid columns={4} gap="md">
          {/* Header Card - Full width */}
          <BentoCard size="full" className="col-span-full">
            <BentoCardHeader>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  {isYouTubeUrl ? (
                    <Youtube className="w-5 h-5 text-red-500" />
                  ) : (
                    sourceIcon
                  )}
                  <Badge variant="secondary" className="text-xs">
                    {sourceType}
                  </Badge>
                  {source.embedded && (
                    <Badge variant="outline" className="text-xs gap-1">
                      <Database className="w-3 h-3" />
                      Embedded
                    </Badge>
                  )}
                </div>
                <InlineEdit
                  value={source.title || ''}
                  onSave={handleUpdateTitle}
                  className="text-2xl font-semibold"
                  inputClassName="text-2xl font-semibold"
                  placeholder="Source title"
                  emptyText="Untitled Source"
                />
                <BentoCardDescription className="mt-1">
                  <span>{formattedDate}</span>
                  {source.asset?.url && (
                    <a
                      href={source.asset.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-2 text-primary hover:underline inline-flex items-center gap-1"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <ExternalLink className="w-3 h-3" />
                      Open link
                    </a>
                  )}
                  {hasAcmData && (
                    <Badge variant="secondary" className="ml-2 gap-1">
                      <TableProperties className="w-3 h-3" />
                      {acmStats?.total_records || 0} ACM Records
                    </Badge>
                  )}
                </BentoCardDescription>
              </div>
              <BentoCardActions>
                {source.asset?.file_path && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleDownloadFile}
                    disabled={isDownloadingFile}
                    aria-label="Download source file"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    {isDownloadingFile ? 'Downloading...' : 'Download'}
                  </Button>
                )}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="icon" aria-label="Source actions">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                      onClick={handleEmbedContent}
                      disabled={isEmbedding || source.embedded}
                    >
                      <Database className="mr-2 h-4 w-4" />
                      {isEmbedding
                        ? 'Embedding...'
                        : source.embedded
                          ? 'Already Embedded'
                          : 'Embed Content'}
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      className="text-destructive"
                      onClick={handleDelete}
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete Source
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </BentoCardActions>
            </BentoCardHeader>
          </BentoCard>

          {/* Content Tabs Card - Large left */}
          <BentoCard
            size="lg"
            className="col-span-full lg:col-span-2 lg:row-span-2 min-h-[500px]"
          >
            <Tabs
              value={activeTab}
              onValueChange={setActiveTab}
              className="flex flex-col h-full"
            >
              <BentoCardHeader className="flex-shrink-0">
                <TabsList>
                  <TabsTrigger value="content" className="gap-1.5">
                    <FileText className="w-4 h-4" />
                    Content
                  </TabsTrigger>
                  <TabsTrigger value="acm" className="gap-1.5">
                    <TableProperties className="w-4 h-4" />
                    ACM
                    {acmStats?.total_records ? (
                      <Badge variant="secondary" className="ml-1 text-xs">
                        {acmStats.total_records}
                      </Badge>
                    ) : null}
                  </TabsTrigger>
                  <TabsTrigger value="insights" className="gap-1.5">
                    <Lightbulb className="w-4 h-4" />
                    Insights
                    {insightsCount > 0 && (
                      <Badge variant="secondary" className="ml-1 text-xs">
                        {insightsCount}
                      </Badge>
                    )}
                  </TabsTrigger>
                  <TabsTrigger value="details" className="gap-1.5">
                    <Info className="w-4 h-4" />
                    Details
                  </TabsTrigger>
                </TabsList>
              </BentoCardHeader>
              <BentoCardContent noPadding className="flex-1 overflow-hidden">
                <TabsContent value="content" className="h-full m-0 p-4">
                  <SourceContentPanel source={source} />
                </TabsContent>
                <TabsContent
                  value="acm"
                  className="h-full m-0 p-4 overflow-auto"
                >
                  <ACMTab sourceId={sourceId} />
                </TabsContent>
                <TabsContent
                  value="insights"
                  className="h-full m-0 p-4 overflow-auto"
                >
                  <SourceInsightsPanel sourceId={sourceId} />
                </TabsContent>
                <TabsContent
                  value="details"
                  className="h-full m-0 p-4 overflow-auto"
                >
                  <SourceDetailsPanel
                    source={source}
                    onEmbedContent={handleEmbedContent}
                    isEmbedding={isEmbedding}
                    onRefetch={refetchSource}
                  />
                </TabsContent>
              </BentoCardContent>
            </Tabs>
          </BentoCard>

          {/* Chat Card - Medium right */}
          <BentoCard
            size="md"
            className={cn(
              'col-span-full lg:col-span-2',
              chatExpanded ? 'lg:row-span-2 min-h-[500px]' : ''
            )}
          >
            <BentoCardHeader>
              <div className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5" />
                <BentoCardTitle>Chat</BentoCardTitle>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setChatExpanded(!chatExpanded)}
                aria-label={chatExpanded ? 'Collapse chat' : 'Expand chat'}
              >
                {chatExpanded ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </Button>
            </BentoCardHeader>
            {chatExpanded && (
              <BentoCardContent noPadding className="flex-1 overflow-hidden">
                <ChatPanel
                  messages={chat.messages}
                  isStreaming={chat.isStreaming}
                  contextIndicators={chat.contextIndicators}
                  onSendMessage={(message, model, includeAcm) =>
                    chat.sendMessage(message, model, includeAcm)
                  }
                  modelOverride={chat.currentSession?.model_override}
                  onModelChange={(model) => {
                    if (chat.currentSessionId) {
                      chat.updateSession(chat.currentSessionId, {
                        model_override: model,
                      });
                    }
                  }}
                  sessions={chat.sessions}
                  currentSessionId={chat.currentSessionId}
                  onCreateSession={(title) => chat.createSession({ title })}
                  onSelectSession={chat.switchSession}
                  onUpdateSession={(sessionId, title) =>
                    chat.updateSession(sessionId, { title })
                  }
                  onDeleteSession={chat.deleteSession}
                  loadingSessions={chat.loadingSessions}
                  sourceId={sourceId}
                  hasAcmData={showAcmToggle}
                />
              </BentoCardContent>
            )}
          </BentoCard>
        </BentoGrid>
      </div>
    </div>
  );
}

function SourceNotFound({ onBack }: { onBack: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4">
      <FileText className="w-12 h-12 text-muted-foreground" />
      <h2 className="text-xl font-semibold">Source Not Found</h2>
      <p className="text-muted-foreground">
        The requested source could not be found.
      </p>
      <Button onClick={onBack}>
        <ArrowLeft className="mr-2 h-4 w-4" />
        Go Back
      </Button>
    </div>
  );
}
