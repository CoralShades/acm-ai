You are implementing E22-S3: Job Detail Page = Source Detail Layout.
You are Amelia (Developer). This is the LARGEST story — take your time.

## MANDATORY PRE-READ — Read ALL before writing ANY code

### Your story:
- docs/sprint-artifacts/e22-s3-job-detail-source-layout.md

### THE REFERENCE LAYOUT (study this page CAREFULLY — it's what we're replicating):
- frontend/src/app/(dashboard)/sources/[id]/page.tsx
- docs/sprint-artifacts/tech-spec-e8-s7-source-detail.md

### Source page components to understand and reuse:
- frontend/src/components/source/SourceContentPanel.tsx — renders markdown content
- frontend/src/components/source/ChatPanel.tsx — chat widget
- frontend/src/components/source/SourceInsightsPanel.tsx
- frontend/src/components/source/SourceDetailsPanel.tsx

### The page you're REDESIGNING:
- frontend/src/app/(dashboard)/jobs/[id]/page.tsx
- frontend/src/components/jobs/ — list all files in this directory

### Chat infrastructure:
- frontend/src/app/(dashboard)/jobs/[id]/chat/page.tsx — existing CRUD chat page
- frontend/src/app/copilot-crud/route.ts — CRUD chat runtime
- frontend/src/components/providers/CopilotProvider.tsx

### Hooks:
- frontend/src/hooks/use-source.ts — how source data is fetched
- frontend/src/hooks/use-acm-records.ts

### ACM Register (reference for grid patterns):
- frontend/src/app/(dashboard)/acm/page.tsx

### Dependencies check:
```bash
grep -r "react-markdown\|ReactMarkdown" frontend/package.json frontend/src/ --include="*.tsx" --include="*.ts" --include="*.json" | head -10
```
If react-markdown is NOT in package.json, check what the Source page uses for rendering markdown.

## DESIGN BRIEF

The user wants the Job Detail page to look like the Source Detail page (Image 4 from screenshots).

### Current Source Detail Layout (the page they LOVE):
```
┌──────────────────────────────────────────┬─────────────────────┐
│ Source Title          ✏️  Download        │                     │
│ [File] [Embedded]                        │                     │
│ [metadata: uploaded X ago, N records]    │                     │
├──────────────────────────────────────────┤  Chat Widget Panel  │
│ Content | ACM (54) | Graph | Insights    │  [Chat | Classic |  │
│                                          │   Smart Chat]       │
│ Tab content area:                        │                     │
│ - Content: rendered markdown text        │  "Chat with Source" │
│ - ACM: record grid with count            │                     │
│ - Graph: knowledge graph visualization   │  [start a           │
│ - Insights: AI-generated insights        │   conversation]     │
│ - Details: source metadata               │                     │
└──────────────────────────────────────────┴─────────────────────┘
```

### Target Job Detail Layout (what we're building):
```
┌──────────────────────────────────────────┬─────────────────────┐
│ Document Title  ✏️  Published            │                     │
│ [Re-Extract] [Export CSV] [Export Excel]  │                     │
│ Uploaded: X ago  N records  N buildings   │                     │
├──────────────────────────────────────────┤  Chat Widget Panel  │
│ Overview|Buildings|ACM Records|Content|   │  (CRUD Chat)       │
│ Extraction Log                           │                     │
│                                          │  Uses existing      │
│ Tab content:                             │  CopilotProvider +  │
│ - Overview: stats + quick actions        │  /copilot-crud      │
│ - Buildings: building review grid        │  runtime            │
│ - ACM Records: records grid (+ bldg tabs)│                     │
│ - Content: PDF preview + styled markdown │  Collapsible on     │
│ - Extraction Log: progress panel         │  narrow screens     │
│                                          │                     │
└──────────────────────────────────────────┴─────────────────────┘
```

## IMPLEMENTATION TASKS

### Task 1: Study Source Page Layout Structure

Read `frontend/src/app/(dashboard)/sources/[id]/page.tsx` line by line.
Understand:
- How it creates the two-column layout (content left, chat right)
- How tabs are structured (Content, ACM, Graph, Insights, Details)
- How ChatPanel is rendered (collapsible, right side)
- How the header card works (title, badges, actions)
- What BentoGrid/BentoCard components are used

### Task 2: Create Content Tab Component

Create a new component for the "Content" tab on the Job Detail page.
This tab shows the document's extracted text rendered as styled markdown.

```tsx
// frontend/src/components/jobs/JobContentPanel.tsx
// - Fetch source.full_text (the Docling markdown output)
// - Render it with whatever markdown renderer the Source page uses
//   (check SourceContentPanel.tsx — it may use react-markdown or dangerouslySetInnerHTML)
// - Style it to look like the Content tab on the Source page
// - Include a "Download PDF" link/button for the original file
```

The source data should be available via the same hooks used by the Source page.
The Job Detail page already has the source ID — use it to fetch content.

### Task 3: Add Inline Chat Panel to Job Detail

Move the CRUD Chat from a separate page (`/jobs/[id]/chat`) to an inline
right-side panel, matching the Source page's chat layout.

Steps:
1. Study how ChatPanel.tsx works on the Source page
2. In the Job Detail page, add a right column with the chat panel
3. Use the existing CopilotProvider with the `copilot-crud` runtime
4. Make the chat panel collapsible (expand/collapse button)
5. On narrow screens (< lg breakpoint), collapse to a floating button

The existing `/jobs/[id]/chat` route can remain as a fallback but the
primary experience should be the inline panel.

### Task 4: Restructure Job Detail Page Layout

Redesign the Job Detail page to use the Source page's two-column layout:

```tsx
<div className="flex flex-col h-full">
  {/* Header */}
  <div className="p-6 border-b">
    {/* Title, badges, action buttons */}
  </div>
  
  {/* Two-column layout */}
  <div className="flex flex-1 overflow-hidden">
    {/* Left: Tabs content */}
    <div className="flex-1 overflow-auto">
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="buildings">Buildings</TabsTrigger>
          <TabsTrigger value="acm-records">ACM Records</TabsTrigger>
          <TabsTrigger value="content">Content</TabsTrigger>
          <TabsTrigger value="extraction-log">Extraction Log</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview">
          {/* Stats cards + quick actions (keep existing) */}
        </TabsContent>
        <TabsContent value="buildings">
          {/* Building review grid (keep existing) */}
        </TabsContent>
        <TabsContent value="acm-records">
          {/* ACM records grid (keep existing, E22-S4 adds building tabs later) */}
        </TabsContent>
        <TabsContent value="content">
          <JobContentPanel sourceId={sourceId} />
        </TabsContent>
        <TabsContent value="extraction-log">
          {/* ExtractionProgressPanel (keep existing) */}
        </TabsContent>
      </Tabs>
    </div>
    
    {/* Right: Chat panel */}
    <div className="w-[380px] border-l hidden lg:block">
      <ChatPanel sourceId={sourceId} hasAcmData={true} />
    </div>
  </div>
</div>
```

### Task 5: Fix Unicode Arrow Rendering

Search for `\u2192` or `→` that renders as text instead of the arrow character.
Common locations:
- Button labels ("Next: Review Records \u2192")
- "Proceed to Building Review →"
- Any navigation buttons

Fix options:
1. Replace string `\u2192` with actual → character
2. Use Lucide `ArrowRight` icon instead of text arrow
3. Ensure the font supports the arrow character

```bash
# Find all instances
grep -rn "\\\\u2192\|→\|ArrowRight\|arrow" frontend/src/ --include="*.tsx" | head -20
```

### Task 6: Remove CRUD Chat Tab (now inline)

Since chat is now an inline panel (not a tab), remove or hide the "CRUD Chat"
tab from the tab list. The `/jobs/[id]/chat` route can remain for direct access
but shouldn't be a primary tab anymore.

### Task 7: Verification

```bash
cd frontend
npm run build    # MUST pass
npm run lint     # MUST pass
```

Manual checks:
- Navigate to any job detail page
- Verify Content tab shows rendered markdown text
- Verify chat panel appears on right side
- Verify chat is functional (can send messages)
- Verify all existing tabs still work (Overview, Buildings, ACM Records, Extraction Log)
- Verify unicode arrows render as actual arrows
- Verify responsive: on narrow screen, chat collapses

### Task 8: Update BMAD Artifacts

Update docs/sprint-artifacts/sprint-status.yaml:
```yaml
e22-s3-job-detail-source-layout: done  # 2026-02-26: Two-column layout with Content tab (markdown), inline CRUD chat panel, unicode arrow fix
```

### Task 9: Git Commit

```bash
git add frontend/ docs/
git commit -m "feat(e22-s3): job detail redesign — source layout with PDF preview and inline chat

- New Content tab with rendered markdown (source.full_text via Docling)
- Inline CRUD chat panel (right side, collapsible, matches Source page)
- Two-column layout replicating Source Detail page structure
- Fixed unicode arrow rendering on navigation buttons
- Chat moved from separate /chat route to inline panel
- All existing tabs preserved (Overview, Buildings, ACM Records, Extraction Log)"
```

## GUARD RAILS
- Do NOT modify Python files
- Do NOT delete the Source Detail page — it still works and users may access it
- Do NOT break the extraction flow or building review wizard
- Do NOT modify AG Grid column definitions
- Do NOT install new npm packages unless absolutely necessary for markdown rendering
  (check what the Source page already uses first)
- REUSE existing components: ChatPanel, CopilotProvider, ExtractionProgressPanel
- REUSE the Source page's layout patterns — don't invent new ones
- Keep the CRUD Chat tab route as a fallback even if inline panel is primary
