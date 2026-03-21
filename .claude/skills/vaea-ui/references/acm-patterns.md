# ACM Component Patterns — Hard Rules

Load this file when implementing or modifying frontend components. Every rule includes
a code example. Violations block story completion.

---

## 1. AG Grid Theming

### Rule: Single theme definition in globals.css

AG Grid MUST use the `.ag-theme-custom` class defined once in `frontend/src/app/globals.css`.
Never define AG Grid styles inline or in component files.

```tsx
// CORRECT
import { DataGrid } from "@/components/ui/data-grid";

<DataGrid
  rowData={records}
  columnDefs={columnDefs}
  // DataGrid wrapper applies ag-theme-custom automatically
/>

// WRONG — inline style block
<style jsx global>{`
  .ag-theme-alpine {
    --ag-header-background-color: var(--muted);
  }
`}</style>
```

### Rule: Custom AG Grid CSS variables map to semantic tokens

```css
/* In globals.css .ag-theme-custom — ALREADY DEFINED, do not duplicate */
.ag-theme-custom {
  --ag-background-color: var(--card);
  --ag-foreground-color: var(--foreground);
  --ag-header-background-color: var(--muted);
  --ag-border-color: var(--border);
  --ag-row-hover-color: oklch(from var(--primary) l c h / 0.06);
  --ag-selected-row-background-color: oklch(from var(--primary) l c h / 0.10);
  --ag-font-size: 14px;
  --ag-row-height: 40px;
  --ag-header-height: 44px;
}
```

---

## 2. Risk Badge Dual Encoding

### Rule: Every risk level MUST have icon + color

Never rely on color alone. Color-blind users must be able to distinguish risk levels.

```tsx
import { CheckCircle, AlertTriangle, XCircle, HelpCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

// Risk level to icon mapping — MANDATORY
const RISK_ICONS = {
  low: CheckCircle,
  medium: AlertTriangle,
  high: XCircle,
  presumed: HelpCircle,
} as const;

// CORRECT — dual encoded
function RiskBadge({ level }: { level: keyof typeof RISK_ICONS }) {
  const Icon = RISK_ICONS[level];
  return (
    <Badge className={`bg-risk-${level} text-risk-${level}-foreground`}>
      <Icon className="h-3 w-3 mr-1" />
      {level.charAt(0).toUpperCase() + level.slice(1)}
    </Badge>
  );
}

// WRONG — color only
<Badge className="bg-risk-high">High</Badge>
```

### Risk color tokens (defined in globals.css)

| Level | CSS Token | Light | Dark |
|-------|-----------|-------|------|
| Low | `--risk-low` | Green | Brighter green |
| Medium | `--risk-medium` | Amber | Brighter amber |
| High | `--risk-high` | Red | Brighter red |
| Presumed | `--risk-presumed` | Purple | Brighter purple |

---

## 3. Mobile Card Fallback for Data Grids

### Rule: AG Grid replaced with card stack below md breakpoint

```tsx
import { useMediaQuery } from "@/hooks/useMediaQuery";

function ACMRecordsView({ records }: { records: ACMRecord[] }) {
  const isMobile = useMediaQuery("(max-width: 767px)");

  if (isMobile) {
    return (
      <div className="space-y-3 p-4">
        {records.map((record) => (
          <RecordCard key={record.id} record={record} />
        ))}
      </div>
    );
  }

  return <DataGrid rowData={records} columnDefs={columnDefs} />;
}

// RecordCard shows: building code, item name, risk level, location
// Tap to expand shows full record details
function RecordCard({ record }: { record: ACMRecord }) {
  return (
    <Card className="p-4">
      <div className="flex items-center justify-between">
        <Text variant="body" className="font-medium">{record.item_name}</Text>
        <RiskBadge level={record.risk_level} />
      </div>
      <Text variant="caption" className="mt-1">
        {record.building_code} &middot; {record.location_detail}
      </Text>
    </Card>
  );
}
```

---

## 4. Font Loading via next/font

### Rule: Self-host fonts, no external CDN requests

Government privacy compliance — no data sent to Google.

```tsx
// CORRECT — in frontend/src/app/layout.tsx
import { Inter, JetBrains_Mono } from "next/font/google";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains",
  display: "swap",
});

export default function RootLayout({ children }) {
  return (
    <html className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="font-sans">{children}</body>
    </html>
  );
}

// WRONG — runtime Google Fonts link
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@100..900" />
```

---

## 5. ARIA Patterns for ACM Components

### Rule: All interactive elements have accessible names

```tsx
// Buttons with icons only
<button onClick={handleSearch} aria-label="Search ACM records">
  <Search className="h-4 w-4" />
</button>

// Data grids
<div role="region" aria-label="ACM Records Data Grid">
  <DataGrid ... />
</div>

// Progress bars
<Progress
  value={extractionProgress}
  role="progressbar"
  aria-valuemin={0}
  aria-valuemax={100}
  aria-valuenow={extractionProgress}
  aria-label="Extraction progress"
/>

// Loading states
<div role="status" aria-busy="true">
  <span className="sr-only">Loading ACM records...</span>
  <Skeleton variant="shimmer" className="h-[400px]" />
</div>

// Search inputs
<Input
  type="search"
  placeholder="Search records..."
  aria-label="Search ACM records by name, building, or location"
/>

// Breadcrumbs
<nav aria-label="Breadcrumb">
  <ol className="flex items-center gap-2">
    <li><a href="/jobs">Jobs</a></li>
    <li aria-hidden="true"><ChevronRight className="h-4 w-4" /></li>
    <li aria-current="page">{jobTitle}</li>
  </ol>
</nav>
```

### Keyboard Navigation (AG Grid)

```
Enter     → View record detail
E         → Edit record
Delete    → Delete record (with confirmation)
Space     → Expand/collapse group row
Ctrl+K    → Command palette
```

---

## 6. Coral Usage (Expanded Role)

### Rule: Coral (#EB787A) for CTAs, badges, notifications — not just focus rings

```tsx
// Primary CTA — coral stands out against teal UI
<Button variant="default" className="bg-vaea-coral hover:bg-vaea-coral/90 text-white">
  Export to Salesforce
</Button>

// Secondary action — teal (default)
<Button variant="default">
  View Details
</Button>

// Notification dot
<span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-vaea-coral" />

// Important badge
<Badge className="bg-vaea-coral/10 text-vaea-coral border-vaea-coral/20">
  3 Issues
</Badge>

// Focus ring — original role (preserved)
<button className="focus-visible:ring-2 focus-visible:ring-ring">
  {/* ring token maps to vaea-coral */}
</button>
```

---

## 7. Design Token Usage

### Rule: No raw hex, px, or color values in component code

```tsx
// CORRECT — semantic tokens
className="bg-primary text-primary-foreground"
className="text-muted-foreground"
className="border-border"
className="shadow-md"
className="rounded-lg"
className="p-space-4"
className="text-sm leading-snug"

// CORRECT — VAEA brand tokens
className="bg-vaea-teal-300"
className="text-vaea-coral"
className="shadow-vaea-md"

// WRONG — raw values
className="bg-[#53A69D]"
className="text-[14px]"
className="p-[16px]"
className="rounded-[12px]"
style={{ color: '#EB787A' }}
```

---

## 8. Typography via Text Component

### Rule: Use `<Text>` component variants, not raw heading tags

```tsx
import { Text } from "@/components/ui/typography";

// CORRECT
<Text variant="h1">Job Details</Text>
<Text variant="h2">Buildings</Text>
<Text variant="body">Description text here</Text>
<Text variant="body-sm">Smaller body text</Text>
<Text variant="caption">Last updated 3 hours ago</Text>
<Text variant="label">Building Code</Text>
<Text variant="data">BLD#ABC_001</Text>
<Text variant="metric">247</Text>

// WRONG — raw heading tags
<h1 className="text-4xl font-bold tracking-tight">Job Details</h1>
<p className="text-sm text-muted-foreground">Description</p>
```

---

## 9. Dark Mode — Teal-Tinted Backgrounds

### Rule: Dark mode uses teal-tinted backgrounds, never neutral grey

```css
/* CORRECT — teal-tinted dark backgrounds (in globals.css) */
.dark {
  --background: oklch(0.175 0.025 170);    /* Dark teal-tinted */
  --card: oklch(0.225 0.030 172);           /* Slightly lighter teal */
  --secondary: oklch(0.270 0.030 173);      /* Medium dark teal */
}

/* WRONG — neutral grey */
.dark {
  --background: oklch(0.15 0 0);            /* Pure dark grey — off-brand */
  --card: oklch(0.20 0 0);
}
```

When adding new dark mode colors, always include a teal hue component (hue ~170-175 in oklch).

---

## 10. Loading & Error States

### Rule: Skeletons match final layout structure

```tsx
// CORRECT — skeleton mirrors the actual card grid
function JobsPageSkeleton() {
  return (
    <div role="status" aria-busy="true">
      <span className="sr-only">Loading jobs...</span>
      {/* 4 stat card skeletons */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} variant="shimmer" className="h-24 rounded-lg" />
        ))}
      </div>
      {/* 8 job card skeletons */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} variant="shimmer" className="h-48 rounded-lg" />
        ))}
      </div>
    </div>
  );
}

// WRONG — generic spinner
function JobsPageLoading() {
  return <LoadingSpinner size="lg" />;
}
```

### Rule: ErrorBoundary on every page and section

```tsx
// Every page wrapped in ErrorBoundary with meaningful fallback
<ErrorBoundary fallback={<PageErrorFallback />}>
  <JobDetailPage />
</ErrorBoundary>

// Chat panel gets its own boundary
<ErrorBoundary fallback={<SmartChatErrorBoundary onRetry={handleRetry} />}>
  <SmartChatPanel />
</ErrorBoundary>
```

---

## 11. Government Design Patterns

### Aboriginal Acknowledgment Footer
Required for all Victorian government applications. Always present via `branding.ts`.
Never remove or conditionally render it.

### 12px Border Radius
Government standard. Use `rounded-lg` (maps to `--radius: 0.75rem`).
Never use `rounded-full` for card containers (pills/chips are fine).

### Branded Teal Shadows
Light mode shadows use `rgba(42, 89, 81, ...)` (VAEA teal-700 tint).
Use `shadow-sm` through `shadow-xl` tokens, never raw box-shadow values.

### Left-Border Accent Cards
Signature government UI pattern for important information:
```tsx
<Card className="border-l-4 border-l-vaea-teal-300 pl-4">
  <Text variant="body-sm">Important compliance notice</Text>
</Card>
```

---

## 12. Component Import Patterns

### shadcn/ui components from @/components/ui/
```tsx
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Dialog } from "@/components/ui/dialog";
import { Text } from "@/components/ui/typography";
import { DataGrid } from "@/components/ui/data-grid";
import { Skeleton } from "@/components/ui/skeleton";
```

### Icons from lucide-react only
```tsx
import { Search, ChevronRight, AlertTriangle } from "lucide-react";

// Icon sizing conventions:
// h-3 w-3 or h-3.5 w-3.5 — compact contexts (badges, inline)
// h-4 w-4 — standard inline (buttons, menu items)
// h-5 w-5 — card headers, section titles
// h-12 w-12 — empty states, hero illustrations
```

### State management
```tsx
// Server state — React Query
import { useQuery, useMutation } from "@tanstack/react-query";

// Client state — Zustand (v5, named export)
import { create } from "zustand";

// Forms — React Hook Form + Zod
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
```
