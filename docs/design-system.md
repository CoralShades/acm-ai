# VAEA ACM-AI Design System

> **Version:** 1.0.0
> **Updated:** 2026-02-08
> **Status:** Active specification
> **Compatibility:** Tailwind CSS 4 with `@theme inline`, Next.js 15, AG Grid 33

---

## Table of Contents

1. [Design Principles](#1-design-principles)
2. [Color System](#2-color-system)
3. [Typography](#3-typography)
4. [Spacing](#4-spacing)
5. [Border Radius](#5-border-radius)
6. [Shadows and Elevation](#6-shadows-and-elevation)
7. [Animation and Transitions](#7-animation-and-transitions)
8. [Z-Index Scale](#8-z-index-scale)
9. [Component Variants](#9-component-variants)
10. [AG Grid Theme](#10-ag-grid-theme)
11. [Government Design Patterns](#11-government-design-patterns)
12. [Gradient System](#12-gradient-system)
13. [Icon System](#13-icon-system)
14. [Accessibility Requirements](#14-accessibility-requirements)
15. [Footer Specifications](#15-footer-specifications)
16. [Full CSS Reference](#16-full-css-reference)

---

## 1. Design Principles

1. **Government-grade professionalism** -- Clean, authoritative layouts suitable for Victorian government compliance workflows.
2. **Accessibility first** -- WCAG 2.1 AA minimum. System fonts, sufficient contrast, visible focus indicators.
3. **Data density without clutter** -- ACM registers contain hundreds of rows; every pixel of information density matters.
4. **Dual persona support** -- Compliance officers see simple defaults; asbestos consultants can reveal advanced controls.
5. **Environmental brand alignment** -- Teal/green palette reflects VAEA's environmental stewardship mission.

---

## 2. Color System

### 2.1 Brand Palette

| Token Name | Hex | OKLCH | Usage |
|---|---|---|---|
| `--vaea-teal-100` | `#9AD9D9` | `oklch(0.835 0.065 192)` | Soft backgrounds, muted accents |
| `--vaea-teal-300` | `#53A69D` | `oklch(0.645 0.085 180)` | Primary brand, buttons, links |
| `--vaea-teal-500` | `#01A09C` | `oklch(0.620 0.105 183)` | Alternative primary (website) |
| `--vaea-teal-700` | `#2A5951` | `oklch(0.385 0.055 175)` | Hover states, headings, deep accents |
| `--vaea-teal-900` | `#01706D` | `oklch(0.465 0.080 180)` | Dark accents |
| `--vaea-green-200` | `#A9D9AC` | `oklch(0.830 0.070 148)` | Success, environmental accent |
| `--vaea-green-500` | `#95D60C` | `oklch(0.810 0.185 120)` | Vibrant green (gradient endpoint) |
| `--vaea-coral` | `#EB787A` | `oklch(0.660 0.140 20)` | Focus ring, accessibility indicator |
| `--vaea-gold` | `#D4A843` | `oklch(0.745 0.125 80)` | Gradient endpoint, premium accent |

### 2.2 Neutral Palette

| Token Name | Hex | OKLCH | Usage |
|---|---|---|---|
| `--vaea-grey-50` | `#F2F2F2` | `oklch(0.955 0 0)` | Page background (light) |
| `--vaea-grey-100` | `#E6E6E6` | `oklch(0.920 0 0)` | Borders, dividers |
| `--vaea-grey-200` | `#D9D9D9` | `oklch(0.878 0 0)` | Disabled backgrounds |
| `--vaea-grey-300` | `#BFBFBF` | `oklch(0.790 0 0)` | Muted text, placeholders |
| `--vaea-grey-500` | `#808080` | `oklch(0.600 0 0)` | Secondary text |
| `--vaea-grey-700` | `#4C4D52` | `oklch(0.400 0.005 270)` | Body text |
| `--vaea-grey-900` | `#1F1F1F` | `oklch(0.200 0 0)` | Headings, primary text |

### 2.3 Semantic Color Tokens -- Light Mode

These map to Tailwind/shadcn semantic slots via CSS custom properties.

| Semantic Token | Hex Value | OKLCH Value | Purpose |
|---|---|---|---|
| `--background` | `#F2F2F2` | `oklch(0.955 0 0)` | Page background |
| `--foreground` | `#1F1F1F` | `oklch(0.200 0 0)` | Primary text |
| `--card` | `#FFFFFF` | `oklch(1 0 0)` | Card/surface background |
| `--card-foreground` | `#1F1F1F` | `oklch(0.200 0 0)` | Card text |
| `--popover` | `#FFFFFF` | `oklch(1 0 0)` | Popover background |
| `--popover-foreground` | `#1F1F1F` | `oklch(0.200 0 0)` | Popover text |
| `--primary` | `#53A69D` | `oklch(0.645 0.085 180)` | Primary actions |
| `--primary-foreground` | `#FFFFFF` | `oklch(1 0 0)` | Text on primary |
| `--secondary` | `#E6E6E6` | `oklch(0.920 0 0)` | Secondary backgrounds |
| `--secondary-foreground` | `#1F1F1F` | `oklch(0.200 0 0)` | Text on secondary |
| `--muted` | `#E6E6E6` | `oklch(0.920 0 0)` | Muted backgrounds |
| `--muted-foreground` | `#4C4D52` | `oklch(0.400 0.005 270)` | Muted text |
| `--accent` | `#9AD9D9` | `oklch(0.835 0.065 192)` | Accent highlights |
| `--accent-foreground` | `#2A5951` | `oklch(0.385 0.055 175)` | Text on accent |
| `--destructive` | `#DC2626` | `oklch(0.577 0.245 27)` | Destructive actions |
| `--border` | `#E6E6E6` | `oklch(0.920 0 0)` | Default borders |
| `--input` | `#E6E6E6` | `oklch(0.920 0 0)` | Input borders |
| `--ring` | `#EB787A` | `oklch(0.660 0.140 20)` | Focus ring (coral) |

### 2.4 Semantic Color Tokens -- Dark Mode

| Semantic Token | Hex Value | OKLCH Value | Purpose |
|---|---|---|---|
| `--background` | `#0F1F1D` | `oklch(0.175 0.025 170)` | Page background |
| `--foreground` | `#E6F2F1` | `oklch(0.945 0.010 180)` | Primary text |
| `--card` | `#162B28` | `oklch(0.225 0.030 172)` | Card/surface background |
| `--card-foreground` | `#E6F2F1` | `oklch(0.945 0.010 180)` | Card text |
| `--popover` | `#162B28` | `oklch(0.225 0.030 172)` | Popover background |
| `--popover-foreground` | `#E6F2F1` | `oklch(0.945 0.010 180)` | Popover text |
| `--primary` | `#9AD9D9` | `oklch(0.835 0.065 192)` | Primary actions (inverted for dark) |
| `--primary-foreground` | `#0F1F1D` | `oklch(0.175 0.025 170)` | Text on primary |
| `--secondary` | `#1D3633` | `oklch(0.270 0.030 173)` | Secondary backgrounds |
| `--secondary-foreground` | `#E6F2F1` | `oklch(0.945 0.010 180)` | Text on secondary |
| `--muted` | `#1D3633` | `oklch(0.270 0.030 173)` | Muted backgrounds |
| `--muted-foreground` | `#B8D9D6` | `oklch(0.845 0.030 180)` | Muted text |
| `--accent` | `#244743` | `oklch(0.325 0.035 174)` | Accent highlights |
| `--accent-foreground` | `#9AD9D9` | `oklch(0.835 0.065 192)` | Text on accent |
| `--destructive` | `#F87171` | `oklch(0.704 0.191 22)` | Destructive actions (lighter in dark) |
| `--border` | `#244743` | `oklch(0.325 0.035 174)` | Default borders |
| `--input` | `#2D524E` | `oklch(0.375 0.040 175)` | Input borders |
| `--ring` | `#EB787A` | `oklch(0.660 0.140 20)` | Focus ring (coral, unchanged) |

### 2.5 Risk Status Colors

Risk colors are critical for ACM compliance. They must meet WCAG AA contrast requirements against their respective backgrounds.

#### Light Mode

| Token | Hex | OKLCH | Usage |
|---|---|---|---|
| `--risk-low` | `#16A34A` | `oklch(0.600 0.170 145)` | Low risk indicator |
| `--risk-low-bg` | `#DCFCE7` | `oklch(0.950 0.050 145)` | Low risk background |
| `--risk-low-foreground` | `#166534` | `oklch(0.350 0.100 145)` | Low risk text |
| `--risk-medium` | `#D97706` | `oklch(0.700 0.180 75)` | Medium risk indicator |
| `--risk-medium-bg` | `#FEF3C7` | `oklch(0.950 0.060 85)` | Medium risk background |
| `--risk-medium-foreground` | `#92400E` | `oklch(0.400 0.120 65)` | Medium risk text |
| `--risk-high` | `#DC2626` | `oklch(0.577 0.245 27)` | High risk indicator |
| `--risk-high-bg` | `#FEE2E2` | `oklch(0.950 0.040 20)` | High risk background |
| `--risk-high-foreground` | `#991B1B` | `oklch(0.380 0.160 25)` | High risk text |
| `--risk-presumed` | `#7C3AED` | `oklch(0.541 0.240 295)` | Presumed risk indicator |
| `--risk-presumed-bg` | `#EDE9FE` | `oklch(0.940 0.040 295)` | Presumed risk background |
| `--risk-presumed-foreground` | `#5B21B6` | `oklch(0.370 0.170 295)` | Presumed risk text |

#### Dark Mode

| Token | Hex | OKLCH | Usage |
|---|---|---|---|
| `--risk-low` | `#4ADE80` | `oklch(0.750 0.160 150)` | Low risk indicator |
| `--risk-low-bg` | `#14532D` | `oklch(0.280 0.070 150)` | Low risk background |
| `--risk-low-foreground` | `#BBF7D0` | `oklch(0.900 0.075 150)` | Low risk text |
| `--risk-medium` | `#FBBF24` | `oklch(0.820 0.165 80)` | Medium risk indicator |
| `--risk-medium-bg` | `#78350F` | `oklch(0.330 0.090 60)` | Medium risk background |
| `--risk-medium-foreground` | `#FDE68A` | `oklch(0.910 0.100 90)` | Medium risk text |
| `--risk-high` | `#F87171` | `oklch(0.704 0.191 22)` | High risk indicator |
| `--risk-high-bg` | `#7F1D1D` | `oklch(0.270 0.110 25)` | High risk background |
| `--risk-high-foreground` | `#FECACA` | `oklch(0.890 0.065 20)` | High risk text |
| `--risk-presumed` | `#A78BFA` | `oklch(0.700 0.150 290)` | Presumed risk indicator |
| `--risk-presumed-bg` | `#3B0764` | `oklch(0.250 0.110 300)` | Presumed risk background |
| `--risk-presumed-foreground` | `#DDD6FE` | `oklch(0.880 0.060 290)` | Presumed risk text |

### 2.6 Sidebar Tokens

| Token | Light Mode | Dark Mode |
|---|---|---|
| `--sidebar` | `#FFFFFF` `oklch(1 0 0)` | `#162B28` `oklch(0.225 0.030 172)` |
| `--sidebar-foreground` | `#1F1F1F` `oklch(0.200 0 0)` | `#E6F2F1` `oklch(0.945 0.010 180)` |
| `--sidebar-primary` | `#53A69D` `oklch(0.645 0.085 180)` | `#9AD9D9` `oklch(0.835 0.065 192)` |
| `--sidebar-primary-foreground` | `#FFFFFF` `oklch(1 0 0)` | `#0F1F1D` `oklch(0.175 0.025 170)` |
| `--sidebar-accent` | `#9AD9D9` `oklch(0.835 0.065 192)` | `#244743` `oklch(0.325 0.035 174)` |
| `--sidebar-accent-foreground` | `#2A5951` `oklch(0.385 0.055 175)` | `#9AD9D9` `oklch(0.835 0.065 192)` |
| `--sidebar-border` | `#E6E6E6` `oklch(0.920 0 0)` | `#244743` `oklch(0.325 0.035 174)` |
| `--sidebar-ring` | `#EB787A` `oklch(0.660 0.140 20)` | `#EB787A` `oklch(0.660 0.140 20)` |

### 2.7 Chart Colors

| Token | Light Mode OKLCH | Dark Mode OKLCH |
|---|---|---|
| `--chart-1` | `oklch(0.645 0.085 180)` (teal-300) | `oklch(0.835 0.065 192)` (teal-100) |
| `--chart-2` | `oklch(0.830 0.070 148)` (green-200) | `oklch(0.750 0.160 150)` (green bright) |
| `--chart-3` | `oklch(0.385 0.055 175)` (teal-700) | `oklch(0.620 0.105 183)` (teal-500) |
| `--chart-4` | `oklch(0.745 0.125 80)` (gold) | `oklch(0.820 0.165 80)` (gold bright) |
| `--chart-5` | `oklch(0.660 0.140 20)` (coral) | `oklch(0.704 0.191 22)` (coral bright) |

---

## 3. Typography

### 3.1 Font Stack

```css
/* System font stack -- no custom fonts for government accessibility */
--font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue",
             Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji";

/* Data font -- monospace with tabular numerals for AG Grid and metrics */
--font-mono: "JetBrains Mono", ui-monospace, SFMono-Regular, "SF Mono", Menlo,
             Consolas, "Liberation Mono", monospace;
--font-data: var(--font-mono);
```

**Note:** Inter can optionally be loaded via `next/font/google` for enhanced readability, but the system stack is the baseline. JetBrains Mono is loaded for data display and code blocks.

### 3.2 Size Scale

| Token | Value | Tailwind Class | Usage |
|---|---|---|---|
| `--text-xs` | `0.75rem` (12px) | `text-xs` | Captions, labels, metadata |
| `--text-sm` | `0.875rem` (14px) | `text-sm` | Body small, table cells, form labels |
| `--text-base` | `1rem` (16px) | `text-base` | Body text, paragraphs |
| `--text-lg` | `1.125rem` (18px) | `text-lg` | H5, section labels |
| `--text-xl` | `1.25rem` (20px) | `text-xl` | H4, card titles |
| `--text-2xl` | `1.5rem` (24px) | `text-2xl` | H3, section headings |
| `--text-3xl` | `1.875rem` (30px) | `text-3xl` | H2, page subtitles, metrics |
| `--text-4xl` | `2.25rem` (36px) | `text-4xl` | H1, page titles |

### 3.3 Weight Scale

| Token | Value | Tailwind Class | Usage |
|---|---|---|---|
| `--font-normal` | `400` | `font-normal` | Body text |
| `--font-medium` | `500` | `font-medium` | Labels, navigation items |
| `--font-semibold` | `600` | `font-semibold` | Headings (H2-H5), card titles |
| `--font-bold` | `700` | `font-bold` | H1, metrics, emphasis |

### 3.4 Line Height Scale

| Token | Value | Tailwind Class | Usage |
|---|---|---|---|
| `--leading-none` | `1` | `leading-none` | Metrics, single-line values |
| `--leading-tight` | `1.25` | `leading-tight` | Headings |
| `--leading-snug` | `1.375` | `leading-snug` | Subheadings |
| `--leading-normal` | `1.5` | `leading-normal` | Body text |
| `--leading-relaxed` | `1.625` | `leading-relaxed` | Long-form text, descriptions |
| `--leading-loose` | `2` | `leading-loose` | Spacious text blocks |

### 3.5 Heading Hierarchy

| Level | Size | Weight | Line Height | Letter Spacing |
|---|---|---|---|---|
| H1 | `--text-4xl` (36px) | `700` | `1.25` | `-0.02em` |
| H2 | `--text-3xl` (30px) | `600` | `1.25` | `-0.01em` |
| H3 | `--text-2xl` (24px) | `600` | `1.375` | `0` |
| H4 | `--text-xl` (20px) | `600` | `1.375` | `0` |
| H5 | `--text-lg` (18px) | `500` | `1.5` | `0` |
| H6 | `--text-base` (16px) | `500` | `1.5` | `0` |

### 3.6 Utility Classes

| Class | Description |
|---|---|
| `.text-body` | Base body text (16px, relaxed line height) |
| `.text-body-sm` | Small body text (14px, relaxed line height) |
| `.text-data` | Monospace with `tabular-nums` for numerical data |
| `.text-metric` | Large bold number display (30px, `tabular-nums`, `line-height: 1`) |
| `.text-caption` | Tiny muted text (12px, muted-foreground color) |
| `.text-label` | Form label style (14px, medium weight, slight tracking) |

---

## 4. Spacing

Base unit: **4px** (`0.25rem`).

| Token | Value | Pixels | Usage |
|---|---|---|---|
| `--space-0` | `0` | 0 | Reset |
| `--space-1` | `0.25rem` | 4px | Tight gaps, inline spacing |
| `--space-2` | `0.5rem` | 8px | Icon gaps, small padding |
| `--space-3` | `0.75rem` | 12px | Form field gaps |
| `--space-4` | `1rem` | 16px | Card padding, standard gap |
| `--space-5` | `1.25rem` | 20px | Section padding |
| `--space-6` | `1.5rem` | 24px | Card content padding |
| `--space-8` | `2rem` | 32px | Section margins |
| `--space-10` | `2.5rem` | 40px | Large section gaps |
| `--space-12` | `3rem` | 48px | Page-level spacing |
| `--space-16` | `4rem` | 64px | Major layout gaps |
| `--space-20` | `5rem` | 80px | Hero spacing |
| `--space-24` | `6rem` | 96px | Maximum spacing |

---

## 5. Border Radius

Government design standard: **12px** base radius for a modern but professional appearance.

| Token | Value | Tailwind Class | Usage |
|---|---|---|---|
| `--radius` | `0.75rem` (12px) | -- | Base value |
| `--radius-sm` | `calc(var(--radius) - 4px)` = 8px | `rounded-sm` | Badges, small buttons, inputs |
| `--radius-md` | `calc(var(--radius) - 2px)` = 10px | `rounded-md` | Buttons, form elements |
| `--radius-lg` | `var(--radius)` = 12px | `rounded-lg` | Cards, panels, dialogs |
| `--radius-xl` | `calc(var(--radius) + 4px)` = 16px | `rounded-xl` | Hero cards, large containers |

---

## 6. Shadows and Elevation

Shadows use a teal tint to match the VAEA brand, departing from standard grey shadows.

### Light Mode

| Token | Value | Usage |
|---|---|---|
| `--shadow-xs` | `0 1px 2px rgba(42, 89, 81, 0.05)` | Subtle lift (buttons) |
| `--shadow-sm` | `0 1px 3px rgba(42, 89, 81, 0.08), 0 1px 2px rgba(42, 89, 81, 0.04)` | Cards at rest |
| `--shadow-md` | `0 4px 12px rgba(42, 89, 81, 0.08)` | Elevated cards (VAEA standard) |
| `--shadow-lg` | `0 10px 15px rgba(42, 89, 81, 0.10), 0 4px 6px rgba(42, 89, 81, 0.05)` | Dropdowns, popovers |
| `--shadow-xl` | `0 20px 25px rgba(42, 89, 81, 0.10), 0 10px 10px rgba(42, 89, 81, 0.04)` | Modals, dialogs |

### Dark Mode

| Token | Value |
|---|---|
| `--shadow-xs` | `0 1px 2px rgba(0, 0, 0, 0.25)` |
| `--shadow-sm` | `0 1px 3px rgba(0, 0, 0, 0.35), 0 1px 2px rgba(0, 0, 0, 0.25)` |
| `--shadow-md` | `0 4px 12px rgba(0, 0, 0, 0.30)` |
| `--shadow-lg` | `0 10px 15px rgba(0, 0, 0, 0.35), 0 4px 6px rgba(0, 0, 0, 0.25)` |
| `--shadow-xl` | `0 20px 25px rgba(0, 0, 0, 0.40), 0 10px 10px rgba(0, 0, 0, 0.25)` |

---

## 7. Animation and Transitions

| Token | Value | Usage |
|---|---|---|
| `--duration-fast` | `150ms` | Hover effects, color changes, toggles |
| `--duration-normal` | `250ms` | Panel slides, card transitions, theme switch |
| `--duration-slow` | `350ms` | Page transitions, accordion open/close, dialog enter |
| `--ease-default` | `cubic-bezier(0.4, 0, 0.2, 1)` | General purpose (ease-in-out) |
| `--ease-in` | `cubic-bezier(0.4, 0, 1, 1)` | Elements leaving the viewport |
| `--ease-out` | `cubic-bezier(0, 0, 0.2, 1)` | Elements entering the viewport |

**Theme transition handling:** Apply `disable-transitions` class to `<html>` during theme switch to prevent flash-of-wrong-theme:

```css
html.disable-transitions,
html.disable-transitions *,
html.disable-transitions *::before,
html.disable-transitions *::after {
  transition: none !important;
}
```

---

## 8. Z-Index Scale

| Token | Value | Usage |
|---|---|---|
| `--z-base` | `0` | Default stacking |
| `--z-dropdown` | `10` | Dropdown menus |
| `--z-sticky` | `20` | Sticky headers, toolbar |
| `--z-modal` | `30` | Modal backdrops and dialogs |
| `--z-popover` | `40` | Popovers, tooltips, command palette |
| `--z-toast` | `50` | Toast notifications (always on top) |

---

## 9. Component Variants

### 9.1 Buttons

All buttons use `border-radius: var(--radius-md)` (10px) and transition `background-color` over `var(--duration-fast)`.

#### Primary

```
Background:  var(--primary)       /* #53A69D light / #9AD9D9 dark */
Text:        var(--primary-foreground)  /* #FFFFFF light / #0F1F1D dark */
Hover:       var(--vaea-teal-700)  /* #2A5951 light */  /  var(--vaea-green-200) /* #A9D9AC dark */
Shadow:      var(--shadow-xs)
Focus ring:  3px var(--ring) at 50% opacity
```

**Tailwind classes:** `bg-primary text-primary-foreground shadow-xs hover:bg-primary/90`

#### Secondary (Outline)

```
Background:  transparent
Text:        var(--primary)
Border:      1px solid var(--primary)
Hover bg:    var(--accent)          /* #9AD9D9 at 10% opacity */
```

**Tailwind classes:** `border border-primary text-primary hover:bg-accent`

#### Ghost

```
Background:  transparent
Text:        var(--foreground)
Hover bg:    var(--accent)
```

**Tailwind classes:** `hover:bg-accent hover:text-accent-foreground`

#### Destructive

```
Background:  var(--destructive)
Text:        #FFFFFF
Hover:       var(--destructive) at 90% opacity
Focus ring:  var(--destructive) at 20% opacity
```

**Tailwind classes:** `bg-destructive text-white shadow-xs hover:bg-destructive/90`

#### Button Sizes

| Size | Height | Padding | Class |
|---|---|---|---|
| `sm` | `h-8` (32px) | `px-3` | `size="sm"` |
| `default` | `h-9` (36px) | `px-4 py-2` | `size="default"` |
| `lg` | `h-10` (40px) | `px-6` | `size="lg"` |
| `icon` | `size-9` (36x36) | -- | `size="icon"` |

### 9.2 Cards

#### Default Card

```css
.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);  /* 12px */
  box-shadow: var(--shadow-md);     /* teal-tinted */
}
```

#### Accent Card (Government Pattern)

Left-border accent card used for important notices, stat summaries, and call-to-action panels.

```css
.card-accent {
  background: var(--card);
  border: 1px solid var(--border);
  border-left: 6px solid var(--primary);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}
```

#### Stat Card

Used for dashboard KPI displays.

```css
.card-stat {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  padding: var(--space-6);
}
.card-stat .metric {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  font-variant-numeric: tabular-nums;
  color: var(--primary);
}
.card-stat .label {
  font-size: var(--text-sm);
  color: var(--muted-foreground);
  font-weight: var(--font-medium);
}
```

#### Alert Card

```css
.card-alert {
  border: 1px solid var(--destructive);
  border-left: 6px solid var(--destructive);
  background: color-mix(in oklch, var(--destructive) 5%, var(--card));
}
```

#### Dark Mode Card Enhancement

```css
.dark .card,
.dark [data-slot="card"] {
  box-shadow: 0 0 0 1px var(--border), var(--shadow-sm);
}
```

### 9.3 Badges

Risk badges are the primary badge type in ACM-AI.

| Variant | Background | Text | Border |
|---|---|---|---|
| `risk-high` | `var(--risk-high-bg)` | `var(--risk-high-foreground)` | `var(--risk-high)` |
| `risk-medium` | `var(--risk-medium-bg)` | `var(--risk-medium-foreground)` | `var(--risk-medium)` |
| `risk-low` | `var(--risk-low-bg)` | `var(--risk-low-foreground)` | `var(--risk-low)` |
| `risk-presumed` | `var(--risk-presumed-bg)` | `var(--risk-presumed-foreground)` | `var(--risk-presumed)` |

**Badge CSS pattern:**

```css
.badge-risk {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 2px 10px;
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
  border-radius: 9999px;  /* pill shape */
  border: 1px solid;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
```

### 9.4 Status Indicators

Pipeline and extraction status indicators.

| Status | Color | Icon | Animation |
|---|---|---|---|
| `idle` | `var(--muted-foreground)` | `Circle` | None |
| `processing` | `var(--primary)` | `Loader2` | `spin 1s linear infinite` |
| `complete` | `var(--risk-low)` | `CheckCircle2` | None |
| `failed` | `var(--destructive)` | `XCircle` | None |

---

## 10. AG Grid Theme

AG Grid is the core data display component for ACM registers. The custom theme applies VAEA tokens.

### 10.1 CSS Custom Properties

```css
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
```

### 10.2 Dark Mode Overrides

```css
.dark .ag-theme-custom,
[data-theme="dark"] .ag-theme-custom {
  --ag-background-color: var(--background);
  --ag-foreground-color: var(--foreground);
  --ag-header-background-color: var(--muted);
  --ag-header-foreground-color: var(--foreground);
  --ag-odd-row-background-color: var(--card);
  --ag-row-hover-color: color-mix(in oklch, var(--primary) 8%, var(--card));
  --ag-selected-row-background-color: color-mix(in oklch, var(--primary) 12%, var(--card));
  --ag-border-color: var(--border);
}
```

### 10.3 Cell Interaction Styles

```css
/* Clickable cells (ACM records open detail dialog) */
.ag-theme-custom .ag-cell {
  cursor: pointer;
  transition: background-color var(--duration-fast) var(--ease-default);
}

.ag-theme-custom .ag-cell:hover {
  background-color: color-mix(in oklch, var(--primary) 8%, transparent);
}

/* Group rows and action columns are not clickable */
.ag-theme-custom .ag-row-group .ag-cell,
.ag-theme-custom .ag-cell[col-id="actions"],
.ag-theme-custom .ag-pinned-right-cols-container .ag-cell {
  cursor: default;
}
.ag-theme-custom .ag-row-group .ag-cell:hover,
.ag-theme-custom .ag-cell[col-id="actions"]:hover,
.ag-theme-custom .ag-pinned-right-cols-container .ag-cell:hover {
  background-color: transparent;
}
```

### 10.4 Risk Cell Rendering

Risk columns in AG Grid use colored badges inline. The cell renderer should apply `badge-risk` styling with the appropriate risk variant class.

```tsx
// Cell renderer for risk columns
function RiskCellRenderer({ value }: { value: string }) {
  const variant = value?.toLowerCase() as 'low' | 'medium' | 'high' | 'presumed';
  return (
    <span className={`badge-risk badge-risk-${variant}`}>
      {value}
    </span>
  );
}
```

---

## 11. Government Design Patterns

### 11.1 Left-Border Accent Cards

The signature Victorian government UI pattern: a thick left border indicating importance level.

```css
/* Primary accent (informational) */
.gov-card-accent {
  border-left: 6px solid var(--primary);
}

/* Warning accent */
.gov-card-warning {
  border-left: 6px solid var(--risk-medium);
}

/* Critical accent */
.gov-card-critical {
  border-left: 6px solid var(--risk-high);
}

/* Success accent */
.gov-card-success {
  border-left: 6px solid var(--risk-low);
}
```

### 11.2 Data Table Standards

- Row height: 40px minimum for touch targets
- Header: Muted background, semibold text, uppercase for column groups
- Zebra striping: Subtle alternating rows (optional, off by default in VAEA theme)
- Sticky header: Always visible during scroll
- Horizontal scrolling: Pinned columns for identifiers (Building, Level, Room)

### 11.3 Form Patterns

- Labels above inputs (never placeholder-only)
- Required fields marked with `*` in the label
- Error messages below the input in `--destructive` color
- Help text below the input in `--muted-foreground`
- Group related fields in `<fieldset>` with `<legend>`

### 11.4 Status Communication

Government systems require explicit status feedback:

- Always show operation status (idle / processing / complete / failed)
- Use progress indicators for operations exceeding 2 seconds
- Provide textual status in addition to color indicators (never color-only)
- Toast notifications for completed operations with undo where applicable

---

## 12. Gradient System

### 12.1 VAEA Brand Gradient

The signature VAEA gradient flows from teal through lime to gold, representing the environmental spectrum.

```css
--vaea-gradient: linear-gradient(
  135deg,
  #53A69D 0%,     /* teal-300 */
  #95D60C 50%,    /* green-500 (lime) */
  #D4A843 100%    /* gold */
);

--vaea-gradient-subtle: linear-gradient(
  135deg,
  rgba(83, 166, 157, 0.15) 0%,
  rgba(149, 214, 12, 0.10) 50%,
  rgba(212, 168, 67, 0.08) 100%
);
```

### 12.2 Usage

| Context | Gradient | Opacity |
|---|---|---|
| Hero section background | `--vaea-gradient-subtle` | Full |
| Active nav item indicator | `--vaea-gradient` | 100%, 3px left border |
| CTA button hover shimmer | `--vaea-gradient` | 10% overlay |
| Loading skeleton pulse | `--vaea-gradient-subtle` | Animated sweep |
| Page divider accent | `--vaea-gradient` | 2px height, full width |

### 12.3 Dark Mode Gradient

```css
[data-theme="dark"] {
  --vaea-gradient: linear-gradient(
    135deg,
    #9AD9D9 0%,    /* teal-100 (brighter in dark) */
    #A9D9AC 50%,   /* green-200 */
    #D4A843 100%   /* gold */
  );

  --vaea-gradient-subtle: linear-gradient(
    135deg,
    rgba(154, 217, 217, 0.12) 0%,
    rgba(169, 217, 172, 0.08) 50%,
    rgba(212, 168, 67, 0.06) 100%
  );
}
```

---

## 13. Icon System

### 13.1 Library

**Primary:** [Lucide React](https://lucide.dev) -- consistent 24x24 stroke icons at 1.5px stroke width.

### 13.2 Core Icon Set

| Icon | Lucide Name | Usage |
|---|---|---|
| Upload | `Upload` | Upload document CTA |
| File | `FileText` | Document/source items |
| Building | `Building2` | Building references |
| Shield | `ShieldAlert` | Risk indicators |
| Check | `CheckCircle2` | Success / complete |
| Warning | `AlertTriangle` | Medium risk / warning |
| Error | `XCircle` | Failed / high risk |
| Search | `Search` | Search functionality |
| Settings | `Settings` | Configuration pages |
| Filter | `Filter` | Column filters |
| Download | `Download` | Export actions |
| Eye | `Eye` | View/preview |
| Edit | `Pencil` | Edit actions |
| Trash | `Trash2` | Delete actions |
| Loader | `Loader2` | Processing spinner |
| Info | `Info` | Information tooltips |
| Map | `MapPin` | Location references |
| Grid | `LayoutGrid` | Grid view toggle |
| List | `LayoutList` | List view toggle |
| Sidebar | `PanelLeft` | Sidebar toggle |
| Sun | `Sun` | Light mode |
| Moon | `Moon` | Dark mode |

### 13.3 Risk Icons

| Risk Level | Icon | Color Token |
|---|---|---|
| Low | `ShieldCheck` | `--risk-low` |
| Medium | `ShieldAlert` | `--risk-medium` |
| High | `ShieldX` or `AlertOctagon` | `--risk-high` |
| Presumed | `ShieldQuestion` | `--risk-presumed` |

### 13.4 Icon Sizing

| Context | Size | Tailwind Class |
|---|---|---|
| Inline with text | 16px | `size-4` |
| Button icon | 16px | `size-4` (auto via `[&_svg]:size-4`) |
| Navigation item | 20px | `size-5` |
| Status indicator | 20px | `size-5` |
| Empty state | 48px | `size-12` |
| Hero illustration | 64px | `size-16` |

---

## 14. Accessibility Requirements

### 14.1 WCAG 2.1 AA Compliance

| Requirement | Standard | Implementation |
|---|---|---|
| Text contrast (normal) | 4.5:1 minimum | All `--foreground` on `--background` combinations verified |
| Text contrast (large) | 3:1 minimum | Headings and large text |
| Non-text contrast | 3:1 minimum | Icons, borders, form controls |
| Focus visibility | Visible focus indicator | 3px `--ring` (coral `#EB787A`) at 50% opacity |
| Touch target | 44x44px minimum | Buttons `h-9` (36px) with padding meet 44px; icon buttons use `size-9` |
| Color independence | Never color-only info | Risk badges include text labels, not just color |
| Motion reduction | `prefers-reduced-motion` | Disable animations when preference set |
| Screen reader | Meaningful labels | All interactive elements have accessible names |

### 14.2 Focus Ring Specification

```css
/* Focus ring using coral for maximum visibility on teal backgrounds */
*:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px color-mix(in oklch, var(--ring) 50%, transparent);
  border-color: var(--ring);
}
```

The coral focus ring (`#EB787A`) was specifically chosen because:
- It has sufficient contrast against both teal and white backgrounds
- It is visually distinct from the teal brand palette
- It meets WCAG 2.1 AA non-text contrast requirements (3:1 against all surface colors)

### 14.3 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

---

## 15. Footer Specifications

### 15.1 Aboriginal and Torres Strait Islander Acknowledgment

Required for Victorian government applications. Placed in the application footer, visible on all pages.

**Text:**

> VAEA acknowledges the Traditional Owners of Country throughout Victoria and recognises their continuing connection to land, waters and culture. We pay our respects to their Elders past, present and emerging.

**Styling:**

```css
.acknowledgment-footer {
  font-size: var(--text-xs);
  color: var(--muted-foreground);
  text-align: center;
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--border);
  line-height: var(--leading-relaxed);
}
```

### 15.2 CoralShades Vendor Attribution

Placed below the acknowledgment or in the sidebar footer.

**Layout:**

```
[CS_Logo.svg icon, 16px]  Powered by CoralShades
```

**Styling:**

```css
.vendor-attribution {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xs);
  color: var(--muted-foreground);
  padding: var(--space-2) var(--space-4);
}
.vendor-attribution img {
  width: 16px;
  height: 16px;
  opacity: 0.6;
}
```

---

## 16. Full CSS Reference

The complete CSS custom property definitions for integration into `globals.css`.

### 16.1 Light Mode (`:root`)

```css
:root {
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

  /* ========================================
     BORDER RADIUS
     ======================================== */
  --radius: 0.75rem;

  /* ========================================
     TYPOGRAPHY
     ======================================== */
  --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue",
               Arial, "Noto Sans", sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
  --font-mono: "JetBrains Mono", ui-monospace, SFMono-Regular, "SF Mono", Menlo,
               Consolas, "Liberation Mono", monospace;
  --font-data: var(--font-mono);

  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --text-lg: 1.125rem;
  --text-xl: 1.25rem;
  --text-2xl: 1.5rem;
  --text-3xl: 1.875rem;
  --text-4xl: 2.25rem;

  --leading-none: 1;
  --leading-tight: 1.25;
  --leading-snug: 1.375;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;
  --leading-loose: 2;

  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;

  /* ========================================
     SPACING (base: 4px)
     ======================================== */
  --space-0: 0;
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;
  --space-16: 4rem;
  --space-20: 5rem;
  --space-24: 6rem;

  /* ========================================
     SHADOWS (teal-tinted for VAEA)
     ======================================== */
  --shadow-xs: 0 1px 2px rgba(42, 89, 81, 0.05);
  --shadow-sm: 0 1px 3px rgba(42, 89, 81, 0.08), 0 1px 2px rgba(42, 89, 81, 0.04);
  --shadow-md: 0 4px 12px rgba(42, 89, 81, 0.08);
  --shadow-lg: 0 10px 15px rgba(42, 89, 81, 0.10), 0 4px 6px rgba(42, 89, 81, 0.05);
  --shadow-xl: 0 20px 25px rgba(42, 89, 81, 0.10), 0 10px 10px rgba(42, 89, 81, 0.04);

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

  /* ========================================
     SEMANTIC COLOR TOKENS -- LIGHT MODE
     ======================================== */
  --background: oklch(0.955 0 0);             /* #F2F2F2 */
  --foreground: oklch(0.200 0 0);             /* #1F1F1F */
  --card: oklch(1 0 0);                       /* #FFFFFF */
  --card-foreground: oklch(0.200 0 0);        /* #1F1F1F */
  --popover: oklch(1 0 0);                    /* #FFFFFF */
  --popover-foreground: oklch(0.200 0 0);     /* #1F1F1F */
  --primary: oklch(0.645 0.085 180);          /* #53A69D */
  --primary-foreground: oklch(1 0 0);         /* #FFFFFF */
  --secondary: oklch(0.920 0 0);              /* #E6E6E6 */
  --secondary-foreground: oklch(0.200 0 0);   /* #1F1F1F */
  --muted: oklch(0.920 0 0);                  /* #E6E6E6 */
  --muted-foreground: oklch(0.400 0.005 270); /* #4C4D52 */
  --accent: oklch(0.835 0.065 192);           /* #9AD9D9 */
  --accent-foreground: oklch(0.385 0.055 175);/* #2A5951 */
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
}
```

### 16.2 Dark Mode (`[data-theme="dark"]` / `.dark`)

```css
.dark,
[data-theme="dark"] {
  /* ========================================
     SHADOWS -- DARK MODE
     ======================================== */
  --shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.25);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.35), 0 1px 2px rgba(0, 0, 0, 0.25);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.30);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.35), 0 4px 6px rgba(0, 0, 0, 0.25);
  --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.40), 0 10px 10px rgba(0, 0, 0, 0.25);

  /* ========================================
     GRADIENTS -- DARK MODE
     ======================================== */
  --vaea-gradient: linear-gradient(135deg, #9AD9D9 0%, #A9D9AC 50%, #D4A843 100%);
  --vaea-gradient-subtle: linear-gradient(135deg, rgba(154,217,217,0.12) 0%, rgba(169,217,172,0.08) 50%, rgba(212,168,67,0.06) 100%);

  /* ========================================
     SEMANTIC COLOR TOKENS -- DARK MODE
     ======================================== */
  --background: oklch(0.175 0.025 170);         /* #0F1F1D */
  --foreground: oklch(0.945 0.010 180);          /* #E6F2F1 */
  --card: oklch(0.225 0.030 172);                /* #162B28 */
  --card-foreground: oklch(0.945 0.010 180);     /* #E6F2F1 */
  --popover: oklch(0.225 0.030 172);             /* #162B28 */
  --popover-foreground: oklch(0.945 0.010 180);  /* #E6F2F1 */
  --primary: oklch(0.835 0.065 192);             /* #9AD9D9 */
  --primary-foreground: oklch(0.175 0.025 170);  /* #0F1F1D */
  --secondary: oklch(0.270 0.030 173);           /* #1D3633 */
  --secondary-foreground: oklch(0.945 0.010 180);/* #E6F2F1 */
  --muted: oklch(0.270 0.030 173);               /* #1D3633 */
  --muted-foreground: oklch(0.845 0.030 180);    /* #B8D9D6 */
  --accent: oklch(0.325 0.035 174);              /* #244743 */
  --accent-foreground: oklch(0.835 0.065 192);   /* #9AD9D9 */
  --destructive: oklch(0.704 0.191 22);          /* #F87171 */
  --border: oklch(0.325 0.035 174);              /* #244743 */
  --input: oklch(0.375 0.040 175);               /* #2D524E */
  --ring: oklch(0.660 0.140 20);                 /* #EB787A (coral, unchanged) */

  /* Chart colors -- dark mode */
  --chart-1: oklch(0.835 0.065 192);             /* teal-100 */
  --chart-2: oklch(0.750 0.160 150);             /* green bright */
  --chart-3: oklch(0.620 0.105 183);             /* teal-500 */
  --chart-4: oklch(0.820 0.165 80);              /* gold bright */
  --chart-5: oklch(0.704 0.191 22);              /* coral bright */

  /* Sidebar -- dark mode */
  --sidebar: oklch(0.225 0.030 172);             /* #162B28 */
  --sidebar-foreground: oklch(0.945 0.010 180);  /* #E6F2F1 */
  --sidebar-primary: oklch(0.835 0.065 192);     /* #9AD9D9 */
  --sidebar-primary-foreground: oklch(0.175 0.025 170); /* #0F1F1D */
  --sidebar-accent: oklch(0.325 0.035 174);      /* #244743 */
  --sidebar-accent-foreground: oklch(0.835 0.065 192);  /* #9AD9D9 */
  --sidebar-border: oklch(0.325 0.035 174);      /* #244743 */
  --sidebar-ring: oklch(0.660 0.140 20);         /* #EB787A */

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

### 16.3 Tailwind 4 `@theme inline` Block

This maps CSS custom properties to Tailwind utility classes.

```css
@theme inline {
  /* Colors */
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
  --color-popover: var(--popover);
  --color-popover-foreground: var(--popover-foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-foreground);
  --color-destructive: var(--destructive);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);

  /* Risk colors */
  --color-risk-low: var(--risk-low);
  --color-risk-low-bg: var(--risk-low-bg);
  --color-risk-low-foreground: var(--risk-low-foreground);
  --color-risk-medium: var(--risk-medium);
  --color-risk-medium-bg: var(--risk-medium-bg);
  --color-risk-medium-foreground: var(--risk-medium-foreground);
  --color-risk-high: var(--risk-high);
  --color-risk-high-bg: var(--risk-high-bg);
  --color-risk-high-foreground: var(--risk-high-foreground);
  --color-risk-presumed: var(--risk-presumed);
  --color-risk-presumed-bg: var(--risk-presumed-bg);
  --color-risk-presumed-foreground: var(--risk-presumed-foreground);

  /* Charts */
  --color-chart-1: var(--chart-1);
  --color-chart-2: var(--chart-2);
  --color-chart-3: var(--chart-3);
  --color-chart-4: var(--chart-4);
  --color-chart-5: var(--chart-5);

  /* Sidebar */
  --color-sidebar: var(--sidebar);
  --color-sidebar-foreground: var(--sidebar-foreground);
  --color-sidebar-primary: var(--sidebar-primary);
  --color-sidebar-primary-foreground: var(--sidebar-primary-foreground);
  --color-sidebar-accent: var(--sidebar-accent);
  --color-sidebar-accent-foreground: var(--sidebar-accent-foreground);
  --color-sidebar-border: var(--sidebar-border);
  --color-sidebar-ring: var(--sidebar-ring);

  /* Typography */
  --font-sans: var(--font-sans);
  --font-mono: var(--font-mono);

  /* Border Radius */
  --radius-sm: calc(var(--radius) - 4px);
  --radius-md: calc(var(--radius) - 2px);
  --radius-lg: var(--radius);
  --radius-xl: calc(var(--radius) + 4px);
}
```

---

## Appendix: Token Migration Checklist

When migrating from the current (shadcn default blue) theme to VAEA:

1. Replace `:root` color block in `globals.css` with Section 16.1
2. Replace `.dark` color block in `globals.css` with Section 16.2
3. Update `@theme inline` block to match Section 16.3
4. Update `--radius` from `0.65rem` to `0.75rem`
5. Replace neutral grey shadows with teal-tinted shadows (Section 6)
6. Update AG Grid `.ag-theme-custom` with Section 10 values
7. Add `--vaea-gradient` and `--vaea-gradient-subtle` custom properties
8. Add brand palette variables (`--vaea-teal-*`, `--vaea-green-*`, etc.)
9. Update button hover states to use `--vaea-teal-700` instead of `/90` opacity
10. Verify all risk badge colors render correctly in both modes
11. Add Aboriginal/Torres Strait Islander acknowledgment to footer
12. Add CoralShades vendor attribution to sidebar footer
13. Run WCAG contrast checker on all text/background combinations
14. Test AG Grid rendering in both light and dark modes
