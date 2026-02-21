# Design Command

Use the UI/UX Pro Max Skill for design intelligence and decisions.

## Overview

This command activates the UI/UX Pro Max skill which provides:
- 50+ UI styles (glassmorphism, bento grid, minimalism, neumorphism, etc.)
- 21 color palettes optimized for different product types
- 50 font pairings with Google Fonts imports
- 20 chart type recommendations
- Stack-specific guidelines (React, Next.js, Vue, shadcn/ui, etc.)

## Usage

Reference the skill when designing UI components:

```
Using ui-ux-pro-max-skill, create a bento grid layout for the dashboard
```

```
Apply the design tokens from ui-ux-pro-max-skill to the ACM Register theme
```

## Search Command

Search the design database directly:

```bash
python .claude/skills/ui-ux-pro-max-skill/.claude/skills/ui-ux-pro-max/scripts/search.py "<query>" --domain <domain> [-n <results>]
```

### Available Domains

| Domain | Use For | Example |
|--------|---------|---------|
| `product` | Product type recommendations | SaaS, dashboard, e-commerce |
| `style` | UI styles and effects | glassmorphism, bento grid |
| `typography` | Font pairings | elegant, professional, modern |
| `color` | Color palettes | healthcare, fintech, SaaS |
| `landing` | Page structure | hero, pricing, testimonials |
| `chart` | Chart types | trend, comparison, funnel |
| `ux` | Best practices | accessibility, animation |

### Available Stacks

| Stack | Focus |
|-------|-------|
| `html-tailwind` | Tailwind utilities (default) |
| `react` | React patterns, hooks |
| `nextjs` | SSR, App Router, images |
| `shadcn` | shadcn/ui components |
| `vue` | Vue 3 Composition API |

## Example Workflow

For ACM-AI UI refresh:

```bash
# Get bento grid style guidelines
python .claude/skills/ui-ux-pro-max-skill/.claude/skills/ui-ux-pro-max/scripts/search.py "bento grid dashboard" --domain style

# Get color palette for SaaS dashboard
python .claude/skills/ui-ux-pro-max-skill/.claude/skills/ui-ux-pro-max/scripts/search.py "saas dashboard" --domain color

# Get shadcn/ui specific patterns
python .claude/skills/ui-ux-pro-max-skill/.claude/skills/ui-ux-pro-max/scripts/search.py "card grid layout" --stack shadcn
```

## Key Design Principles

From the skill's guidelines:

1. **No emoji icons** - Use Lucide icons (already in project)
2. **Stable hover states** - Use color/opacity, not scale transforms
3. **Cursor pointer** - Add to all clickable elements
4. **Light/dark mode contrast** - Test both modes
5. **Floating navbar** - Add spacing from edges
6. **Consistent max-width** - Use same container widths

## Pre-Delivery Checklist

Before delivering UI code:
- [ ] No emojis as icons (use Lucide)
- [ ] All clickable elements have `cursor-pointer`
- [ ] Hover states provide visual feedback
- [ ] Light mode text has sufficient contrast
- [ ] Responsive at 320px, 768px, 1024px, 1440px
- [ ] All images have alt text

## Related

- Skill location: `.claude/skills/ui-ux-pro-max-skill/`
- Full documentation: `.claude/skills/ui-ux-pro-max-skill/README.md`
- Skill definition: `.claude/skills/ui-ux-pro-max-skill/.claude/skills/ui-ux-pro-max/SKILL.md`
