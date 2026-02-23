# Plan: ACM-AI Marketing Site — Full Data Sync + Page Builds

## Context

The marketing site lives at `marketing-site/` (NOT `/home/claude/acm-ai-site/` — that
path doesn't exist; all changes go to `marketing-site/src/`). The site was built when
the project was ~92% complete. Since then all 19 active epics finished. Data throughout
the site is stale or fabricated.

**Real data (from sprint-status.yaml + git log + E18-S5 story file — verified 2026-02-23):**

| Metric | Site Shows | Reality |
|--------|-----------|---------|
| Stories delivered | 112 | **121** (non-archived active stories) |
| Total stories | 122 | **131** (incl. 10 archived E8 stories) |
| Epics complete | 16 | **19** |
| Total epics | 17 | **20** (incl. 1 archived E8) |
| Commits | 281 | **318** (on `release` branch) |
| Completion rate | 92% | **100%** (all 121 active stories done) |
| Extraction accuracy | 96% (StatsCounter) | **87%** (27/31 records) |
| Hero extraction | 87% ← correct! | 87% — leave this alone |

**4 known missing extraction records (real, from E18-S5):**
1. Fuse cartridge — Auto Battery Charger, Switch Room (L1)
2. Flange joints — East Ductwork, Roof (G)
3. No-access: Internal lining — Lift, Lift Foyer (G)
4. No-access: Unknown — Room adj. Disabled Toilet, Main Foyer (G)

**VAEA Authority Theme (apply consistently everywhere):**
- Primary: `#3a8f8a` (teal)
- Accent: `#d4614a` (coral)
- Dark bg: `#2a2f45` (navy)
- Success: `#4caf82` (green)
- Warning: `#f59e0b` (amber)
- Error: `#ef4444` (red)
- Fonts: DM Serif Display (display) + DM Sans (body) + JetBrains Mono (code)

---

## Task 1: Data Truth Foundation

### Create `marketing-site/src/lib/project-truth.ts`

Single canonical TypeScript object. All components import from here, no more scattered
hardcoding. Key shape:

```typescript
export const PROJECT_TRUTH = {
  stories: {
    done: 121,        // non-archived active stories
    archived: 10,     // E8 stories (skipped by architectural decision)
    total: 131,       // all tracked
    activeTotal: 121,
    completionRate: 100, // 121/121 active
  },
  epics: {
    total: 20,
    done: 19,
    archived: 1,      // E8 — Bento Grid redesign, skipped
    completionRate: 95, // 19/20
    breakdown: [/* E1-E20 with storiesTotal, storiesDone, keyFeature */],
  },
  git: {
    totalCommits: 318,
    workflows: 12,
  },
  extraction: {
    currentAccuracy: 87,
    testRecordsPassing: 27,
    testRecordsTotal: 31,
    targetAccuracy: 100,
    knownIssues: [4 strings],
    status: 'in-progress',
    activeIssueCount: 4,
  },
}
export const VELOCITY_DATA = [/* 12-week stubs */]
```

### Update `marketing-site/src/lib/sprint-data.ts`

Fix `projectStats` (8 value changes — this cascades to StatsCounter, ProgressSection):

```typescript
// Before → After
storiesDelivered: 112  → 121
totalStories: 122      → 131
epicsComplete: 16      → 19
totalEpics: 17         → 20
commits: 281           → 318
completionRate: 92     → 100
extractionAccuracy: 96 → 87
featureComplete: "22 Feb 2026" → "23 Feb 2026"
```

### Update `marketing-site/src/lib/epic-data.ts`

Verify and add E17, E18, E19, E20 to the completed epics list if missing (the explore
agent found it only showed 16 epics). All 19 active epics must be listed.

---

## Task 2: Component Fixes (existing files)

### `marketing-site/src/components/landing/Hero.tsx`
Fix stories count only (accuracy 87% is already correct):
```typescript
{ label: 'Stories Shipped', value: '131' }  // was 122
```

### `marketing-site/src/components/landing/StatsCounter.tsx`
Will cascade automatically from `sprint-data.ts` fix if it imports `projectStats`.
Verify it does; if hardcoded, update 6 values to match PROJECT_TRUTH.

### `marketing-site/src/app/roadmap/page.tsx` — inline stats strip
Three hardcoded values (not from sprint-data.ts):
- "17 Epics complete" → 19
- "112 Stories delivered" → 121
- "281 Commits" → 318

---

## Task 3: Status Page Rebuild

**File:** `marketing-site/src/app/status/page.tsx`
**Design direction:** "Mission Control" — dark operational dashboard.
Read current implementation first, then replace/extend.

### 3A. Hero Status Bar
Full-width strip, auto-updates every 30s via SWR:
```tsx
// Derives overall status from GitHub + Vercel + Railway API responses
"🟢 All Systems Operational" | "🟡 Degraded" | "🔴 Incident"
"Last checked: {timeAgo}"
```

### 3B. Infrastructure Cards (3-column grid)
Reuse and extend existing `StatusCard` pattern. Real card specs:

**GitHub card** — from `/api/github/stats`:
- Total Commits: 318 (live from Octokit)
- Open PRs, CI Status, Last Push (live)
- Detail: last commit message + author

**Vercel card** — from `/api/vercel/status`:
- Environment: Production, State, Last Deploy, Build Time

**Railway card** — from `/api/railway/status`:
- API Service, SurrealDB, Worker — each with operational/degraded badge

**StatusCard visual spec:**
- bg: `#1a2035`, border: `1px solid rgba(58,143,138,0.2)`
- Status dot: 8px circle, top-right — green pulse (operational), amber (degraded), red (incident)
- Metric rows: label gray-400, value gray-100 bold

### 3C. Project Health Section
Fix hardcoded rings using real PROJECT_TRUTH values:
- Story completion: 92% → **100%**
- Epic completion: 94% → **95%** (19/20)
- Test coverage: replace hardcoded 87% with note "642/813 tests (171 pre-existing import failures)"

Fix test suite section — replace fabricated (142/156 unit, 38/42 integration, 24/28 E2E)
with real numbers: 642 passing / 813 total, or replace section with a link to live CI
(cleaner — uses existing `/api/github/stats` route).

Add ExtractionAccuracyWidget here (see Task 5) replacing green "Operational" with amber.

### 3D. Incident History
Fetch from GitHub Issues API via `/api/github/stats` if issues data is available.
If live data unavailable, show the 3 resolved incidents as static fallback:
- Feb 22: Migration runner registration fix (resolved)
- Feb 21: Negative results regression (resolved)
- Feb 16: E2E accuracy 70% → 87% via PR #30 (resolved)
Prefer live over static — only use static if API returns nothing.

---

## Task 4: Roadmap Page Rebuild

**File:** `marketing-site/src/app/roadmap/page.tsx`
**Design direction:** "Structured Time" — horizontal Gantt elevated to art.
Read current implementation first.

### 4A. Horizontal Scrollable Timeline
Full-width, scrollable/draggable. Teal spine (#3a8f8a, 2px) with dots at each epic.
Date labels above spine, milestone cards below.

**Milestone data corrected to real current state** (all epics complete as of Feb 23):
```typescript
const milestones = [
  { id:'e1', epic:'E1', title:'ACM Extraction Pipeline', stories:31,
    status:'done', date:'Jan 2026', highlight:'MinerU + 7-stage LangGraph' },
  { id:'e2', epic:'E2', title:'AG Grid Spreadsheet', stories:12,
    status:'done', date:'Jan 2026', highlight:'47-column BAR schema' },
  { id:'e3', epic:'E3', title:'Citations & PDF Viewer', stories:4,
    status:'done', date:'Jan 2026', highlight:'Click any cell → source PDF page' },
  { id:'e4', epic:'E4', title:'AI Chat Integration', stories:4,
    status:'done', date:'Feb 2026', highlight:'CopilotKit + AG-UI SSE streaming' },
  { id:'e5', epic:'E5', title:'BAR Export', stories:4,
    status:'done', date:'Feb 2026', highlight:'VAEA Excel + CSV export' },
  { id:'e14', epic:'E14', title:'Enterprise UX', stories:11,
    status:'done', date:'Feb 2026', highlight:'WCAG 2.1 AA, VAEA branding' },
  { id:'e17', epic:'E17', title:'Live AI Intelligence', stories:6,
    status:'done', date:'Feb 2026', highlight:'AG-UI streaming, A2A protocol' },
  { id:'e18', epic:'E18', title:'Extraction Quality', stories:6,
    status:'done', date:'Feb 2026', highlight:'87% accuracy (27/31 records)' },
  { id:'e19', epic:'E19', title:'Marketing Site', stories:1,
    status:'done', date:'Feb 2026', highlight:'This site!' },
  { id:'e20', epic:'E20', title:'Cross-Site Navigation', stories:2,
    status:'done', date:'Feb 2026', highlight:'Domain cutover + nav integration' },
  // Future items (genuine upcoming):
  { id:'extraction-100', epic:'Future', title:'Extraction 100% Accuracy', stories:0,
    status:'upcoming', date:'Mar 2026', highlight:'Resolve 4 remaining records' },
  { id:'e-knowledge', epic:'Future', title:'Knowledge Graph', stories:3,
    status:'upcoming', date:'Q2 2026', highlight:'React Flow visualization' },
]
```

**Card visual by status:**
- `done`: teal fill, white text, checkmark, solid border
- `in-progress`: teal outline, teal text, animated pulse border, coral "Live" badge
- `upcoming`: 50% navy fill, gray text, outlined, "Planned" badge

### 4B. Framer Motion Entrance
- Timeline spine draws left→right (scaleX: 0→1, transformOrigin: left)
- Dots appear staggered (scale: 0→1, 100ms delay between)
- Cards drop in (y: -20→0, staggered 80ms)
- Trigger via IntersectionObserver (useInView hook already exists)

### 4C. "What's Next" Section
3 priority cards below timeline:
1. 🎯 TOP PRIORITY — Extraction 100%: resolve 4 missing records
2. ⚡ QUICK WIN — Knowledge Graph E13 visualizations
3. 🔬 RESEARCH — Production monitoring & alerting

Replace the old "E5-S3 BAR Template" priorities (those stories are done now).

---

## Task 5: New Components

### `marketing-site/src/components/ExtractionAccuracyWidget.tsx`
Amber progress bar widget:
- Animated progress bar to 87% (amber, not green — "Active Work" not "Operational")
- "27/31 test records passing" label
- Collapsible list of 4 known missing records
- "Active Work" badge
- Import from PROJECT_TRUTH

### `marketing-site/src/components/demo/enhanced-rings/RingMetric.tsx` (or inline)
SVG donut chart component for ProgressSection:
```tsx
function RingMetric({ value, max, label, color }) {
  // Animated strokeDashoffset ring via Framer Motion
  // Radius 40, center text shows value
}
```

### `marketing-site/scripts/sync-github-issues.sh`
Shell script listing untracked bugs and pre-formatted `gh issue create` commands
(commented out, user confirms before running). Documents 4 extraction issues.

---

## Task 6: Demo ProgressSection Enhancement

**File:** `marketing-site/src/components/demo/ProgressSection.tsx`
Read current implementation first.

### 6A. Animated Ring Charts (replace flat stat cards)
Four rings using the RingMetric component:
- **Stories**: 121/131 done — teal
- **Epics**: 19/20 done — coral
- **E2E Accuracy**: 87% — amber (honest, not green)
- **Git Commits**: 318 — navy (show as counter, no ring needed)

**Note:** The user's task spec shows `storiesDone: 87, storiesTotal: 122` — these are
wrong. Use PROJECT_TRUTH values: 121/131.

### 6B. GitHub Integration
useSWR from `/api/github/stats` for live commit count.

### 6C. Recharts Upgrades

**BarChart (epic stories):**
- LinearGradient fill (teal → coral, top to bottom)
- Custom rounded tooltip
- ReferenceLine at average velocity
- X-axis labels rotated -35deg, fontSize 11px

**LineChart → AreaChart (sprint velocity):**
- Gradient area fill (teal, 0.3→0 opacity)
- Animated pulse dot on last data point
- Second dashed line "Target" in coral

**Radar chart (NEW — feature coverage):**
```tsx
const radarData = [
  { subject: 'Extraction', completion: 100 },    // E1 done
  { subject: 'Grid/UX', completion: 100 },        // E2, E14 done
  { subject: 'Export', completion: 100 },          // E5 done
  { subject: 'Chat', completion: 100 },            // E4 done
  { subject: 'Infrastructure', completion: 95 },   // E18 done, 4 issues
  { subject: 'Testing', completion: 87 },          // 87% accuracy
]
```

### 6D. Epic Status Table
Add animated progress bar column per row (Framer Motion width animation, staggered).

---

## Task 7: Polish Pass (cross-cutting)

### 7A. Icon Consistency
- Audit all imports: remove any `@radix-ui/react-icons`, standardize on `lucide-react`
- Replace any emoji used as icons with Lucide SVG components
- Size standards: 16px inline, 20px buttons, 24px section headers, 32px hero
- `aria-hidden="true"` on all decorative icons

### 7B. Color Consistency
- Search for non-VAEA hex codes (any hex not in theme palette)
- Replace with CSS variables (`var(--teal)`, `var(--coral)`, etc.)

### 7C. Typography
- All h1: DM Serif Display
- All h2/h3: DM Sans weight-600
- Body: DM Sans weight-400
- Code: JetBrains Mono
- Verify `layout.tsx` loads all 3 fonts via `next/font/google`

### 7D. Responsive
Fix at 375px/768px/1280px/1920px:
- Pipeline pills: `overflow-x: auto` on container
- Charts: `ResponsiveContainer` with fixed height not 100%
- Demo sidebar: collapse to horizontal tab bar on <768px
- Hero headline: 40px max on mobile

### 7E. SEO & Metadata
Add `export const metadata: Metadata = {...}` to each `page.tsx` with:
- Title, description, keywords (en_AU locale)
- OpenGraph tags

### 7F. Loading States
Add `animate-pulse` skeleton `div`s to all SWR-fetching components.

### 7G. Accessibility
- `focus-visible:ring-2 focus-visible:ring-teal focus-visible:ring-offset-2` on all interactive elements
- Skip-to-content link in `layout.tsx`
- All `<img>` → alt text; all icon-only buttons → `aria-label`

### 7H. Performance
- Dynamic import Excalidraw (`ssr: false`)
- next/image for any static images with explicit width/height
- Error boundaries around Lottie + Excalidraw

### 7I. Favicon
Create `marketing-site/public/favicon.svg`:
```svg
<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
  <rect width="32" height="32" rx="6" fill="#3a8f8a"/>
  <text x="16" y="22" font-family="Georgia" font-size="18" font-weight="bold"
        fill="white" text-anchor="middle">A</text>
</svg>
```

---

## Execution Order

1. **project-truth.ts** (new) — foundation for everything
2. **sprint-data.ts** (update 8 values) — cascades to StatsCounter, ProgressSection
3. **epic-data.ts** (verify/add E17-E20)
4. **Hero.tsx** (1 value fix)
5. **ExtractionAccuracyWidget.tsx** (new)
6. **status/page.tsx** (major rebuild) — Mission Control
7. **roadmap/page.tsx** (major rebuild) — Structured Time
8. **demo/ProgressSection.tsx** (ring charts + recharts upgrades)
9. **sync-github-issues.sh** (new script)
10. **Polish pass** (Tasks 7A–7I across all files)

---

## Verification

```bash
cd marketing-site

# Type check
npx tsc --noEmit

# Lint
npm run lint

# Build (catches missing imports, type errors)
npm run build

# Spot-check (manual in browser):
# / → Hero: 131 stories, 87% accuracy; StatsCounter: 121 stories, 318 commits, 19 epics
# /status → Hero bar, 3 cards, 100%/95% rings, amber extraction badge
# /roadmap → All 10 milestones showing "done", horizontal timeline scrollable
# /demo → Ring charts, radar chart, updated epic table
```

---

## Key Decisions

- **Path**: All files in `marketing-site/src/` — NOT `/home/claude/acm-ai-site/`
- **Milestone data**: All epics show `done` (they ARE done per sprint-status.yaml);
  future items are genuine next priorities (extraction 100%, knowledge graph)
- **Test suite**: Replace fabricated test numbers with real (642/813) or link to CI
- **Extraction status**: Amber "Active Work" at 87% — honest about 4 missing records
- **project-truth.ts**: Makes all future data updates a single-file change
- **No new dependencies**: All charts use existing Recharts; all animations use
  existing Framer Motion; all icons use existing lucide-react
