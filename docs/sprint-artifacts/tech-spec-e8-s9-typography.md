# Tech Spec: E8-S9 - Typography & Font Updates

> **Story:** E8-S9
> **Epic:** UI Refresh (Bento Grid Design)
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Update typography system with modern font pairing and optimized styles for data-heavy interfaces.

---

## User Story

**As a** user
**I want** professional, readable typography
**So that** data is easy to scan

---

## Acceptance Criteria

- [ ] Updated font pairing (Inter + monospace for data)
- [ ] Consistent heading hierarchy
- [ ] Data table typography optimized
- [ ] Line height and spacing adjusted

---

## Technical Design

### 1. Font Installation

Update `frontend/src/app/layout.tsx`:

```tsx
import { Inter, JetBrains_Mono } from 'next/font/google';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
});

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
```

### 2. Typography CSS

Add to `frontend/src/app/globals.css`:

```css
/* Typography System */

/* Base Typography */
body {
  font-family: var(--font-sans);
  font-size: var(--text-base);
  line-height: var(--leading-normal);
  color: hsl(var(--foreground));
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Heading Hierarchy */
h1, .h1 {
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  letter-spacing: -0.02em;
}

h2, .h2 {
  font-size: var(--text-3xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-tight);
  letter-spacing: -0.01em;
}

h3, .h3 {
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-snug);
}

h4, .h4 {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-snug);
}

h5, .h5 {
  font-size: var(--text-lg);
  font-weight: var(--font-medium);
  line-height: var(--leading-normal);
}

h6, .h6 {
  font-size: var(--text-base);
  font-weight: var(--font-medium);
  line-height: var(--leading-normal);
}

/* Body Text */
.text-body {
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
}

.text-body-sm {
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
}

/* Data Typography - For tables and metrics */
.text-data {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  font-variant-numeric: tabular-nums;
  letter-spacing: 0;
}

.text-metric {
  font-family: var(--font-sans);
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

/* Caption and Label */
.text-caption {
  font-size: var(--text-xs);
  line-height: var(--leading-normal);
  color: hsl(var(--muted-foreground));
}

.text-label {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  letter-spacing: 0.01em;
}

/* Code and Technical */
code, .text-code {
  font-family: var(--font-mono);
  font-size: 0.9em;
  background: hsl(var(--muted));
  padding: 0.2em 0.4em;
  border-radius: var(--radius-sm);
}

pre {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  overflow-x: auto;
}

/* Link Styles */
a {
  color: hsl(var(--primary));
  text-decoration: none;
}

a:hover {
  text-decoration: underline;
}

/* Selection */
::selection {
  background: hsl(var(--primary) / 0.2);
  color: hsl(var(--foreground));
}
```

### 3. Tailwind Typography Plugin Config

Update `frontend/tailwind.config.ts`:

```typescript
import type { Config } from 'tailwindcss';
import typography from '@tailwindcss/typography';

const config: Config = {
  plugins: [typography],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-sans)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-mono)', 'monospace'],
      },
      typography: {
        DEFAULT: {
          css: {
            '--tw-prose-body': 'hsl(var(--foreground))',
            '--tw-prose-headings': 'hsl(var(--foreground))',
            '--tw-prose-links': 'hsl(var(--primary))',
            '--tw-prose-code': 'hsl(var(--foreground))',
            maxWidth: 'none',
          },
        },
      },
    },
  },
};

export default config;
```

### 4. Typography Component

Create `frontend/src/components/ui/typography.tsx`:

```tsx
import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

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
});

interface TextProps
  extends React.HTMLAttributes<HTMLElement>,
    VariantProps<typeof textVariants> {
  as?: keyof JSX.IntrinsicElements;
}

export function Text({ as, variant, className, ...props }: TextProps) {
  const Component = as || getDefaultElement(variant);
  return (
    <Component
      className={cn(textVariants({ variant }), className)}
      {...props}
    />
  );
}

function getDefaultElement(variant: TextProps['variant']): keyof JSX.IntrinsicElements {
  switch (variant) {
    case 'h1': return 'h1';
    case 'h2': return 'h2';
    case 'h3': return 'h3';
    case 'h4': return 'h4';
    case 'h5': return 'h5';
    default: return 'p';
  }
}
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/app/layout.tsx` | Add font imports |
| `frontend/src/app/globals.css` | Add typography styles |
| `frontend/tailwind.config.ts` | Typography plugin config |
| `frontend/src/components/ui/typography.tsx` | New component |

---

## Dependencies

- E8-S2: Design tokens (font references)

---

## Testing

1. Verify Inter font loads correctly
2. Verify JetBrains Mono for code/data
3. Check heading hierarchy visually
4. Verify tabular nums in data tables
5. Test dark mode typography
6. Check line heights for readability
7. Verify responsive font sizing

---

## Estimated Complexity

**Low** - CSS and font configuration

---
