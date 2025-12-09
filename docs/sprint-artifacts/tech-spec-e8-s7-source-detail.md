# Tech Spec: E8-S7 - Redesign Source Detail Page

> **Story:** E8-S7
> **Epic:** UI Refresh (Bento Grid Design)
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Redesign the source detail page using bento sections to organize document content, ACM data, chat, notes, and insights.

---

## User Story

**As a** user
**I want** the source detail page organized as bento sections
**So that** information is easier to find

---

## Acceptance Criteria

- [ ] Header card: Source title, metadata, actions
- [ ] Content card: Document preview/text
- [ ] ACM card: Spreadsheet view (if ACM data exists)
- [ ] Chat card: Collapsible chat panel
- [ ] Notes card: Related notes
- [ ] Insights card: AI-generated insights
- [ ] Responsive stacking on mobile

---

## Technical Design

### 1. Source Detail Page Layout

Update `frontend/src/app/(dashboard)/sources/[id]/page.tsx`:

```tsx
'use client';

import { useParams } from 'next/navigation';
import { useSource } from '@/hooks/use-source';
import { useACMRecords } from '@/hooks/use-acm-records';
import { BentoGrid } from '@/components/ui/bento-grid';
import {
  BentoCard,
  BentoCardHeader,
  BentoCardTitle,
  BentoCardContent,
  BentoCardActions,
} from '@/components/ui/bento-card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  FileText,
  MessageSquare,
  StickyNote,
  Lightbulb,
  TableProperties,
  Download,
  Trash2,
  MoreHorizontal,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { formatDate } from '@/lib/utils/format';
import { useState } from 'react';
import { SourceContent } from '@/components/sources/SourceContent';
import { ACMSpreadsheet } from '@/components/acm/ACMSpreadsheet';
import { ChatPanel } from '@/components/source/ChatPanel';
import { NotesPanel } from '@/components/source/NotesPanel';
import { InsightsPanel } from '@/components/source/InsightsPanel';

export default function SourceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: source, isLoading } = useSource(id);
  const { data: acmRecords } = useACMRecords(id);
  const [chatExpanded, setChatExpanded] = useState(true);

  if (isLoading) {
    return <SourceDetailSkeleton />;
  }

  if (!source) {
    return <SourceNotFound />;
  }

  const hasAcmData = acmRecords && acmRecords.length > 0;

  return (
    <div className="p-6">
      <BentoGrid columns={4} gap="md">
        {/* Header Card - Full width */}
        <BentoCard size="full" className="col-span-full">
          <BentoCardHeader>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <FileText className="w-5 h-5 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">
                  {source.media_type || 'Document'}
                </span>
              </div>
              <BentoCardTitle className="text-2xl">
                {source.title || 'Untitled Source'}
              </BentoCardTitle>
              <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                <span>Uploaded {formatDate(source.created_at)}</span>
                {hasAcmData && (
                  <Badge variant="secondary" className="gap-1">
                    <TableProperties className="w-3 h-3" />
                    {acmRecords.length} ACM Records
                  </Badge>
                )}
              </div>
            </div>
            <BentoCardActions>
              <Button variant="outline" size="sm">
                <Download className="w-4 h-4 mr-2" />
                Download
              </Button>
              <Button variant="outline" size="sm" className="text-destructive">
                <Trash2 className="w-4 h-4" />
              </Button>
            </BentoCardActions>
          </BentoCardHeader>
        </BentoCard>

        {/* Content Tabs - Large left */}
        <BentoCard size="lg" className="col-span-full lg:col-span-2 lg:row-span-2">
          <Tabs defaultValue={hasAcmData ? 'acm' : 'content'}>
            <BentoCardHeader>
              <TabsList>
                <TabsTrigger value="content">
                  <FileText className="w-4 h-4 mr-2" />
                  Content
                </TabsTrigger>
                {hasAcmData && (
                  <TabsTrigger value="acm">
                    <TableProperties className="w-4 h-4 mr-2" />
                    ACM Data
                  </TabsTrigger>
                )}
              </TabsList>
            </BentoCardHeader>
            <BentoCardContent noPadding className="h-[500px]">
              <TabsContent value="content" className="h-full m-0">
                <SourceContent source={source} />
              </TabsContent>
              {hasAcmData && (
                <TabsContent value="acm" className="h-full m-0">
                  <ACMSpreadsheet sourceId={id} />
                </TabsContent>
              )}
            </BentoCardContent>
          </Tabs>
        </BentoCard>

        {/* Chat Card - Medium right */}
        <BentoCard
          size="md"
          className="col-span-full lg:col-span-2 lg:row-span-2"
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
            >
              {chatExpanded ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </Button>
          </BentoCardHeader>
          {chatExpanded && (
            <BentoCardContent noPadding className="h-[400px]">
              <ChatPanel sourceId={id} hasAcmData={hasAcmData} />
            </BentoCardContent>
          )}
        </BentoCard>

        {/* Notes Card - Small */}
        <BentoCard size="md">
          <BentoCardHeader>
            <div className="flex items-center gap-2">
              <StickyNote className="w-5 h-5" />
              <BentoCardTitle>Notes</BentoCardTitle>
            </div>
          </BentoCardHeader>
          <BentoCardContent className="h-48 overflow-y-auto">
            <NotesPanel sourceId={id} />
          </BentoCardContent>
        </BentoCard>

        {/* Insights Card - Small */}
        <BentoCard size="md">
          <BentoCardHeader>
            <div className="flex items-center gap-2">
              <Lightbulb className="w-5 h-5" />
              <BentoCardTitle>Insights</BentoCardTitle>
            </div>
          </BentoCardHeader>
          <BentoCardContent className="h-48 overflow-y-auto">
            <InsightsPanel sourceId={id} />
          </BentoCardContent>
        </BentoCard>
      </BentoGrid>
    </div>
  );
}

function SourceDetailSkeleton() {
  return (
    <div className="p-6">
      <BentoGrid columns={4} gap="md">
        <BentoCard size="full" isLoading />
        <BentoCard size="lg" isLoading />
        <BentoCard size="md" isLoading />
        <BentoCard size="sm" isLoading />
        <BentoCard size="sm" isLoading />
      </BentoGrid>
    </div>
  );
}

function SourceNotFound() {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <FileText className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
        <h2 className="text-xl font-semibold mb-2">Source Not Found</h2>
        <p className="text-muted-foreground">
          The requested source could not be found.
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
| `frontend/src/app/(dashboard)/sources/[id]/page.tsx` | Redesign layout |
| `frontend/src/components/sources/SourceContent.tsx` | Update/create |
| `frontend/src/components/source/NotesPanel.tsx` | Update/create |
| `frontend/src/components/source/InsightsPanel.tsx` | Update/create |

---

## Dependencies

- E8-S3: BentoCard component
- E8-S4: BentoGrid component
- E2-S2: ACMSpreadsheet component

---

## Testing

1. View source with ACM data - verify tabs work
2. View source without ACM data - verify content shows
3. Toggle chat panel - verify collapse/expand
4. Test responsive stacking on mobile
5. Verify loading states
6. Test 404 state for missing source

---

## Estimated Complexity

**Medium** - Complex layout with multiple panels

---
