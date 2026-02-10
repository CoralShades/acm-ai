# Tech Spec: E14-S1 - Apply VAEA Branding and Design Tokens

> **Story:** E14-S1
> **Epic:** UX & Enterprise Readiness
> **Status:** Ready for Dev
> **Created:** 2026-02-08

---

## Overview

This story transforms ACM-AI from the current shadcn default blue theme to the official VAEA (Victorian Asbestos Eradication Agency) government brand identity. It implements the complete VAEA design system including teal/green color palette, government design patterns, and brand assets.

---

## User Story

**As a** government client
**I want** the application to use VAEA's official branding
**So that** it meets government presentation standards

---

## Acceptance Criteria

- [ ] CSS custom properties defined for VAEA color palette (light + dark mode)
- [ ] Tailwind 4 `@theme inline` configured with VAEA tokens
- [ ] OKLCH color space used for all brand colors
- [ ] VAEA logo (`VAEA-Ripple2-Logo_Print.png`) replaces current logo
- [ ] VAEA favicon replaces current favicon
- [ ] CoralShades vendor attribution in sidebar footer
- [ ] Focus ring color set to VAEA coral (#EB787A) for accessibility
- [ ] Government design patterns: left-border accent cards, system font stack, 12px border-radius

---

## Technical Design

### 1. Update CSS Custom Properties in `globals.css`

Replace the current `:root` color token block (lines 62-179) with the complete VAEA design system.

#### 1.1 Brand Palette Variables (Add to `:root`)

Insert after line 62, before semantic tokens:

```css
/* ========================================
   VAEA BRAND PALETTE
   ======================================== */
--vaea-teal-100: #9AD9D9;
--vaea-teal-300: #53A69D;
--vaea-teal-500: #01A09C;
--vaea-teal-700: #2A5951;
--vaea-teal-900: #01706D;
--vaea-green-200: #A9D9AC;
--vaea-green-500: #95D60C;
--vaea-coral: #EB787A;
--vaea-gold: #D4A843;
--vaea-grey-50:  #F2F2F2;
--vaea-grey-100: #E6E6E6;
--vaea-grey-200: #D9D9D9;
--vaea-grey-300: #BFBFBF;
--vaea-grey-500: #808080;
--vaea-grey-700: #4C4D52;
--vaea-grey-900: #1F1F1F;

/* ========================================
   GRADIENTS
   ======================================== */
--vaea-gradient: linear-gradient(135deg, #53A69D 0%, #95D60C 50%, #D4A843 100%);
--vaea-gradient-subtle: linear-gradient(135deg, rgba(83,166,157,0.15) 0%, rgba(149,214,12,0.10) 50%, rgba(212,168,67,0.08) 100%);
```

#### 1.2 Update Border Radius

Change line 68:

```css
/* BEFORE */
--radius: 0.65rem;

/* AFTER */
--radius: 0.75rem;  /* 12px government standard */
```

#### 1.3 Update Typography Tokens

Replace the `--font-sans` variable (currently references `--font-inter`) with the system font stack:

```css
/* BEFORE */
--font-sans: var(--font-inter, ui-sans-serif, system-ui, sans-serif);

/* AFTER */
--font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue",
             Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
```

Note: Inter can still be optionally loaded, but the system stack is the baseline.

#### 1.4 Update Shadows to Teal-Tinted

Replace lines 107-112 with teal-tinted shadows:

```css
/* BEFORE: Neutral grey shadows */
--shadow-xs: 0 1px 2px oklch(0% 0 0 / 0.05);
--shadow-sm: 0 1px 3px oklch(0% 0 0 / 0.1), 0 1px 2px oklch(0% 0 0 / 0.06);
--shadow-md: 0 4px 6px oklch(0% 0 0 / 0.1), 0 2px 4px oklch(0% 0 0 / 0.06);
--shadow-lg: 0 10px 15px oklch(0% 0 0 / 0.1), 0 4px 6px oklch(0% 0 0 / 0.05);
--shadow-xl: 0 20px 25px oklch(0% 0 0 / 0.1), 0 10px 10px oklch(0% 0 0 / 0.04);

/* AFTER: Teal-tinted shadows for VAEA */
--shadow-xs: 0 1px 2px rgba(42, 89, 81, 0.05);
--shadow-sm: 0 1px 3px rgba(42, 89, 81, 0.08), 0 1px 2px rgba(42, 89, 81, 0.04);
--shadow-md: 0 4px 12px rgba(42, 89, 81, 0.08);
--shadow-lg: 0 10px 15px rgba(42, 89, 81, 0.10), 0 4px 6px rgba(42, 89, 81, 0.05);
--shadow-xl: 0 20px 25px rgba(42, 89, 81, 0.10), 0 10px 10px rgba(42, 89, 81, 0.04);
```

#### 1.5 Replace Semantic Color Tokens - Light Mode

Replace lines 134-179 with VAEA semantic tokens:

```css
/* ========================================
   SEMANTIC COLOR TOKENS -- LIGHT MODE
   ======================================== */
--background: oklch(0.955 0 0);             /* #F2F2F2 */
--foreground: oklch(0.200 0 0);             /* #1F1F1F */
--card: oklch(1 0 0);                       /* #FFFFFF */
--card-foreground: oklch(0.200 0 0);        /* #1F1F1F */
--popover: oklch(1 0 0);                    /* #FFFFFF */
--popover-foreground: oklch(0.200 0 0);     /* #1F1F1F */
--primary: oklch(0.645 0.085 180);          /* #53A69D (teal-300) */
--primary-foreground: oklch(1 0 0);         /* #FFFFFF */
--secondary: oklch(0.920 0 0);              /* #E6E6E6 */
--secondary-foreground: oklch(0.200 0 0);   /* #1F1F1F */
--muted: oklch(0.920 0 0);                  /* #E6E6E6 */
--muted-foreground: oklch(0.400 0.005 270); /* #4C4D52 */
--accent: oklch(0.835 0.065 192);           /* #9AD9D9 (teal-100) */
--accent-foreground: oklch(0.385 0.055 175);/* #2A5951 (teal-700) */
--destructive: oklch(0.577 0.245 27);       /* #DC2626 */
--border: oklch(0.920 0 0);                 /* #E6E6E6 */
--input: oklch(0.920 0 0);                  /* #E6E6E6 */
--ring: oklch(0.660 0.140 20);              /* #EB787A (coral focus) */

/* Chart colors */
--chart-1: oklch(0.645 0.085 180);          /* teal-300 */
--chart-2: oklch(0.830 0.070 148);          /* green-200 */
--chart-3: oklch(0.385 0.055 175);          /* teal-700 */
--chart-4: oklch(0.745 0.125 80);           /* gold */
--chart-5: oklch(0.660 0.140 20);           /* coral */

/* Sidebar */
--sidebar: oklch(1 0 0);                    /* #FFFFFF */
--sidebar-foreground: oklch(0.200 0 0);     /* #1F1F1F */
--sidebar-primary: oklch(0.645 0.085 180);  /* #53A69D */
--sidebar-primary-foreground: oklch(1 0 0); /* #FFFFFF */
--sidebar-accent: oklch(0.835 0.065 192);   /* #9AD9D9 */
--sidebar-accent-foreground: oklch(0.385 0.055 175); /* #2A5951 */
--sidebar-border: oklch(0.920 0 0);         /* #E6E6E6 */
--sidebar-ring: oklch(0.660 0.140 20);      /* #EB787A */

/* Risk status -- light mode */
--risk-low: oklch(0.600 0.170 145);
--risk-low-bg: oklch(0.950 0.050 145);
--risk-low-foreground: oklch(0.350 0.100 145);
--risk-medium: oklch(0.700 0.180 75);
--risk-medium-bg: oklch(0.950 0.060 85);
--risk-medium-foreground: oklch(0.400 0.120 65);
--risk-high: oklch(0.577 0.245 27);
--risk-high-bg: oklch(0.950 0.040 20);
--risk-high-foreground: oklch(0.380 0.160 25);
--risk-presumed: oklch(0.541 0.240 295);
--risk-presumed-bg: oklch(0.940 0.040 295);
--risk-presumed-foreground: oklch(0.370 0.170 295);
```

#### 1.6 Update Dark Mode Tokens

Replace `.dark` block (lines 181-234) with VAEA dark mode colors:

```css
.dark {
  /* Dark mode shadow overrides */
  --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.25);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.35), 0 1px 2px rgba(0, 0, 0, 0.25);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.30);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.35), 0 4px 6px rgba(0, 0, 0, 0.25);
  --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.40), 0 10px 10px rgba(0, 0, 0, 0.25);

  /* VAEA gradient overrides for dark mode */
  --vaea-gradient: linear-gradient(135deg, #9AD9D9 0%, #A9D9AC 50%, #D4A843 100%);
  --vaea-gradient-subtle: linear-gradient(135deg, rgba(154,217,217,0.12) 0%, rgba(169,217,172,0.08) 50%, rgba(212,168,67,0.06) 100%);

  /* Semantic tokens -- dark mode */
  --background: oklch(0.175 0.025 170);         /* #0F1F1D (dark teal) */
  --foreground: oklch(0.945 0.010 180);         /* #E6F2F1 */
  --card: oklch(0.225 0.030 172);               /* #162B28 */
  --card-foreground: oklch(0.945 0.010 180);    /* #E6F2F1 */
  --popover: oklch(0.225 0.030 172);            /* #162B28 */
  --popover-foreground: oklch(0.945 0.010 180); /* #E6F2F1 */
  --primary: oklch(0.835 0.065 192);            /* #9AD9D9 (teal-100, inverted) */
  --primary-foreground: oklch(0.175 0.025 170); /* #0F1F1D */
  --secondary: oklch(0.270 0.030 173);          /* #1D3633 */
  --secondary-foreground: oklch(0.945 0.010 180);/* #E6F2F1 */
  --muted: oklch(0.270 0.030 173);              /* #1D3633 */
  --muted-foreground: oklch(0.845 0.030 180);   /* #B8D9D6 */
  --accent: oklch(0.325 0.035 174);             /* #244743 */
  --accent-foreground: oklch(0.835 0.065 192);  /* #9AD9D9 */
  --destructive: oklch(0.704 0.191 22);         /* #F87171 */
  --border: oklch(0.325 0.035 174);             /* #244743 */
  --input: oklch(0.375 0.040 175);              /* #2D524E */
  --ring: oklch(0.660 0.140 20);                /* #EB787A (coral, unchanged) */

  /* Chart colors -- dark mode */
  --chart-1: oklch(0.835 0.065 192);            /* teal-100 */
  --chart-2: oklch(0.750 0.160 150);            /* green bright */
  --chart-3: oklch(0.620 0.105 183);            /* teal-500 */
  --chart-4: oklch(0.820 0.165 80);             /* gold bright */
  --chart-5: oklch(0.704 0.191 22);             /* coral bright */

  /* Sidebar -- dark mode */
  --sidebar: oklch(0.225 0.030 172);            /* #162B28 */
  --sidebar-foreground: oklch(0.945 0.010 180); /* #E6F2F1 */
  --sidebar-primary: oklch(0.835 0.065 192);    /* #9AD9D9 */
  --sidebar-primary-foreground: oklch(0.175 0.025 170); /* #0F1F1D */
  --sidebar-accent: oklch(0.325 0.035 174);     /* #244743 */
  --sidebar-accent-foreground: oklch(0.835 0.065 192);  /* #9AD9D9 */
  --sidebar-border: oklch(0.325 0.035 174);     /* #244743 */
  --sidebar-ring: oklch(0.660 0.140 20);        /* #EB787A */

  /* Risk status -- dark mode */
  --risk-low: oklch(0.750 0.160 150);
  --risk-low-bg: oklch(0.280 0.070 150);
  --risk-low-foreground: oklch(0.900 0.075 150);
  --risk-medium: oklch(0.820 0.165 80);
  --risk-medium-bg: oklch(0.330 0.090 60);
  --risk-medium-foreground: oklch(0.910 0.100 90);
  --risk-high: oklch(0.704 0.191 22);
  --risk-high-bg: oklch(0.270 0.110 25);
  --risk-high-foreground: oklch(0.890 0.065 20);
  --risk-presumed: oklch(0.700 0.150 290);
  --risk-presumed-bg: oklch(0.250 0.110 300);
  --risk-presumed-foreground: oklch(0.880 0.060 290);
}
```

### 2. Update Tailwind 4 `@theme inline` Block

The current `@theme inline` block (lines 8-60) is mostly correct. **No changes needed** - it already maps CSS custom properties to Tailwind utilities correctly, including risk colors.

### 3. Update AG Grid Theme Variables

Replace the `.ag-theme-custom` block (lines 237-251) to use VAEA tokens properly:

```css
/* AG Grid Theme Customization */
.ag-theme-custom {
  /* Layout */
  --ag-row-height: 40px;
  --ag-header-height: 44px;
  --ag-font-size: 14px;
  --ag-font-family: var(--font-sans);

  /* Colors - Light */
  --ag-background-color: var(--card);
  --ag-foreground-color: var(--foreground);
  --ag-header-background-color: var(--muted);
  --ag-header-foreground-color: var(--foreground);
  --ag-odd-row-background-color: var(--card);
  --ag-row-hover-color: color-mix(in oklch, var(--primary) 6%, var(--card));
  --ag-selected-row-background-color: color-mix(in oklch, var(--primary) 10%, var(--card));
  --ag-border-color: var(--border);
  --ag-cell-horizontal-border: 1px solid var(--border);

  /* Spacing */
  --ag-cell-horizontal-padding: 12px;
  --ag-grid-size: 6px;

  /* Interaction */
  --ag-range-selection-border-color: var(--primary);
  --ag-range-selection-background-color: color-mix(in oklch, var(--primary) 8%, transparent);
}

/* Dark mode support for AG Grid */
.dark .ag-theme-custom {
  --ag-background-color: var(--background);
  --ag-foreground-color: var(--foreground);
  --ag-header-background-color: var(--muted);
  --ag-odd-row-background-color: var(--card);
  --ag-row-hover-color: color-mix(in oklch, var(--primary) 8%, var(--card));
  --ag-selected-row-background-color: color-mix(in oklch, var(--primary) 12%, var(--card));
  --ag-border-color: var(--border);
}
```

### 4. Update Branding Configuration

Replace `frontend/src/config/branding.ts` entirely:

```typescript
/**
 * Centralized branding configuration for ACM-AI
 *
 * VAEA (Victorian Asbestos Eradication Agency) branding
 */

export const BRANDING = {
  /** Organization name */
  organization: 'VAEA',

  /** Full organization name */
  organizationFull: 'Victorian Asbestos Eradication Agency',

  /** Short application name */
  name: 'ACM-AI',

  /** Full application name with description */
  fullName: 'VAEA ACM-AI - Asbestos Register Management',

  /** Brief tagline for the application */
  tagline: 'AI-powered compliance document analysis',

  /** Longer description for metadata and marketing */
  description: 'Victorian government platform for managing Asbestos Containing Material registers with AI assistance',

  /** SEO keywords */
  keywords: ['VAEA', 'ACM', 'asbestos', 'SAMP', 'compliance', 'AI', 'register', 'management', 'Victorian government'],

  /** API information */
  api: {
    title: 'VAEA ACM-AI API',
    description: 'API for VAEA ACM-AI - Asbestos Containing Material Register Analysis',
    version: '1.0.0',
  },

  /** Footer text */
  footer: {
    acknowledgment: 'VAEA acknowledges the Traditional Owners of Country throughout Victoria and recognises their continuing connection to land, waters and culture. We pay our respects to their Elders past, present and emerging.',
    vendor: 'Powered by CoralShades',
  },
} as const

/** Type for the branding configuration */
export type BrandingConfig = typeof BRANDING
```

### 5. Update Logo Component

Replace `frontend/src/components/brand/Logo.tsx` to use the VAEA Ripple logo image:

```tsx
'use client'

import Image from 'next/image'
import { cn } from '@/lib/utils'
import { BRANDING } from '@/config/branding'

interface LogoProps {
  variant?: 'full' | 'icon'
  className?: string
  iconClassName?: string
}

/**
 * VAEA ACM-AI Logo Component
 *
 * Uses the official VAEA Ripple logo for government branding compliance.
 */
export function Logo({ variant = 'full', className, iconClassName }: LogoProps) {
  const icon = (
    <Image
      src="/logo.png"
      alt="VAEA Logo"
      width={32}
      height={32}
      className={cn('w-8 h-8', iconClassName)}
      priority
    />
  )

  if (variant === 'icon') {
    return (
      <div className={className}>
        {icon}
      </div>
    )
  }

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {icon}
      <span className="font-semibold text-lg text-foreground">{BRANDING.name}</span>
    </div>
  )
}

export default Logo
```

### 6. Replace Public Assets

Copy brand assets from `docs/vaea-assets/` to `frontend/public/`:

1. **Logo**: Copy `VAEA-Ripple2-Logo_Print.png` → `frontend/public/logo.png`
2. **Favicon**: Copy `VAEA_Ripple2_FavIcon_0.png` → `frontend/public/favicon.ico` (rename to .ico)
3. **Icon**: Copy `VAEA_Ripple2_FavIcon_0.png` → `frontend/public/icon.png`

### 7. Update Web Manifest

Replace `frontend/public/manifest.json`:

```json
{
  "name": "VAEA ACM-AI",
  "short_name": "ACM-AI",
  "description": "Victorian government platform for managing Asbestos Containing Material registers",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#F2F2F2",
  "theme_color": "#53A69D",
  "icons": [
    {
      "src": "/icon.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### 8. Add CoralShades Footer Attribution

Create a new component `frontend/src/components/brand/VendorAttribution.tsx`:

```tsx
'use client'

import { cn } from '@/lib/utils'
import { BRANDING } from '@/config/branding'

interface VendorAttributionProps {
  className?: string
}

/**
 * CoralShades vendor attribution for sidebar footer
 */
export function VendorAttribution({ className }: VendorAttributionProps) {
  return (
    <div className={cn('flex items-center gap-2 px-4 py-2', className)}>
      <div className="w-4 h-4 rounded-full bg-gradient-to-br from-coral-400 to-coral-600 opacity-60" />
      <span className="text-xs text-muted-foreground">
        {BRANDING.footer.vendor}
      </span>
    </div>
  )
}
```

### 9. Add Aboriginal Acknowledgment Footer

Create `frontend/src/components/brand/AcknowledgmentFooter.tsx`:

```tsx
'use client'

import { cn } from '@/lib/utils'
import { BRANDING } from '@/config/branding'

interface AcknowledgmentFooterProps {
  className?: string
}

/**
 * Aboriginal and Torres Strait Islander Acknowledgment
 * Required for Victorian government applications
 */
export function AcknowledgmentFooter({ className }: AcknowledgmentFooterProps) {
  return (
    <footer className={cn(
      'text-xs text-center text-muted-foreground leading-relaxed',
      'border-t border-border px-6 py-4',
      className
    )}>
      <p>{BRANDING.footer.acknowledgment}</p>
    </footer>
  )
}
```

### 10. Update Tailwind Config (Optional Enhancement)

In `frontend/tailwind.config.ts`, add VAEA-specific color shortcuts (optional, for convenience):

```typescript
// Add to theme.extend.colors:
colors: {
  vaea: {
    teal: {
      100: '#9AD9D9',
      300: '#53A69D',
      500: '#01A09C',
      700: '#2A5951',
      900: '#01706D',
    },
    green: {
      200: '#A9D9AC',
      500: '#95D60C',
    },
    coral: '#EB787A',
    gold: '#D4A843',
  },
},
```

---

## File Changes

| File | Change | Description |
|------|--------|-------------|
| `frontend/src/app/globals.css` | **Modify** | Replace color tokens, shadows, radius for VAEA brand |
| `frontend/src/config/branding.ts` | **Modify** | Update to VAEA organization and footer text |
| `frontend/src/components/brand/Logo.tsx` | **Modify** | Switch from SVG icon to VAEA Ripple logo PNG |
| `frontend/src/components/brand/VendorAttribution.tsx` | **Create** | CoralShades footer attribution component |
| `frontend/src/components/brand/AcknowledgmentFooter.tsx` | **Create** | Aboriginal and Torres Strait Islander acknowledgment |
| `frontend/public/logo.png` | **Create** | Copy from `docs/vaea-assets/VAEA-Ripple2-Logo_Print.png` |
| `frontend/public/icon.png` | **Create** | Copy from `docs/vaea-assets/VAEA_Ripple2_FavIcon_0.png` |
| `frontend/public/favicon.ico` | **Create** | Rename `VAEA_Ripple2_FavIcon_0.png` to `.ico` |
| `frontend/public/manifest.json` | **Modify** | Update app name, colors, icons to VAEA branding |
| `frontend/tailwind.config.ts` | **Modify** (optional) | Add VAEA color shortcuts for convenience |
| `frontend/public/logo.svg` | **Delete** (optional) | Old logo no longer needed |
| `frontend/public/icon.svg` | **Delete** (optional) | Old icon no longer needed |

---

## Dependencies

### Story Dependencies

- None - this is the first story in Epic 14 and has no dependencies.

### System Dependencies

- **Tailwind CSS 4** with `@theme inline` support (already installed)
- **Next.js Image optimization** for logo rendering (already available)
- **VAEA brand assets** available in `docs/vaea-assets/` (already present)

---

## Testing

### 1. Visual Testing (Light Mode)

1. Start the frontend: `cd frontend && npm run dev`
2. Open browser to `http://localhost:8502`
3. Verify:
   - [ ] Background is `#F2F2F2` (light grey)
   - [ ] Primary buttons use teal `#53A69D`
   - [ ] VAEA Ripple logo appears in header/sidebar
   - [ ] Cards have 12px border-radius
   - [ ] Shadows have subtle teal tint (visible on white cards)
   - [ ] Focus rings are coral `#EB787A` (tab through interactive elements)

### 2. Visual Testing (Dark Mode)

1. Toggle to dark mode
2. Verify:
   - [ ] Background is dark teal `#0F1F1D`
   - [ ] Primary buttons use light teal `#9AD9D9`
   - [ ] Text is readable (contrast meets WCAG AA)
   - [ ] Cards have subtle border glow
   - [ ] Focus rings remain coral `#EB787A`

### 3. Component Testing

1. Check Logo component:
   - [ ] Renders at multiple sizes (sidebar, header)
   - [ ] `variant="icon"` shows logo only
   - [ ] `variant="full"` shows logo + "ACM-AI" text

2. Check Footer components:
   - [ ] Aboriginal acknowledgment displays in page footer
   - [ ] CoralShades attribution displays in sidebar footer
   - [ ] Text is readable in both light/dark modes

### 4. AG Grid Testing

1. Navigate to ACM registers page
2. Verify:
   - [ ] Grid header uses muted grey background
   - [ ] Row hover shows subtle teal highlight
   - [ ] Selected rows have teal background tint
   - [ ] Grid borders use consistent grey `#E6E6E6`

### 5. Accessibility Testing

1. Keyboard navigation:
   - [ ] All interactive elements have visible coral focus rings
   - [ ] Focus rings are 3px wide and 50% opacity
   - [ ] Focus rings visible against both teal and white backgrounds

2. Contrast testing:
   - [ ] Run WCAG contrast checker on text/background combinations
   - [ ] All text meets minimum 4.5:1 ratio (normal text)
   - [ ] Headings meet 3:1 ratio (large text)
   - [ ] Risk badges have sufficient contrast

### 6. Build Testing

```bash
cd frontend
npm run build
```

- [ ] Build completes without errors
- [ ] No missing image warnings for logo files
- [ ] No color token reference errors

---

## Estimated Complexity

**Medium** - Mostly configuration and asset replacement

**Justification:**
- Most changes are straightforward CSS token replacements
- VAEA brand assets are already provided in `docs/vaea-assets/`
- No complex component refactoring required
- Tailwind 4 `@theme inline` block requires minimal changes
- Risk: Ensuring all color references are updated consistently across light/dark modes
- Risk: Image optimization for logo files (PNG → optimized formats)

**Estimated Time:** 4-6 hours
- 2 hours: CSS token updates and verification
- 1 hour: Logo component and asset integration
- 1 hour: Footer components
- 1-2 hours: Testing across light/dark modes and accessibility checks

---

## Notes

### Design System Reference

The complete VAEA design system is documented in `docs/design-system.md`. Key sections:

- Section 2: Color system (brand palette + semantic tokens)
- Section 6: Shadows and elevation (teal-tinted)
- Section 11: Government design patterns (left-border cards)
- Section 14: Accessibility requirements (coral focus rings)
- Section 16: Full CSS reference (copy-paste ready)

### Government Design Standards

This implementation follows Victorian government design patterns:
- **System font stack**: No custom web fonts for accessibility
- **12px border-radius**: Professional appearance
- **Left-border accent cards**: Signature government UI pattern
- **Aboriginal acknowledgment**: Required for all Victorian government applications
- **Teal color palette**: Reflects environmental stewardship mission

### CoralShades Vendor Attribution

The vendor attribution is a contractual requirement. It should be placed in the sidebar footer, visible but unobtrusive.

### Color Space Decision

OKLCH was chosen over hex for semantic tokens because:
- Perceptually uniform color space
- Better interpolation for dark mode
- Native browser support in modern browsers
- Brand palette hex values are preserved for reference

### Migration Path

If issues arise during implementation:
1. **Incremental approach**: Apply light mode first, then dark mode
2. **Rollback strategy**: Keep old `:root` and `.dark` blocks commented out for 1 sprint
3. **AB testing**: Consider feature flag for VAEA theme toggle during transition

---

## Acceptance Sign-off

**Definition of Done:**
- [ ] All CSS tokens updated in `globals.css`
- [ ] VAEA logo appears in all branding locations
- [ ] CoralShades attribution in sidebar footer
- [ ] Aboriginal acknowledgment in page footer
- [ ] Coral focus rings on all interactive elements
- [ ] 12px border-radius applied consistently
- [ ] Light and dark modes tested visually
- [ ] WCAG AA contrast verified
- [ ] `npm run build` succeeds
- [ ] Tech spec reviewed by UX lead
- [ ] Changes merged to `lane-b` branch
