# Tech Spec: E8-S3 - Create Bento Card Component

> **Story:** E8-S3
> **Epic:** UI Refresh (Bento Grid Design)
> **Status:** Draft
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

- [ ] `BentoCard` component with size variants (sm, md, lg, xl)
- [ ] Header with title and optional actions
- [ ] Content area with padding options
- [ ] Footer slot for actions
- [ ] Hover state with subtle elevation
- [ ] Loading skeleton state
- [ ] Responsive sizing

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
