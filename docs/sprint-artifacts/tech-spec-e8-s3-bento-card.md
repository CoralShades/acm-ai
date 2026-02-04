# Tech Spec: E8-S3 - Create Bento Card Component

> **Story:** E8-S3
> **Epic:** UI Refresh (Bento Grid Design)
> **Status:** Done
> **Created:** 2025-12-08

---

## Overview

Create a reusable bento card component with multiple size variants for building dashboard layouts.

---

## User Story

**As a** developer
**I want** a reusable bento card component
**So that** I can build grid layouts consistently

---

## Acceptance Criteria

- [x] `BentoCard` component with size variants (sm, md, lg, xl)
- [x] Header with title and optional actions
- [x] Content area with padding options
- [x] Footer slot for actions
- [x] Hover state with subtle elevation
- [x] Loading skeleton state
- [x] Responsive sizing

---

## Technical Design

### 1. BentoCard Component

Create `frontend/src/components/ui/bento-card.tsx`:

```tsx
import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';

const bentoCardVariants = cva(
  'relative rounded-xl border bg-card text-card-foreground transition-all duration-200',
  {
    variants: {
      size: {
        sm: 'col-span-1 row-span-1',
        md: 'col-span-1 row-span-2 md:col-span-2 md:row-span-1',
        lg: 'col-span-1 row-span-2 md:col-span-2 md:row-span-2',
        xl: 'col-span-1 row-span-3 md:col-span-3 md:row-span-2',
        full: 'col-span-full',
      },
      interactive: {
        true: 'cursor-pointer hover:shadow-lg hover:-translate-y-0.5',
        false: '',
      },
    },
    defaultVariants: {
      size: 'sm',
      interactive: false,
    },
  }
);

export interface BentoCardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof bentoCardVariants> {
  isLoading?: boolean;
}

const BentoCard = React.forwardRef<HTMLDivElement, BentoCardProps>(
  ({ className, size, interactive, isLoading, children, ...props }, ref) => {
    if (isLoading) {
      return (
        <div
          ref={ref}
          className={cn(bentoCardVariants({ size }), className)}
          {...props}
        >
          <BentoCardSkeleton />
        </div>
      );
    }

    return (
      <div
        ref={ref}
        className={cn(bentoCardVariants({ size, interactive }), className)}
        {...props}
      >
        {children}
      </div>
    );
  }
);
BentoCard.displayName = 'BentoCard';

const BentoCardHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      'flex items-center justify-between p-4 pb-2',
      className
    )}
    {...props}
  />
));
BentoCardHeader.displayName = 'BentoCardHeader';

const BentoCardTitle = React.forwardRef<
  HTMLHeadingElement,
  React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={cn('text-lg font-semibold leading-none tracking-tight', className)}
    {...props}
  />
));
BentoCardTitle.displayName = 'BentoCardTitle';

const BentoCardDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn('text-sm text-muted-foreground', className)}
    {...props}
  />
));
BentoCardDescription.displayName = 'BentoCardDescription';

const BentoCardActions = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('flex items-center gap-2', className)}
    {...props}
  />
));
BentoCardActions.displayName = 'BentoCardActions';

const BentoCardContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { noPadding?: boolean }
>(({ className, noPadding, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      'flex-1',
      !noPadding && 'p-4 pt-0',
      className
    )}
    {...props}
  />
));
BentoCardContent.displayName = 'BentoCardContent';

const BentoCardFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      'flex items-center justify-between p-4 pt-0 mt-auto',
      className
    )}
    {...props}
  />
));
BentoCardFooter.displayName = 'BentoCardFooter';

const BentoCardIcon = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn(
      'flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary',
      className
    )}
    {...props}
  />
));
BentoCardIcon.displayName = 'BentoCardIcon';

const BentoCardValue = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn('text-3xl font-bold tracking-tight', className)}
    {...props}
  />
));
BentoCardValue.displayName = 'BentoCardValue';

function BentoCardSkeleton() {
  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-24" />
        <Skeleton className="h-8 w-8 rounded-lg" />
      </div>
      <Skeleton className="h-8 w-16" />
      <Skeleton className="h-4 w-32" />
    </div>
  );
}

export {
  BentoCard,
  BentoCardHeader,
  BentoCardTitle,
  BentoCardDescription,
  BentoCardActions,
  BentoCardContent,
  BentoCardFooter,
  BentoCardIcon,
  BentoCardValue,
  BentoCardSkeleton,
};
```

### 2. Usage Examples

```tsx
import {
  BentoCard,
  BentoCardHeader,
  BentoCardTitle,
  BentoCardContent,
  BentoCardIcon,
  BentoCardValue,
} from '@/components/ui/bento-card';
import { FileText, AlertTriangle } from 'lucide-react';

// Small metric card
<BentoCard size="sm">
  <BentoCardHeader>
    <BentoCardTitle>Total Sources</BentoCardTitle>
    <BentoCardIcon>
      <FileText className="w-5 h-5" />
    </BentoCardIcon>
  </BentoCardHeader>
  <BentoCardContent>
    <BentoCardValue>42</BentoCardValue>
    <p className="text-sm text-muted-foreground">+5 this week</p>
  </BentoCardContent>
</BentoCard>

// Large interactive card
<BentoCard size="lg" interactive onClick={() => navigate('/acm')}>
  <BentoCardHeader>
    <BentoCardTitle>High Risk Items</BentoCardTitle>
  </BentoCardHeader>
  <BentoCardContent>
    {/* Chart or list content */}
  </BentoCardContent>
</BentoCard>

// Loading state
<BentoCard size="md" isLoading />
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/components/ui/bento-card.tsx` | New component |

---

## Dependencies

- E8-S2: Design Tokens (colors, shadows, spacing)

---

## Testing

1. Render cards in all size variants
2. Test hover animation on interactive cards
3. Verify loading skeleton displays
4. Test responsive sizing at breakpoints
5. Verify header/content/footer layout
6. Check dark mode appearance

---

## Estimated Complexity

**Medium** - Compound component with variants

---

## Dev Agent Record

### Implementation Date: 2026-01-11

### Files Created:
| File | Change |
|------|--------|
| `frontend/src/components/ui/bento-card.tsx` | New - Complete bento card component system |

### Implementation Notes:

**Components Created:**
- `BentoCard` - Main container with size variants (sm, md, lg, xl, full) and interactive hover state
- `BentoCardHeader` - Flex container for title and actions
- `BentoCardTitle` - Styled h3 heading
- `BentoCardDescription` - Muted text description
- `BentoCardActions` - Flex container for action buttons
- `BentoCardContent` - Content area with optional `noPadding` prop
- `BentoCardFooter` - Footer aligned to bottom with `mt-auto`
- `BentoCardIcon` - Icon container with primary background tint
- `BentoCardValue` - Large bold value display
- `BentoCardSkeleton` - Loading skeleton using CSS animations

**Design Decisions:**
1. Used `class-variance-authority` for type-safe variant handling
2. Skeleton uses inline CSS `animate-pulse` instead of separate Skeleton component (not present in project)
3. Used `duration-normal` token from design tokens for transitions
4. Added `flex flex-col` to base card for proper footer alignment
5. All components use `forwardRef` for ref forwarding compatibility

**Acceptance Criteria Verification:**
- [x] Size variants: sm, md, lg, xl, full - all implemented in `bentoCardVariants`
- [x] Header with actions: `BentoCardHeader` + `BentoCardActions` slots
- [x] Content padding: `noPadding` prop on `BentoCardContent`
- [x] Footer slot: `BentoCardFooter` with `mt-auto` positioning
- [x] Hover elevation: `interactive` variant adds `hover:shadow-lg hover:-translate-y-0.5`
- [x] Loading skeleton: `isLoading` prop renders `BentoCardSkeleton`
- [x] Responsive sizing: Grid spans adjust at `md:` breakpoint

### Verification:
- TypeScript: PASS
- ESLint: PASS

### Code Review Fixes (2026-01-11):

**M1: Added focus state for keyboard accessibility**
- Added `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2` to interactive variant
- Ensures keyboard users can see focus state when tabbing to interactive cards

**M2: Added aria-busy for loading state**
- Added `aria-busy="true"` and `aria-label="Loading"` to loading state container
- Screen readers now announce when content is loading

**L1: Added tabIndex for keyboard focus**
- Added `tabIndex={interactive ? 0 : undefined}` to BentoCard
- Interactive cards are now focusable via keyboard

**L2: Tech-spec code example noted**
- Tech-spec shows Skeleton import that doesn't exist in project
- Implementation correctly uses inline skeleton - documented as intentional deviation

**L3: Added data-slot attributes for styling consistency**
- Added `data-slot` attribute to all subcomponents matching existing card.tsx pattern:
  - `bento-card`, `bento-card-header`, `bento-card-title`, `bento-card-description`
  - `bento-card-actions`, `bento-card-content`, `bento-card-footer`
  - `bento-card-icon`, `bento-card-value`

---
