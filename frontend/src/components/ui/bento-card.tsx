import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const bentoCardVariants = cva(
  'relative rounded-xl border bg-card text-card-foreground transition-all duration-normal flex flex-col',
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
        true: 'cursor-pointer hover:shadow-lg hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
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
          data-slot="bento-card"
          className={cn(bentoCardVariants({ size }), className)}
          aria-busy="true"
          aria-label="Loading"
          {...props}
        >
          <BentoCardSkeleton />
        </div>
      );
    }

    return (
      <div
        ref={ref}
        data-slot="bento-card"
        className={cn(bentoCardVariants({ size, interactive }), className)}
        tabIndex={interactive ? 0 : undefined}
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
    data-slot="bento-card-header"
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
    data-slot="bento-card-title"
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
    data-slot="bento-card-description"
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
    data-slot="bento-card-actions"
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
    data-slot="bento-card-content"
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
    data-slot="bento-card-footer"
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
    data-slot="bento-card-icon"
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
    data-slot="bento-card-value"
    className={cn('text-3xl font-bold tracking-tight', className)}
    {...props}
  />
));
BentoCardValue.displayName = 'BentoCardValue';

function BentoCardSkeleton() {
  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="h-5 w-24 rounded-md bg-muted animate-pulse" />
        <div className="h-8 w-8 rounded-lg bg-muted animate-pulse" />
      </div>
      <div className="h-8 w-16 rounded-md bg-muted animate-pulse" />
      <div className="h-4 w-32 rounded-md bg-muted animate-pulse" />
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
