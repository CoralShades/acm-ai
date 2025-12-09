# Tech Spec: E8-S2 - Define ACM-AI Design Tokens

> **Story:** E8-S2
> **Epic:** UI Refresh (Bento Grid Design)
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Create a comprehensive design token system for ACM-AI including colors, typography, spacing, and other visual properties.

---

## User Story

**As a** designer/developer
**I want** a consistent design token system
**So that** the UI is cohesive

---

## Acceptance Criteria

- [ ] Color palette defined (primary, secondary, accent, semantic)
- [ ] Typography scale (headings, body, data)
- [ ] Spacing scale
- [ ] Border radius tokens
- [ ] Shadow tokens for elevation
- [ ] Dark mode variants

---

## Technical Design

### 1. Design Tokens File

Create `frontend/src/styles/tokens.css`:

```css
/* ACM-AI Design Tokens */
/* Using OKLch color space for perceptually uniform colors */

:root {
  /* ========================================
     COLORS - Primary Palette
     ======================================== */

  /* Primary - Professional Blue */
  --color-primary-50: oklch(97% 0.01 250);
  --color-primary-100: oklch(93% 0.03 250);
  --color-primary-200: oklch(86% 0.06 250);
  --color-primary-300: oklch(75% 0.12 250);
  --color-primary-400: oklch(63% 0.18 250);
  --color-primary-500: oklch(55% 0.21 250);
  --color-primary-600: oklch(48% 0.21 250);
  --color-primary-700: oklch(42% 0.18 250);
  --color-primary-800: oklch(35% 0.14 250);
  --color-primary-900: oklch(28% 0.10 250);

  /* Secondary - Neutral Slate */
  --color-secondary-50: oklch(98% 0.005 260);
  --color-secondary-100: oklch(95% 0.01 260);
  --color-secondary-200: oklch(90% 0.015 260);
  --color-secondary-300: oklch(82% 0.02 260);
  --color-secondary-400: oklch(65% 0.02 260);
  --color-secondary-500: oklch(55% 0.02 260);
  --color-secondary-600: oklch(45% 0.02 260);
  --color-secondary-700: oklch(35% 0.015 260);
  --color-secondary-800: oklch(25% 0.01 260);
  --color-secondary-900: oklch(18% 0.005 260);

  /* Accent - Cyan/Teal for AI/Tech feel */
  --color-accent-500: oklch(70% 0.15 195);

  /* ========================================
     COLORS - Semantic
     ======================================== */

  /* Success - Green (Low Risk) */
  --color-success-50: oklch(97% 0.03 145);
  --color-success-100: oklch(93% 0.06 145);
  --color-success-500: oklch(60% 0.18 145);
  --color-success-600: oklch(52% 0.16 145);
  --color-success-700: oklch(45% 0.14 145);

  /* Warning - Amber (Medium Risk) */
  --color-warning-50: oklch(98% 0.03 85);
  --color-warning-100: oklch(95% 0.08 85);
  --color-warning-500: oklch(75% 0.18 75);
  --color-warning-600: oklch(65% 0.18 70);
  --color-warning-700: oklch(55% 0.16 65);

  /* Danger - Red (High Risk) */
  --color-danger-50: oklch(97% 0.02 25);
  --color-danger-100: oklch(93% 0.05 25);
  --color-danger-500: oklch(60% 0.22 25);
  --color-danger-600: oklch(52% 0.20 25);
  --color-danger-700: oklch(45% 0.18 25);

  /* ========================================
     TYPOGRAPHY
     ======================================== */

  /* Font Families */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  --font-data: 'Tabular Nums', var(--font-mono);

  /* Font Sizes - Modular Scale (1.25 ratio) */
  --text-xs: 0.75rem;     /* 12px */
  --text-sm: 0.875rem;    /* 14px */
  --text-base: 1rem;      /* 16px */
  --text-lg: 1.125rem;    /* 18px */
  --text-xl: 1.25rem;     /* 20px */
  --text-2xl: 1.5rem;     /* 24px */
  --text-3xl: 1.875rem;   /* 30px */
  --text-4xl: 2.25rem;    /* 36px */

  /* Line Heights */
  --leading-none: 1;
  --leading-tight: 1.25;
  --leading-snug: 1.375;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;
  --leading-loose: 2;

  /* Font Weights */
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;

  /* ========================================
     SPACING
     ======================================== */

  /* Base unit: 4px */
  --space-0: 0;
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-5: 1.25rem;   /* 20px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-10: 2.5rem;   /* 40px */
  --space-12: 3rem;     /* 48px */
  --space-16: 4rem;     /* 64px */
  --space-20: 5rem;     /* 80px */
  --space-24: 6rem;     /* 96px */

  /* ========================================
     BORDER RADIUS
     ======================================== */

  --radius-none: 0;
  --radius-sm: 0.25rem;   /* 4px */
  --radius-md: 0.5rem;    /* 8px */
  --radius-lg: 0.75rem;   /* 12px */
  --radius-xl: 1rem;      /* 16px */
  --radius-2xl: 1.5rem;   /* 24px */
  --radius-full: 9999px;

  /* ========================================
     SHADOWS / ELEVATION
     ======================================== */

  --shadow-xs: 0 1px 2px oklch(0% 0 0 / 0.05);
  --shadow-sm: 0 1px 3px oklch(0% 0 0 / 0.1), 0 1px 2px oklch(0% 0 0 / 0.06);
  --shadow-md: 0 4px 6px oklch(0% 0 0 / 0.1), 0 2px 4px oklch(0% 0 0 / 0.06);
  --shadow-lg: 0 10px 15px oklch(0% 0 0 / 0.1), 0 4px 6px oklch(0% 0 0 / 0.05);
  --shadow-xl: 0 20px 25px oklch(0% 0 0 / 0.1), 0 10px 10px oklch(0% 0 0 / 0.04);

  /* ========================================
     TRANSITIONS
     ======================================== */

  --duration-fast: 150ms;
  --duration-normal: 250ms;
  --duration-slow: 350ms;
  --ease-default: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);

  /* ========================================
     Z-INDEX
     ======================================== */

  --z-base: 0;
  --z-dropdown: 10;
  --z-sticky: 20;
  --z-modal: 30;
  --z-popover: 40;
  --z-toast: 50;
}

/* ========================================
   DARK MODE OVERRIDES
   ======================================== */

.dark {
  --color-primary-50: oklch(20% 0.02 250);
  --color-primary-100: oklch(25% 0.04 250);
  --color-primary-200: oklch(30% 0.08 250);
  --color-primary-500: oklch(65% 0.18 250);
  --color-primary-600: oklch(72% 0.16 250);

  --color-secondary-50: oklch(15% 0.005 260);
  --color-secondary-100: oklch(20% 0.01 260);
  --color-secondary-800: oklch(90% 0.01 260);
  --color-secondary-900: oklch(95% 0.005 260);

  --shadow-xs: 0 1px 2px oklch(0% 0 0 / 0.3);
  --shadow-sm: 0 1px 3px oklch(0% 0 0 / 0.4);
  --shadow-md: 0 4px 6px oklch(0% 0 0 / 0.4);
}
```

### 2. Tailwind Integration

Update `frontend/tailwind.config.ts`:

```typescript
import type { Config } from 'tailwindcss';

const config: Config = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: 'var(--color-primary-50)',
          100: 'var(--color-primary-100)',
          // ... all shades
          900: 'var(--color-primary-900)',
        },
        // Similar for secondary, success, warning, danger
      },
      fontFamily: {
        sans: 'var(--font-sans)',
        mono: 'var(--font-mono)',
        data: 'var(--font-data)',
      },
      borderRadius: {
        sm: 'var(--radius-sm)',
        md: 'var(--radius-md)',
        lg: 'var(--radius-lg)',
        xl: 'var(--radius-xl)',
      },
      boxShadow: {
        xs: 'var(--shadow-xs)',
        sm: 'var(--shadow-sm)',
        md: 'var(--shadow-md)',
        lg: 'var(--shadow-lg)',
        xl: 'var(--shadow-xl)',
      },
    },
  },
};

export default config;
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/styles/tokens.css` | New - Design tokens |
| `frontend/tailwind.config.ts` | Update with token references |
| `frontend/src/app/globals.css` | Import tokens |

---

## Dependencies

- E8-S1: UI/UX Pro Max Skill (design guidance)

---

## Testing

1. Import tokens in app
2. Verify Tailwind classes work with tokens
3. Test light/dark mode switching
4. Verify colors render correctly in browser
5. Check typography scales visually
6. Test shadow elevations

---

## Estimated Complexity

**Medium** - Comprehensive token system with OKLch colors

---
