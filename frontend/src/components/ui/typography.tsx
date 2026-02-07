import * as React from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const textVariants = cva('', {
  variants: {
    variant: {
      h1: 'text-4xl font-bold tracking-tight',
      h2: 'text-3xl font-semibold tracking-tight',
      h3: 'text-2xl font-semibold',
      h4: 'text-xl font-semibold',
      h5: 'text-lg font-medium',
      body: 'text-base leading-relaxed',
      'body-sm': 'text-sm leading-relaxed',
      caption: 'text-xs text-muted-foreground',
      label: 'text-sm font-medium',
      data: 'font-mono text-sm tabular-nums',
      metric: 'text-3xl font-bold tabular-nums',
    },
  },
  defaultVariants: {
    variant: 'body',
  },
})

type TextVariant = NonNullable<VariantProps<typeof textVariants>['variant']>

interface TextProps
  extends React.HTMLAttributes<HTMLElement>,
    VariantProps<typeof textVariants> {
  as?: React.ElementType
}

function getDefaultElement(variant: TextVariant | null | undefined): React.ElementType {
  switch (variant) {
    case 'h1':
      return 'h1'
    case 'h2':
      return 'h2'
    case 'h3':
      return 'h3'
    case 'h4':
      return 'h4'
    case 'h5':
      return 'h5'
    case 'metric':
      return 'span'
    case 'data':
      return 'span'
    case 'caption':
      return 'span'
    case 'label':
      return 'label'
    default:
      return 'p'
  }
}

export function Text({ as, variant, className, ...props }: TextProps) {
  const Component = as || getDefaultElement(variant)
  return <Component className={cn(textVariants({ variant }), className)} {...props} />
}

export { textVariants }
