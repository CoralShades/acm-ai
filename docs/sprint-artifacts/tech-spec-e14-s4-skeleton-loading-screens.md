# Tech Spec: E14-S4 - Add Shimmer Skeleton Loading Screens

> **Story:** E14-S4
> **Epic:** E14 - UX & Enterprise Readiness
> **Status:** Ready for Dev
> **Created:** 2026-02-08
> **Spec Reference:** `docs/state-loading-spec.md` Section 4 & 5

---

## Overview

This story implements shimmer skeleton loading screens for all major pages in the ACM-AI application. Skeleton screens replace blank/spinner-only loading states with placeholder content that matches the final layout, creating a perception of faster loading and preventing Cumulative Layout Shift (CLS).

**Key Technical Changes:**
- Enhance existing `Skeleton` component with shimmer animation variant
- Create page-specific skeleton components matching actual layouts
- Add shimmer CSS animation with dark mode support
- Integrate skeletons into page components with React Suspense or conditional rendering
- Ensure accessibility with `aria-busy` and screen reader announcements

---

## User Story

**As a** user
**I want** skeleton loading placeholders on every page
**So that** I see content structure immediately instead of a blank screen

---

## Acceptance Criteria

- [ ] Skeleton screen for Dashboard (bento grid layout)
- [ ] Skeleton screen for Documents page (card grid + filters)
- [ ] Skeleton screen for ACM Register (toolbar + AG Grid rows)
- [ ] Skeleton screen for Source Detail (panels layout)
- [ ] Skeleton screen for Search page
- [ ] Shimmer animation with CSS keyframes (2s linear infinite)
- [ ] Dark mode adaptation (lighter shimmer on dark surfaces)
- [ ] `aria-busy="true"` and screen reader announcements
- [ ] Zero CLS (skeleton dimensions match actual content)

---

## Technical Design

### 1. Base Skeleton Component Enhancement

The existing `Skeleton` component at `frontend/src/components/ui/skeleton.tsx` currently uses `animate-pulse`. We enhance it to support a shimmer variant while maintaining backward compatibility.

**Current Implementation:**
```tsx
// src/components/ui/skeleton.tsx
import { cn } from "@/lib/utils"

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    />
  )
}
```

**Enhanced Implementation:**
```tsx
// src/components/ui/skeleton.tsx
import { cn } from "@/lib/utils"

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'pulse' | 'shimmer'
}

function Skeleton({
  className,
  variant = 'shimmer',
  ...props
}: SkeletonProps) {
  return (
    <div
      className={cn(
        'rounded-md bg-muted',
        variant === 'shimmer' ? 'animate-shimmer' : 'animate-pulse',
        className
      )}
      {...props}
    />
  )
}

export { Skeleton }
export type { SkeletonProps }
```

**Backward Compatibility:**
- Default changed to `shimmer` (new standard)
- Existing uses without `variant` prop will automatically get shimmer
- Components that explicitly need pulse can pass `variant="pulse"`

---

### 2. Shimmer CSS Animation

Add shimmer animation keyframes and utility classes to the global CSS and Tailwind configuration.

#### 2.1 Tailwind Config Changes

**File:** `frontend/tailwind.config.ts`

Add to `theme.extend.animation` and `theme.extend.keyframes`:

```typescript
export default {
  theme: {
    extend: {
      animation: {
        shimmer: 'shimmer 2s linear infinite',
        // ... existing animations
      },
      keyframes: {
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        // ... existing keyframes
      },
    },
  },
}
```

#### 2.2 Global CSS Changes

**File:** `frontend/src/app/globals.css`

Add shimmer animation with dark mode support and reduced motion handling:

```css
/* Shimmer Animation */
@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

.animate-shimmer {
  background: linear-gradient(
    90deg,
    hsl(var(--muted)) 25%,
    hsl(var(--muted-foreground) / 0.08) 50%,
    hsl(var(--muted)) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 2s linear infinite;
}

/* Reduced Motion Support */
@media (prefers-reduced-motion: reduce) {
  .animate-shimmer {
    animation: none;
    background: hsl(var(--muted));
  }
}
```

**Design Notes:**
- Gradient uses CSS custom properties (`--muted`, `--muted-foreground`) which automatically adapt to dark mode
- Reduced motion preference honored for accessibility
- 2-second linear infinite animation provides smooth, continuous shimmer

---

### 3. Page-Specific Skeleton Components

Create dedicated skeleton components for each major page in `frontend/src/components/skeletons/`.

#### 3.1 Dashboard Skeleton

**File:** `frontend/src/components/skeletons/DashboardSkeleton.tsx`

Matches the bento grid layout with 4 stat cards, risk chart, recent sources list, and quick actions.

```tsx
import { Skeleton } from '@/components/ui/skeleton'

export function DashboardSkeleton() {
  return (
    <div className="space-y-6 p-6" aria-busy="true">
      <span className="sr-only" role="status">Loading dashboard</span>

      {/* Page title */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-4 w-64" />
      </div>

      {/* Stats cards row - 4 bento cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-xl border p-6 space-y-3">
            <div className="flex items-center justify-between">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-10 w-10 rounded-lg" />
            </div>
            <Skeleton className="h-8 w-16" />
            <Skeleton className="h-3 w-32" />
          </div>
        ))}
      </div>

      {/* Risk chart + recent sources */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk donut chart placeholder */}
        <div className="rounded-xl border p-6 space-y-4">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-48 w-48 rounded-full mx-auto" />
          <Skeleton className="h-4 w-40 mx-auto" />
        </div>

        {/* Recent sources list */}
        <div className="rounded-xl border p-6 space-y-4">
          <Skeleton className="h-5 w-40" />
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="h-10 w-10 rounded" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            </div>
          ))}
          <Skeleton className="h-4 w-32" />
        </div>
      </div>

      {/* Quick actions card */}
      <div className="rounded-xl border p-6 space-y-4 lg:max-w-md">
        <Skeleton className="h-5 w-32" />
        <div className="space-y-3">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      </div>
    </div>
  )
}
```

**Layout Matching:**
- Matches `BentoGrid columns={4}` layout
- 4 small stat cards (Total Sources, High/Medium/Low Risk)
- 1 large card (Risk Chart) + 1 medium card (Recent Sources)
- 1 medium card (Quick Actions)

#### 3.2 Documents Skeleton

**File:** `frontend/src/components/skeletons/DocumentsSkeleton.tsx`

Matches the Documents page with tabs, filters, and card grid.

```tsx
import { Skeleton } from '@/components/ui/skeleton'

export function DocumentsSkeleton() {
  return (
    <div className="space-y-6 p-6" aria-busy="true">
      <span className="sr-only" role="status">Loading documents</span>

      {/* Header */}
      <div className="space-y-2">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-4 w-64" />
      </div>

      {/* Tabs */}
      <div className="flex gap-2">
        <Skeleton className="h-10 w-32 rounded-md" />
        <Skeleton className="h-10 w-32 rounded-md" />
      </div>

      {/* Toolbar: filters + view toggle */}
      <div className="flex flex-wrap items-center gap-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-10 w-36" />
        <Skeleton className="h-10 w-36" />
        <div className="flex-1" />
        <Skeleton className="h-10 w-20" />
      </div>

      {/* Document cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="rounded-xl border p-4 space-y-3">
            <div className="flex items-start justify-between">
              <Skeleton className="h-10 w-10 rounded" />
              <Skeleton className="h-5 w-16 rounded-full" />
            </div>
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-3 w-full" />
            <Skeleton className="h-3 w-2/3" />
            <div className="flex gap-2 pt-2">
              <Skeleton className="h-6 w-16 rounded-full" />
              <Skeleton className="h-6 w-20 rounded-full" />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
```

**Layout Matching:**
- Tabs: Library / Processing
- Filter bar: search input, type/status dropdowns, view toggle
- Responsive grid: 1/2/3/4 columns
- Document cards with icon, title, metadata, badges

#### 3.3 ACM Register Skeleton

**File:** `frontend/src/components/skeletons/ACMRegisterSkeleton.tsx`

Matches the ACM page with stats cards, source selector, toolbar, and AG Grid.

```tsx
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

export function ACMRegisterSkeleton() {
  return (
    <div className="space-y-6 p-6" aria-busy="true">
      <span className="sr-only" role="status">Loading ACM register</span>

      {/* Page header */}
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <Skeleton className="h-8 w-8 rounded" />
          <Skeleton className="h-8 w-48" />
        </div>
        <Skeleton className="h-4 w-96" />
      </div>

      {/* Source selector card */}
      <div className="rounded-lg border p-6 space-y-4">
        <div className="space-y-2">
          <Skeleton className="h-5 w-48" />
          <Skeleton className="h-4 w-80" />
        </div>
        <Skeleton className="h-10 w-full max-w-md" />
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-lg border p-4 space-y-2">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-7 w-12" />
          </div>
        ))}
      </div>

      {/* ACM Records card */}
      <div className="rounded-lg border p-6 space-y-4">
        {/* Card header */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Skeleton className="h-5 w-5" />
            <Skeleton className="h-5 w-32" />
          </div>
          <Skeleton className="h-4 w-96" />
        </div>

        {/* Toolbar: search + filters + actions */}
        <div className="flex items-center gap-3 flex-wrap">
          <Skeleton className="h-9 w-64" />
          <div className="flex gap-1">
            <Skeleton className="h-8 w-20 rounded-full" />
            <Skeleton className="h-8 w-24 rounded-full" />
            <Skeleton className="h-8 w-28 rounded-full" />
          </div>
          <div className="ml-auto flex gap-2">
            <Skeleton className="h-9 w-32" />
            <Skeleton className="h-9 w-9" />
            <Skeleton className="h-9 w-9" />
          </div>
        </div>

        {/* AG Grid skeleton: header + 10 rows, 8 columns */}
        <div className="rounded-lg border overflow-hidden">
          {/* Header row */}
          <div className="flex border-b bg-muted/30 p-2 gap-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton
                key={i}
                className="h-4 flex-1"
                style={{ maxWidth: i === 0 ? 40 : undefined }}
              />
            ))}
          </div>
          {/* Data rows */}
          {Array.from({ length: 10 }).map((_, row) => (
            <div key={row} className="flex border-b p-3 gap-2">
              {Array.from({ length: 8 }).map((_, col) => (
                <Skeleton
                  key={col}
                  className={cn('h-4 flex-1', col === 0 && 'max-w-[40px]')}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
```

**Layout Matching:**
- Page header with icon + title
- Source selector card with dropdown
- 4-column stats cards (Total, High/Medium/Low Risk)
- ACM Records card with toolbar and grid
- Grid header + 10 skeleton rows mimicking AG Grid

#### 3.4 Source Detail Skeleton

**File:** `frontend/src/components/skeletons/SourceDetailSkeleton.tsx`

Matches the Source Detail page's bento grid layout with header, content tabs, and chat panel.

```tsx
import { Skeleton } from '@/components/ui/skeleton'

export function SourceDetailSkeleton() {
  return (
    <div className="flex flex-col h-screen" aria-busy="true">
      <span className="sr-only" role="status">Loading source details</span>

      {/* Back button */}
      <div className="pt-4 pb-2 px-6 flex-shrink-0">
        <Skeleton className="h-9 w-32" />
      </div>

      {/* Bento Grid Layout */}
      <div className="flex-1 overflow-auto px-6 pb-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* Header Card - Full width */}
          <div className="col-span-full rounded-xl border p-6 space-y-3">
            <div className="flex items-center gap-2">
              <Skeleton className="h-5 w-5 rounded" />
              <Skeleton className="h-5 w-16 rounded-full" />
              <Skeleton className="h-5 w-24 rounded-full" />
            </div>
            <Skeleton className="h-8 w-3/4" />
            <div className="flex items-center gap-2">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-4 w-40" />
            </div>
          </div>

          {/* Content Tabs Card - Large left (2 cols) */}
          <div className="col-span-full lg:col-span-2 lg:row-span-2 rounded-xl border min-h-[500px]">
            <div className="p-6 space-y-4">
              {/* Tabs */}
              <div className="flex gap-2">
                <Skeleton className="h-10 w-24" />
                <Skeleton className="h-10 w-24" />
                <Skeleton className="h-10 w-24" />
                <Skeleton className="h-10 w-24" />
              </div>
              {/* Tab content */}
              <div className="space-y-3">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-5/6" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-4/5" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            </div>
          </div>

          {/* Chat Card - Medium right (2 cols) */}
          <div className="col-span-full lg:col-span-2 lg:row-span-2 rounded-xl border min-h-[500px]">
            <div className="p-6 space-y-4">
              {/* Chat header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Skeleton className="h-5 w-5" />
                  <Skeleton className="h-5 w-16" />
                </div>
                <Skeleton className="h-8 w-8" />
              </div>
              {/* Chat messages */}
              <div className="space-y-4">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="space-y-2">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-16 w-full rounded-lg" />
                  </div>
                ))}
              </div>
              {/* Chat input */}
              <Skeleton className="h-20 w-full rounded-lg" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
```

**Layout Matching:**
- Back button
- Full-width header card with badges
- 4-column bento grid:
  - Content tabs card: 2 cols, 2 rows (lg screens)
  - Chat panel card: 2 cols, 2 rows (lg screens)

**Note:** This skeleton already exists in the Source Detail page component as `SourceDetailSkeleton`. We extract it to the shared location and reuse it.

#### 3.5 Search Skeleton

**File:** `frontend/src/components/skeletons/SearchSkeleton.tsx`

Matches the Search/Ask page with tabs, input, model selectors, and results.

```tsx
import { Skeleton } from '@/components/ui/skeleton'

export function SearchSkeleton() {
  return (
    <div className="p-6 space-y-6" aria-busy="true">
      <span className="sr-only" role="status">Loading search</span>

      {/* Page title */}
      <Skeleton className="h-8 w-48" />

      {/* Mode selector label */}
      <div className="space-y-2">
        <Skeleton className="h-3 w-32" />
        <Skeleton className="h-10 w-full max-w-xl" />
      </div>

      {/* Search/Ask Card */}
      <div className="rounded-lg border p-6 space-y-4 max-w-4xl">
        {/* Card title */}
        <div className="space-y-2">
          <Skeleton className="h-5 w-64" />
          <Skeleton className="h-4 w-96" />
        </div>

        {/* Input area */}
        <div className="space-y-2">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-24 w-full rounded-lg" />
          <Skeleton className="h-3 w-48" />
        </div>

        {/* Model selectors */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Skeleton className="h-3 w-40" />
            <Skeleton className="h-8 w-24" />
          </div>
          <div className="flex gap-2 flex-wrap">
            <Skeleton className="h-6 w-32 rounded-full" />
            <Skeleton className="h-6 w-28 rounded-full" />
            <Skeleton className="h-6 w-36 rounded-full" />
          </div>
        </div>

        {/* Action button */}
        <Skeleton className="h-10 w-full" />

        {/* Results placeholder */}
        <div className="space-y-3 pt-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="rounded-lg border p-4 space-y-2">
              <div className="flex items-center justify-between">
                <Skeleton className="h-5 w-2/3" />
                <Skeleton className="h-5 w-12 rounded-full" />
              </div>
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-1/2" />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
```

**Layout Matching:**
- Page title + mode selector (Ask/Search tabs)
- Card with input, model badges, action button
- Result cards (3 placeholders)

---

### ⚠️ Conflict Guard — `acm/page.tsx` Preservation (E2-S9)

`frontend/src/app/(dashboard)/acm/page.tsx` was modified by E2-S9 and contains:
- `ACMRecordDetailDialog` import and JSX (`<ACMRecordDetailDialog ... />`)
- `selectedRecord` state and `handleRowClick` / `handleCloseDetail` handlers
- `onResetColumns` callback wired to `ACMGrid`

When adding skeleton loading to this page, **do not overwrite these additions**.
Use an additive pattern:

```tsx
// CORRECT — additive
const { data: sources, isLoading: sourcesLoading } = useSources()
if (sourcesLoading) return <ACMRegisterSkeleton />

// Below the loading guard, existing JSX (including ACMRecordDetailDialog) remains unchanged
```

Do NOT restructure the page component's return statement in a way that removes
`<ACMRecordDetailDialog>` or its state handlers.

### ⚠️ Skeleton Height Must Match Grid

`ACMRegisterSkeleton.tsx` must use the same grid container height as `ACMGrid.tsx`.
Before implementing, check the current value of the `className` on the `.ag-theme-alpine` div
in `frontend/src/components/acm/ACMGrid.tsx`. As of E8-S11 (review), this is:
`h-[calc(100vh-280px)] min-h-[400px]`

Use the same value in the skeleton grid placeholder rows.
If the value differs in the live file, use whatever is currently in `ACMGrid.tsx`.

### ⚠️ Sequencing with Other `acm/page.tsx` Stories

Three other ready-for-dev stories also modify `acm/page.tsx`:
- **E14-S8** (Error Recovery) — additive
- **E14-S10** (Breadcrumb Navigation) — layout change, will increase offset from 280px → 320px

Recommended sequence: **E14-S4 → E14-S8 → E14-S10**
Each must be merged and the next story's developer must read the updated file before starting.

### 4. Integration Pattern

Each page component conditionally renders its skeleton while data is loading.

#### 4.1 Dashboard Integration

**File:** `frontend/src/app/(dashboard)/page.tsx`

```tsx
import { DashboardSkeleton } from '@/components/skeletons/DashboardSkeleton'

export default function DashboardPage() {
  const { data: sources, isLoading: sourcesLoading, error: sourcesError } = useSources()
  const { data: acmSummary, isLoading: acmLoading, error: acmError } = useACMSummary()

  // Show skeleton if either query is loading
  if (sourcesLoading || acmLoading) {
    return <DashboardSkeleton />
  }

  // ... rest of component
}
```

#### 4.2 Documents Integration

**File:** `frontend/src/app/(dashboard)/documents/page.tsx`

**Note:** Documents page already has a skeleton (`DocumentLibrarySkeleton`) in `DocumentLibrary.tsx`. We create a consistent page-level skeleton.

```tsx
import { DocumentsSkeleton } from '@/components/skeletons/DocumentsSkeleton'

export default function DocumentsPage() {
  return (
    <AppShell>
      <div className="flex flex-col h-full w-full max-w-none px-6 py-6">
        {/* Header */}
        <div className="mb-6 flex-shrink-0">
          <h1 className="text-2xl font-bold">Document Library</h1>
          <p className="text-muted-foreground">
            Manage your ACM documents and SAMP files
          </p>
        </div>
        <Tabs defaultValue="library" className="flex flex-col flex-1">
          <TabsList className="w-fit flex-shrink-0">
            <TabsTrigger value="library" className="gap-2">
              <FileText className="w-4 h-4" />
              Library
            </TabsTrigger>
            <TabsTrigger value="processing" className="gap-2">
              <Activity className="w-4 h-4" />
              Processing
            </TabsTrigger>
          </TabsList>
          <TabsContent value="library" className="flex-1 mt-4">
            <DocumentLibrary />
          </TabsContent>
          <TabsContent value="processing" className="flex-1 mt-4">
            <ProcessingStatus />
          </TabsContent>
        </Tabs>
      </div>
    </AppShell>
  )
}
```

**Update:** `DocumentLibrary.tsx` already handles its own loading skeleton. We keep this pattern but ensure consistency with the shimmer animation.

#### 4.3 ACM Register Integration

**File:** `frontend/src/app/(dashboard)/acm/page.tsx`

```tsx
import { ACMRegisterSkeleton } from '@/components/skeletons/ACMRegisterSkeleton'

export default function ACMPage() {
  const { data: sources, isLoading: isLoadingSources } = useSources('')

  // Show skeleton while loading sources
  if (isLoadingSources) {
    return (
      <AppShell>
        <ACMRegisterSkeleton />
      </AppShell>
    )
  }

  // ... rest of component
}
```

#### 4.4 Source Detail Integration

**File:** `frontend/src/app/(dashboard)/sources/[id]/page.tsx`

**Note:** Source Detail page already has `SourceDetailSkeleton`. We extract it and import from shared location.

```tsx
import { SourceDetailSkeleton } from '@/components/skeletons/SourceDetailSkeleton'

export default function SourceDetailPage() {
  const {
    data: source,
    isLoading: isLoadingSource,
    refetch: refetchSource,
  } = useSource(sourceId)

  if (isLoadingSource) {
    return <SourceDetailSkeleton />
  }

  // ... rest of component
}
```

#### 4.5 Search Integration

**File:** `frontend/src/app/(dashboard)/search/page.tsx`

Search page doesn't have initial loading state (data loads on demand). Skeleton shown only when auto-triggering from URL params.

```tsx
import { SearchSkeleton } from '@/components/skeletons/SearchSkeleton'

export default function SearchPage() {
  const { data: modelDefaults, isLoading: modelsLoading } = useModelDefaults()
  const [isInitializing, setIsInitializing] = useState(true)

  useEffect(() => {
    // Wait for models to load before showing page
    if (!modelsLoading) {
      setIsInitializing(false)
    }
  }, [modelsLoading])

  if (isInitializing) {
    return (
      <AppShell>
        <SearchSkeleton />
      </AppShell>
    )
  }

  // ... rest of component
}
```

---

### 5. Accessibility Implementation

Every skeleton component includes:

1. **Container Attributes:**
   ```tsx
   <div aria-busy="true">
   ```

2. **Screen Reader Announcement:**
   ```tsx
   <span className="sr-only" role="status">Loading [page name]</span>
   ```

3. **Reduced Motion:**
   Shimmer animation automatically disabled via `prefers-reduced-motion` media query in CSS.

**Screen Reader Utility Class:**
The existing `sr-only` class (from Tailwind or globals.css):
```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
```

---

### 6. Zero CLS Strategy

**Cumulative Layout Shift Prevention:**

1. **Fixed Skeleton Dimensions:**
   - All skeleton elements use explicit height classes (`h-4`, `h-8`, `h-10`, etc.)
   - Grid layouts match actual content grids (same `grid-cols-*` classes)
   - Card padding and spacing match real components

2. **Minimum Heights:**
   - Large cards: `min-h-[500px]`
   - AG Grid: Header + 10 rows with consistent row height

3. **Responsive Breakpoints:**
   - Skeleton grids use same breakpoints as actual content (`md:grid-cols-2`, `lg:grid-cols-4`)

4. **Match Actual Components:**
   - Dashboard skeleton mirrors `BentoGrid columns={4}` layout
   - Document cards match `DocumentGrid` dimensions
   - ACM Grid skeleton matches AG Grid cell heights

**Testing CLS:**
Use Chrome DevTools Performance panel to measure layout shift during loading. Target: CLS score < 0.1.

---

### 7. Dark Mode Adaptation

**Automatic Theme Support:**
The shimmer gradient uses CSS custom properties that change with theme:

```css
.animate-shimmer {
  background: linear-gradient(
    90deg,
    hsl(var(--muted)) 25%,
    hsl(var(--muted-foreground) / 0.08) 50%,
    hsl(var(--muted)) 75%
  );
}
```

**Light Mode:**
- `--muted`: Light gray background
- `--muted-foreground` at 8% opacity: Subtle highlight

**Dark Mode:**
- `--muted`: Dark gray background
- `--muted-foreground` at 8% opacity: Lighter shimmer (creates contrast on dark surface)

No manual dark mode classes needed—theme system handles it automatically.

---

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/components/ui/skeleton.tsx` | Modify | Add `variant` prop supporting `pulse` and `shimmer` |
| `frontend/tailwind.config.ts` | Modify | Add `shimmer` animation and keyframes to theme config |
| `frontend/src/app/globals.css` | Modify | Add `@keyframes shimmer`, `.animate-shimmer` class, reduced motion handling |
| `frontend/src/components/skeletons/DashboardSkeleton.tsx` | Create | Dashboard page skeleton with bento grid layout |
| `frontend/src/components/skeletons/DocumentsSkeleton.tsx` | Create | Documents page skeleton with grid and filters |
| `frontend/src/components/skeletons/ACMRegisterSkeleton.tsx` | Create | ACM Register skeleton with stats, toolbar, grid |
| `frontend/src/components/skeletons/SourceDetailSkeleton.tsx` | Create | Source detail skeleton with bento panels |
| `frontend/src/components/skeletons/SearchSkeleton.tsx` | Create | Search/Ask page skeleton with input and results |
| `frontend/src/app/(dashboard)/page.tsx` | Modify | Import and use `DashboardSkeleton` |
| `frontend/src/app/(dashboard)/acm/page.tsx` | Modify | Import and use `ACMRegisterSkeleton` |
| `frontend/src/app/(dashboard)/sources/[id]/page.tsx` | Modify | Extract `SourceDetailSkeleton` to shared location, import from there |
| `frontend/src/app/(dashboard)/search/page.tsx` | Modify | Add initial loading state with `SearchSkeleton` |

**Total:** 12 files (4 modified, 6 created, 2 refactored)

---

## Dependencies

**Required Before Starting:**
- ✅ Existing `Skeleton` component (`frontend/src/components/ui/skeleton.tsx`)
- ✅ Tailwind CSS configuration with `extend` support
- ✅ Theme system with CSS custom properties (`--muted`, `--muted-foreground`)
- ✅ Existing page components (Dashboard, Documents, ACM, Source Detail, Search)

**No External Dependencies:**
- No new npm packages required
- No API changes required
- No backend changes required

---

## Testing Strategy

### Unit Tests

No new unit tests required for this story (skeleton components are presentational only).

### Manual Testing Checklist

**Per Page:**
- [ ] Skeleton appears immediately on page load
- [ ] Shimmer animation runs smoothly (2s loop)
- [ ] Skeleton dimensions match actual content (no CLS)
- [ ] Dark mode: Shimmer gradient visible on dark background
- [ ] Reduced motion: Animation disabled when `prefers-reduced-motion: reduce`
- [ ] Screen reader: Announces "Loading [page]" status

**Dashboard:**
- [ ] 4 stat cards skeleton visible
- [ ] Risk chart placeholder (circular)
- [ ] Recent sources list skeleton (5 items)
- [ ] Quick actions skeleton (3 buttons)

**Documents:**
- [ ] Tabs skeleton visible
- [ ] Filter bar skeleton visible
- [ ] Document grid skeleton (8 cards, responsive)

**ACM Register:**
- [ ] Source selector skeleton visible
- [ ] Stats cards skeleton (4 cards)
- [ ] Toolbar skeleton (search, filters, actions)
- [ ] Grid skeleton (header + 10 rows)

**Source Detail:**
- [ ] Back button skeleton
- [ ] Header card skeleton with badges
- [ ] Content tabs card skeleton
- [ ] Chat panel skeleton

**Search:**
- [ ] Mode selector skeleton
- [ ] Input area skeleton
- [ ] Model badges skeleton
- [ ] Results skeleton (3 cards)

### Accessibility Testing

**Screen Reader:**
```bash
# Test with macOS VoiceOver
# Navigate to each page, verify announcement
# Expected: "Loading [page name]" announced immediately
```

**Keyboard Navigation:**
- [ ] Skeleton does not trap focus
- [ ] Tab key skips over skeleton elements

**Reduced Motion:**
```css
/* Test with Chrome DevTools > Rendering > Emulate CSS prefers-reduced-motion */
/* Verify shimmer animation is disabled, static gray background shown */
```

### Performance Testing

**Lighthouse CLS Score:**
```bash
# Run Lighthouse in Chrome DevTools
# Navigate to each page
# Measure Cumulative Layout Shift (CLS)
# Target: CLS < 0.1
```

**Visual Comparison:**
- [ ] Take screenshots of skeleton vs. loaded page
- [ ] Overlay images to verify exact dimension matching

---

## Estimated Complexity

**Story Points:** 3

**Time Estimate:** 4-6 hours

**Breakdown:**
- CSS shimmer animation: 0.5 hour
- Skeleton component enhancement: 0.5 hour
- Dashboard skeleton: 1 hour
- Documents skeleton: 0.5 hour
- ACM Register skeleton: 1 hour
- Source Detail skeleton extraction: 0.5 hour
- Search skeleton: 0.5 hour
- Integration (5 pages): 1 hour
- Testing (manual + accessibility): 1 hour

**Risk Level:** Low

**Complexity Factors:**
- ✅ No new dependencies
- ✅ No API changes
- ✅ Presentational components only
- ⚠️ Requires pixel-perfect layout matching for zero CLS
- ⚠️ Must test across multiple screen sizes and themes

---

## Implementation Notes

### Code Standards

1. **Component Structure:**
   - All skeleton components are pure functional components
   - No state or hooks
   - Props are minimal (if any)

2. **Naming Conventions:**
   - Pattern: `[PageName]Skeleton.tsx`
   - Export: Named export `export function [PageName]Skeleton()`

3. **Accessibility:**
   - Always include `aria-busy="true"` on container
   - Always include screen reader announcement with `role="status"`

4. **Styling:**
   - Use Tailwind utility classes only
   - Match border radius, padding, gaps exactly to actual components
   - Use `space-y-*` for vertical spacing consistency

### Edge Cases

1. **Empty States:**
   - Skeleton should not show if page has empty state immediately (e.g., no sources uploaded)
   - Check for `isLoading` flag, not just data absence

2. **Partial Loading:**
   - Dashboard: Show skeleton until BOTH sources and ACM data are loaded
   - Source Detail: Show skeleton only for initial source fetch, not for chat/ACM tabs

3. **Error States:**
   - Do not show skeleton if query returns error immediately
   - Transition from skeleton to error message

### Future Enhancements

**Not in Scope for E14-S4:**
- Animated transitions between skeleton and content (E14-S5 or later)
- Skeleton variants for different data densities
- Skeleton for modal dialogs
- Skeleton for Settings page (not in acceptance criteria)

---

## Related Stories

- **E14-S1:** Navigation restructure (provides context for which pages need skeletons)
- **E14-S2:** Document Library page (Documents skeleton targets this)
- **E14-S5:** Loading state polish (may enhance skeleton transitions)
- **E14-S6:** Multi-stage pipeline progress (future enhancement to show extraction progress instead of static skeleton)

---

## References

- **Specification:** `docs/state-loading-spec.md` Section 4 (Skeleton Screen Specifications) and Section 5 (Shimmer Animation CSS)
- **Existing Skeleton:** `frontend/src/components/ui/skeleton.tsx`
- **Theme System:** `frontend/src/app/globals.css` (CSS custom properties)
- **Accessibility:** [WCAG 2.1 Loading Guidance](https://www.w3.org/WAI/WCAG21/Understanding/status-messages.html)

---

## Success Criteria

✅ Story is complete when:
1. All 5 page-specific skeleton components are created
2. Shimmer animation runs at 2s linear infinite
3. Dark mode shimmer is visible and aesthetically pleasing
4. Reduced motion preference disables animation
5. All skeletons are integrated into their respective pages
6. CLS score < 0.1 for all pages
7. Screen reader announces loading state on each page
8. Manual testing checklist is 100% passed
9. Code review approved
10. PR merged to `main`
