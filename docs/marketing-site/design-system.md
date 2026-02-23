# Design System

The marketing site uses the VAEA (Victorian Asbestos Eradication Agency) design system, ported from the main application's `frontend/src/app/globals.css`.

## Color Tokens

Defined as CSS custom properties in `src/app/globals.css`:

### Primary Palette

| Token | Value | Usage |
|-------|-------|-------|
| `--vaea-teal-300` | `#53A69D` | Primary brand, links, active states |
| `--vaea-teal-400` | `#458B83` | Hover states |
| `--vaea-coral` | `#EB787A` | CTAs, alerts, accent |
| `--vaea-navy` | `#1e2235` | Headings, dark backgrounds |
| `--vaea-navy-light` | `#2a2f45` | Card backgrounds, sidebar |
| `--vaea-gold` | `#D4A843` | Highlights, badges |
| `--vaea-green-500` | `#22C55E` | Success, operational status |

### Using Colors in Tailwind

Colors are available as Tailwind utilities via `@theme inline` in globals.css:

```html
<div class="bg-vaea-teal-300 text-white">Primary teal</div>
<div class="text-vaea-navy">Navy heading</div>
<div class="border-vaea-coral">Coral border</div>
```

## Typography

Three font families loaded via Google Fonts in `src/app/layout.tsx`:

| Font | CSS Variable | Usage | Weight |
|------|-------------|-------|--------|
| DM Serif Display | `--font-dm-serif` | Display headings, hero text, large numbers | 400 |
| DM Sans | `--font-dm-sans` | Body text, UI labels, navigation | 400-700 |
| JetBrains Mono | `--font-jetbrains-mono` | Code snippets, technical labels, citations | 400-600 |

Usage in Tailwind:
```html
<h1 class="font-[family-name:var(--font-dm-serif)]">Display Heading</h1>
<code class="font-[family-name:var(--font-jetbrains-mono)]">code_example</code>
```

DM Sans is the default body font (set on `<body>`).

## Animation System

### Framer Motion Variants (`src/lib/animations.ts`)

| Variant | Effect | Duration | Delay |
|---------|--------|----------|-------|
| `fadeUp` | Fade in + 20px slide up | 0.6s | 0 |
| `fadeIn` | Simple opacity fade | 0.6s | 0 |
| `slideInLeft` | Slide from -30px left | 0.6s | 0 |
| `slideInRight` | Slide from +30px right | 0.6s | 0 |
| `scaleIn` | Scale from 0.9 to 1.0 | 0.5s | 0 |
| `staggerContainer` | Parent stagger | — | 0.1s per child |
| `staggerFast` | Parent stagger (fast) | — | 0.05s per child |

### Standard Usage Pattern

```typescript
import { motion } from "framer-motion";
import { fadeUp } from "@/lib/animations";
import { useInView } from "@/hooks/useInView";

function MyComponent() {
  const { ref, isInView } = useInView({ threshold: 0.1 });
  return (
    <div ref={ref}>
      <motion.div variants={fadeUp} initial="hidden" animate={isInView ? "visible" : "hidden"}>
        Content reveals when scrolled into view
      </motion.div>
    </div>
  );
}
```

### CSS Animations (globals.css)

| Class | Effect |
|-------|--------|
| `typing-cursor` | Blinking cursor for typewriter effect |
| `terminal-scanline` | CRT scanline overlay for terminal UI |
| `hero-grid` | Subtle grid pattern for hero backgrounds |
| `glass` | Glass-morphism (backdrop-blur + semi-transparent bg) |

## Custom Hooks

### `useInView` — Scroll-triggered visibility

```typescript
const { ref, isInView } = useInView({
  threshold: 0.1,      // 10% visible triggers
  rootMargin: "0px",   // No margin offset
  once: true,          // Only trigger once (default)
});
```

### `useCounter` — Animated count-up

```typescript
const count = useCounter({
  end: 96,             // Target number
  start: 0,            // Starting number (default: 0)
  duration: 2000,      // Animation duration in ms (default: 2000)
  enabled: isInView,   // Trigger condition
});
```

### `useTypewriter` — Character-by-character text reveal

```typescript
const { displayed, isComplete } = useTypewriter({
  text: "Full text to reveal...",
  speed: 18,           // ms per character
  delay: 800,          // ms before starting
  enabled: isInView,   // Trigger condition
});
```

## Component Patterns

### Card Pattern
```html
<div class="rounded-xl border border-border p-5 bg-card">
  <!-- Card content -->
</div>
```

### Glass Card Pattern
```html
<div class="glass rounded-xl p-5 border border-white/10">
  <!-- Glass-morphism content -->
</div>
```

### Status Indicator Pattern
```html
<div class="flex items-center gap-2">
  <span class="relative flex h-2 w-2">
    <span class="animate-ping absolute h-full w-full rounded-full bg-vaea-green-500 opacity-75" />
    <span class="relative rounded-full h-2 w-2 bg-vaea-green-500" />
  </span>
  <span class="text-xs">Operational</span>
</div>
```

### Section Layout Pattern
```html
<section class="py-20 px-6">
  <div class="max-w-6xl mx-auto">
    <!-- Section content -->
  </div>
</section>
```

## Dark Mode

The site uses `next-themes` with `defaultTheme="light"`. Dark mode support is available through Tailwind's `dark:` variants and CSS custom properties that switch between light/dark values.

The theme toggle is handled by the ThemeProvider in the root layout. Components use semantic color tokens (`bg-card`, `text-foreground`, `border-border`) that automatically adapt.

## Design Direction

"Institutional Precision" — Financial Times meets Linear.app:
- Navy backgrounds with teal accents
- Coral for CTAs and alerts
- NO purple gradients
- NO Inter font
- Clean data presentation with monospace technical labels
- Government-grade visual authority
