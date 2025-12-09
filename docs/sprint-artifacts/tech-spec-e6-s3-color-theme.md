# Tech Spec: E6-S3 - Update Color Theme

> **Story:** E6-S3
> **Epic:** Rebranding to ACM-AI
> **Status:** Draft
> **Created:** 2025-12-08

---

## Overview

Update the application color scheme to a professional palette appropriate for compliance/safety software, with proper dark mode support.

---

## User Story

**As a** user
**I want** a professional color scheme
**So that** the app feels appropriate for compliance work

---

## Acceptance Criteria

- [ ] Primary color updated (suggested: blue/teal)
- [ ] Accent color for risk indicators
- [ ] Dark mode colors adjusted
- [ ] Consistent across all components

---

## Technical Design

### 1. Color Palette Definition

ACM-AI color palette:

```
Primary:      Blue (#2563EB / blue-600) - Trust, professionalism
Secondary:    Slate (#475569 / slate-600) - Neutral, professional
Accent:       Cyan (#06B6D4 / cyan-500) - Technology, AI

Semantic:
Success:      Green (#22C55E / green-500) - Low risk
Warning:      Amber (#F59E0B / amber-500) - Medium risk
Danger:       Red (#EF4444 / red-500) - High risk

Background:
Light:        White (#FFFFFF)
Dark:         Slate 950 (#020617)
```

### 2. CSS Variables Update

Update `frontend/src/app/globals.css`:

```css
@layer base {
  :root {
    /* Base colors */
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;

    /* Card and popover */
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;

    /* Primary - Blue */
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;

    /* Secondary - Slate */
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;

    /* Muted */
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;

    /* Accent - Cyan tint */
    --accent: 186 94% 82%;
    --accent-foreground: 222.2 47.4% 11.2%;

    /* Semantic colors */
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;

    /* Risk status colors */
    --risk-low: 142 76% 36%;
    --risk-low-bg: 142 76% 90%;
    --risk-medium: 45 93% 47%;
    --risk-medium-bg: 45 93% 90%;
    --risk-high: 0 84% 60%;
    --risk-high-bg: 0 84% 93%;

    /* Border and input */
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 221.2 83.2% 53.3%;

    /* Chart colors */
    --chart-1: 221.2 83.2% 53.3%;
    --chart-2: 186 94% 42%;
    --chart-3: 142 76% 36%;
    --chart-4: 45 93% 47%;
    --chart-5: 0 84% 60%;

    --radius: 0.5rem;
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;

    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;

    /* Primary - Lighter blue for dark mode */
    --primary: 217.2 91.2% 59.8%;
    --primary-foreground: 222.2 47.4% 11.2%;

    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;

    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;

    --accent: 186 94% 25%;
    --accent-foreground: 210 40% 98%;

    --destructive: 0 62.8% 50.6%;
    --destructive-foreground: 210 40% 98%;

    /* Risk status colors - darker backgrounds */
    --risk-low: 142 70% 45%;
    --risk-low-bg: 142 70% 15%;
    --risk-medium: 45 93% 55%;
    --risk-medium-bg: 45 93% 15%;
    --risk-high: 0 84% 65%;
    --risk-high-bg: 0 84% 15%;

    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: 224.3 76.3% 48%;
  }
}
```

### 3. Tailwind Config Update

Update `frontend/tailwind.config.ts`:

```ts
import type { Config } from 'tailwindcss';

const config: Config = {
  theme: {
    extend: {
      colors: {
        // Risk status utility classes
        'risk-low': 'hsl(var(--risk-low))',
        'risk-low-bg': 'hsl(var(--risk-low-bg))',
        'risk-medium': 'hsl(var(--risk-medium))',
        'risk-medium-bg': 'hsl(var(--risk-medium-bg))',
        'risk-high': 'hsl(var(--risk-high))',
        'risk-high-bg': 'hsl(var(--risk-high-bg))',
      },
    },
  },
};

export default config;
```

### 4. Component Updates

Update shadcn/ui components to use new colors:

```tsx
// Example: Risk status badge
<Badge className="bg-risk-low-bg text-risk-low">Low</Badge>
<Badge className="bg-risk-medium-bg text-risk-medium">Medium</Badge>
<Badge className="bg-risk-high-bg text-risk-high">High</Badge>
```

---

## File Changes

| File | Change |
|------|--------|
| `frontend/src/app/globals.css` | Update CSS variables |
| `frontend/tailwind.config.ts` | Add risk color utilities |
| Various components | Update to use new colors |

---

## Dependencies

None - can be done independently

---

## Testing

1. Visual review of all pages in light mode
2. Visual review of all pages in dark mode
3. Check risk status colors are distinguishable
4. Run color contrast checker (WCAG AA minimum)
5. Test on different monitors/devices
6. Verify charts use new color palette

---

## Color Accessibility

Ensure all text meets WCAG AA contrast ratios:
- Normal text: 4.5:1
- Large text: 3:1
- UI components: 3:1

Tools:
- https://webaim.org/resources/contrastchecker/
- Chrome DevTools accessibility panel

---

## Estimated Complexity

**Low** - CSS variable updates, minimal component changes

---
