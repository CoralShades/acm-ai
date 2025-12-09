# Tech Spec: E8-S4 - Create Bento Grid Layout Component

> **Story:** E8-S4
> **Epic:** UI Refresh (Bento Grid Design)
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Create a responsive bento grid container component that automatically arranges cards in an asymmetric grid layout.

---

## User Story

**As a** developer
**I want** a bento grid container component
**So that** cards arrange automatically

---

## Acceptance Criteria

- [ ] `BentoGrid` container with responsive columns
- [ ] Auto-placement algorithm
- [ ] Gap configuration
- [ ] Breakpoint support (1/2/3/4 columns)

---

## Technical Design

### 1. BentoGrid Component

Create `frontend/src/components/ui/bento-grid.tsx`:

```tsx
import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const bentoGridVariants = cva(
  'grid auto-rows-[minmax(180px,auto)]',
  {
    variants: {
      columns: {
        2: 'grid-cols-1 md:grid-cols-2',
        3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
        4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
        auto: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4',
      },
      gap: {
        sm: 'gap-2',
        md: 'gap-4',
        lg: 'gap-6',
      },
    },
    defaultVariants: {
      columns: 'auto',
      gap: 'md',
    },
  }
);

export interface BentoGridProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof bentoGridVariants> {}

const BentoGrid = React.forwardRef<HTMLDivElement, BentoGridProps>(
  ({ className, columns, gap, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(bentoGridVariants({ columns, gap }), className)}
      {...props}
    />
  )
);
BentoGrid.displayName = 'BentoGrid';

export { BentoGrid, bentoGridVariants };
```

### 2. Advanced Grid with Masonry-like Layout

For more complex layouts:

```tsx
import * as React from 'react';
import { cn } from '@/lib/utils';

interface BentoGridAdvancedProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  minColWidth?: number;
  gap?: number;
}

export function BentoGridAdvanced({
  children,
  minColWidth = 280,
  gap = 16,
  className,
  ...props
}: BentoGridAdvancedProps) {
  return (
    <div
      className={cn('w-full', className)}
      style={{
        display: 'grid',
        gridTemplateColumns: `repeat(auto-fill, minmax(${minColWidth}px, 1fr))`,
        gridAutoRows: 'minmax(180px, auto)',
        gap: `${gap}px`,
      }}
      {...props}
    >
      {children}
    </div>
  );
}
```

### 3. Named Grid Areas (Optional)

For explicit layouts:

```tsx
interface BentoGridTemplateProps {
  template: string;
  children: React.ReactNode;
  className?: string;
}

export function BentoGridTemplate({
  template,
  children,
  className,
}: BentoGridTemplateProps) {
  return (
    <div
      className={cn('grid gap-4', className)}
      style={{
        gridTemplateAreas: template,
        gridTemplateColumns: 'repeat(4, 1fr)',
        gridAutoRows: 'minmax(180px, auto)',
      }}
    >
      {children}
    </div>
  );
}

// Usage:
<BentoGridTemplate
  template={`
    "hero hero stats stats"
    "chart chart list list"
    "chart chart list list"
  `}
>
  <div style={{ gridArea: 'hero' }}>Hero Card</div>
  <div style={{ gridArea: 'stats' }}>Stats Card</div>
  <div style={{ gridArea: 'chart' }}>Chart Card</div>
  <div style={{ gridArea: 'list' }}>List Card</div>
</BentoGridTemplate>
```

### 4. Responsive Configuration

Create responsive utilities:

```tsx
// Hook for responsive grid columns
import { useMediaQuery } from '@/hooks/use-media-query';

export function useGridColumns() {
  const isXl = useMediaQuery('(min-width: 1280px)');
  const isLg = useMediaQuery('(min-width: 1024px)');
  const isMd = useMediaQuery('(min-width: 768px)');

  if (isXl) return 4;
  if (isLg) return 3;
  if (isMd) return 2;
  return 1;
}
```

### 5. Usage Example

```tsx
import { BentoGrid } from '@/components/ui/bento-grid';
import {
  BentoCard,
  BentoCardHeader,
  BentoCardTitle,
  BentoCardContent,
} from '@/components/ui/bento-card';

export function Dashboard() {
  return (
    <BentoGrid columns={4} gap="md">
      {/* Large hero card */}
      <BentoCard size="lg">
        <BentoCardHeader>
          <BentoCardTitle>Welcome to ACM-AI</BentoCardTitle>
        </BentoCardHeader>
        <BentoCardContent>
          <p>Your ACM compliance dashboard</p>
        </BentoCardContent>
      </BentoCard>

      {/* Small metric cards */}
      <BentoCard size="sm">
        <BentoCardHeader>
          <BentoCardTitle>Sources</BentoCardTitle>
        </BentoCardHeader>
        <BentoCardContent>
          <span className="text-3xl font-bold">24</span>
        </BentoCardContent>
      </BentoCard>

      <BentoCard size="sm">
        <BentoCardHeader>
          <BentoCardTitle>High Risk</BentoCardTitle>
        </BentoCardHeader>
        <BentoCardContent>
          <span className="text-3xl font-bold text-danger-500">3</span>
        </BentoCardContent>
      </BentoCard>

      {/* Medium chart card */}
      <BentoCard size="md">
        <BentoCardHeader>
          <BentoCardTitle>Risk Distribution</BentoCardTitle>
        </BentoCardHeader>
        <BentoCardContent>
          {/* Chart component */}
        </BentoCardContent>
      </BentoCard>
    </BentoGrid>
  );
}
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/components/ui/bento-grid.tsx` | New component |
| `frontend/src/hooks/use-media-query.ts` | New hook (if not exists) |

---

## Dependencies

- E8-S3: BentoCard component

---

## Testing

1. Test with various card size combinations
2. Verify responsive column changes at breakpoints
3. Test gap variants
4. Verify auto-row sizing with different content
5. Test with many cards (10+)
6. Verify no overflow or layout breaks

---

## Estimated Complexity

**Low** - CSS Grid with utility classes

---
