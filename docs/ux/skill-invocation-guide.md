# Claude Code Skill Invocation Guide — Frontend, UI/UX & Design

> **Updated:** 2026-03-11 | **Total Skills:** 21 installed | **Project:** ACM-AI

---

## How Skills Work in Claude Code

Skills are markdown instruction files that Claude Code loads **on demand** to provide specialized domain knowledge. They work in three ways:

```
┌─────────────────────────────────────────────────────────────────┐
│                 SKILL INVOCATION METHODS                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. EXPLICIT INVOCATION (slash command)                          │
│     User types: /skill-name [args]                               │
│     Claude loads the skill.md and follows its instructions        │
│                                                                  │
│  2. AUTO-TRIGGER (keyword/file pattern)                          │
│     User mentions trigger keyword or edits matching files         │
│     Claude automatically activates the skill                     │
│                                                                  │
│  3. IMPLICIT REFERENCE (context-loaded)                          │
│     Skill is loaded as background constraint                     │
│     Claude applies rules without explicit invocation              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Syntax

```bash
# No arguments — load skill as context
/skill-name

# With arguments — skill receives them
/skill-name <argument>

# With inline context — Claude infers from prompt
"Build a landing page"  # triggers frontend-design automatically
```

### Where Skills Live

```
.claude/skills/              # Project-level skills (checked into repo)
~/.claude/skills/            # User-level skills (global, all projects)
~/.agents/skills/            # User-level agent skills (cross-IDE)
~/.claude/plugins/           # Plugin skills (marketplace installs)
```

---

## Skill Quick Reference

| # | Slash Command | Arguments | Trigger | Category |
|---|--------------|-----------|---------|----------|
| 1 | `/uncodixfy` | — | Auto on frontend code | Anti-Slop |
| 2 | `/baseline-ui` | `<file>` | Auto on UI work | Constraints |
| 3 | `/taste-skill` | — | Auto on design work | Engineering |
| 4 | `/frontend-design` | — | Explicit | Aesthetics |
| 5 | `/ui-ux-pro-max` | — | Explicit | Intelligence |
| 6 | `/web-artifacts-builder` | — | Explicit | Prototyping |
| 7 | `/design-system-creation` | — | Auto on design systems | Design Systems |
| 8 | `/web-design-guidelines` | `<file-or-pattern>` | Explicit | Compliance |
| 9 | `/react-best-practices` | — | Auto on React code | Framework |
| 10 | `/next-best-practices` | — | Reference only | Framework |
| 11 | `/fixing-accessibility` | `<file>` | Auto on forms/controls | Quality |
| 12 | `/fixing-metadata` | — | Auto on SEO work | Quality |
| 13 | `/fixing-motion-performance` | `<file>` | Auto on animations | Quality |
| 14 | `/copilotkit` | — | Auto on CopilotKit code | AI/Agent UI |
| 15 | `/a2a-protocol` | `server` or `client` | Explicit | Protocol |
| 16 | `/sse-streaming` | — | Auto on realtime work | Streaming |
| 17 | `/webapp-testing` | — | Explicit | Testing |
| 18 | `/playwright-skill` | — | Explicit | Testing |
| 19 | `/e2e-test` | — | Explicit | Testing |
| 20 | `/dogfood` | `<url>` | Explicit | QA |
| 21 | `/electron` | — | Explicit | Desktop |

---

## Detailed Invocation Guide

### DESIGN SKILLS

---

#### 1. `/uncodixfy` — Anti-AI-Slop Foundation

**Invocation:** Automatic (triggers on any frontend code generation)

```
# Explicit load (optional — usually auto-applied)
/uncodixfy

# Example prompts that trigger it:
"Build a sidebar component"
"Create a dashboard layout"
"Style this card component"
```

**What it does:** Prevents 130+ generic AI UI patterns. Enforces Linear/Raycast/Stripe aesthetics. Bans Inter font, purple gradients, oversized corners, glassmorphism shells, KPI card grids.

**Expected output:** Clean, human-designed UI code without AI tells.

**Common mistakes:**
- Trying to override its bans — they're intentional constraints
- Using it for non-UI work (it's frontend-specific)

**Combo:** Always pair with `/baseline-ui` for constraint validation.

---

#### 2. `/baseline-ui` — Constraint Validator

**Invocation:** `/baseline-ui [file]`

```bash
# Apply as background constraint (no specific file)
/baseline-ui

# Audit a specific file
/baseline-ui frontend/src/components/acm/ItemGrid.tsx

# Example prompts:
"Check this component against baseline rules"
"Validate the animation in Hero.tsx"
```

**Arguments:**
| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| `<file>` | path | No | Specific file to audit (argument-hint) |

**What it does:** Validates 38+ MUST/NEVER rules across animation (never animate layout), typography (use text-balance), components (use accessible primitives), interactions (AlertDialog for destructive), layout (no h-screen), performance (no will-change outside active animation), design (no gradients unless requested).

**Expected output:** List of violations with rule references and fixes.

**Common mistakes:**
- Ignoring "NEVER add animation unless explicitly requested" — this is strict
- Using `h-screen` instead of `h-dvh`
- Adding gradients without explicit user request

---

#### 3. `/taste-skill` — Design Engineer

**Invocation:** Automatic (triggers on design/frontend work)

```
# Explicit load
/taste-skill

# Control dials via prompt:
"Build a dashboard with MOTION_INTENSITY=9"
"Create a minimal card layout (VISUAL_DENSITY=2)"
"Design with high variance (DESIGN_VARIANCE=10)"
```

**Control Dials (adjustable via prompt):**
| Dial | Default | Range | Effect |
|------|---------|-------|--------|
| DESIGN_VARIANCE | 8 | 1-10 | 1=predictable, 10=asymmetric |
| MOTION_INTENSITY | 6 | 1-10 | 1=static, 10=choreographed |
| VISUAL_DENSITY | 4 | 1-10 | 1=art gallery, 10=cockpit |

**What it does:** Applies Spring physics (mass 0.8, stiffness 140, damping 28), Bento grid archetypes, liquid glass refraction, magnetic micro-physics, staggered orchestration. Includes "LILA BAN" on purple/blue accents.

**Expected output:** Polished React components with motion/react animations, Tailwind CSS, and metric-driven design decisions.

**Common mistakes:**
- Setting MOTION_INTENSITY too high conflicts with baseline-ui's "no animation unless requested"
- Forgetting to pair with uncodixfy for anti-slop protection

---

#### 4. `/frontend-design` — Aesthetic Director

**Invocation:** `/frontend-design`

```
# Load and specify direction
/frontend-design

# Example prompts:
"Build an art deco landing page"
"Create a brutalist portfolio site"
"Design a luxury product showcase with editorial typography"
"Make a retro-futuristic dashboard"
```

**Available Aesthetic Directions:**
- Minimalist, Maximalist, Retro-futuristic, Organic
- Luxury, Playful, Editorial, Brutalist, Art Deco
- (More available based on context)

**What it does:** Selects bold aesthetic direction, applies typography pairing (extreme weight 100/200 vs 800/900), color themes via CSS variables, motion choreography, spatial composition with asymmetry/overlap/grid-breaking, visual details (noise, geometric patterns, grain overlays).

**Expected output:** Production-grade, visually distinctive UI with intentional aesthetic choices.

**Common mistakes:**
- Being too vague ("make it look nice") — be specific about the aesthetic direction
- Not specifying the audience/context

---

#### 5. `/ui-ux-pro-max` — Design Intelligence Database

**Invocation:** `/ui-ux-pro-max` (plugin)

```
# Load the design intelligence
/ui-ux-pro-max

# The skill provides searchable databases:
# - 50+ styles
# - 97 color palettes
# - 57 font pairings
# - 99 UX guidelines
# - 25 chart types
# - 9 technology stacks

# Example prompts:
"What color palette works for a healthcare dashboard?"
"Suggest font pairings for a fintech app"
"Which chart type for time-series data?"
"Review this for UX best practices"
```

**What it does:** Provides searchable CSV databases covering styles, colors, typography, UX guidelines, charts, icons, landing pages, products, web-interface patterns, and react-performance. Uses Python CLI scripts for searching.

**Expected output:** Prioritized recommendations from its databases with rationale.

**Common mistakes:**
- Using it without specifying the product type — it matches style to product
- Not specifying the tech stack (it covers 13 stacks)

---

#### 6. `/web-artifacts-builder` — Single-File Prototyping

**Invocation:** Script-based workflow

```bash
# Step 1: Initialize a new artifact project
bash scripts/init-artifact.sh my-dashboard

# Step 2: Develop (edit files in the project)
cd my-dashboard
# Edit src/App.tsx, add components, etc.

# Step 3: Bundle into single HTML file
bash scripts/bundle-artifact.sh

# Step 4: Display to user
```

**Stack:** React 18 + TypeScript + Vite + Parcel + Tailwind CSS 3.4.1 + 40+ shadcn/ui components pre-installed

**What it does:** Creates multi-component React applications that bundle into a single HTML file via Parcel. Includes all Radix UI dependencies, path aliases (`@/`), and theming system.

**Expected output:** Single `index.html` file containing entire React application.

**Common mistakes:**
- Using for simple artifacts — this is for **complex** multi-component artifacts
- Forgetting to run bundle step before sharing

---

#### 7. `/design-system-creation` — Design System Builder

**Invocation:** Automatic (triggers on design system work)

```
# Explicit load
/design-system-creation

# Example prompts:
"Create a design system for our ACM-AI product"
"Document our color tokens and typography scale"
"Build a component library with consistent patterns"
"Set up design tokens for theming"
```

**What it does:** Provides structure for Foundation Layer (tokens, colors, typography, spacing), Component Layer (buttons, inputs, cards, layouts), Pattern Layer (navigation, forms, data display), and Guidelines Layer (voice, accessibility, responsive).

**Expected output:** Design system documentation with tokens, components, patterns.

**Common mistakes:**
- Starting too complex — begin with Foundation Layer
- Not connecting tokens to actual Tailwind/CSS implementation

---

#### 8. `/web-design-guidelines` — Vercel Compliance Check

**Invocation:** `/web-design-guidelines <file-or-pattern>`

```bash
# Audit specific files
/web-design-guidelines frontend/src/components/acm/BuildingSidebar.tsx

# Audit glob pattern
/web-design-guidelines frontend/src/components/**/*.tsx

# Audit without specifying (prompts for files)
/web-design-guidelines
```

**Arguments:**
| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| `<file-or-pattern>` | path/glob | No | Files to check (argument-hint) |

**What it does:** Fetches latest guidelines from `vercel-labs/web-interface-guidelines`, reads your specified files, and checks against all rules. Output is terse `file:line` format.

**Expected output:** Violation list in `file:line` format with rule references.

**Common mistakes:**
- Using too broad a glob (e.g., `**/*`) — be specific to avoid noise
- Running before fixing-accessibility (it overlaps with a11y rules)

---

### FRAMEWORK SKILLS

---

#### 9. `/react-best-practices` — 57 Performance Rules

**Invocation:** Automatic (triggers on React code work)

```
# Explicit load
/react-best-practices

# Example prompts:
"Optimize this component for performance"
"Review the data fetching pattern in this page"
"Check for re-render issues in ItemGrid.tsx"
"Eliminate waterfalls in the dashboard"
```

**What it does:** Applies 57 Vercel Engineering rules across 8 priority categories: waterfall elimination (Promise.all), bundle size (dynamic imports, barrel imports), server-side (React.cache), client data (SWR dedup), re-render (useMemo, useTransition), rendering performance (content-visibility), JS performance (batch DOM, index maps), advanced patterns.

**Expected output:** Rule violations identified with specific fixes.

---

#### 10. `/next-best-practices` — Next.js 15+ Guide

**Invocation:** Reference documentation (not user-invocable — loads as context)

```
# NOT invokable via slash command
# Referenced implicitly when working on Next.js code

# Example prompts that reference it:
"Review this page for RSC boundary issues"
"Is this the right data pattern for this route?"
"Check async/await usage in this Server Component"
```

**What it does:** 18-section reference covering file conventions, RSC boundaries, async APIs (Next.js 15+), directives (`'use client'`, `'use server'`, `'use cache'`), route handlers, metadata/OG, image/font optimization, bundling, hydration errors, Suspense, parallel/intercepting routes, self-hosting.

**Note:** This skill has `user-invocable: false` — it's loaded as reference context, not invoked directly.

---

### QUALITY GATE SKILLS

---

#### 11. `/fixing-accessibility` — WCAG 2.1 AA

**Invocation:** `/fixing-accessibility [file]`

```bash
# Audit specific file
/fixing-accessibility frontend/src/components/acm/ItemGrid.tsx

# Apply as constraint
/fixing-accessibility

# Example prompts:
"Add ARIA labels to the icon-only buttons"
"Fix keyboard navigation in the modal"
"Check form error linking for the upload form"
```

**Arguments:**
| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| `<file>` | path | No | Specific file to audit |

**What it does:** 9 rule categories (accessible names, keyboard access, focus/dialogs, semantics, forms/errors, announcements, contrast/states, media/motion, tool boundaries). Provides specific fixes like adding `aria-label`, using native `<button>`, linking errors with `aria-describedby`.

**Expected output:** Prioritized a11y violations with ready-to-apply fixes.

---

#### 12. `/fixing-metadata` — SEO & Social

**Invocation:** Automatic (triggers on metadata/SEO work)

```
# Example prompts:
"Add Open Graph tags to the source detail page"
"Fix the social preview for the ACM dashboard"
"Check canonical URLs across all pages"
"Add JSON-LD structured data to the homepage"
```

**What it does:** 8 rule categories covering correctness/duplication, title/description, canonical/indexing, social cards (OG + Twitter), icons/manifest, structured data (JSON-LD), locale/alternates, tool boundaries.

**Expected output:** Metadata audit with missing/incorrect tags identified.

---

#### 13. `/fixing-motion-performance` — Animation 60fps

**Invocation:** `/fixing-motion-performance [file]`

```bash
# Audit specific animation file
/fixing-motion-performance frontend/src/components/common/LoadingSpinner.tsx

# Apply as constraint
/fixing-motion-performance

# Example prompts:
"Why is this animation janking?"
"Optimize the scroll-linked motion in the sidebar"
"Review the FLIP transition in the card"
```

**Arguments:**
| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| `<file>` | path | No | Specific file to audit |

**What it does:** Enforces compositor-only animation (transform, opacity), prevents layout thrashing, validates scroll-linked motion (use Scroll/View Timelines), limits blur effects, validates FLIP pattern usage, reviews layer promotion. 9 rule categories.

**Expected output:** Performance violations with render-step classification (composite/paint/layout).

---

### AI / AGENT UI SKILLS

---

#### 14. `/copilotkit` — AI Copilot Framework

**Invocation:** Automatic (triggers on CopilotKit imports/keywords)

```
# Explicit load
/copilotkit

# Auto-triggers on:
# - import from '@copilotkit/react-core'
# - useCopilotAction, useCopilotReadable, useCoAgent
# - CopilotPopup, CopilotSidebar, CopilotChat

# Example prompts:
"Add a copilot sidebar to the ACM dashboard"
"Create a CopilotTextarea for the notes editor"
"Connect my LangGraph agent to the React frontend using CoAgents"
"Implement human-in-the-loop for the extraction pipeline"
"Set up AG-UI protocol for agent-to-UI communication"
```

**Key Components:**
```
Frontend:      CopilotPopup | CopilotSidebar | CopilotChat | CopilotTextarea
Hooks:         useCopilotAction | useCopilotReadable | useCoAgent | useAgent
Backend:       CopilotRuntime | BuiltInAgent | BasicAgent | LangGraphAgent
Protocols:     AG-UI (Agent-to-UI) | MCP Apps
```

**Expected output:** Working CopilotKit integration with React hooks, components, and backend runtime.

---

#### 15. `/a2a-protocol` — Agent-to-Agent Communication

**Invocation:** `/a2a-protocol [server|client]`

```bash
# Build an A2A server
/a2a-protocol server

# Build an A2A client
/a2a-protocol client

# Example prompts:
"Create an A2A server that exposes our extraction agent"
"Build a client that discovers and calls remote agents"
"Set up AgentCard discovery at /.well-known/agent-card.json"
```

**Arguments:**
| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| `server` or `client` | keyword | No | Agent type to build (argument-hint) |

**What it does:** Implements A2A Protocol v0.3.0 — core structures (AgentCard, Task, Message, Part, Artifact), abstract operations (SendMessage, GetTask, CancelTask), protocol bindings (JSON-RPC 2.0, gRPC, HTTP/REST).

**Expected output:** Working A2A server or client with AgentCard, message handling, and task management.

---

#### 16. `/sse-streaming` — Server-Sent Events

**Invocation:** Automatic (triggers on real-time/streaming work)

```
# Explicit load
/sse-streaming

# Example prompts:
"Add SSE streaming to the extraction progress endpoint"
"Implement live notifications for the ACM dashboard"
"Build a progress indicator using SSE"
"Add auto-reconnection to the event stream"
```

**ACM-AI Relevance:** Directly applicable to:
- `PipelineEventBus` in `open_notebook/extractors/pipeline_event_bus.py`
- SSE endpoints in `api/routers/v3_streaming.py`
- Frontend hook `useV3SSE.ts`
- Zustand `streamingStore.ts`

**What it does:** Provides TypeScript and Python implementations for SSE server + client with auto-reconnection, heartbeats, event-ID tracking, and proper error handling.

**Expected output:** Working SSE server endpoint + client with reconnection logic.

---

### TESTING SKILLS

---

#### 17. `/webapp-testing` — Basic Playwright Testing

**Invocation:** `/webapp-testing`

```
# Example prompts:
"Test the login flow on localhost:8503"
"Verify the upload wizard works end-to-end"
"Capture a screenshot of the building sidebar"
```

**Workflow:** Navigate → Wait (networkidle) → Screenshot → Inspect DOM → Interact

**Key Script:** `scripts/with_server.py` manages server lifecycle during tests.

**Expected output:** Test results with screenshots and console output.

---

#### 18. `/playwright-skill` — Advanced Browser Automation

**Invocation:** `/playwright-skill`

```
# Example prompts:
"Test the checkout flow with form validation"
"Verify responsive design at 3 viewports"
"Mock the API and test error states"
"Run visual regression on the dashboard"
```

**Auto-detects:** Running dev servers on localhost. Writes scripts to `/tmp/playwright-test-*.js`.

**Helper Functions Available:**
```javascript
detectDevServers()              // Find running servers
safeClick(page, selector)       // Click with retry
safeType(page, selector, text)  // Safe typing
takeScreenshot(page, name)      // Timestamped capture
handleCookieBanner(page)        // Common pattern
extractTableData(page, sel)     // Table parsing
```

**Expected output:** Playwright script + execution results with screenshots.

---

#### 19. `/e2e-test` — Self-Healing E2E

**Invocation:** Command-line based

```bash
# Run by tier
npx playwright test --project=smoke        # <30s, every PR
npx playwright test --project=critical     # <5min, merge to main
npx playwright test --project=feature      # <15min, nightly
npx playwright test --grep @a11y           # Accessibility only

# Run with agent-browser for interactive debugging
agent-browser open http://localhost:8503
agent-browser snapshot -i
```

**Self-Healing Flow:**
```
Research → Select tier → Execute with healing → Collect evidence → Auto-fix (3x) → Report
```

**Selector fallback chain:** data-testid (1.0) → role+name (0.95) → aria-label (0.9) → text (0.8) → CSS (0.6) → XPath (0.4)

**Expected output:** Test results + evidence screenshots + healing report JSON.

---

#### 20. `/dogfood` — Exploratory QA

**Invocation:** `/dogfood <url>`

```bash
# Dogfood a public site
/dogfood vercel.com

# Dogfood local app
/dogfood http://localhost:8503

# With session name
/dogfood http://localhost:8503 --session acm-regression

# Scoped dogfood
"Dogfood the building detail page at localhost:8503/source/123"
```

**Arguments:**
| Arg | Type | Required | Description |
|-----|------|----------|-------------|
| URL | string | Yes | Target to test |
| `--session` | string | No | Custom session name |

**Phases:** Initialize → Authenticate → Orient (map structure) → Explore (systematically) → Document (5-10 issues) → Wrap up

**Evidence rules:**
- Interactive issues: video + step-by-step screenshots
- Static issues: single annotated screenshot
- Depth of evidence > quantity

**Expected output:** QA report with 5-10 well-documented issues + reproduction evidence.

---

#### 21. `/electron` — Desktop App Automation

**Invocation:** Via agent-browser + CDP

```bash
# 1. Launch Electron app with remote debugging
# macOS:
open -a "Slack" --args --remote-debugging-port=9222
# Windows:
"C:\Users\%USERNAME%\AppData\Local\slack\slack.exe" --remote-debugging-port=9222

# 2. Connect
agent-browser connect 9222

# 3. Interact
agent-browser snapshot -i        # See elements with @refs
agent-browser click @e5          # Click element
agent-browser fill @e3 "hello"   # Fill input

# Tab management
agent-browser tab                # List targets
agent-browser tab 2              # Switch tab
agent-browser tab --url "*settings*"  # By URL
```

**Supported apps:** Slack, Discord, VS Code, Figma, Notion, Spotify, Teams, Postman, Obsidian, GitHub Desktop, and any Electron-based app.

**Expected output:** Automated interactions with desktop apps + screenshots.

---

## Skill Combos — Recommended Pipelines

### Full Design Build
```
/uncodixfy → /taste-skill → /frontend-design → /baseline-ui → /ui-ux-pro-max
```
Load all 5 for maximum design quality. Order matters — each constrains the next.

### Quick Component
```
/uncodixfy → /baseline-ui → /fixing-accessibility
```
Minimum viable design quality for a single component.

### Full Page / Landing Page
```
/uncodixfy → /frontend-design → /taste-skill → /fixing-metadata → /fixing-accessibility
```
Complete page with aesthetics + SEO + a11y.

### Design System Setup
```
/design-system-creation → /ui-ux-pro-max → /uncodixfy → /baseline-ui
```
Build a consistent design system from scratch.

### AI-Powered UI
```
/copilotkit → /sse-streaming → /a2a-protocol → /react-best-practices
```
Full agentic UI with streaming and agent communication.

### Pre-Release QA
```
/e2e-test → /dogfood → /fixing-accessibility → /web-design-guidelines
```
Comprehensive testing before shipping.

### Performance Audit
```
/react-best-practices → /fixing-motion-performance → /web-design-guidelines
```
Optimize React rendering + animation + compliance.

### Prototype → Production
```
/web-artifacts-builder → /uncodixfy → /frontend-design → /baseline-ui → /e2e-test
```
Build prototype, then harden for production.

---

## Marketplace — Skills Available for Future Install

Found via `/find-skills` searches (2026-03-11):

| Skill | Source | Installs | Relevance to ACM-AI | Install |
|-------|--------|----------|---------------------|---------|
| **ag-grid** | joabgonzalez | 30 | Direct — ACM-AI uses AG Grid | `npx skills add joabgonzalez/ai-agents-framework@ag-grid -g -y` |
| **motion** | jezweb | 781 | Framer Motion / motion-react | `npx skills add jezweb/claude-skills@motion -g -y` |
| **shadcn-ui** | bobmatnyc | 216 | Direct — ACM-AI uses shadcn/ui | `npx skills add bobmatnyc/claude-mpm-skills@shadcn-ui -g -y` |
| **zustand** | bobmatnyc | 104 | Direct — ACM-AI uses Zustand | `npx skills add bobmatnyc/claude-mpm-skills@zustand -g -y` |
| **zustand-patterns** | yonatangross | 89 | More Zustand patterns | `npx skills add yonatangross/orchestkit@zustand-patterns -g -y` |
| **figma** | hoodini | 212 | Figma design handoff | `npx skills add hoodini/ai-agents-skills@figma -g -y` |
| **ui-design-system** | alirezarezvani | 228 | Design system creation | `npx skills add alirezarezvani/claude-skills@ui-design-system -g -y` |
| **framer-motion** | dylantarre | 89 | Animation principles | `npx skills add dylantarre/animation-principles@framer-motion -g -y` |
| **storybook-play-functions** | thebushidocollective | 67 | Component testing | `npx skills add thebushidocollective/han@storybook-play-functions -g -y` |
| **building-tables** | ancoleman | 16 | Table component patterns | `npx skills add ancoleman/ai-design-components@building-tables -g -y` |
| **llm-streaming** | yonatangross | 12 | LLM response streaming | `npx skills add yonatangross/orchestkit@llm-streaming -g -y` |

### High-Priority Recommendations for ACM-AI

1. **`ag-grid`** — ACM-AI's ItemGrid uses AG Grid extensively. Direct match.
2. **`shadcn-ui`** — ACM-AI uses shadcn/ui components. 216 installs, well-maintained.
3. **`zustand`** — ACM-AI uses Zustand stores. Patterns skill adds advanced patterns.
4. **`motion`** — 781 installs, covers motion/react (Framer Motion successor) which ACM-AI already uses.

---

## Troubleshooting

### Skill not loading?
```bash
# Check if skill exists
ls .claude/skills/<skill-name>/skill.md

# Check if symlink is broken (Windows)
ls -la .claude/skills/<skill-name>

# Re-install
npx skills add <source>@<skill-name> -g -y
```

### Skill conflict?
Skills are applied in enforcement hierarchy order (see `frontend-skills-inventory.md`). If two skills disagree:
- Lower-layer skills (uncodixfy, baseline-ui) take precedence
- Explicitly mention which rule to follow in your prompt

### Skill not auto-triggering?
Some skills require explicit invocation. Check the "Trigger" column in the Quick Reference table. If it says "Explicit", you must type `/skill-name`.

### Plugin skill vs regular skill?
- `/ui-ux-pro-max` is a **plugin** (installed via marketplace, lives in `~/.claude/plugins/`)
- All others are **skills** (installed via `npx skills add`, lives in `.claude/skills/` or `~/.agents/skills/`)
- Both are invoked the same way via slash commands
