# Tech Spec: E8-S10 - Dark Mode Refinement

> **Story:** E8-S10
> **Epic:** UI Refresh (Bento Grid Design)
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Refine dark mode colors and ensure all components have proper contrast and visual polish in dark mode.

---

## User Story

**As a** user
**I want** a polished dark mode
**So that** I can work comfortably at night

---

## Acceptance Criteria

- [ ] Dark mode colors reviewed and refined
- [ ] Sufficient contrast ratios (WCAG AA)
- [ ] Charts and data vis updated
- [ ] Smooth transition between modes

---

## Technical Design

### 1. Dark Mode Color Refinement

Update `frontend/src/app/globals.css`:

```css
.dark {
  /* Background layers with subtle hierarchy */
  --background: 222 47% 6%;        /* Darkest - page bg */
  --card: 222 47% 8%;              /* Card background */
  --popover: 222 47% 10%;          /* Elevated surfaces */
  --muted: 217 33% 12%;            /* Muted backgrounds */

  /* Foreground with proper contrast */
  --foreground: 210 40% 98%;       /* Primary text - high contrast */
  --card-foreground: 210 40% 98%;
  --popover-foreground: 210 40% 98%;
  --muted-foreground: 215 20% 60%; /* Secondary text */

  /* Primary colors - brighter for dark mode */
  --primary: 217 91% 65%;          /* Brighter blue */
  --primary-foreground: 222 47% 11%;

  /* Secondary - subtle contrast */
  --secondary: 217 33% 17%;
  --secondary-foreground: 210 40% 98%;

  /* Accent - visible but not harsh */
  --accent: 217 33% 17%;
  --accent-foreground: 210 40% 98%;

  /* Semantic colors - adjusted for dark bg */
  --destructive: 0 63% 55%;        /* Less saturated red */
  --destructive-foreground: 210 40% 98%;

  /* Risk colors - darker backgrounds, brighter text */
  --risk-low: 142 55% 50%;
  --risk-low-bg: 142 55% 12%;
  --risk-medium: 45 80% 55%;
  --risk-medium-bg: 45 80% 12%;
  --risk-high: 0 70% 55%;
  --risk-high-bg: 0 70% 12%;

  /* Borders - subtle but visible */
  --border: 217 33% 17%;
  --input: 217 33% 17%;
  --ring: 217 91% 65%;

  /* Shadows - more pronounced for dark mode */
  --shadow-color: 222 47% 3%;
}

/* Smooth dark mode transition */
html {
  color-scheme: light dark;
}

html.dark {
  color-scheme: dark;
}

* {
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

/* Disable transitions during theme switch to prevent flash */
html.disable-transitions * {
  transition: none !important;
}
```

### 2. Component-Specific Dark Mode Fixes

```css
/* Cards with subtle border glow in dark mode */
.dark .card {
  box-shadow:
    0 0 0 1px hsl(var(--border)),
    0 1px 3px hsl(var(--shadow-color) / 0.3);
}

/* Input fields - better visibility */
.dark input,
.dark textarea,
.dark select {
  background-color: hsl(var(--background));
}

.dark input:focus,
.dark textarea:focus {
  box-shadow: 0 0 0 2px hsl(var(--ring) / 0.5);
}

/* Buttons - ensure visibility */
.dark .btn-primary {
  background: hsl(var(--primary));
  color: hsl(var(--primary-foreground));
}

/* AG Grid dark mode */
.dark .ag-theme-custom {
  --ag-background-color: hsl(var(--card));
  --ag-foreground-color: hsl(var(--foreground));
  --ag-header-background-color: hsl(var(--muted));
  --ag-odd-row-background-color: hsl(var(--background));
  --ag-row-hover-color: hsl(var(--accent));
  --ag-border-color: hsl(var(--border));
}

/* Charts - use dark-friendly colors */
.dark .chart-container {
  --chart-grid-color: hsl(var(--border));
  --chart-text-color: hsl(var(--muted-foreground));
}

/* Scrollbars */
.dark ::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.dark ::-webkit-scrollbar-track {
  background: hsl(var(--muted));
}

.dark ::-webkit-scrollbar-thumb {
  background: hsl(var(--border));
  border-radius: 4px;
}

.dark ::-webkit-scrollbar-thumb:hover {
  background: hsl(var(--muted-foreground) / 0.3);
}
```

### 3. Theme Toggle Enhancement

Update `frontend/src/components/ui/theme-toggle.tsx`:

```tsx
'use client';

import * as React from 'react';
import { Moon, Sun, Monitor } from 'lucide-react';
import { useTheme } from 'next-themes';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const handleThemeChange = (newTheme: string) => {
    // Disable transitions during switch
    document.documentElement.classList.add('disable-transitions');
    setTheme(newTheme);
    setTimeout(() => {
      document.documentElement.classList.remove('disable-transitions');
    }, 100);
  };

  if (!mounted) {
    return (
      <Button variant="ghost" size="icon">
        <Sun className="h-5 w-5" />
      </Button>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon">
          <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => handleThemeChange('light')}>
          <Sun className="mr-2 h-4 w-4" />
          Light
          {theme === 'light' && <span className="ml-auto">✓</span>}
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleThemeChange('dark')}>
          <Moon className="mr-2 h-4 w-4" />
          Dark
          {theme === 'dark' && <span className="ml-auto">✓</span>}
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => handleThemeChange('system')}>
          <Monitor className="mr-2 h-4 w-4" />
          System
          {theme === 'system' && <span className="ml-auto">✓</span>}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

### 4. Contrast Checker Utility

Create `frontend/src/lib/utils/contrast.ts`:

```typescript
/**
 * Calculate contrast ratio between two colors.
 * Returns ratio as number (e.g., 4.5 means 4.5:1)
 */
export function getContrastRatio(foreground: string, background: string): number {
  const lum1 = getLuminance(foreground);
  const lum2 = getLuminance(background);
  const lighter = Math.max(lum1, lum2);
  const darker = Math.min(lum1, lum2);
  return (lighter + 0.05) / (darker + 0.05);
}

function getLuminance(hex: string): number {
  const rgb = hexToRgb(hex);
  if (!rgb) return 0;

  const [r, g, b] = [rgb.r, rgb.g, rgb.b].map((v) => {
    v /= 255;
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  });

  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null;
}

/**
 * Check if contrast meets WCAG AA standard
 * @param ratio - Contrast ratio
 * @param largeText - Whether text is large (18pt+ or 14pt+ bold)
 */
export function meetsWCAG_AA(ratio: number, largeText = false): boolean {
  return largeText ? ratio >= 3 : ratio >= 4.5;
}
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/app/globals.css` | Refined dark mode colors |
| `frontend/src/components/ui/theme-toggle.tsx` | Enhanced toggle |
| `frontend/src/lib/utils/contrast.ts` | New - contrast utility |

---

## Dependencies

- E8-S2: Design tokens (color system)

---

## Testing

1. Toggle through light/dark/system modes
2. Verify smooth transitions
3. Check all pages in dark mode
4. Verify AG Grid styling in dark mode
5. Check charts render correctly
6. Run contrast checker on key text
7. Test on different monitors/brightness

### WCAG Contrast Checklist

| Element | Foreground | Background | Ratio | Pass |
|---------|------------|------------|-------|------|
| Body text | 98% white | 6% dark | 17.5:1 | ✓ |
| Muted text | 60% gray | 6% dark | 7.2:1 | ✓ |
| Primary button | 11% dark | 65% blue | 5.8:1 | ✓ |
| Link on dark | 65% blue | 6% dark | 6.5:1 | ✓ |

---

## Estimated Complexity

**Medium** - Color system refinement across all components

---
