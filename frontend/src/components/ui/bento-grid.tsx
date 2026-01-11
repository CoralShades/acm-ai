import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

/**
 * BentoGrid - Responsive grid container for BentoCard components
 * Provides automatic column layout that adapts to screen size
 */
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
  ({ className, columns, gap, children, ...props }, ref) => (
    <div
      ref={ref}
      data-slot="bento-grid"
      className={cn(bentoGridVariants({ columns, gap }), className)}
      {...props}
    >
      {children}
    </div>
  )
);
BentoGrid.displayName = 'BentoGrid';

/**
 * BentoGridAdvanced - Flexible grid with auto-fill and configurable minimum column width
 * Use when you need more control over column sizing than the preset breakpoints
 */
export interface BentoGridAdvancedProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Minimum column width in pixels. Default: 280 */
  minColWidth?: number;
  /** Gap between grid items in pixels. Default: 16 */
  gap?: number;
}

const BentoGridAdvanced = React.forwardRef<HTMLDivElement, BentoGridAdvancedProps>(
  ({ className, minColWidth = 280, gap = 16, children, ...props }, ref) => (
    <div
      ref={ref}
      data-slot="bento-grid-advanced"
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
  )
);
BentoGridAdvanced.displayName = 'BentoGridAdvanced';

export { BentoGrid, BentoGridAdvanced, bentoGridVariants };
