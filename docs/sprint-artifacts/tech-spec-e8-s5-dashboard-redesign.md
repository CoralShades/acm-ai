# Tech Spec: E8-S5 - Redesign Dashboard/Home Page

> **Story:** E8-S5
> **Epic:** UI Refresh (Bento Grid Design)
> **Status:** Done
> **Created:** 2025-12-08

---

## Overview

Redesign the dashboard home page using bento grid layout to provide a clear overview of ACM data and quick access to key features.

---

## User Story

**As a** user
**I want** a dashboard showing my ACM data overview
**So that** I can quickly understand my portfolio

---

## Acceptance Criteria

- [x] Bento grid layout with key metrics
- [x] Card 1: Total sources with recent activity
- [x] Card 2: ACM summary (risk distribution chart)
- [x] Card 3: Recent uploads list
- [x] Card 4: Quick actions
- [x] Responsive collapse on mobile

---

## Technical Design

### 1. Dashboard Page

Update `frontend/src/app/(dashboard)/page.tsx`:

```tsx
'use client';

import { BentoGrid } from '@/components/ui/bento-grid';
import {
  BentoCard,
  BentoCardHeader,
  BentoCardTitle,
  BentoCardContent,
  BentoCardFooter,
  BentoCardIcon,
  BentoCardValue,
} from '@/components/ui/bento-card';
import { Button } from '@/components/ui/button';
import { useSources } from '@/hooks/use-sources';
import { useACMSummary } from '@/hooks/use-acm-summary';
import {
  FileText,
  AlertTriangle,
  CheckCircle,
  Upload,
  Search,
  TrendingUp,
  Clock,
  ExternalLink,
} from 'lucide-react';
import Link from 'next/link';
import { RiskChart } from '@/components/dashboard/RiskChart';
import { RecentSourcesList } from '@/components/dashboard/RecentSourcesList';

export default function DashboardPage() {
  const { data: sources, isLoading: sourcesLoading } = useSources();
  const { data: acmSummary, isLoading: acmLoading } = useACMSummary();

  const totalSources = sources?.length || 0;
  const recentSources = sources?.slice(0, 5) || [];

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-muted-foreground">
          Your ACM compliance overview
        </p>
      </div>

      <BentoGrid columns={4} gap="md">
        {/* Total Sources - Small */}
        <BentoCard size="sm" isLoading={sourcesLoading}>
          <BentoCardHeader>
            <BentoCardTitle>Total Sources</BentoCardTitle>
            <BentoCardIcon>
              <FileText className="w-5 h-5" />
            </BentoCardIcon>
          </BentoCardHeader>
          <BentoCardContent>
            <BentoCardValue>{totalSources}</BentoCardValue>
            <p className="text-sm text-muted-foreground mt-1">
              Documents uploaded
            </p>
          </BentoCardContent>
        </BentoCard>

        {/* High Risk Count - Small */}
        <BentoCard size="sm" isLoading={acmLoading}>
          <BentoCardHeader>
            <BentoCardTitle>High Risk Items</BentoCardTitle>
            <BentoCardIcon className="bg-danger-100 text-danger-600">
              <AlertTriangle className="w-5 h-5" />
            </BentoCardIcon>
          </BentoCardHeader>
          <BentoCardContent>
            <BentoCardValue className="text-danger-600">
              {acmSummary?.highRisk || 0}
            </BentoCardValue>
            <p className="text-sm text-muted-foreground mt-1">
              Require attention
            </p>
          </BentoCardContent>
        </BentoCard>

        {/* Medium Risk Count - Small */}
        <BentoCard size="sm" isLoading={acmLoading}>
          <BentoCardHeader>
            <BentoCardTitle>Medium Risk</BentoCardTitle>
            <BentoCardIcon className="bg-warning-100 text-warning-600">
              <TrendingUp className="w-5 h-5" />
            </BentoCardIcon>
          </BentoCardHeader>
          <BentoCardContent>
            <BentoCardValue className="text-warning-600">
              {acmSummary?.mediumRisk || 0}
            </BentoCardValue>
            <p className="text-sm text-muted-foreground mt-1">
              Monitor regularly
            </p>
          </BentoCardContent>
        </BentoCard>

        {/* Low Risk Count - Small */}
        <BentoCard size="sm" isLoading={acmLoading}>
          <BentoCardHeader>
            <BentoCardTitle>Low Risk</BentoCardTitle>
            <BentoCardIcon className="bg-success-100 text-success-600">
              <CheckCircle className="w-5 h-5" />
            </BentoCardIcon>
          </BentoCardHeader>
          <BentoCardContent>
            <BentoCardValue className="text-success-600">
              {acmSummary?.lowRisk || 0}
            </BentoCardValue>
            <p className="text-sm text-muted-foreground mt-1">
              In good condition
            </p>
          </BentoCardContent>
        </BentoCard>

        {/* Risk Distribution Chart - Large */}
        <BentoCard size="lg" isLoading={acmLoading}>
          <BentoCardHeader>
            <BentoCardTitle>Risk Distribution</BentoCardTitle>
          </BentoCardHeader>
          <BentoCardContent>
            <RiskChart data={acmSummary} />
          </BentoCardContent>
          <BentoCardFooter>
            <Link href="/acm" className="text-sm text-primary hover:underline">
              View all ACM data →
            </Link>
          </BentoCardFooter>
        </BentoCard>

        {/* Recent Uploads - Medium */}
        <BentoCard size="md" isLoading={sourcesLoading}>
          <BentoCardHeader>
            <BentoCardTitle>Recent Uploads</BentoCardTitle>
            <BentoCardIcon>
              <Clock className="w-5 h-5" />
            </BentoCardIcon>
          </BentoCardHeader>
          <BentoCardContent>
            <RecentSourcesList sources={recentSources} />
          </BentoCardContent>
          <BentoCardFooter>
            <Link href="/sources" className="text-sm text-primary hover:underline">
              View all sources →
            </Link>
          </BentoCardFooter>
        </BentoCard>

        {/* Quick Actions - Medium */}
        <BentoCard size="md">
          <BentoCardHeader>
            <BentoCardTitle>Quick Actions</BentoCardTitle>
          </BentoCardHeader>
          <BentoCardContent className="space-y-3">
            <Button asChild className="w-full justify-start">
              <Link href="/sources/new">
                <Upload className="w-4 h-4 mr-2" />
                Upload New Document
              </Link>
            </Button>
            <Button variant="outline" asChild className="w-full justify-start">
              <Link href="/sources">
                <Search className="w-4 h-4 mr-2" />
                Search Sources
              </Link>
            </Button>
            <Button variant="outline" asChild className="w-full justify-start">
              <Link href="/acm">
                <ExternalLink className="w-4 h-4 mr-2" />
                View ACM Register
              </Link>
            </Button>
          </BentoCardContent>
        </BentoCard>
      </BentoGrid>
    </div>
  );
}
```

### 2. Risk Chart Component

Create `frontend/src/components/dashboard/RiskChart.tsx`:

```tsx
'use client';

import { useMemo } from 'react';

interface RiskChartProps {
  data?: {
    highRisk: number;
    mediumRisk: number;
    lowRisk: number;
  };
}

export function RiskChart({ data }: RiskChartProps) {
  const chartData = useMemo(() => {
    if (!data) return [];
    const total = data.highRisk + data.mediumRisk + data.lowRisk;
    if (total === 0) return [];

    return [
      { label: 'High', value: data.highRisk, percent: (data.highRisk / total) * 100, color: 'bg-danger-500' },
      { label: 'Medium', value: data.mediumRisk, percent: (data.mediumRisk / total) * 100, color: 'bg-warning-500' },
      { label: 'Low', value: data.lowRisk, percent: (data.lowRisk / total) * 100, color: 'bg-success-500' },
    ];
  }, [data]);

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        No ACM data available
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Bar chart */}
      <div className="flex h-8 rounded-lg overflow-hidden">
        {chartData.map((item) => (
          <div
            key={item.label}
            className={`${item.color} transition-all`}
            style={{ width: `${item.percent}%` }}
          />
        ))}
      </div>

      {/* Legend */}
      <div className="flex justify-between">
        {chartData.map((item) => (
          <div key={item.label} className="text-center">
            <div className={`w-3 h-3 rounded-full ${item.color} mx-auto mb-1`} />
            <p className="text-sm font-medium">{item.value}</p>
            <p className="text-xs text-muted-foreground">{item.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 3. Recent Sources List

Create `frontend/src/components/dashboard/RecentSourcesList.tsx`:

```tsx
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import { FileText } from 'lucide-react';

interface Source {
  id: string;
  title: string;
  created_at: string;
}

export function RecentSourcesList({ sources }: { sources: Source[] }) {
  if (sources.length === 0) {
    return (
      <div className="text-center text-muted-foreground py-4">
        No sources yet
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {sources.map((source) => (
        <Link
          key={source.id}
          href={`/sources/${source.id}`}
          className="flex items-center gap-3 p-2 rounded-lg hover:bg-muted transition-colors"
        >
          <FileText className="w-4 h-4 text-muted-foreground" />
          <div className="flex-1 min-w-0">
            <p className="font-medium truncate">{source.title}</p>
            <p className="text-xs text-muted-foreground">
              {formatDistanceToNow(new Date(source.created_at), { addSuffix: true })}
            </p>
          </div>
        </Link>
      ))}
    </div>
  );
}
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/app/(dashboard)/page.tsx` | Redesign with bento grid |
| `frontend/src/components/dashboard/RiskChart.tsx` | New component |
| `frontend/src/components/dashboard/RecentSourcesList.tsx` | New component |
| `frontend/src/lib/hooks/use-acm-summary.ts` | New hook for ACM stats |

---

## Implementation Notes (2026-01-11)

### Files Created/Modified
- **`frontend/src/app/(dashboard)/page.tsx`** - New dashboard page with bento grid layout showing:
  - 4 metric cards (Total Sources, High Risk, Medium Risk, Low Risk)
  - Risk Distribution chart (large card)
  - Recent Uploads list (medium card)
  - Quick Actions (medium card)
- **`frontend/src/components/dashboard/RiskChart.tsx`** - Horizontal stacked bar chart for risk distribution with legend
- **`frontend/src/components/dashboard/RecentSourcesList.tsx`** - List of recent sources with time formatting using date-fns
- **`frontend/src/lib/hooks/use-acm-summary.ts`** - Wrapper hook around useACMStats with normalized field names

### Implementation Details
- Uses existing `useSources()` and `useACMStats()` hooks via new `useACMSummary()` wrapper
- RiskChart uses the existing ACM stats API fields (high_risk_count, medium_risk_count, low_risk_count)
- RecentSourcesList handles nullable titles with fallback to "Untitled"
- All cards support loading states via BentoCard's `isLoading` prop
- Responsive layout via BentoGrid's column variants (1-4 columns based on screen size)

---

## Senior Developer Review (AI)

**Review Date:** 2026-01-12
**Outcome:** Approved with fixes applied

### Issues Found & Fixed (6 total)

| Severity | Issue | Fix Applied |
|----------|-------|-------------|
| HIGH | No error state handling for API failures | Added error state UI for sources and ACM cards |
| HIGH | Upload link goes to /sources instead of upload action | Changed to `/sources?action=upload` |
| MEDIUM | Sources not sorted by date (newest first) | Added date sorting before slicing |
| MEDIUM | Date parsing could throw on invalid dates | Added try-catch wrapper in `formatCreatedDate()` |
| MEDIUM | RiskChart bar segments have no accessibility labels | Added `role`, `aria-label`, and screen reader summary |
| MEDIUM | No "recent activity" indicator per AC | Added weekly activity count display |

### Low Issues (Not Fixed - Accepted)
- Hardcoded English strings (i18n out of scope)
- "No ACM data" shown during loading (minor UX)
- Large card has sparse content (acceptable design choice)

---

## Dependencies

- E8-S3: BentoCard component
- E8-S4: BentoGrid component

---

## Testing

1. Verify all metric cards display correctly
2. Test loading states for each card
3. Verify risk chart renders with data
4. Test empty states (no sources, no ACM data)
5. Verify responsive layout on mobile
6. Test navigation links work

---

## Estimated Complexity

**Medium** - Page composition with multiple data sources

---
