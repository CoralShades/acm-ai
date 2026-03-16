# Frontend, UI/UX & Design Skills Inventory

> **Generated:** 2026-03-11 | **Project:** ACM-AI | **Branch:** ACMV3

---

## Table of Contents

1. [Skills Overview Matrix](#skills-overview-matrix)
2. [Installed Skills — Detailed Profiles](#installed-skills--detailed-profiles)
3. [Marketplace Skills — Available for Install](#marketplace-skills--available-for-install)
4. [Capability Comparison Matrix](#capability-comparison-matrix)
5. [Enforcement Hierarchy](#enforcement-hierarchy)
6. [Integration Architecture](#integration-architecture)
7. [Blog Comparison — Claude Frontend Design Best Practices](#blog-comparison)
8. [Gaps & Recommendations](#gaps--recommendations)

---

## Skills Overview Matrix

### Installed Skills (21 frontend/UI/design-related)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ACM-AI DESIGN SKILL ARSENAL                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ uncodixfy   │  │ baseline-ui  │  │ taste-skill  │  │ frontend-   │ │
│  │ (Anti-Slop  │──│ (Constraint  │──│ (Design      │──│  design     │ │
│  │  Foundation)│  │  Validator)  │  │  Engineer)   │  │ (Aesthetic  │ │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘  │  Director)  │ │
│         │                │                  │          └──────┬──────┘ │
│         ▼                ▼                  ▼                 ▼        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              FRAMEWORK LAYER                                     │  │
│  │  ┌────────────────────┐    ┌─────────────────────┐              │  │
│  │  │ react-best-        │    │ next-best-           │              │  │
│  │  │ practices (57      │    │ practices (18        │              │  │
│  │  │ perf rules)        │    │ sections, RSC/App    │              │  │
│  │  └────────────────────┘    │ Router)              │              │  │
│  │                            └─────────────────────┘              │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│         │                │                  │                 │        │
│         ▼                ▼                  ▼                 ▼        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              QUALITY GATES                                       │  │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │  │
│  │  │ fixing-      │ │ fixing-      │ │ fixing-motion-           │ │  │
│  │  │ accessibility│ │ metadata     │ │ performance              │ │  │
│  │  │ (WCAG 2.1)  │ │ (SEO/OG)     │ │ (Compositor/Layout)      │ │  │
│  │  └──────────────┘ └──────────────┘ └──────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│         │                │                  │                 │        │
│         ▼                ▼                  ▼                 ▼        │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │              TESTING & VALIDATION                                │  │
│  │  ┌──────────┐ ┌──────────────┐ ┌────────┐ ┌──────────┐         │  │
│  │  │ webapp-  │ │ playwright-  │ │ e2e-   │ │ dogfood  │         │  │
│  │  │ testing  │ │ skill        │ │ test   │ │ (QA      │         │  │
│  │  │ (Basic)  │ │ (Advanced)   │ │ (Self- │ │  Hunter) │         │  │
│  │  │          │ │              │ │ Heal)  │ │          │         │  │
│  │  └──────────┘ └──────────────┘ └────────┘ └──────────┘         │  │
│  │  ┌──────────┐ ┌──────────────────────────┐                      │  │
│  │  │ electron │ │ web-design-guidelines    │                      │  │
│  │  │ (Desktop)│ │ (Vercel Compliance)      │                      │  │
│  │  └──────────┘ └──────────────────────────┘                      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Installed Skills — Detailed Profiles

### 1. `uncodixfy` — Anti-AI-Slop Foundation

| Attribute | Detail |
|-----------|--------|
| **Location** | `.agents/skills/uncodixfy/` (symlinked to `.claude/skills/`) |
| **Purpose** | Prevent generic AI/Codex UI patterns; enforce clean human-designed aesthetics |
| **Inspiration** | Linear, Raycast, Stripe, GitHub |
| **Ban Count** | 130+ explicitly banned patterns |

**Core Capabilities:**
- Pattern detection for 30+ component types (sidebar, header, card, form, modal, dropdown, table, etc.)
- 10 dark + 10 light predefined color palettes (Midnight Canvas, Pearl Minimal, etc.)
- Explicit size/radius constraints (8-12px card radius, 8-10px button radius, <8px shadow blur)
- Typography enforcement: ban Inter, Roboto, Segoe UI, Trebuchet MS, Arial
- Spacing scale: 4/8/12/16/24/32px only
- Transition limits: 100-200ms ease only, no bounce/transform

**Hard Bans (top examples):**
- Oversized rounded corners (>12px)
- Pill shape overload
- Floating glassmorphism shells
- Soft corporate gradients
- Generic dark SaaS composition
- Metric-card grid as default
- Hero sections inside internal UI
- Blue-black gradients + cyan accents
- KPI card grids, pipeline bars with gradients

---

### 2. `baseline-ui` — Constraint Validator

| Attribute | Detail |
|-----------|--------|
| **Location** | `.claude/skills/baseline-ui/` |
| **Purpose** | Validate animations, typography, accessibility, layout anti-patterns |
| **Stack** | Tailwind CSS, motion/react, tw-animate-css, clsx+tailwind-merge |

**Constraint Categories:**

| Category | Rule Count | Severity |
|----------|-----------|----------|
| Animation | 10 rules | MUST/NEVER |
| Typography | 5 rules | MUST/SHOULD |
| Components | 6 rules | MUST/NEVER |
| Interactions | 5 rules | MUST/NEVER |
| Layout | 2 rules | MUST/SHOULD |
| Performance | 3 rules | NEVER |
| Design | 7 rules | NEVER/SHOULD |

**Key Enforcements:**
- NEVER animate layout props (width, height, margin, padding)
- MUST animate only compositor props (transform, opacity)
- NEVER exceed 200ms for interaction feedback
- MUST use accessible primitives (Base UI / React Aria / Radix)
- NEVER use `h-screen` (use `h-dvh`)
- NEVER use gradients unless explicitly requested
- NEVER use purple/multicolor gradients

---

### 3. `taste-skill` — Design Engineer

| Attribute | Detail |
|-----------|--------|
| **Location** | `.claude/skills/taste-skill/` |
| **Purpose** | Senior UI/UX engineer with metric-based design controls |
| **Installs** | 741 (skills.sh) |

**Control Dials:**

```
DESIGN_VARIANCE ─────────── [████████░░] 8/10
   1=predictable  ···  10=asymmetric

MOTION_INTENSITY ────────── [██████░░░░] 6/10
   1=static  ···  10=choreographed

VISUAL_DENSITY ──────────── [████░░░░░░] 4/10
   1=art gallery  ···  10=cockpit
```

**Unique Features:**
- 5 Bento Grid archetype cards with specific CSS animations
- Liquid glass refraction system (inner borders, shadow layers)
- Magnetic micro-physics for hover interactions
- Spring-based physics (mass 0.8, stiffness 140, damping 28)
- Staggered orchestration via layout/layoutId
- 100+ AI tell prevention patterns
- "LILA BAN" — purple/blue accent prohibition

---

### 4. `frontend-design` — Aesthetic Director

| Attribute | Detail |
|-----------|--------|
| **Location** | `.claude/skills/frontend-design/` |
| **Purpose** | Create distinctive, production-grade interfaces avoiding AI slop |

**Aesthetic Directions Available:**
- Minimalist, Maximalist, Retro-futuristic, Organic
- Luxury, Playful, Editorial, Brutalist, Art Deco
- And more — chosen per project context

**Design Dimensions:**
1. **Typography** — Display + body pairing, extreme weight variations (100/200 vs 800/900)
2. **Color & Theme** — CSS variables, dominant + sharp accent, anti-AI-purple
3. **Motion** — CSS animations, scroll-triggering, hover states, page load choreography
4. **Spatial Composition** — Asymmetry, overlap, diagonal flow, grid-breaking
5. **Visual Details** — Noise textures, geometric patterns, layered transparencies, grain overlays

---

### 5. `react-best-practices` — Performance Optimizer

| Attribute | Detail |
|-----------|--------|
| **Location** | `.claude/skills/react-best-practices/` |
| **Source** | Vercel Engineering |
| **Rule Count** | 57 rules across 8 categories |

**Rule Distribution:**

```
Priority 1  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  Eliminating Waterfalls (CRITICAL)
Priority 2  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓    Bundle Size (CRITICAL)
Priority 3  ▓▓▓▓▓▓▓▓▓▓▓▓      Server-Side (HIGH)
Priority 4  ▓▓▓▓▓▓▓▓           Client Data Fetching (MED-HIGH)
Priority 5  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  Re-render Optimization (12 rules)
Priority 6  ▓▓▓▓▓▓▓▓▓▓▓▓      Rendering Performance (9 rules)
Priority 7  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  JS Performance (12 rules)
Priority 8  ▓▓▓▓               Advanced Patterns (LOW)
```

**Key Patterns:** Promise.all(), Suspense streaming, React.cache(), dynamic imports, SWR dedup, useTransition

---

### 6. `next-best-practices` — Framework Guide

| Attribute | Detail |
|-----------|--------|
| **Location** | `.claude/skills/next-best-practices/` |
| **Coverage** | 18 sections, Next.js 15+, React 19, App Router |

**Section Map:**

```
File Conventions ──── RSC Boundaries ──── Async Patterns
       │                    │                   │
   Directives ────── Runtime Selection ──── Functions
       │                    │                   │
  Error Handling ──── Data Patterns ───── Route Handlers
       │                    │                   │
  Metadata/OG ────── Image/Font Opt ──── Bundling
       │                    │                   │
    Scripts ──── Hydration Errors ──── Suspense
       │                    │
  Parallel Routes ──── Self-Hosting
```

---

### 7. `fixing-accessibility` — WCAG Compliance

| Attribute | Detail |
|-----------|--------|
| **Location** | `.claude/skills/fixing-accessibility/` |
| **Standard** | WCAG 2.1 AA |
| **Categories** | 9 rule groups |

**Priority Map:**

| Priority | Category | Examples |
|----------|----------|----------|
| CRITICAL | Accessible names | aria-label, aria-labelledby |
| CRITICAL | Keyboard access | Tab navigation, focus management |
| CRITICAL | Focus/Dialogs | Focus trapping, restoration |
| HIGH | Semantics | Semantic HTML elements |
| HIGH | Forms/Errors | aria-describedby, aria-invalid |
| MED-HIGH | Announcements | aria-live regions |
| MEDIUM | Contrast/States | Color contrast, state indicators |
| LOW-MED | Media/Motion | prefers-reduced-motion |

---

### 8. `fixing-metadata` — SEO & Social

| Attribute | Detail |
|-----------|--------|
| **Categories** | 8 rule groups covering title, OG, Twitter, JSON-LD, favicons |

---

### 9. `fixing-motion-performance` — Animation Perf

| Attribute | Detail |
|-----------|--------|
| **Categories** | 9 rule groups |
| **Core Principle** | Compositor props only (transform, opacity) |

**Rendering Pipeline:**

```
Composite (FAST)     transform, opacity
    ↑
Paint (MEDIUM)       color, borders, gradients, filters
    ↑
Layout (SLOW)        size, position, flow, grid, flex
```

**Critical Never Patterns:**
- Don't interleave layout reads/writes in same frame
- Don't animate layout continuously
- Don't drive animation from scroll events
- No rAF loops without stop condition

---

### 10. `webapp-testing` — Basic Interactive Testing

| Attribute | Detail |
|-----------|--------|
| **Stack** | Playwright (sync_api), Python |
| **Pattern** | Navigate → Wait → Screenshot → Inspect → Interact |

---

### 11. `playwright-skill` — Advanced Browser Automation

| Attribute | Detail |
|-----------|--------|
| **Stack** | Playwright, Chromium/Firefox/WebKit |
| **Features** | Auto server detection, viewport testing, API mocking, auth, visual regression |
| **Helper Functions** | detectDevServers, safeClick, safeType, takeScreenshot, extractTableData |

---

### 12. `e2e-test` — Self-Healing E2E

| Attribute | Detail |
|-----------|--------|
| **Stack** | Playwright, agent-browser, chrome-devtools, axe-core |
| **Phases** | 6 (research → select → execute → evidence → fix → report) |

**Test Tiers:**

```
SMOKE        ████░░░░░░  <30s   Every PR     Route walking, API health
CRITICAL     ██████░░░░  <5min  Merge→main   Upload wizard, jobs pipeline
FEATURE      ████████░░  <15min Nightly      Settings, building detail
A11Y         █████░░░░░  <5min  Nightly      WCAG 2.1 AA audits
```

**Selector Strategy Chain:**

```
data-testid ──── ████████████████████ 1.00 confidence
role+name   ──── ███████████████████░ 0.95
aria-label  ──── ██████████████████░░ 0.90
text        ──── ████████████████░░░░ 0.80
CSS         ──── ████████████░░░░░░░░ 0.60
XPath       ──── ████████░░░░░░░░░░░░ 0.40
```

---

### 13. `dogfood` — QA Bug Hunter

| Attribute | Detail |
|-----------|--------|
| **Stack** | agent-browser CLI, screenshot/video |
| **Phases** | 6 (Initialize → Auth → Orient → Explore → Document → Wrap up) |
| **Target** | 5-10 well-documented issues per session |

---

### 14. `electron` — Desktop App Automation

| Attribute | Detail |
|-----------|--------|
| **Stack** | agent-browser, Chrome DevTools Protocol (CDP) |
| **Supported Apps** | Slack, Discord, VS Code, Figma, Notion, Spotify, etc. |

---

### 15. `web-design-guidelines` — Vercel Compliance

| Attribute | Detail |
|-----------|--------|
| **Source** | vercel-labs/web-interface-guidelines |
| **Output** | `file:line` terse format |

---

### 16. `ui-ux-pro-max` — Design Intelligence (PLUGIN)

| Attribute | Detail |
|-----------|--------|
| **Location** | Plugin: `~/.claude/plugins/marketplaces/ui-ux-pro-max-skill/` |
| **Version** | 2.0.1 |
| **Purpose** | Comprehensive design guide: 50+ styles, 97 palettes, 57 font pairings, 99 UX guidelines, 25 chart types, 9 stacks |
| **Invoke** | `/ui-ux-pro-max` |

**Rule Categories by Priority:**

| Priority | Category | Impact |
|----------|----------|--------|
| 1 | Accessibility | CRITICAL |
| 2 | Touch & Interaction | CRITICAL |
| 3 | Performance | HIGH |
| 4 | Layout & Responsive | HIGH |
| 5 | Typography & Color | MEDIUM |
| 6 | Animation | MEDIUM |
| 7 | Style Selection | MEDIUM |
| 8 | Charts & Data | LOW |

**Data Files:** styles.csv, colors.csv, typography.csv, ux-guidelines.csv, charts.csv, icons.csv, landing.csv, products.csv, web-interface.csv, ui-reasoning.csv, react-performance.csv

**Stacks Covered:** React, Next.js, Vue, Svelte, SwiftUI, React Native, Flutter, HTML+Tailwind, shadcn/ui, Nuxt, Nuxt UI, Astro, Jetpack Compose

---

### 17. `web-artifacts-builder` — Single-File React Prototyping

| Attribute | Detail |
|-----------|--------|
| **Location** | `~/.agents/skills/web-artifacts-builder/` (symlinked) |
| **Source** | `anthropics/skills` (official, 12.8K installs) |
| **Purpose** | Build multi-component React artifacts bundled into single HTML files |
| **Stack** | React 18 + TypeScript + Vite + Parcel + Tailwind CSS + 40+ shadcn/ui components |

**Anti-slop policy:** Explicitly avoids centered layouts, purple gradients, uniform rounded corners, Inter font.

---

### 18. `copilotkit` — AI Copilot Framework

| Attribute | Detail |
|-----------|--------|
| **Location** | `~/.agents/skills/copilotkit/` (symlinked) |
| **Version** | v1.51.3 (React), v0.1.78 (Python SDK) |
| **Purpose** | Build AI copilots, chatbots, and agentic UIs in React/Next.js/Angular |

**Key Components:**
- Chat UIs: `CopilotPopup`, `CopilotSidebar`, `CopilotChat`
- Hooks: `useCopilotAction`, `useCopilotReadable`, `useCoAgent`, `useAgent`
- AI Textarea: `CopilotTextarea` for AI-powered form completion
- CoAgents: LangGraph Python agent ↔ React state sync
- AG-UI Protocol: Agent-to-UI communication standard
- MCP Apps: Model Context Protocol integration
- Human-in-the-Loop: `useLangGraphInterrupt`, `useHumanInTheLoop`

---

### 19. `a2a-protocol` — Agent-to-Agent Communication

| Attribute | Detail |
|-----------|--------|
| **Location** | `~/.agents/skills/a2a-protocol/` (symlinked) |
| **Protocol** | A2A v0.3.0 |
| **Purpose** | Build agents that communicate via the Agent2Agent protocol |

**Core Structures:** AgentCard, Task, Message, Part, Artifact
**Protocol Bindings:** JSON-RPC 2.0, gRPC, HTTP/REST
**Discovery:** `/.well-known/agent-card.json` manifest

---

### 20. `sse-streaming` — Server-Sent Events

| Attribute | Detail |
|-----------|--------|
| **Location** | `~/.agents/skills/sse-streaming/` (symlinked) |
| **Languages** | TypeScript/JavaScript, Python |
| **Purpose** | Implement SSE for real-time updates with auto-reconnection and heartbeats |

**Use Cases:** Live dashboards, notifications, progress indicators, AI streaming responses
**ACM-AI Relevance:** Directly applicable to `PipelineEventBus` SSE streaming architecture

---

### 21. `design-system-creation` — Design System Builder

| Attribute | Detail |
|-----------|--------|
| **Location** | `~/.agents/skills/design-system-creation/` (symlinked) |
| **Purpose** | Build comprehensive design systems with components, patterns, and guidelines |

**Layers:** Foundation (tokens, colors, typography) → Components → Patterns → Guidelines

---

## Marketplace Skills — Still Available

### Not Yet Installed (Lower Priority)

| Skill | Source | Installs | Category | Install Command |
|-------|--------|----------|----------|-----------------|
| **frontend-ui-ux-engineer** | 404kidwiz | 920 | Design | `npx skills add 404kidwiz/claude-supercode-skills@frontend-ui-ux-engineer` |
| **design-taste-frontend** | leonxlnx | 741 | Aesthetics | `npx skills add leonxlnx/taste-skill@design-taste-frontend` |
| **innovative-ux-designer** | bencium | 230 | UX | `npx skills add bencium/bencium-claude-code-design-skill@bencium-innovative-ux-designer` |
| **design-system-architect** | daffy0208 | 88 | Systems | `npx skills add daffy0208/ai-dev-standards@design-system-architect` |
| **a2a-patterns** | vanman2024 | 5 | A2A | `npx skills add vanman2024/ai-dev-marketplace@a2a-patterns` |
| **a2a-server-config** | vanman2024 | 6 | A2A | `npx skills add vanman2024/ai-dev-marketplace@a2a-server-config` |
| **llm-streaming** | yonatangross | 12 | Streaming | `npx skills add yonatangross/orchestkit@llm-streaming` |
| **implementing-realtime-sync** | ancoleman | 21 | Realtime | `npx skills add ancoleman/ai-design-components@implementing-realtime-sync` |
| **react-artifacts** | eyadsibai | 29 | Artifacts | `npx skills add eyadsibai/ltk@react-artifacts` |
| **google-material-design** | copyleftdev | 30 | Design System | `npx skills add copyleftdev/sk1llz@google-material-design` |

---

## Capability Comparison Matrix

### Design Quality Enforcement

```
                    uncodixfy  baseline  taste   frontend  web-guide
                    ─────────  ────────  ──────  ────────  ─────────
Anti-AI-Slop        ██████████ ████████  ██████  ████████  ░░░░░░░░
Color Control       ██████████ ████████  ██████  ████████  ░░░░░░░░
Typography          ██████████ ██████░░  ████░░  ██████░░  ░░░░░░░░
Animation Rules     ████░░░░░░ ██████████ ██████ ████████  ░░░░░░░░
Layout Patterns     ██████████ ████████  ██████  ██████░░  ██████░░
Component Rules     ██████████ ██████████ ████░░ ██░░░░░░  ██████░░
Accessibility       ░░░░░░░░░░ ████████  ░░░░░░ ░░░░░░░░  ██████░░
Performance         ░░░░░░░░░░ ██████░░  ████░░ ░░░░░░░░  ░░░░░░░░
SEO/Metadata        ░░░░░░░░░░ ░░░░░░░░  ░░░░░░ ░░░░░░░░  ░░░░░░░░
```

### Testing Coverage

```
                    webapp  playwright  e2e-test  dogfood  electron
                    ──────  ──────────  ────────  ───────  ────────
Unit Tests          ░░░░░░  ░░░░░░░░░░  ░░░░░░░░ ░░░░░░░  ░░░░░░░░
Integration         ████░░  ████████░░  ████████ ░░░░░░░  ░░░░░░░░
E2E Flows           ████░░  ██████████  ████████ ████████ ██████░░
Visual Regression   ░░░░░░  ██████░░░░  ████░░░░ ████████ ████░░░░
Accessibility       ░░░░░░  ░░░░░░░░░░  ████████ ░░░░░░░  ░░░░░░░░
Responsive          ████░░  ██████████  ████░░░░ ████████ ░░░░░░░░
Self-Healing        ░░░░░░  ░░░░░░░░░░  ████████ ░░░░░░░  ░░░░░░░░
Evidence Capture    ████░░  ██████░░░░  ████████ ████████ ████████
Desktop Apps        ░░░░░░  ░░░░░░░░░░  ░░░░░░░░ ░░░░░░░  ████████
```

### Framework Coverage

```
                    react-bp  next-bp   baseline  taste
                    ────────  ────────  ────────  ──────
React 19            ████████  ████████  ████████  ████████
Next.js 15          ████░░░░  ████████  ░░░░░░░░  ████████
RSC/App Router      ████████  ████████  ░░░░░░░░  ░░░░░░░░
Server Actions      ░░░░░░░░  ████████  ░░░░░░░░  ░░░░░░░░
Tailwind CSS        ░░░░░░░░  ████░░░░  ████████  ████████
Zustand             ░░░░░░░░  ░░░░░░░░  ░░░░░░░░  ████████
Framer Motion       ░░░░░░░░  ░░░░░░░░  ████████  ████████
Radix UI            ░░░░░░░░  ░░░░░░░░  ████████  ░░░░░░░░
```

---

## Enforcement Hierarchy

Skills are applied in a specific order — each layer constrains the one above it:

```
Layer 1 (Foundation)     uncodixfy
    │                    Prevents generic AI patterns at generation time
    │                    130+ banned patterns, component size constraints
    ▼
Layer 2 (Constraints)    baseline-ui
    │                    Validates Tailwind usage, animation limits, a11y
    │                    38+ MUST/NEVER rules across 7 categories
    ▼
Layer 3 (Engineering)    taste-skill
    │                    Applies design variance/motion/density controls
    │                    Spring physics, Bento grids, micro-interactions
    ▼
Layer 4 (Direction)      frontend-design
    │                    Selects aesthetic direction, typography pairs
    │                    Bold visual choices, spatial composition
    ▼
Layer 5 (Framework)      react-best-practices + next-best-practices
    │                    57 perf rules, RSC patterns, data fetching
    │                    Waterfall elimination, bundle optimization
    ▼
Layer 6 (Quality)        fixing-accessibility + fixing-metadata + fixing-motion-performance
    │                    WCAG compliance, SEO, animation performance
    ▼
Layer 7 (Validation)     webapp-testing → playwright-skill → e2e-test → dogfood
                         Progressive testing depth, self-healing, evidence
```

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DESIGN PHASE                                  │
│                                                                  │
│  User Request ──→ uncodixfy (filter) ──→ baseline-ui (validate) │
│                       │                       │                  │
│                       ▼                       ▼                  │
│              taste-skill (engineer) ──→ frontend-design (direct) │
│                       │                       │                  │
│                       ▼                       ▼                  │
│         react-best-practices ──→ next-best-practices             │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                    BUILD PHASE                                   │
│                                                                  │
│  Component Code ──→ fixing-accessibility (WCAG)                  │
│                 ──→ fixing-metadata (SEO)                        │
│                 ──→ fixing-motion-performance (60fps)             │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                    TEST PHASE                                    │
│                                                                  │
│  webapp-testing (basic)                                          │
│       │                                                          │
│       ▼                                                          │
│  playwright-skill (scripted automation)                          │
│       │                                                          │
│       ▼                                                          │
│  e2e-test (self-healing, a11y audit, evidence)                   │
│       │                                                          │
│       ▼                                                          │
│  dogfood (exploratory QA, bug hunting)                           │
│       │                                                          │
│       ▼                                                          │
│  web-design-guidelines (Vercel compliance check)                 │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                    DESKTOP TESTING                                │
│                                                                  │
│  electron (CDP automation for Slack, VS Code, Figma, etc.)       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Blog Comparison

### Claude Blog: "Improving Frontend Design Through Skills"

**Blog URL:** `https://claude.com/blog/improving-frontend-design-through-skills`

The blog identifies the core problem of **distributional convergence** — AI models favor statistically common patterns, creating generic "AI slop" aesthetics. It recommends skills as "just-in-time" expertise injection.

#### Blog Recommendations vs Our Implementation

| Blog Recommendation | Our Status | Implementing Skill(s) |
|---------------------|-----------|----------------------|
| **Avoid Inter, Roboto, Open Sans, Arial** | IMPLEMENTED | `uncodixfy` (bans these), `taste-skill` (alternative fonts) |
| **Prefer JetBrains Mono, Playfair Display, IBM Plex** | PARTIALLY | `frontend-design` (font pairing), `taste-skill` (typography rules) |
| **Use high contrast font pairings** | IMPLEMENTED | `frontend-design` (display + monospace, serif + sans) |
| **Extreme weight variations (100/200 vs 800/900)** | IMPLEMENTED | `frontend-design` |
| **RPG/thematic aesthetic direction** | IMPLEMENTED | `frontend-design` (10+ aesthetic directions), `taste-skill` (design variance dial) |
| **CSS-only or Motion library animations** | IMPLEMENTED | `baseline-ui` (motion/react enforcement), `taste-skill` (Spring physics) |
| **Staggered page-load reveals** | IMPLEMENTED | `taste-skill` (Bento archetype cards, staggered orchestration) |
| **Layer CSS gradients/geometric patterns** | PARTIALLY | `frontend-design` (visual details), BUT `baseline-ui` bans gradients unless requested |
| **Frontend Aesthetics Skill (~400 tokens)** | EXCEEDED | Multiple skills cover this with far more depth |
| **Web-Artifacts-Builder** | INSTALLED | `web-artifacts-builder` (official anthropics/skills, 12.8K installs) |
| **Prompt at right altitude** | IMPLEMENTED | `taste-skill` control dials (1-10 scales), `uncodixfy` golden rules |

#### Coverage Assessment

```
Blog Dimension        Coverage Level        Notes
──────────────        ──────────────        ─────
Typography            ████████████ 95%      Full coverage via 3 skills
Color/Theme           ██████████░░ 85%      Strong but gradient tension*
Motion/Animation      ████████████ 95%      Excellent via taste + baseline
Backgrounds           ██████████░░ 80%      Patterns yes, layered gradients restricted
Anti-AI-Slop          ████████████ 100%     Best-in-class via uncodixfy
Right-Altitude Prompt ██████████░░ 90%      Control dials, golden rules
Web-Artifacts-Builder ████████████ 100%    INSTALLED — anthropics/skills official

* baseline-ui restricts gradients by default (NEVER unless requested)
  while blog recommends layered gradients for atmosphere.
  Resolution: explicitly request gradients in prompts when desired.
```

---

## Gaps & Recommendations

### Recently Installed (This Session)

| Skill | Status | Security |
|-------|--------|----------|
| **web-artifacts-builder** | INSTALLED (official anthropics/skills) | Safe / 0 alerts / Low Risk |
| **ui-ux-pro-max** | INSTALLED (plugin v2.0.1) | N/A (plugin) |
| **copilotkit** | INSTALLED | Safe / 0 alerts / Med Risk |
| **a2a-protocol** | INSTALLED | Critical Risk* |
| **sse-streaming** | INSTALLED | Critical Risk* / 0 alerts / Med Risk |
| **design-system-creation** | INSTALLED | Safe / 0 alerts / Low Risk |

*\* Critical risk flags from Gen scanner — review skill.md content before using in production.*

### Still Available (Lower Priority)

| Skill | Why | Install Command |
|-------|-----|-----------------|
| **a2a-patterns** | Additional A2A design patterns | `npx skills add vanman2024/ai-dev-marketplace@a2a-patterns` |
| **implementing-realtime-sync** | Real-time sync patterns | `npx skills add ancoleman/ai-design-components@implementing-realtime-sync` |
| **google-material-design** | Material Design reference | `npx skills add copyleftdev/sk1llz@google-material-design` |
| **frontend-ui-ux-engineer** | Alternative design skill (920 installs) | `npx skills add 404kidwiz/claude-supercode-skills@frontend-ui-ux-engineer` |
| **llm-streaming** | LLM-specific streaming patterns | `npx skills add yonatangross/orchestkit@llm-streaming` |

### Identified Tensions

1. **Gradient Tension**: `baseline-ui` bans gradients; blog recommends layered gradients. Resolution: explicitly request in prompts when wanted.
2. **Animation Conservatism**: `baseline-ui` says "NEVER add animation unless explicitly requested" vs `taste-skill`'s "perpetual micro-interactions." Resolution: `taste-skill` overrides when its motion dial is > 4.
3. **A2A + CopilotKit overlap**: Both handle agent-UI communication. `copilotkit` is React-focused; `a2a-protocol` is protocol-level. Use together for full-stack agent UIs.

---

## Skill Load Commands (Quick Reference)

```bash
# DESIGN SKILLS (invoke via slash commands):
/frontend-design        # Aesthetic direction
/uncodixfy              # Anti-AI-slop filter (130+ bans)
/baseline-ui            # Constraint validation (38+ rules)
/taste-skill            # Design engineering (control dials)
/ui-ux-pro-max          # Design intelligence (50 styles, 97 palettes)
/web-artifacts-builder  # Single-file React prototyping
/design-system-creation # Design system builder
/web-design-guidelines  # Vercel compliance check

# QUALITY GATE SKILLS:
/fixing-accessibility       # WCAG 2.1 AA fixes
/fixing-metadata            # SEO/OG/social fixes
/fixing-motion-performance  # Animation performance

# FRAMEWORK SKILLS:
/react-best-practices   # React 57 perf rules (Vercel)
/next-best-practices    # Next.js 15+ App Router guide

# TESTING SKILLS:
/webapp-testing         # Basic Playwright testing
/playwright-skill       # Advanced browser automation
/e2e-test               # Self-healing E2E with a11y
/dogfood                # Exploratory QA bug hunting
/electron               # Desktop Electron app automation

# PROTOCOL / STREAMING SKILLS:
/copilotkit             # AI copilot framework (React/LangGraph)
/a2a-protocol           # Agent-to-Agent communication (v0.3.0)
/sse-streaming          # Server-Sent Events patterns

# SESSION MANAGEMENT SKILLS (loaded for this session):
/planning-with-files    # Persistent task planning
/multi-agent-patterns   # Multi-agent architecture patterns
/subagent-driven-development  # Subagent workflow with review
```
